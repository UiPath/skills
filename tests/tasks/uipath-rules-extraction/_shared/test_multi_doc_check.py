"""Unit tests for multi_doc_check.py. Run with ``pytest`` from any directory.

Pins that a correct reading of the travel-expense documents (Amendment 1 applied,
Amendment 2 not, SOP and FAQ not overriding) passes every scenario, and that each
plausible misreading fails at least one.
"""

import sys
from pathlib import Path
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import multi_doc_check as mdc  # noqa: E402

NS = "https://www.omg.org/spec/DMN/20230324/MODEL/"
pc = mdc.pc
# expenseType, travelType, amount, hasReceipt, hasManagerPreApproval, isAlcohol, daysAfterTripEnd
W = "-"


def table(rows):
    xml = [f'<decisionTable xmlns="{NS}" hitPolicy="FIRST">']
    xml += [f"<input><inputExpression><text>{name}</text></inputExpression></input>" for name in pc.INPUTS]
    xml += ['<output name="outcome"/>']
    for cells, value in rows:
        xml.append("<rule>")
        xml += [f"<inputEntry><text>{escape(cell)}</text></inputEntry>" for cell in cells]
        xml.append(f'<outputEntry><text>"{value}"</text></outputEntry></rule>')
    xml.append("</decisionTable>")
    return ET.fromstring("".join(xml))


def gold(domestic_hotel=225, domestic_meal=65, receipt_over=25, window=30):
    return [
        ((W, W, "null", W, W, W, W), "Refer"),
        ((W, W, W, "null", W, W, W), "Refer"),
        ((W, W, W, W, W, W, "null"), "Refer"),
        ((W, W, W, W, W, "true", W), "Reject"),
        ((W, W, W, W, W, W, f"> {window}"), "Refer"),
        ((W, W, f"> {receipt_over}", "false", W, W, W), "Reject"),
        (('"Airfare"', W, "> 800", W, "false", W, W), "Reject"),
        (('"Hotel"', '"Domestic"', f"> {domestic_hotel}", W, W, W, W), "Reject"),
        (('"Hotel"', '"International"', "> 300", W, W, W, W), "Reject"),
        (('"Meal"', '"Domestic"', f"> {domestic_meal}", W, W, W, W), "Reject"),
        (('"Meal"', '"International"', "> 90", W, W, W, W), "Reject"),
        ((W, W, W, W, W, W, W), "Approve"),
    ]


def wrong(rows):
    t = table(rows)
    return [label for label, values, expected in pc.SCENARIOS
            if pc.evaluate(t, dict(zip(pc.INPUTS, values))) != expected]


def test_gold_table_matches_every_scenario():
    assert wrong(gold()) == []


@pytest.mark.parametrize("name, rows", [
    ("amendment 1 ignored (base hotel cap)", gold(domestic_hotel=200)),
    ("amendment 1 ignored (base meal cap)", gold(domestic_meal=60)),
    ("amendment 2 applied (receipt threshold)", gold(receipt_over=20)),
    ("amendment 2 applied (45-day window)", gold(window=45)),
    ("SOP's $250 practice overrides the hotel cap", gold(domestic_hotel=250)),
    ("FAQ's verbal approval up to $1,000", [r for r in gold() if r[0][2] != "> 800"]
        + []),
    ("missing trip end date approves", [r for r in gold() if r[0][6] != "null"]),
])
def test_misreadings_fail(name, rows):
    if name.startswith("FAQ"):
        rows = [((r[0][0], r[0][1], "> 1000" if r[0][2] == "> 800" else r[0][2], *r[0][3:]), r[1]) for r in gold()]
    assert wrong(rows), name


def test_scenarios_use_only_the_named_inputs():
    assert all(len(values) == len(pc.INPUTS) for _, values, _ in pc.SCENARIOS)


def test_checker_copy_does_not_change_the_reimbursement_checker():
    import policy_check as original
    assert original.PROJECT_NAME == "ReimbursementRules" and pc is not original


LIGHT_GOLD = [  # expenseType, amount, hasReceipt, daysAfterTripEnd
    (("-", "null", "-", "-"), "Refer"),
    (("-", "-", "null", "-"), "Refer"),
    (("-", "-", "-", "null"), "Refer"),
    (("-", "-", "-", "> 30"), "Refer"),
    (("-", "> 25", "false", "-"), "Reject"),
    (('"Hotel"', "> 225", "-", "-"), "Reject"),
    (('"Meal"', "> 60", "-", "-"), "Reject"),
    (("-", "-", "-", "-"), "Approve"),
]


def light_wrong(rows):
    mdc.configure("light")
    try:
        xml = [f'<decisionTable xmlns="{NS}" hitPolicy="FIRST">']
        xml += [f"<input><inputExpression><text>{n}</text></inputExpression></input>" for n in pc.INPUTS]
        xml += ['<output name="outcome"/>']
        for cells, value in rows:
            xml.append("<rule>" + "".join(f"<inputEntry><text>{escape(c)}</text></inputEntry>" for c in cells)
                       + f'<outputEntry><text>"{value}"</text></outputEntry></rule>')
        xml.append("</decisionTable>")
        t = ET.fromstring("".join(xml))
        return [label for label, values, expected in pc.SCENARIOS
                if pc.evaluate(t, dict(zip(pc.INPUTS, values))) != expected]
    finally:
        mdc.configure("full")


def test_light_gold_matches_every_scenario():
    assert light_wrong(LIGHT_GOLD) == []


@pytest.mark.parametrize("name, rows", [
    ("amendment 1 ignored", [(c[:1] + ("> 200",) + c[2:], v) if c[1] == "> 225" else (c, v) for c, v in LIGHT_GOLD]),
    ("faq's $250 applied", [(c[:1] + ("> 250",) + c[2:], v) if c[1] == "> 225" else (c, v) for c, v in LIGHT_GOLD]),
    ("amendment 2 applied", [(c[:1] + ("> 20",) + c[2:], v) if c[1] == "> 25" else (c, v) for c, v in LIGHT_GOLD]),
    ("missing amount approves", LIGHT_GOLD[1:]),
])
def test_light_misreadings_fail(name, rows):
    assert light_wrong(rows), name


def test_ledger_needs_both_amendments_and_the_not_applied_wording_near_amendment_2():
    good = "Amendment 1 applied (effective 2026-07-01). Amendment 2 is not yet effective on the as-of date, so no row uses it."
    assert mdc.ledger_ok(good) is None
    assert mdc.ledger_ok("Amendment 1 applied.") is not None
    assert mdc.ledger_ok("Amendment 1 and amendment 2 are listed.") is not None
    far = "Amendment 2 is listed. " + "x " * 200 + "Some other item is not yet effective."
    assert mdc.ledger_ok("Amendment 1 applied. " + far) is not None
