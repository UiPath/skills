"""The seeded customer email of the escalation tasks, fed to the agent's inputs.

The Slack-alert, Jira-ticket and orchestrator graders seed the same email
fields under the same role names; each task seeds the roles its prompt names.
`feed_roles` maps them onto the inputs the agent declared by meaning
(`flow_io_roles.map_inputs`), with a fallback object for fields a script reads
off an object input where no `$vars` path shows.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from _shared import flow_io_roles as io
from _shared.flow_check import _SLACK_TS_RE, find_flow_file

SLACK_KEY = "uipath-salesforce-slack"
SLACK_SEND = "send-message-to-channel"
SLACK_CHANNEL = "C0B2FDZD1M3"  # coding-agent-testing

# What each seeded value means, as fragments of an input name.
KEYWORDS = {
    "senderEmail": ["senderemail", "fromemail", "emailaddress", "senderaddress", "fromaddress",
                    "^sender$", "^from$", "email"],
    "senderDomain": ["senderdomain", "emaildomain", "domain"],
    "subject": ["emailsubject", "subject", "title"],
    "body": ["emailbody", "body", "content", "message", "description", "text"],
    "tier": ["customertier", "tier", "plan", "segment", "level"],
    "productionDown": ["productiondown", "proddown", "outage", "production", "down"],
    "workaround": ["workaround"],
    "attachments": ["attachment"],
    "match": ["customermatch", "matchstatus", "matchtype", "matchcount", "matchresult", "matches",
              "matched", "match"],
    "duplicate": ["duplicate", "dup"],
    "caseRef": ["casereference", "correlationid", "caseref", "casekey", "caseid", "casenumber",
                "correlation", "reference", "case", "ref"],
}
# Field names a script may read off an object input where no `$vars` path shows.
FALLBACK_KEYS = {
    "senderEmail": ["senderEmail", "email", "from", "fromEmail", "sender"],
    "senderDomain": ["senderDomain", "domain"],
    "subject": ["subject", "emailSubject"],
    "body": ["body", "emailBody", "content"],
    "tier": ["customerTier", "tier"],
    "productionDown": ["productionDown", "isProductionDown", "prodDown"],
    "workaround": ["workaroundAvailable", "hasWorkaround", "workaround"],
    "attachments": ["hasAttachments"],
    "match": ["customerMatchStatus", "matchStatus", "customerMatch", "match"],
    "duplicate": ["isDuplicate", "duplicate"],
    "caseRef": ["caseReference", "caseRef", "caseId", "correlationId", "reference"],
}


def _stop(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def is_slack_ts(value) -> bool:
    return isinstance(value, str) and bool(_SLACK_TS_RE.match(value.strip()))


def load_flow() -> dict:
    return json.loads(Path(find_flow_file()).read_text(encoding="utf-8"))


def is_match_input(var_id: str) -> bool:
    """True when an input's name means the customer-match state."""
    return io.means([var_id], KEYWORDS["match"]) > 0


def feed_roles(flow: dict, case: dict, values: dict, required, required_any=()) -> dict:
    """The `--inputs` for one case, keyed by the inputs the agent declared.

    Fails, naming the flow's inputs, when a role in `required` (or every role
    of a group in `required_any`) found no input. A yes/no declared as text
    gets "true"/"false", not Python's "True"."""
    roles = {role: {"value": value, "keywords": KEYWORDS[role]} for role, value in values.items()}
    fallback = {key: values[role] for role, keys in FALLBACK_KEYS.items() if role in values for key in keys}
    inputs, _, unmapped = io.map_inputs(flow, roles, object_fallback=fallback, file_path=None)
    missing = [r for r in required if r in unmapped]
    missing += ["/".join(group) for group in required_any if all(r in unmapped for r in group)]
    error = io.unmapped_error(flow, missing, inputs)
    if error:
        _stop(f"{case['name']}: {error}")
    types = input_types(flow)
    return {
        k: v.lower() if types.get(k) == "string" and v in ("True", "False") else v
        for k, v in inputs.items()
    }


def input_types(flow: dict) -> dict[str, str]:
    return {v["id"]: str(v.get("type") or "").lower() for v in io.declared(flow, "in")}


def check_same_outputs(per_case: list[dict[str, list[str]]]) -> None:
    """One output carries each result in every case, not a constant that fit once."""
    for result in per_case[0]:
        if not set.intersection(*(set(h[result]) for h in per_case)):
            _stop(
                f"no single output holds the {result} in every case "
                f"(outputs per case: {[h[result] for h in per_case]})"
            )
