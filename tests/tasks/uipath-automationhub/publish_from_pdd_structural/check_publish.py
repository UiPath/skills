#!/usr/bin/env python3
"""Grade the Automation Hub publish the agent SUBMITTED to the live tenant.

The agent's `uip` is the real CLI behind `.uip-recorder/uip`, which appends every
call to `.uip-recorder/.calls.jsonl` and snapshots each `--file` before the call
runs. The tenant's read-back normalizes a record (it cannot tell an application
attached by inventory id from one created by name), so the grade reads the payload
as sent. Expectations come from `seed.json`: preflight_ah.py's snapshot of the
tenant at the start of the run (owner, flow, inventory, categories) and
seed_publish.py's token and staged-file digests. What the PDD itself implies (its
process name, the systems it names, which documents to attach) comes from an
expectation manifest outside the sandbox, so the agent cannot read the answer key:
`--expect <file>`, default `expected.json` beside this script. Each subcommand is
one criterion:

    create-once    exactly one successful `automations create --from-schema` on the Business Process flow
                   (a rejected attempt before it is fine; nothing after it)
    payload        required answers resolved from the material and the tenant, not placeholders
    applications   applications match the systems the PDD names: no more, no fewer
    documents      PDD and process map uploaded once each, as the staged bytes, with the right type ids
    verify         attachments and the record read back after the create
    users          every owner lookup (if any) is server-side and carries --invite-status all
    fallback       (publish_from_pdd_403_fallback) admin upsert attempted once, refused, published anyway

Usage: check_publish.py <check> [--expect <manifest.json>]

Exit 0 = pass; non-zero prints the first failing reason.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

CALL_LOG = Path(".uip-recorder") / ".calls.jsonl"
SETUP_DIR = Path(__file__).resolve().parent.parent / "_setup"
SEED_FILE = Path("seed.json")
DEFAULT_EXPECT = Path(__file__).resolve().parent / "expected.json"

# "Documentation available" options on the Business Process flow: 0 work
# instructions, 1 SOP, 2 process maps/flowcharts, 3 input files, 4 output files,
# 5 misc, 6 none, 7 don't know. No option says "PDD", so WHICH codes describe a
# PDD + BPMN hand-off is the agent's call; claiming "none" or "don't know" with two
# documents in hand never is.
DOC_CODE_PREFIX = "ah-answer_option-ovrbp-0-3-0-"
NO_DOCUMENTATION_CODES = {DOC_CODE_PREFIX + "6", DOC_CODE_PREFIX + "7"}
# Document type ids per staged document role: PDD 1, SDD 2; a process map is PM (6)
# or MISC (9) when unsure (both allowed by the skill).
DOCUMENT_TYPE_IDS = {"pdd": {"1"}, "sdd": {"2"}, "process_map": {"6", "9"}}
DOCUMENT_LABELS = {"pdd": "PDD", "sdd": "SDD", "process_map": "process map"}
NEW_APP_KEYS = {
    "application_name",
    "application_version",
    "application_language",
    "application_is_citrix_client",
    "application_comments",
}
PLACEHOLDERS = ("sample input", "first.last@example.com", "example.com")


class CheckFailed(Exception):
    pass


@dataclass(frozen=True)
class Expectation:
    """What one fixture PDD implies, from its manifest.

    `systems` must all be answered; `optional_systems` (generic or future-state rows
    of the PDD's systems table) may be answered or left out. Each maps a canonical
    name to the lower-case aliases that identify it inside an application name.
    Anything else is a system the PDD does not name.
    """

    name_contains: str
    documents: dict[str, str]
    systems: dict[str, tuple[str, ...]] = field(default_factory=dict)
    optional_systems: dict[str, tuple[str, ...]] = field(default_factory=dict)
    out_of_scope: tuple[str, ...] = ()
    # The tenant's own "Other" category is an honest answer when its tree has no node
    # for the process's domain (the default AH taxonomy has no healthcare or telco).
    allow_other_category: bool = False

    @property
    def allowed(self) -> dict[str, tuple[str, ...]]:
        return {**self.optional_systems, **self.systems}


def load_expectation(path: Path) -> Expectation:
    if not path.is_file():
        raise CheckFailed(f"expectation manifest {path} missing")
    raw = json.loads(path.read_text(encoding="utf-8"))
    def aliases(table: dict) -> dict[str, tuple[str, ...]]:
        return {normalized(name): tuple(normalized(a) for a in (names or [name])) for name, names in table.items()}
    documents = {role: raw["documents"][role] for role in DOCUMENT_TYPE_IDS if raw["documents"].get(role)}
    if "pdd" not in documents:
        raise CheckFailed(f"{path} names no PDD document")
    return Expectation(
        name_contains=normalized(raw["name_contains"]),
        documents=documents,
        systems=aliases(raw.get("systems") or {}),
        optional_systems=aliases(raw.get("optional_systems") or {}),
        out_of_scope=tuple(normalized(s) for s in raw.get("out_of_scope") or []),
        allow_other_category=bool(raw.get("allow_other_category")),
    )


EXPECT: Expectation  # set by main() from --expect


def load_calls() -> list[dict]:
    if not CALL_LOG.is_file():
        raise CheckFailed(f"{CALL_LOG} missing: the agent never invoked uip")
    return [json.loads(line) for line in CALL_LOG.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_seed() -> dict:
    if not SEED_FILE.is_file():
        raise CheckFailed(f"{SEED_FILE} missing: pre_run preflight/seed did not run")
    return json.loads(SEED_FILE.read_text(encoding="utf-8"))


def is_help(call: dict) -> bool:
    return any(token in ("--help", "-h") for token in call["args"].split())


def calls_matching(calls: list[dict], verb: str) -> list[dict]:
    """Calls whose argv carries `verb` as a contiguous token run (help lookups excluded)."""
    return [c for c in calls if f" {verb} " in f" {c['args']} " and not is_help(c)]


def flag(call: dict, name: str) -> str | None:
    tokens = call["args"].split()
    for i, token in enumerate(tokens):
        if token == name and i + 1 < len(tokens):
            return tokens[i + 1].strip("\"'")
        if token.startswith(name + "="):
            return token[len(name) + 1:].strip("\"'")
    return None


def positional_after(call: dict, verb: str) -> str | None:
    tokens = call["args"].split()
    if verb in tokens:
        index = tokens.index(verb)
        if index + 1 < len(tokens):
            return tokens[index + 1].strip("\"'")
    return None


# A rejected create (CLI usage error or the service's validation) creates nothing, and
# the skill says to fix it and retry; a success must never be re-run.
MAX_REJECTED_CREATES = 2


def the_create(calls: list[dict]) -> dict:
    """The one create that counts: the successful one, else the last attempt."""
    creates = calls_matching(calls, "ah automations create")
    if not creates:
        raise CheckFailed("expected exactly 1 automations create, got 0")
    success = next((c for c in creates if c.get("result") == "Success"), None)
    if success is None:
        return creates[-1]
    after = creates[creates.index(success) + 1:]
    if after:
        raise CheckFailed(f"expected exactly 1 successful automations create: {len(after)} more after it "
                          f"(a success is never re-run)")
    rejected = len(creates) - 1
    if rejected > MAX_REJECTED_CREATES:
        raise CheckFailed(f"{rejected} rejected creates before the success; fix locally and retry once, not by trial")
    return success


def created_id(calls: list[dict]) -> str:
    create = the_create(calls)
    if create.get("result") != "Success" or create.get("data_id") is None:
        raise CheckFailed(f"the create did not succeed on the tenant (exit {create.get('exit_code')}, "
                          f"result {create.get('result')!r})")
    return str(create["data_id"])


def submitted_answers(create: dict) -> dict:
    captured = create.get("captured") or {}
    document = captured.get("json")
    if not isinstance(document, dict):
        raise CheckFailed(f"create --file was not a readable JSON answers file: {captured}")
    # The CLI accepts the whole schema-get document or just the answers map.
    answers = document.get("user_inputs", document)
    flat: dict = {}
    for assessment in answers.values():
        if not isinstance(assessment, dict):
            continue
        for section in assessment.values():
            if isinstance(section, dict):
                flat.update(section)
    if not flat:
        raise CheckFailed("answers file has no assessment > section > question answers")
    return flat


def value_of(answers: dict, key: str):
    answer = answers.get(key)
    return answer.get("value") if isinstance(answer, dict) else None


def as_int(value):
    """Ids are `number` in the schema, but a `"12"` the agent copied from CLI text is the same id."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return value


def normalized(name: str) -> str:
    return re.sub(r"\s+", " ", str(name)).strip().lower()


def system_of(name: str) -> str | None:
    """The PDD system (required or optional) an application name stands for, if any."""
    text = normalized(name)
    return next((system for system, names in EXPECT.allowed.items() if any(a in text for a in names)), None)


def inventory_by_system(seed: dict) -> dict[str, set[int]]:
    """PDD system -> the inventory ids that carry it, as the tenant stood at the start of the run."""
    found: dict[str, set[int]] = {}
    for app in seed.get("inventory") or []:
        system = system_of(app.get("Name", ""))
        if system:
            found.setdefault(system, set()).add(as_int(app.get("Id")))
    return found


def check_create_once(calls: list[dict], seed: dict) -> str:
    create = the_create(calls)
    if "--from-schema" not in create["args"].split():
        raise CheckFailed("create did not use --from-schema")
    flow_id = str(seed.get("business_process_flow_id"))
    if flag(create, "--idea-flow-id") != flow_id:
        raise CheckFailed(f"create targeted idea flow {flag(create, '--idea-flow-id')}, "
                          f"not the Business Process flow ({flow_id})")
    retries = len(calls_matching(calls, "ah automations create")) - 1
    note = f" after {retries} rejected attempt(s)" if retries else ""
    return f"one successful create on the Business Process flow (process {created_id(calls)}){note}"


def check_payload(calls: list[dict], seed: dict) -> str:
    answers = submitted_answers(the_create(calls))
    serialized = json.dumps(answers).lower()
    leftover = [p for p in PLACEHOLDERS if p in serialized]
    if leftover:
        raise CheckFailed(f"template placeholders submitted: {leftover}")

    name = value_of(answers, "OVR-OVERVIEW_NAME")
    if not isinstance(name, str) or EXPECT.name_contains not in normalized(name):
        raise CheckFailed(f"process name {name!r} is not the PDD's process")
    if seed.get("run_token") and seed["run_token"] not in name:
        raise CheckFailed(f"process name {name!r} dropped the PDD's reference code {seed['run_token']}")
    description = value_of(answers, "OVR-OVERVIEW_DESCRIPTION")
    if not isinstance(description, str) or len(description.strip()) < 20:
        raise CheckFailed(f"description missing or too thin: {description!r}")
    category = as_int(value_of(answers, "OVR-OVERVIEW_CATEGORY"))
    allowed_categories = set(seed.get("active_category_ids") or [])
    if EXPECT.allow_other_category:
        allowed_categories |= set(seed.get("other_category_ids") or [])
    if category not in allowed_categories:
        state = "archived or 'Other'" if category in set(seed.get("category_ids") or []) else "not on this tenant"
        raise CheckFailed(f"category {category!r} is {state}; the publish needs an active category")

    # User questions take the email as a direct string; the server also accepts the
    # `{"value": <email>}` wrapper for them. Either shape passes.
    owner = seed.get("owner_email")
    for key in ("OVR-PROCESS_OWNER", "OVR-OVERVIEW_PROCESS_SUBMITTER"):
        if answers.get(key) != owner and value_of(answers, key) != owner:
            raise CheckFailed(f"{key} must be the auth-info email {owner!r} (bare or value-wrapped), "
                              f"got {answers.get(key)!r}")

    codes = value_of(answers, "OVR-PROCESS_DOCUMENTS")
    if not isinstance(codes, list) or not codes:
        raise CheckFailed(f"documentation answer missing: {codes!r}")
    unknown = [c for c in codes if not re.fullmatch(re.escape(DOC_CODE_PREFIX) + r"[0-7]", str(c))]
    if unknown:
        raise CheckFailed(f"documentation codes not verbatim from the schema enum: {unknown}")
    if NO_DOCUMENTATION_CODES & set(codes):
        raise CheckFailed(f"documentation answer claims none/don't know despite {len(EXPECT.documents)} "
                          f"attached document(s): {codes}")
    return "required answers resolved from the material and tenant"


def applications_answer(answers: dict) -> dict:
    apps = answers.get("OVR-COUNT_APPS")
    if apps is None and not EXPECT.systems:
        apps = {}
    if not isinstance(apps, dict):
        raise CheckFailed(f"Applications used was not answered, although the PDD names "
                          f"{len(EXPECT.systems)} system(s)")
    thin = value_of(answers, "OVR-COUNT_THIN_APPS")
    if thin:
        raise CheckFailed(f"thin applications answered although the PDD names none: {thin}")
    leaked = [w for w in EXPECT.out_of_scope if re.search(rf"\b{re.escape(w)}\b", json.dumps(apps).lower())]
    if leaked:
        raise CheckFailed(f"the PDD's out-of-scope system is in the applications answer: {leaked}")
    return apps


def live_inventory() -> list[dict]:
    """The tenant's inventory now, read through the harness helper (never recorded).

    Only consulted for ids the start-of-run snapshot lacks: on a shared tenant a
    parallel run (or this one's earlier attempt) can add an application the agent
    then lists and selects by id, which is correct, not a decoy.
    """
    sys.path.insert(0, str(SETUP_DIR))
    from ah_cli import items, succeeded, uip_json  # noqa: PLC0415

    listing = uip_json(["ah", "applications", "list", "--limit", "500"])
    return items(listing) if succeeded(listing) else []


def attached_systems(apps: dict, by_system: dict[str, set[int]], seed: dict) -> set[str]:
    """The PDD systems the submitted inventory ids stand for; any other id is a decoy."""
    allowed = {app_id: system for system, ids in by_system.items() for app_id in ids}
    ids = {as_int(i) for i in apps.get("value") or []}
    snapshot = {as_int(app.get("Id")) for app in seed.get("inventory") or []}
    if ids - snapshot:
        for app in live_inventory():
            system = system_of(app.get("Name", ""))
            if system and as_int(app.get("Id")) in ids:
                allowed.setdefault(as_int(app.get("Id")), system)
    decoys = sorted(map(str, ids - set(allowed)))
    if decoys:
        raise CheckFailed(f"inventory ids {decoys} are not systems the PDD names")
    return {allowed[i] for i in ids}


def new_application_systems(apps: dict) -> set[str]:
    entries = apps.get("new_applications") or []
    if not isinstance(entries, list) or len(entries) > 20:
        raise CheckFailed("new_applications must be a list of at most 20 entries")
    systems = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) - NEW_APP_KEYS:
            raise CheckFailed(f"new_applications entry has unknown keys: {entry}")
        name = entry.get("application_name")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 50:
            raise CheckFailed(f"new_applications entry needs a 1-50 char application_name: {entry}")
        system = system_of(name)
        if system is None:
            raise CheckFailed(f"new_applications names a system the PDD does not: {name!r}")
        systems.add(system)
    return systems


def check_applications(calls: list[dict], seed: dict) -> str:
    answers = submitted_answers(the_create(calls))
    apps = applications_answer(answers)
    by_system = inventory_by_system(seed)
    by_id = attached_systems(apps, by_system, seed)
    by_name = new_application_systems(apps)

    # Systems the inventory held should come by id (by name dedupes server-side, so it
    # is tolerated); the ones it lacked can only come by name.
    missing = sorted(set(EXPECT.systems) - by_id - by_name)
    if missing:
        raise CheckFailed(f"PDD systems left out of the applications answer: {missing} "
                          f"(inventory held {sorted(by_system)} at the start of the run)")
    optional = len((by_id | by_name) - set(EXPECT.systems))
    return (f"all {len(EXPECT.systems)} required PDD systems answered ({optional} optional too): "
            f"{len(by_id)} by inventory id, {len(by_name - by_id)} by name")


def check_documents(calls: list[dict], seed: dict) -> str:
    process_id = created_id(calls)
    uploads = calls_matching(calls, "ah documents create")
    digests = seed.get("fixtures") or {}
    expected = {DOCUMENT_LABELS[role]: (digests.get(path), DOCUMENT_TYPE_IDS[role])
                for role, path in EXPECT.documents.items()}
    for label, (digest, type_ids) in expected.items():
        if not digest:
            raise CheckFailed(f"seed.json has no digest for the {label}; seed_publish.py did not render it")
        matches = [u for u in uploads if (u.get("captured") or {}).get("sha256") == digest]
        if len(matches) != 1:
            raise CheckFailed(f"{label}: expected one upload of the staged file's exact bytes, got {len(matches)}")
        upload = matches[0]
        if positional_after(upload, "create") != process_id:
            raise CheckFailed(f"{label} attached to {positional_after(upload, 'create')!r}, "
                              f"not the created process {process_id}")
        if flag(upload, "--document-type-id") not in type_ids:
            raise CheckFailed(f"{label} document type id {flag(upload, '--document-type-id')!r} not in {sorted(type_ids)}")
        if upload.get("result") != "Success":
            raise CheckFailed(f"{label} upload did not succeed on the tenant (result {upload.get('result')!r})")
    if len(uploads) != len(expected):
        raise CheckFailed(f"expected {len(expected)} document uploads, got {len(uploads)}")
    return f"{', '.join(expected)} uploaded once each, byte-identical, with the right type ids"


def check_verify(calls: list[dict], seed: dict) -> str:
    process_id = created_id(calls)
    created_at = the_create(calls)["ts"]
    reads = {
        "documents list": [c for c in calls_matching(calls, "ah documents list")
                           if positional_after(c, "list") == process_id and c["ts"] > created_at],
        "automations get": [c for c in calls_matching(calls, "ah automations get")
                            if positional_after(c, "get") == process_id and c["ts"] > created_at],
    }
    missing = [name for name, hits in reads.items() if not hits]
    if missing:
        raise CheckFailed(f"no post-create read-back of process {process_id}: {missing}")
    return "attachments and record read back after the create"


def check_users(calls: list[dict], seed: dict) -> str:
    """The owner lookup is optional, but when it happens it must not hide eligible users.

    RPANAV-19110 changed `GET /users` to default to active users only; the skill
    must pass `--invite-status all` (and keep the lookup server-side with
    `--search`) rather than re-introduce a client-side eligibility pre-check.
    """
    lookups = calls_matching(calls, "users list")
    if not lookups:
        return "no owner lookup — the auth-info email was used directly"
    for call in lookups:
        if flag(call, "--invite-status") != "all":
            raise CheckFailed(f"users list without --invite-status all hides eligible owners: {call['args']}")
        if flag(call, "--search") is None:
            raise CheckFailed(f"users list without --search pages the whole directory client-side: {call['args']}")
    return f"{len(lookups)} owner lookup(s), each server-side with --invite-status all"


def check_fallback(calls: list[dict], seed: dict) -> str:
    """RPANAV-19120: applications never block the publish.

    Used by publish_from_pdd_403_fallback, on a tenant whose schema lacks
    `new_applications` and whose identity cannot manage the inventory: the skill's
    only route to the missing systems is the admin upsert, which the tenant refuses.
    The expected shape is attempt -> refused -> publish anyway, gap stated.
    """
    if seed.get("new_applications_offered"):
        raise CheckFailed("environment: this tenant's schema offers new_applications, so the fallback is unreachable")
    create = the_create(calls)
    attempts = calls_matching(calls, "ah applications update")
    if not attempts:
        raise CheckFailed("the admin applications upsert was never attempted, so the fallback was not exercised")
    create_index = calls.index(create)
    late = [a for a in attempts if calls.index(a) > create_index]
    if late:
        raise CheckFailed(f"applications update retried after the create ({len(late)} call(s)); a refusal is final")
    if len(attempts) > 1:
        raise CheckFailed(f"applications update attempted {len(attempts)} times; one attempt, then fall through")
    if attempts[0].get("result") == "Success":
        raise CheckFailed("environment: the applications upsert succeeded, so this identity is not the "
                          "non-admin the scenario needs")
    created_id(calls)

    answers = submitted_answers(create)
    apps = applications_answer(answers)
    if "new_applications" in apps:
        raise CheckFailed("new_applications sent although this tenant's schema does not offer it")
    by_system = inventory_by_system(seed)
    by_id = attached_systems(apps, by_system, seed)
    dropped = sorted(set(by_system) - by_id)
    if dropped:
        raise CheckFailed(f"PDD systems the inventory held were not attached: {dropped}")

    absent = sorted(set(EXPECT.systems) - set(by_system))
    description = value_of(answers, "OVR-OVERVIEW_DESCRIPTION")
    text = description.lower() if isinstance(description, str) else ""
    unnamed = [system for system in absent if system not in text]
    if unnamed:
        raise CheckFailed(f"description does not name the systems that could not be attached: {unnamed}")
    return (f"upsert attempted once and refused; published with {len(by_id)} inventory system(s), "
            f"gap named: {absent}")


CHECKS = {
    "create-once": check_create_once,
    "payload": check_payload,
    "applications": check_applications,
    "documents": check_documents,
    "verify": check_verify,
    "users": check_users,
    "fallback": check_fallback,
}


def main(argv: list[str]) -> int:
    global EXPECT
    args = argv[1:]
    expect_path = DEFAULT_EXPECT
    if len(args) == 3 and args[1] == "--expect":
        expect_path = Path(args[2])
        args = args[:1]
    if len(args) != 1 or args[0] not in CHECKS:
        print(f"usage: {argv[0]} {{{'|'.join(CHECKS)}}} [--expect <manifest.json>]", file=sys.stderr)
        return 2
    try:
        EXPECT = load_expectation(expect_path)
        print("OK:", CHECKS[args[0]](load_calls(), load_seed()))
        return 0
    except CheckFailed as failure:
        print("FAIL:", failure)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
