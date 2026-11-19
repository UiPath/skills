#!/usr/bin/env python3
"""BillingResolutionWriter: debug the flow once against the live tenant and
grade the drafted email and the Slack message it really posted.

The prompt names no variables, so the seeded values are mapped onto the flow's
declared inputs by meaning (`flow_io_roles.map_inputs`) and the results are
found among its declared outputs by value:

- the email body: a returned text that mentions MCS-2026-05128 and the credit
  written "USD 2,475.50", is signed "Billing Support Team", is prose rather
  than a serialized JSON object, and came from the executed agent node's own
  output (not a template over the inputs);
- the subject: a one-line text in the output that means the subject by its
  name or description (or under such a key in a returned object);
- the case reference, unchanged: a fresh value per run, so it cannot be baked
  into the flow;
- the Slack message id: a returned Slack ts that is the response of an executed
  Slack send to #coding-agent-testing, whose message starts with the case
  reference and carries the invoice and the body.

The sender identity (bot or user) is not graded.
"""
import json
import os
import re
import sys
from uuid import uuid4

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared import flow_io_roles as io  # noqa: E402
from _shared.escalation_inputs import SLACK_CHANNEL, SLACK_KEY, is_slack_ts  # noqa: E402
from _shared.flow_check import (  # noqa: E402
    _fail,
    _fail_with_capture,
    _get_ci,
    _leaves,
    _load_flow,
    assert_flow_uses_connector_target,
    assert_slack_message_posted,
    completed_node_ids_of_type,
    node_output_leaves,
    run_debug,
)
from _shared.slack_journal import journal_slack_posts  # noqa: E402

INVOICE = "MCS-2026-05128"
CREDIT_TEXT = "USD 2,475.50"
SIGNATURE = "Billing Support Team"
AGENT_TYPES = ("uipath.agent.autonomous", "uipath.core.agent.")
CASE_REF = f"RESO-{uuid4().hex[:12]}"
ROLES = {
    "customer name": {"value": "Northwind Traders", "keywords": [
        "customername", "clientname", "companyname", "recipient", "customer", "client", "name"]},
    "invoice number": {"value": INVOICE, "keywords": [
        "invoicenumber", "invoiceno", "invoiceid", "invoiceref", "invoice"]},
    "approved credit": {"value": 2475.5, "keywords": [
        "creditamount", "approvedcredit", "credit", "amount", "refund", "usd"]},
    "case reference": {"value": CASE_REF, "keywords": [
        "casereference", "caseref", "caseid", "casenumber", "correlation", "case", "reference", "ticket"]},
}


def is_serialized_object(text):
    body = text.strip().strip("`").strip()
    if not body.startswith("{"):
        return False
    try:
        return isinstance(json.loads(body), dict)
    except ValueError:
        return False


def with_json_leaves(leaves):
    """The agent's output strings, plus the strings inside any that are JSON text.
    An agent may return its draft as a JSON string that a script then parses
    (`JSON.parse($vars.<agent>.output.body)`)."""
    out = set(leaves)
    for leaf in leaves:
        try:
            parsed = json.loads(leaf)
        except (TypeError, ValueError):
            continue
        stack = [parsed]
        while stack:
            item = stack.pop()
            if isinstance(item, str):
                out.add(item.strip())
            elif isinstance(item, dict):
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
    return out


def find_body(found, agent_leaves):
    cited = [(k, t) for k, t in found if INVOICE in t and CREDIT_TEXT in t]
    if not cited:
        _fail_with_capture(f"no returned text mentions {INVOICE} and the credit written {CREDIT_TEXT!r}: {found}")
    prose = [(k, t) for k, t in cited if not is_serialized_object(t)]
    if not prose:
        _fail_with_capture(f"the email body is a serialized JSON object, not plain text: {cited}")
    signed = [(k, t) for k, t in prose if SIGNATURE in t]
    if not signed:
        _fail_with_capture(f"the email body is not signed {SIGNATURE!r}: {prose}")
    # From the executed agent, not a template over the inputs: the body is one of
    # the agent's own output strings, or holds one of its long ones verbatim.
    # Either way round: a script may wrap the agent's text, or cut the body out of a
    # longer agent reply ("subject: ...\nbody: ...").
    drafted = [(k, t) for k, t in signed
               if t.strip() in agent_leaves
               or any(len(a) >= 80 and a in t for a in agent_leaves)
               or (len(t.strip()) >= 80 and any(t.strip() in a for a in agent_leaves))]
    if not drafted:
        _fail_with_capture("the email body did not come from the executed agent node's output")
    return drafted[0]


SUBJECT_KEYWORDS = ["emailsubject", "subjectline", "subject", "headline", "title"]


def find_subject(flow, outs, body):
    """The one-line subject, from an output that means it, or such a key inside one."""
    named = [(k, outs[k][1]) for k in io.outs_meaning(flow, SUBJECT_KEYWORDS)]
    nested = [(f"{k}.{key}", val) for k, (_t, v) in outs.items() if isinstance(v, dict)
              for key, val in v.items() if io.means([key], SUBJECT_KEYWORDS)]
    texts = [(k, v) for k, v in named + nested if isinstance(v, str) and v.strip()]
    if not texts:
        _fail_with_capture(f"no declared output is the email subject (by its name or description): {outs}")
    lines = [(k, v) for k, v in texts if "\n" not in v.strip() and v != body]
    if not lines:
        _fail_with_capture(f"the email subject is not a one-line email subject: {texts}")
    return lines[0]


def check_slack_post(payload, outs, body):
    ts_ids = io.find_out(outs, is_slack_ts)
    if not ts_ids:
        _fail_with_capture(f"no declared output is a Slack message ts: {outs}")
    ts = assert_slack_message_posted(
        payload,
        ts_ids[0],
        connector_key=SLACK_KEY,
        expected_channel=SLACK_CHANNEL,
        must_contain=[CASE_REF, INVOICE, body.strip()[:80]],
    )
    globals_ = _get_ci(_get_ci(payload, "variables", "Variables") or {}, "globals", "Globals") or {}
    sent = [x for k, v in globals_.items() if str(k).endswith(".output") and ts in _leaves(v)
            for x in _leaves(v) if isinstance(x, str)]
    if not any(re.match(r"^\W*(?:(?i:subject)\s*:\s*)?" + re.escape(CASE_REF), x.strip()) for x in sent):
        _fail_with_capture(f"the posted Slack message does not start with the case reference {CASE_REF}")
    print(f"OK: Slack message {ts} posted to #coding-agent-testing, starting with {CASE_REF} and carrying the body")


def main():
    flow = _load_flow("**/project.uiproj")
    if not any(h in str(n.get("type", "")) for n in flow.get("nodes") or [] for h in AGENT_TYPES):
        _fail("the flow has no agent node (inline or existing tenant agent)")
    assert_flow_uses_connector_target(SLACK_KEY)
    inputs, _attachments, unmapped = io.map_inputs(flow, ROLES, object_fallback=None, file_path=None)
    if problem := io.unmapped_error(flow, unmapped, inputs):
        _fail(problem)
    print(f"debug inputs: {inputs}")

    # retries=1: the flow posts to a shared Slack channel, so a whole-flow retry
    # would post a duplicate message.
    with journal_slack_posts():
        payload = run_debug(inputs=inputs, timeout=540, retries=1)
    outs = io.out_values(flow, payload)
    print(f"outputs: { {k: v for k, (_t, v) in outs.items()} }")
    found = [(k, t) for k, (_t, v) in outs.items() for t in io.texts(v)]

    agents = set()
    for hint in AGENT_TYPES:
        agents |= completed_node_ids_of_type(payload, hint)
    if not agents:
        _fail_with_capture("no agent node completed in the debug run")
    body_id, body = find_body(found, with_json_leaves(node_output_leaves(payload, agents)))
    print(f"OK: the body ({body_id}) mentions {INVOICE} and {CREDIT_TEXT}, is signed {SIGNATURE!r}, and came from the agent")

    subject_id, subject = find_subject(flow, outs, body)
    print(f"OK: subject ({subject_id}) {subject!r}")

    if not io.find_out(outs, io.equals_exact(CASE_REF)):
        _fail_with_capture(f"no declared output is the case reference {CASE_REF} unchanged: {outs}")
    print(f"OK: the case reference {CASE_REF} came back unchanged")

    check_slack_post(payload, outs, body)


if __name__ == "__main__":
    main()
