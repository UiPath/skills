"""Unit tests for plain_check.py. Run with ``pytest`` from any directory.

Pins that a correct ShippingFee table matches every scenario, that a comma-list range is caught, and that
the extraction leftovers the route check looks for are the ones the document route writes.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))

import plain_check as plain  # noqa: E402

NS = plain.rc.DMN_NS
GOLD = [  # weightKg, isPremium -> fee
    (("< 5", "true"), 0), (("[5..20)", "true"), 7.5), ((">= 20", "true"), 15),
    (("< 1", "false"), 5), (("[1..5)", "false"), 8), (("[5..20)", "false"), 15), ((">= 20", "false"), 30),
]


def table(rows):
    xml = [f'<decisionTable xmlns="{NS}" hitPolicy="FIRST">']
    xml += [f"<input><inputExpression><text>{name}</text></inputExpression></input>" for name in plain.INPUTS]
    xml += ['<output name="shippingFee"/>']
    for cells, value in rows:
        xml.append("<rule>" + "".join(f"<inputEntry><text>{escape(c)}</text></inputEntry>" for c in cells))
        xml.append(f"<outputEntry><text>{value}</text></outputEntry></rule>")
    xml.append("</decisionTable>")
    return ET.fromstring("".join(xml))


def mismatches(rows):
    t = table(rows)
    return [(i, plain.rc.evaluate(t, i)["shippingFee"], want) for i, want in plain.SCENARIOS
            if (plain.rc.evaluate(t, i) or {}).get("shippingFee") != want]


def test_gold_table_matches_every_scenario():
    assert mismatches(GOLD) == []


def test_a_comma_list_range_matches_every_number_and_fails_scenarios():
    bad = [r if r[0][0] != "[5..20)" else (("> 5, < 20", r[0][1]), r[1]) for r in GOLD]
    assert mismatches(bad) != []
    assert plain.comma_range_cells(table(bad)) == ["> 5, < 20", "> 5, < 20"]


def test_intervals_and_single_tests_are_not_flagged():
    assert plain.comma_range_cells(table(GOLD)) == []


def test_extraction_leftovers_name_the_artifacts_of_the_document_route(tmp_path):
    assert plain.extraction_leftovers(tmp_path, "<definitions/>") == []
    (tmp_path / "run").mkdir()
    (tmp_path / "run" / "cites.json").write_text("[]")
    found = plain.extraction_leftovers(tmp_path, '<definitions xmlns:uipdm="http://uipath.com/schema/1.0/dmn-ext/decision-model"/>')
    assert len(found) == 2 and any("uipdm" in f for f in found)
