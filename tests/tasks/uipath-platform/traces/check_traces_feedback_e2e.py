#!/usr/bin/env python3
"""Assert feedback round-trip: create → get returns same ID with IsPositive=True, SpanId=agent span."""
import json
import sys
from pathlib import Path


def load(path: str) -> dict:
    p = Path(path)
    if not p.is_file():
        sys.exit(f"FAIL: {path} not found")
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def get_id(data: dict) -> str | None:
    return data.get("Id") or data.get("id")

def get_span_id(data: dict) -> str | None:
    return data.get("SpanId") or data.get("spanId")

def get_is_positive(data: dict) -> bool | None:
    v = data.get("IsPositive")
    return v if v is not None else data.get("isPositive")

def normalize_span_id(span_id: str) -> str:
    """Normalize span ID to 32-char hex for comparison.

    Handles two formats the platform uses:
    - 16-char hex:  2191742ea24ef7f8
    - GUID padded:  00000000-0000-0000-2191-742ea24ef7f8
    Both represent the same span — backend zero-pads hex into GUID form.
    """
    return span_id.replace("-", "").lower().zfill(32)

def find_agent_span(span_list: list) -> tuple[dict | None, str]:
    """Return (span, reason) for the best agent-level span to attach feedback to.

    Strategy:
    1. Span whose Attributes JSON contains "type": "agentRun"
       — set by uipath_agents InstrumentedRuntime; present on RPA-launched agents.
       For that trace shape (RobotJob → RunAgent → Agent run → LLM call),
       this correctly picks "Agent run" rather than the "RobotJob" root.
    2. Fallback: root span (ParentId=null)
       — correct for directly-invoked LangGraph/LlamaIndex agents where the
       framework root IS the agent execution span.
    """
    root = None
    for s in span_list:
        if root is None and s.get("ParentId") is None:
            root = s
        attrs_raw = s.get("Attributes") or s.get("attributes") or ""
        try:
            attrs = json.loads(attrs_raw) if isinstance(attrs_raw, str) else attrs_raw
            if isinstance(attrs, dict) and attrs.get("type") == "agentRun":
                return s, "agentRun attribute"
        except (json.JSONDecodeError, TypeError):
            pass
    if root is None:
        return None, "no agentRun span and no root span found"
    return root, "root span (ParentId=null)"


spans = load("spans.json")
if spans.get("Result") != "Success":
    sys.exit(f"FAIL: spans get Result={spans.get('Result')!r}")
span_list = spans.get("Data") or []
if not span_list:
    sys.exit("FAIL: spans.json has no spans — job produced no trace")

agent_span, selection_reason = find_agent_span(span_list)
if not agent_span:
    sys.exit("FAIL: could not identify agent span in spans.json")
agent_span_id = agent_span.get("Id") or agent_span.get("id")
if not agent_span_id:
    sys.exit("FAIL: agent span has no Id field")

create = load("feedback_create.json")
if create.get("Result") != "Success":
    sys.exit(f"FAIL: feedback create Result={create.get('Result')!r}, Message={create.get('Message')!r}")

feedback_id = get_id(create.get("Data") or {})
if not feedback_id:
    sys.exit("FAIL: feedback_create.json has no Data.Id")

get_data = load("feedback_get.json")
if get_data.get("Result") != "Success":
    sys.exit(f"FAIL: feedback get Result={get_data.get('Result')!r}")
got_feedback = get_data.get("Data") or {}
got_id = get_id(got_feedback)
if got_id != feedback_id:
    sys.exit(f"FAIL: ID mismatch — create={feedback_id!r}, get={got_id!r}")
if get_is_positive(got_feedback) is not True:
    sys.exit(f"FAIL: IsPositive not True in feedback_get.json")

got_span_id = get_span_id(got_feedback)
if got_span_id and normalize_span_id(got_span_id) != normalize_span_id(agent_span_id):
    sys.exit(
        f"FAIL: feedback SpanId={got_span_id!r} does not match agent span Id={agent_span_id!r} "
        f"(selected via: {selection_reason})"
    )

span_note = f"SpanId={got_span_id!r}" if got_span_id else "SpanId not returned by API"
span_name = agent_span.get("Name", "unknown")
print(f"OK: round-trip verified (id={feedback_id}, IsPositive=True, {span_note}, "
      f"agent_span='{span_name}' [{selection_reason}])")
