#!/usr/bin/env python3
"""Structural check for the correlated internal-message send/receive pair.

Asserts:
  - a bpmn:intermediateThrowEvent hosting the registry Maestro.SendMessageEvent
    wrapper with a bpmn:messageEventDefinition;
  - a bpmn:intermediateCatchEvent hosting the registry Maestro.ReceiveMessageEvent
    wrapper with a bpmn:messageEventDefinition;
  - a shared/consistent message reference between the two — the uipath:context
    `name` input value matches (the internal-message correlation key), and where
    a messageRef is present on both, it resolves to the same declared message;
  - DI shapes for both events.
Reuses the shared uipath-maestro-bpmn check helpers.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)

SEND = "Maestro.SendMessageEvent"
RECEIVE = "Maestro.ReceiveMessageEvent"


def has_type(el: ET.Element, token: str) -> bool:
    return token in ET.tostring(el, encoding="unicode")


def context_name(el: ET.Element) -> str:
    for inp in el.findall(".//uipath:context/uipath:input", NS):
        if attr(inp, "name") == "name":
            return attr(inp, "value")
    return ""


def main() -> None:
    path, root = parse_bpmn("OrderCoordination")

    throws = [
        t for t in elements(root, "intermediateThrowEvent")
        if has_type(t, SEND) and t.find("bpmn:messageEventDefinition", NS) is not None
    ]
    catches = [
        c for c in elements(root, "intermediateCatchEvent")
        if has_type(c, RECEIVE) and c.find("bpmn:messageEventDefinition", NS) is not None
    ]
    if not throws:
        fail("no bpmn:intermediateThrowEvent with Maestro.SendMessageEvent and a messageEventDefinition")
    if not catches:
        fail("no bpmn:intermediateCatchEvent with Maestro.ReceiveMessageEvent and a messageEventDefinition")

    # Wrong-host guards: the send must not be a catch, the receive must not be a throw.
    if any(has_type(c, SEND) for c in elements(root, "intermediateCatchEvent")):
        fail("Maestro.SendMessageEvent must be on an intermediateThrowEvent, not a catch")
    if any(has_type(t, RECEIVE) for t in elements(root, "intermediateThrowEvent")):
        fail("Maestro.ReceiveMessageEvent must be on an intermediateCatchEvent, not a throw")

    throw, catch = throws[0], catches[0]

    # Consistent correlation reference via the context `name`.
    send_name = context_name(throw)
    recv_name = context_name(catch)
    if not send_name or not recv_name:
        fail("send/receive missing a uipath:context name (no correlation reference)")
    if send_name != recv_name:
        fail(f"send/receive message names differ ({send_name!r} vs {recv_name!r}); not a correlated pair")

    # If both declare a messageRef, they must resolve to the same declared message.
    def message_ref(el):
        med = el.find("bpmn:messageEventDefinition", NS)
        return attr(med, "messageRef")

    send_ref, recv_ref = message_ref(throw), message_ref(catch)
    if send_ref and recv_ref:
        declared = {attr(m, "id") for m in root.findall("bpmn:message", NS)}
        if send_ref not in declared or recv_ref not in declared:
            fail(f"messageRef(s) {send_ref!r}/{recv_ref!r} do not resolve to a declared bpmn:message")
        if send_ref != recv_ref:
            fail(f"send/receive messageRefs differ ({send_ref!r} vs {recv_ref!r})")

    # DI shapes for both events.
    shaped = {s.attrib.get("bpmnElement") for s in root.findall(".//bpmndi:BPMNShape", NS)}
    for ev in (throw, catch):
        if attr(ev, "id") not in shaped:
            fail(f"message event {attr(ev, 'id')} has no BPMNShape")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} pairs a Maestro send and receive message event on a consistent reference {send_name!r}")


if __name__ == "__main__":
    main()
