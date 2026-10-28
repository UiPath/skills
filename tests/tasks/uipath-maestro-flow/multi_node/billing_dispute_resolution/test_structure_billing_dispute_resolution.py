#!/usr/bin/env python3
"""Unit tests for `check_structure_billing_dispute_resolution.assert_topology`.

The function's own section header has claimed "unit-testable against the
reference" since #1320 and nothing tested it, so the gating structural criterion
was only ever exercised by a live eval run. That is what let the connector-only
entity-read gate survive #3249: both billing references sit in this directory,
and neither was ever fed to the assertion that rejects one of them.

Both reference flows are the same orchestration in the two shapes tenant
availability produces (`flow_check.ENTITY_QUERY_HINTS`), so both MUST pass. A
shape-pinned gate fails exactly one of them, which is the regression these two
cases lock.
"""
import importlib.util
import json
import os

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))

CONNECTOR_REFERENCE = "BillingDisputeResolution.reference.flow"
NATIVE_REFERENCE = "BillingDisputeResolution.native.reference.flow"


def _checker():
    """Load the checker by path — its filename is not an importable module name."""
    path = os.path.join(_HERE, "check_structure_billing_dispute_resolution.py")
    spec = importlib.util.spec_from_file_location("_check_structure_bdr", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _graph(filename):
    with open(os.path.join(_HERE, filename)) as handle:
        flow = json.load(handle)
    return {n["id"]: n for n in flow["nodes"]}, flow["edges"]


@pytest.mark.parametrize("reference", [CONNECTOR_REFERENCE, NATIVE_REFERENCE])
def test_assert_topology_accepts_both_reference_shapes(reference):
    """Neither entity-read shape may fail the gating topology assertion."""
    nodes_by_id, edges = _graph(reference)
    _checker().assert_topology(nodes_by_id, edges)


def test_assert_topology_rejects_a_single_entity_read():
    """The ERP+CRM pair is load-bearing: one lookup is not the orchestration.

    Guards the shape-agnostic union in `ds` — a hint list that silently matched
    nothing would make every count assertion vacuous.
    """
    nodes_by_id, edges = _graph(NATIVE_REFERENCE)
    checker = _checker()
    reads = [
        i for i, n in nodes_by_id.items()
        if any(h in str(n.get("type", "")).lower() for h in checker.ENTITY_QUERY_HINTS)
    ]
    assert len(reads) >= 2, "reference lost its entity reads; fixture is wrong"
    del nodes_by_id[reads[0]]

    with pytest.raises(SystemExit) as exc:
        checker.assert_topology(nodes_by_id, edges)
    assert "entity-read" in str(exc.value)
