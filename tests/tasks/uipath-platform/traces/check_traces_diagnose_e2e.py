#!/usr/bin/env python3
"""Verify the standalone-diagnose run landed on a real failing span.

Grades against spans.json — raw `uip traces spans get` output — not against any
prose the agent wrote. failing_span.txt must name a span ID that actually exists
in that payload and that carries fault evidence, so a guessed or invented ID fails.
"""
import json
import re
import sys
from pathlib import Path

# Word-anchored: a bare "fault" substring also matches "default", which appears in
# ordinary folder names and attribute keys and would make the check vacuous.
FAULT_KEY = re.compile(r"\b(error|exception|fault|failed|failure|stack_?trace)", re.I)
FAULT_VALUE = re.compile(r"\b(error|exception|faulted|failed|failure)", re.I)


def load(path):
    p = Path(path)
    if not p.is_file():
        sys.exit(f"FAIL: {path} not found")
    return p


try:
    payload = json.loads(load("spans.json").read_text())
except json.JSONDecodeError as e:
    sys.exit(f"FAIL: spans.json is not valid JSON: {e}")

if isinstance(payload, list):
    spans = payload
else:
    if payload.get("Result") not in (None, "Success"):
        sys.exit(f"FAIL: Result={payload.get('Result')!r}, Message={payload.get('Message')!r}")
    spans = payload.get("Data") or []

if not isinstance(spans, list) or not spans:
    sys.exit("FAIL: spans.json contains no spans")


def fields(span):
    """Flatten a span's own fields plus its Attributes blob into (key, value) pairs."""
    out = []
    for k, v in span.items():
        if k == "Attributes" and isinstance(v, str):
            try:
                parsed = json.loads(v)
            except json.JSONDecodeError:
                out.append((k, v))
                continue
            if isinstance(parsed, dict):
                out.extend(parsed.items())
            continue
        out.append((k, v))
    return out


def is_faulting(span):
    for key, value in fields(span):
        if value in (None, "", [], {}, False):
            continue
        if FAULT_KEY.search(str(key)):
            return True
        if isinstance(value, str) and FAULT_VALUE.search(value):
            return True
    return False


by_id = {str(s["Id"]): s for s in spans if isinstance(s, dict) and s.get("Id")}
if not by_id:
    sys.exit("FAIL: no span in spans.json carries an Id")

faulting = {sid for sid, s in by_id.items() if is_faulting(s)}
if not faulting:
    sys.exit("FAIL: no span carries fault evidence — the fixture job may not have faulted")
if len(faulting) == len(by_id):
    sys.exit(
        f"FAIL: every one of {len(by_id)} spans matches the fault heuristic — the check is "
        "vacuous and cannot distinguish the failing span. Tighten the markers."
    )

reported = load("failing_span.txt").read_text().strip()
if not reported:
    sys.exit("FAIL: failing_span.txt is empty")
if reported not in by_id:
    sys.exit(
        f"FAIL: failing_span.txt names {reported!r}, which is not a span in spans.json "
        f"({len(by_id)} span(s) returned)"
    )
if reported not in faulting:
    sys.exit(
        f"FAIL: span {reported} carries no fault evidence — the diagnosis points at a span "
        f"that did not fail. Faulting spans in this trace: {sorted(faulting)}"
    )

print(f"OK: {reported} is one of {len(faulting)} faulting span(s) across {len(by_id)} span(s)")
