#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    fail,
    one_or_more,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)


def main() -> None:
    path, root = parse_bpmn("InvoiceTriageBpmn")
    exclusive = one_or_more(root, "exclusiveGateway")
    one_or_more(root, "parallelGateway")
    flows = one_or_more(root, "sequenceFlow")
    if len(flows) < 8:
        fail(f"expected at least 8 sequence flows in {path}, found {len(flows)}")
    if not any(attr(gateway, "default") for gateway in exclusive):
        fail("exclusive gateway is missing a default sequence-flow reference")
    conditioned = [
        flow for flow in flows if flow.find("bpmn:conditionExpression", NS) is not None
    ]
    if not conditioned:
        fail("missing conditional sequence flow")
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} has gateways, conditional/default flows, and BPMN DI")


if __name__ == "__main__":
    main()
