#!/usr/bin/env python3
"""Structural check for the error-end-event + error-catching event subprocess.

Asserts the process throws a configured error and catches it in an event
subprocess:
  - an error END event whose errorEventDefinition carries an errorRef that
    resolves to a bpmn:error with a non-empty errorCode (the runtime-blocking
    ERROR_END_EVENT_MISSING_EXCEPTION would fire otherwise);
  - an EVENT subprocess (triggeredByEvent="true") with exactly one start event
    that is an interrupting error start (errorEventDefinition, not
    isInterrupting="false"), so it catches the thrown error;
  - a DI shape for the event subprocess container.

Element lookups are case-insensitive on the BPMN local name: registry
xmlTemplates emit capitalized element names while hand-authored structural BPMN
uses the lowercase-camel spec names. Reuses the shared uipath-maestro-bpmn
check helpers (stdlib ET, locally authored input — same trust boundary as the
rest of the fixture corpus).
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)

BPMN_NS = NS["bpmn"]


def els(root: ET.Element, kind: str) -> list[ET.Element]:
    """Case-insensitive BPMN element lookup by local name."""
    prefix = "{" + BPMN_NS + "}"
    kl = kind.lower()
    return [
        el for el in root.iter()
        if el.tag.startswith(prefix) and el.tag[len(prefix):].lower() == kl
    ]


def children(el: ET.Element, kind: str) -> list[ET.Element]:
    prefix = "{" + BPMN_NS + "}"
    kl = kind.lower()
    return [c for c in el if c.tag.startswith(prefix) and c.tag[len(prefix):].lower() == kl]


def child(el: ET.Element, kind: str) -> ET.Element | None:
    found = children(el, kind)
    return found[0] if found else None


def main() -> None:
    path, root = parse_bpmn("PaymentErrorHandling")

    if not els(root, "startEvent"):
        fail("no start event")

    codes = {attr(err, "id"): attr(err, "errorCode") for err in els(root, "error")}

    # 1. Error END event with a resolvable errorRef + non-empty errorCode.
    error_ends = []
    for end in els(root, "endEvent"):
        edef = child(end, "errorEventDefinition")
        if edef is not None:
            error_ends.append((end, edef))
    if not error_ends:
        fail("no end event carries a bpmn:errorEventDefinition (nothing throws an error)")
    for end, edef in error_ends:
        ref = attr(edef, "errorRef")
        if not ref:
            fail(f"error end event {attr(end, 'id')} has no errorRef (ERROR_END_EVENT_MISSING_EXCEPTION)")
        if ref not in codes:
            fail(f"error end event errorRef {ref!r} does not resolve to a declared bpmn:error")
        if not codes[ref].strip():
            fail(f"bpmn:error {ref!r} referenced by the error end event has no errorCode")

    # 2. Event subprocess (triggeredByEvent) catching the error.
    event_subs = [sp for sp in els(root, "subProcess") if attr(sp, "triggeredByEvent") == "true"]
    if not event_subs:
        fail('no event subprocess (bpmn:subProcess triggeredByEvent="true")')
    caught = False
    for sp in event_subs:
        starts = children(sp, "startEvent")
        if len(starts) != 1:
            fail(f"event subprocess {attr(sp, 'id')} must have exactly one start event, found {len(starts)}")
        se = starts[0]
        se_err = child(se, "errorEventDefinition")
        if se_err is None:
            continue  # not an error-catching start; keep looking
        # Interrupting: the spec generates an interrupting error start; reject a
        # non-interrupting one (isInterrupting="false").
        if attr(se, "isInterrupting") == "false":
            fail(f"error start event {attr(se, 'id')} is non-interrupting; an interrupting error start is required")
        # The caught error should reference a declared error (ties handler to throw).
        se_ref = attr(se_err, "errorRef")
        if se_ref and se_ref not in codes:
            fail(f"event-subprocess start errorRef {se_ref!r} does not resolve to a declared bpmn:error")
        caught = True
        # 3. DI shape for the event subprocess container.
        shaped = {s.attrib.get("bpmnElement") for s in root.findall(".//bpmndi:BPMNShape", NS)}
        if attr(sp, "id") not in shaped:
            fail(f"event subprocess {attr(sp, 'id')} has no BPMNShape (invisible on the canvas)")
    if not caught:
        fail("no event subprocess has an interrupting error start event catching the thrown error")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} throws a configured error end event and catches it in an interrupting error event subprocess")


if __name__ == "__main__":
    main()
