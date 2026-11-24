#!/usr/bin/env python3
"""Unit tests for check_approved_sdd_fidelity.py. Stdlib and pytest only."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
SPEC = importlib.util.spec_from_file_location("check_approved_sdd_fidelity", HERE / "check_approved_sdd_fidelity.py")
assert SPEC and SPEC.loader
fidelity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fidelity)

NODES = [
    ("startEvent", "S", "Invoice received"),
    ("scriptTask", "N", "Normalize invoice"),
    ("exclusiveGateway", "G1", "Sanctions status"),
    ("scriptTask", "B", "Block payment"),
    ("endEvent", "EB", "Payment blocked"),
    ("scriptTask", "C", "Route to compliance review"),
    ("endEvent", "EC", "Compliance review"),
    ("exclusiveGateway", "G2", "Amount over 10000"),
    ("scriptTask", "D", "Apply dual-control flag"),
    ("scriptTask", "P", "Schedule payment"),
    ("endEvent", "EP", "Payment scheduled"),
]
FLOWS = [
    ("f1", "S", "N", ""),
    ("f2", "N", "G1", ""),
    ("pay", "G1", "G2", "=vars.sanctionsCleared == true"),
    ("blk", "G1", "B", "=vars.sanctionsCleared == false"),
    ("rev", "G1", "C", ""),
    ("f6", "B", "EB", ""),
    ("f7", "C", "EC", ""),
    ("big", "G2", "D", "=vars.normalizedAmount &gt; 10000"),
    ("small", "G2", "P", ""),
    ("f10", "D", "P", ""),
    ("f11", "P", "EP", ""),
]
DEFAULTS = {"G1": "rev", "G2": "small"}


def _xml(nodes=NODES, flows=FLOWS, defaults=DEFAULTS) -> str:
    body = []
    for tag, node_id, name in nodes:
        default = f' default="{defaults[node_id]}"' if node_id in defaults else ""
        body.append(f'<bpmn:{tag} id="{node_id}" name="{name}"{default}/>')
    for flow_id, src, dst, cond in flows:
        inner = f"<bpmn:conditionExpression>{cond}</bpmn:conditionExpression>" if cond else ""
        body.append(f'<bpmn:sequenceFlow id="{flow_id}" sourceRef="{src}" targetRef="{dst}">{inner}</bpmn:sequenceFlow>')
    return (
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">'
        f'<bpmn:process id="p">{"".join(body)}</bpmn:process></bpmn:definitions>'
    )


def _grade(tmp_path: Path, monkeypatch, xml: str) -> None:
    (tmp_path / "SupplierPaymentHold.bpmn").write_text(xml)
    monkeypatch.chdir(tmp_path)
    fidelity.main()


def test_passes_for_the_design_built_1_to_1(tmp_path, monkeypatch, capsys) -> None:
    _grade(tmp_path, monkeypatch, _xml())
    assert "OK" in capsys.readouterr().out


def test_passes_with_a_join_before_schedule_payment(tmp_path, monkeypatch) -> None:
    nodes = NODES + [("exclusiveGateway", "J", "")]
    flows = [f for f in FLOWS if f[0] not in ("small", "f10")] + [
        ("small", "G2", "J", ""),
        ("f10", "D", "J", ""),
        ("j1", "J", "P", ""),
    ]
    _grade(tmp_path, monkeypatch, _xml(nodes, flows))


def test_fails_when_logic_collapses_into_one_script_task(tmp_path, monkeypatch, capsys) -> None:
    nodes = [("startEvent", "S", "Invoice received"), ("scriptTask", "X", "Run payment hold rules")] + [
        n for n in NODES if n[0] == "endEvent"
    ]
    flows = [("f1", "S", "X", ""), ("f2", "X", "EP", "")]
    with pytest.raises(SystemExit) as exc:
        _grade(tmp_path, monkeypatch, _xml(nodes, flows, {}))
    assert "exactly the SDD's five" in str(exc.value)


def test_fails_when_unknown_defaults_toward_payment(tmp_path, monkeypatch) -> None:
    flows = [
        ("pay", "G1", "G2", "") if f[0] == "pay" else ("rev", "G1", "C", "=vars.sanctionsCleared == null") if f[0] == "rev" else f
        for f in FLOWS
    ]
    with pytest.raises(SystemExit) as exc:
        _grade(tmp_path, monkeypatch, _xml(flows=flows, defaults={"G1": "pay", "G2": "small"}))
    assert "BR-01" in str(exc.value)


def test_fails_when_payment_branch_lets_null_through(tmp_path, monkeypatch) -> None:
    flows = [("pay", "G1", "G2", "=vars.sanctionsCleared != false") if f[0] == "pay" else f for f in FLOWS]
    with pytest.raises(SystemExit) as exc:
        _grade(tmp_path, monkeypatch, _xml(flows=flows))
    assert "lets an unknown value through" in str(exc.value)


def test_fails_when_a_tier_3_step_is_invented(tmp_path, monkeypatch) -> None:
    nodes = NODES + [("scriptTask", "T", "Tier 3 supplier check")]
    flows = [f for f in FLOWS if f[0] != "f11"] + [("f11", "P", "T", ""), ("f12", "T", "EP", "")]
    with pytest.raises(SystemExit) as exc:
        _grade(tmp_path, monkeypatch, _xml(nodes, flows))
    assert "exactly the SDD's five" in str(exc.value)


def test_names_a_duplicated_activity(tmp_path, monkeypatch) -> None:
    nodes = NODES + [("scriptTask", "P2", "Schedule payment")]
    flows = [f for f in FLOWS if f[0] != "f11"] + [("f11", "P", "P2", ""), ("f12", "P2", "EP", "")]
    with pytest.raises(SystemExit) as exc:
        _grade(tmp_path, monkeypatch, _xml(nodes, flows))
    message = str(exc.value)
    assert "duplicated ['schedule payment']" in message
    assert "missing []" in message and "extra []" in message


def test_names_a_duplicate_alongside_a_missing_activity(tmp_path, monkeypatch) -> None:
    nodes = [n for n in NODES if n[1] != "D"] + [("scriptTask", "P2", "Schedule payment")]
    flows = [f for f in FLOWS if f[0] not in ("big", "f10", "f11")] + [
        ("big", "G2", "P", "=vars.normalizedAmount &gt; 10000"),
        ("f11", "P", "P2", ""),
        ("f12", "P2", "EP", ""),
    ]
    with pytest.raises(SystemExit) as exc:
        _grade(tmp_path, monkeypatch, _xml(nodes, flows))
    message = str(exc.value)
    assert "missing ['apply dual-control flag']" in message
    assert "duplicated ['schedule payment']" in message


def test_names_a_duplicated_invented_activity(tmp_path, monkeypatch) -> None:
    nodes = NODES + [("scriptTask", "T", "Tier 3 supplier check"), ("scriptTask", "T2", "Tier 3 supplier check")]
    flows = [f for f in FLOWS if f[0] != "f11"] + [("f11", "P", "T", ""), ("f12", "T", "T2", ""), ("f13", "T2", "EP", "")]
    with pytest.raises(SystemExit) as exc:
        _grade(tmp_path, monkeypatch, _xml(nodes, flows))
    assert "duplicated ['tier 3 supplier check']" in str(exc.value)
