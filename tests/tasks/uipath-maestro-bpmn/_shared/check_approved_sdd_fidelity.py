#!/usr/bin/env python3
"""Grade SupplierPaymentHold against its approved SDD (author/approved_sdd_fidelity).

Critical Rule 8: an approved design is built 1:1. The compiled `.bpmn` must hold every
SDD element by name, the SDD's two decision gateways and no other, exactly the SDD's
five activities (no logic collapsed into one script task, no step invented for the
undefined BR-03 Tier 3 check), and BR-01's unknown default routed to compliance review.
An element matches by its SDD name or its SDD id. A join gateway is allowed.
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import NS, attr, elements, fail, parse_bpmn  # noqa: E402

ACTIVITIES = {
    "normalize invoice",
    "block payment",
    "route to compliance review",
    "apply dual-control flag",
    "schedule payment",
}
ENDS = {"payment blocked", "compliance review", "payment scheduled"}
START = "invoice received"
GATEWAYS = {"sanctions status", "amount over 10000"}

ACTIVITY_TAGS = (
    "task",
    "scriptTask",
    "serviceTask",
    "userTask",
    "sendTask",
    "receiveTask",
    "businessRuleTask",
    "manualTask",
    "callActivity",
    "subProcess",
)
GATEWAY_TAGS = ("exclusiveGateway", "inclusiveGateway", "parallelGateway", "eventBasedGateway")
NEGATED_CLEARED = re.compile(r"sanctionsCleared\s*!==?\s*false|!\s*vars\.sanctionsCleared|==\s*null|undefined", re.I)
UNKNOWN_TEST = re.compile(r"null|undefined|!==?\s*true|==\s*null", re.I)


SDD_IDS = {
    "start_invoicereceived": "invoice received",
    "task_normalizeinvoice": "normalize invoice",
    "gateway_sanctionsstatus": "sanctions status",
    "task_blockpayment": "block payment",
    "end_paymentblocked": "payment blocked",
    "task_routetocompliance": "route to compliance review",
    "end_compliancereview": "compliance review",
    "gateway_amountcheck": "amount over 10000",
    "task_applydualcontrol": "apply dual-control flag",
    "task_schedulepayment": "schedule payment",
    "end_paymentscheduled": "payment scheduled",
}


def name_of(element: ET.Element) -> str:
    name = " ".join(attr(element, "name").split()).casefold()
    return name or SDD_IDS.get(attr(element, "id").casefold(), "")


def condition(flow: ET.Element) -> str:
    expr = flow.find("bpmn:conditionExpression", NS)
    return (expr.text or "") if expr is not None else ""


def main() -> None:
    path, root = parse_bpmn("SupplierPaymentHold")

    activities = [el for tag in ACTIVITY_TAGS for el in elements(root, tag)]
    names = sorted(name_of(el) for el in activities)
    if sorted(ACTIVITIES) != names:
        missing = sorted(ACTIVITIES - set(names))
        extra = [n for n in names if n not in ACTIVITIES]
        fail(f"activities must be exactly the SDD's five; missing {missing}, extra {extra}")

    starts = elements(root, "startEvent")
    if [name_of(el) for el in starts] != [START]:
        fail(f"expected one start event named 'Invoice received', found {[name_of(el) for el in starts]}")

    ends = sorted(name_of(el) for el in elements(root, "endEvent"))
    if ends != sorted(ENDS):
        fail(f"end events must be exactly {sorted(ENDS)}, found {ends}")

    flows = elements(root, "sequenceFlow")
    outgoing: dict[str, list[ET.Element]] = {}
    incoming: dict[str, int] = {}
    for flow in flows:
        outgoing.setdefault(attr(flow, "sourceRef"), []).append(flow)
        incoming[attr(flow, "targetRef")] = incoming.get(attr(flow, "targetRef"), 0) + 1

    gateways = [el for tag in GATEWAY_TAGS for el in elements(root, tag)]
    decisions = [gw for gw in gateways if len(outgoing.get(attr(gw, "id"), [])) > 1]
    joins = [gw for gw in gateways if gw not in decisions and incoming.get(attr(gw, "id"), 0) > 1]
    stray = [attr(gw, "name") or attr(gw, "id") for gw in gateways if gw not in decisions and gw not in joins]
    if sorted(name_of(gw) for gw in decisions) != sorted(GATEWAYS) or stray:
        fail(
            f"decision gateways must be exactly {sorted(GATEWAYS)}, "
            f"found {[name_of(gw) for gw in decisions]}; stray gateways {stray}"
        )

    by_id = {attr(el, "id"): el for el in root.iter() if attr(el, "id")}

    def leads_to(target_id: str, wanted: str, seen: frozenset[str] = frozenset()) -> bool:
        node = by_id.get(target_id)
        if node is None or target_id in seen:
            return False
        if name_of(node) == wanted:
            return True
        is_join = node in joins
        return is_join and any(
            leads_to(attr(f, "targetRef"), wanted, seen | {target_id}) for f in outgoing.get(target_id, [])
        )

    sanctions = next(gw for gw in decisions if name_of(gw) == "sanctions status")
    branches = outgoing[attr(sanctions, "id")]
    default_id = attr(sanctions, "default")
    to_amount = [f for f in branches if leads_to(attr(f, "targetRef"), "amount over 10000")]
    to_compliance = [f for f in branches if leads_to(attr(f, "targetRef"), "route to compliance review")]
    if len(branches) != 3 or len(to_amount) != 1 or len(to_compliance) != 1:
        fail("'Sanctions status' needs three branches: amount check, block payment, compliance review")

    pay = to_amount[0]
    if attr(pay, "id") == default_id or not condition(pay).strip():
        fail("BR-01: the branch toward payment must be conditioned, never the default")
    if NEGATED_CLEARED.search(condition(pay)):
        fail(f"BR-01: the payment branch condition lets an unknown value through: {condition(pay)!r}")

    review = to_compliance[0]
    if attr(review, "id") != default_id and not UNKNOWN_TEST.search(condition(review)):
        fail("BR-01: an unknown value must reach compliance review (default flow or a null test)")

    if any("tier" in name_of(el) for el in root.iter() if attr(el, "name")):
        fail("BR-03 is undefined in the SDD; the build invented an element for it")

    print(f"OK: {path} matches the approved SDD element for element")


if __name__ == "__main__":
    main()
