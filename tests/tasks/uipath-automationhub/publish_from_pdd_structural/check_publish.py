#!/usr/bin/env python3
"""Grade the Automation Hub publish the agent sent to the mocked `uip ah`.

The mock (`_shared/mock_template/mocks/uip`) appends every invocation to
`mocks/.calls.jsonl` and snapshots each `--file` argument at call time, so the
grade reflects what was actually submitted, not what the files hold after the
run. Each subcommand is one success criterion:

    create-once    exactly one `automations create --from-schema` on the Business Process flow
    payload        required answers resolved from the material and the tenant, not placeholders
    applications   applications match the systems the PDD names: no more, no fewer
    documents      PDD and process map uploaded once each, as the staged bytes, with the right type ids
    verify         attachments and the record read back after the create

Exit 0 = pass; non-zero prints the first failing reason.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CALL_LOG = Path("mocks") / ".calls.jsonl"

IDEA_FLOW_ID = "7"  # "Business Process Flow" in idea_flows_list.json
PROCESS_ID = "4815"  # Data.Id in automations_create.json
OWNER = "dana.reyes@fjordline.example"  # Data.User.Email in auth_info_get.json
ACTIVE_ONBOARDING_CATEGORIES = {11, 12}  # Retail Banking / Account Onboarding
DOC_CODE_PREFIX = "ah-question-answer-option-ovrbp-0-0-4-"
PDD_CODE = DOC_CODE_PREFIX + "0"
NO_DOCUMENTATION_CODE = DOC_CODE_PREFIX + "3"
PDD_TYPE_ID = "1"
PROCESS_MAP_TYPE_IDS = {"6", "9"}  # PM, or MISC when unsure (both allowed by the skill)

# Inventory ids for the PDD systems that the tenant already has.
EXPECTED_APP_IDS = {21, 22}  # Microsoft Dynamics 365, Signicat
# PDD systems missing from the inventory -> must arrive as new_applications.
REQUIRED_NEW_APPS = {"trapets", "scrive", "temenos t24"}
# Named in the PDD and in the inventory: harmless as new_applications (name+version dedupe).
TOLERATED_NEW_APPS = {"microsoft dynamics 365", "signicat"}
# Never named as in-scope: inventory decoys plus the explicitly out-of-scope Avaloq.
FORBIDDEN_APP_WORDS = ("avaloq", "salesforce", "sap", "servicenow")
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
    calls = []
    for line in CALL_LOG.read_text(encoding="utf-8").splitlines():
        if line.strip():
            calls.append(json.loads(line))
    return calls


def is_help(call: dict) -> bool:
    return any(token in ("--help", "-h") for token in call["args"].split())


def calls_matching(calls: list[dict], rule: str) -> list[dict]:
    return [c for c in calls if c.get("matched_rule") == rule and not is_help(c)]


def flag(call: dict, name: str) -> str | None:
    tokens = call["args"].split()
    for i, token in enumerate(tokens):
        if token == name and i + 1 < len(tokens):
            return tokens[i + 1].strip("\"'")
        if token.startswith(name + "="):
            return token[len(name) + 1 :].strip("\"'")
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


def check_create_once(calls: list[dict]) -> str:
    create = the_create(calls)
    if "--from-schema" not in create["args"].split():
        raise CheckFailed("create did not use --from-schema")
    if flag(create, "--idea-flow-id") != IDEA_FLOW_ID:
        raise CheckFailed(f"create targeted idea flow {flag(create, '--idea-flow-id')}, not the Business Process flow ({IDEA_FLOW_ID})")
    return "one create on the Business Process flow"


def check_payload(calls: list[dict]) -> str:
    answers = submitted_answers(the_create(calls))
    serialized = json.dumps(answers).lower()
    leftover = [p for p in PLACEHOLDERS if p in serialized]
    if leftover:
        raise CheckFailed(f"template placeholders submitted: {leftover}")

    name = value_of(answers, "OVR-OVERVIEW_NAME")
    if not isinstance(name, str) or "retail account onboarding" not in name.lower():
        raise CheckFailed(f"process name {name!r} is not the PDD's process")
    description = value_of(answers, "OVR-OVERVIEW_DESCRIPTION")
    if not isinstance(description, str) or len(description.strip()) < 20:
        raise CheckFailed(f"description missing or too thin: {description!r}")
    category = value_of(answers, "OVR-OVERVIEW_CATEGORY")
    if category not in ACTIVE_ONBOARDING_CATEGORIES:
        raise CheckFailed(f"category {category!r} is not an active onboarding category {sorted(ACTIVE_ONBOARDING_CATEGORIES)}")

    for key in ("OVR-PROCESS_OWNER", "OVR-OVERVIEW_PROCESS_SUBMITTER"):
        if answers.get(key) != OWNER:
            raise CheckFailed(f"{key} must be the auth-info email as a direct string, got {answers.get(key)!r}")

    codes = value_of(answers, "OVR-PROCESS_DOCUMENTS")
    if not isinstance(codes, list) or not codes:
        raise CheckFailed(f"documentation answer missing: {codes!r}")
    unknown = [c for c in codes if not re.fullmatch(re.escape(DOC_CODE_PREFIX) + r"[0-3]", str(c))]
    if unknown:
        raise CheckFailed(f"documentation codes not verbatim from the schema enum: {unknown}")
    if PDD_CODE not in codes or NO_DOCUMENTATION_CODE in codes:
        raise CheckFailed(f"documentation answer does not record the PDD: {codes}")
    return "required answers resolved from the material and tenant"


def normalized(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip().lower()


def check_applications(calls: list[dict]) -> str:
    answers = submitted_answers(the_create(calls))
    apps = answers.get("OVR-COUNT_APPS")
    if not isinstance(apps, dict):
        raise CheckFailed("Applications used (required on this tenant) was not answered")

    ids = set(apps.get("value") or [])
    if ids != EXPECTED_APP_IDS:
        raise CheckFailed(f"inventory ids {sorted(ids)} != PDD systems in the inventory {sorted(EXPECTED_APP_IDS)}")

    entries = apps.get("new_applications") or []
    if not isinstance(entries, list) or len(entries) > 20:
        raise CheckFailed("new_applications must be a list of at most 20 entries")
    names = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) - NEW_APP_KEYS:
            raise CheckFailed(f"new_applications entry has unknown keys: {entry}")
        name = entry.get("application_name")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 50:
            raise CheckFailed(f"new_applications entry needs a 1-50 char application_name: {entry}")
        names.add(normalized(name))

    missing = [want for want in REQUIRED_NEW_APPS if not any(want in got for got in names)]
    if missing:
        raise CheckFailed(f"PDD systems missing from new_applications: {sorted(missing)}")
    allowed = REQUIRED_NEW_APPS | TOLERATED_NEW_APPS
    invented = sorted(n for n in names if not any(a in n for a in allowed))
    if invented:
        raise CheckFailed(f"new_applications names systems the PDD does not: {invented}")

    thin = value_of(answers, "OVR-COUNT_THIN_APPS")
    if thin:
        raise CheckFailed(f"thin applications answered although the PDD names none: {thin}")
    text = json.dumps(apps).lower()
    leaked = [w for w in FORBIDDEN_APP_WORDS if re.search(rf"\b{w}\b", text)]
    if leaked:
        raise CheckFailed(f"out-of-scope or decoy systems in the applications answer: {leaked}")
    return "applications match the PDD's systems exactly"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_documents(calls: list[dict]) -> str:
    uploads = calls_matching(calls, "ah documents create")
    expected = {
        "PDD": (sha256_of(FIXTURES / "pdd-retail-account-onboarding.md"), {PDD_TYPE_ID}),
        "process map": (sha256_of(FIXTURES / "process-map-retail-account-onboarding.bpmn"), PROCESS_MAP_TYPE_IDS),
    }
    for label, (digest, type_ids) in expected.items():
        matches = [u for u in uploads if (u.get("captured") or {}).get("sha256") == digest]
        if len(matches) != 1:
            raise CheckFailed(f"{label}: expected one upload of the staged file's exact bytes, got {len(matches)}")
        upload = matches[0]
        if positional_after(upload, "create") != PROCESS_ID:
            raise CheckFailed(f"{label} attached to {positional_after(upload, 'create')!r}, not the created process {PROCESS_ID}")
        if flag(upload, "--document-type-id") not in type_ids:
            raise CheckFailed(f"{label} document type id {flag(upload, '--document-type-id')!r} not in {sorted(type_ids)}")
    if len(uploads) != len(expected):
        raise CheckFailed(f"expected {len(expected)} document uploads, got {len(uploads)}")
    return "PDD (type 1) and process map uploaded once each, byte-identical"


def check_verify(calls: list[dict]) -> str:
    created_at = the_create(calls)["ts"]
    reads = {
        "documents list": [c for c in calls_matching(calls, "ah documents list")
                           if positional_after(c, "list") == PROCESS_ID and c["ts"] > created_at],
        "automations get": [c for c in calls_matching(calls, "ah automations get")
                            if positional_after(c, "get") == PROCESS_ID and c["ts"] > created_at],
    }
    missing = [name for name, hits in reads.items() if not hits]
    if missing:
        raise CheckFailed(f"no post-create read-back of process {PROCESS_ID}: {missing}")
    return "attachments and record read back after the create"


CHECKS = {
    "create-once": check_create_once,
    "payload": check_payload,
    "applications": check_applications,
    "documents": check_documents,
    "verify": check_verify,
}


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in CHECKS:
        print(f"usage: {argv[0]} {{{'|'.join(CHECKS)}}}", file=sys.stderr)
        return 2
    try:
        print("OK:", CHECKS[argv[1]](load_calls()))
        return 0
    except CheckFailed as failure:
        print("FAIL:", failure)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
