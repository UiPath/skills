#!/usr/bin/env python3
"""Grade the Automation Hub publish the agent SUBMITTED to the live tenant.

The agent's `uip` is the real CLI behind `.uip-recorder/uip`, which appends every
call to `.uip-recorder/.calls.jsonl` and snapshots each `--file` before the call
runs. The tenant's read-back normalizes a record (it cannot tell an application
attached by inventory id from one created by name), so the grade reads the payload
as sent. Expectations come from `seed.json`: preflight_ah.py's snapshot of the
tenant at the start of the run (owner, flow, inventory, categories) and
seed_publish.py's token and staged-file digests. Each subcommand is one criterion:

    create-once    exactly one successful `automations create --from-schema` on the Business Process flow
    payload        required answers resolved from the material and the tenant, not placeholders
    applications   applications match the systems the PDD names: no more, no fewer
    documents      PDD and process map uploaded once each, as the staged bytes, with the right type ids
    verify         attachments and the record read back after the create
    users          every owner lookup (if any) is server-side and carries --invite-status all

Exit 0 = pass; non-zero prints the first failing reason.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CALL_LOG = Path(".uip-recorder") / ".calls.jsonl"
SEED_FILE = Path("seed.json")
PDD_FIXTURE = "pdd-retail-account-onboarding.md"
MAP_FIXTURE = "process-map-retail-account-onboarding.bpmn"

# "Documentation available" options on the Business Process flow: 0 work
# instructions, 1 SOP, 2 process maps/flowcharts, 3 input files, 4 output files,
# 5 misc, 6 none, 7 don't know. No option says "PDD", so WHICH codes describe a
# PDD + BPMN hand-off is the agent's call; claiming "none" or "don't know" with two
# documents in hand never is.
DOC_CODE_PREFIX = "ah-answer_option-ovrbp-0-3-0-"
NO_DOCUMENTATION_CODES = {DOC_CODE_PREFIX + "6", DOC_CODE_PREFIX + "7"}
PDD_TYPE_ID = "1"
PROCESS_MAP_TYPE_IDS = {"6", "9"}  # PM, or MISC when unsure (both allowed by the skill)

# The systems the fixture PDD names, normalized. Avaloq is named too, but as out of scope.
PDD_SYSTEMS = ("microsoft dynamics 365", "signicat", "trapets", "scrive", "temenos t24")
OUT_OF_SCOPE = ("avaloq",)
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


def the_create(calls: list[dict]) -> dict:
    creates = calls_matching(calls, "ah automations create")
    if len(creates) != 1:
        raise CheckFailed(f"expected exactly 1 automations create, got {len(creates)}")
    return creates[0]


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
    """The PDD system an application name stands for, if any."""
    text = normalized(name)
    return next((system for system in PDD_SYSTEMS if system in text), None)


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
    return f"one successful create on the Business Process flow (process {created_id(calls)})"


def check_payload(calls: list[dict], seed: dict) -> str:
    answers = submitted_answers(the_create(calls))
    serialized = json.dumps(answers).lower()
    leftover = [p for p in PLACEHOLDERS if p in serialized]
    if leftover:
        raise CheckFailed(f"template placeholders submitted: {leftover}")

    name = value_of(answers, "OVR-OVERVIEW_NAME")
    if not isinstance(name, str) or "retail account onboarding" not in name.lower():
        raise CheckFailed(f"process name {name!r} is not the PDD's process")
    if seed.get("run_token") and seed["run_token"] not in name:
        raise CheckFailed(f"process name {name!r} dropped the PDD's reference code {seed['run_token']}")
    description = value_of(answers, "OVR-OVERVIEW_DESCRIPTION")
    if not isinstance(description, str) or len(description.strip()) < 20:
        raise CheckFailed(f"description missing or too thin: {description!r}")
    category = as_int(value_of(answers, "OVR-OVERVIEW_CATEGORY"))
    if category not in set(seed.get("active_category_ids") or []):
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
        raise CheckFailed(f"documentation answer claims none/don't know despite two attached documents: {codes}")
    return "required answers resolved from the material and tenant"


def applications_answer(answers: dict) -> dict:
    apps = answers.get("OVR-COUNT_APPS")
    if not isinstance(apps, dict):
        raise CheckFailed("Applications used was not answered, although the PDD names five systems")
    thin = value_of(answers, "OVR-COUNT_THIN_APPS")
    if thin:
        raise CheckFailed(f"thin applications answered although the PDD names none: {thin}")
    leaked = [w for w in OUT_OF_SCOPE if re.search(rf"\b{w}\b", json.dumps(apps).lower())]
    if leaked:
        raise CheckFailed(f"the PDD's out-of-scope system is in the applications answer: {leaked}")
    return apps


def attached_systems(apps: dict, by_system: dict[str, set[int]]) -> set[str]:
    """The PDD systems the submitted inventory ids stand for; any other id is a decoy."""
    allowed = {app_id: system for system, ids in by_system.items() for app_id in ids}
    ids = {as_int(i) for i in apps.get("value") or []}
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
    by_id = attached_systems(apps, by_system)
    by_name = new_application_systems(apps)

    # Systems the inventory held should come by id (by name dedupes server-side, so it
    # is tolerated); the ones it lacked can only come by name.
    missing = sorted(set(PDD_SYSTEMS) - by_id - by_name)
    if missing:
        raise CheckFailed(f"PDD systems left out of the applications answer: {missing} "
                          f"(inventory held {sorted(by_system)} at the start of the run)")
    return (f"all {len(PDD_SYSTEMS)} PDD systems answered: {len(by_id)} by inventory id, "
            f"{len(by_name - by_id)} by name")


def check_documents(calls: list[dict], seed: dict) -> str:
    process_id = created_id(calls)
    uploads = calls_matching(calls, "ah documents create")
    digests = seed.get("fixtures") or {}
    expected = {
        "PDD": (digests.get(PDD_FIXTURE), {PDD_TYPE_ID}),
        "process map": (digests.get(MAP_FIXTURE), PROCESS_MAP_TYPE_IDS),
    }
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
    return "PDD (type 1) and process map uploaded once each, byte-identical"


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


CHECKS = {
    "create-once": check_create_once,
    "payload": check_payload,
    "applications": check_applications,
    "documents": check_documents,
    "verify": check_verify,
    "users": check_users,
}


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in CHECKS:
        print(f"usage: {argv[0]} {{{'|'.join(CHECKS)}}}", file=sys.stderr)
        return 2
    try:
        print("OK:", CHECKS[argv[1]](load_calls(), load_seed()))
        return 0
    except CheckFailed as failure:
        print("FAIL:", failure)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
