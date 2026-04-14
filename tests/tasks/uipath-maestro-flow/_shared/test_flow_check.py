"""Unit tests for flow_check helpers. Run with ``pytest`` from any directory.

These exercise the assertion helpers against hand-crafted ``uip flow debug``
payload shapes so regressions in the eval logic are caught without burning a
real tenant run (as happened with the nested-output flattening bug).
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_int_in_range,
    assert_output_value,
    assert_outputs_contain,
    collect_outputs,
)


def _payload(*, globals_=(), elements=()):
    return {
        "variables": {
            "globalVariables": list(globals_),
            "elements": list(elements),
        }
    }


def _write_flow(tmp_path, node_types):
    """Create a minimal project.uiproj + .flow file tree and return its root."""
    import json

    proj = tmp_path / "MyFlow"
    proj.mkdir()
    (proj / "project.uiproj").write_text("{}")
    flow = {"nodes": [{"id": f"n{i}", "type": t} for i, t in enumerate(node_types)]}
    (proj / "MyFlow.flow").write_text(json.dumps(flow))
    return tmp_path


# ── collect_outputs ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw, expected",
    [
        # scalar global variable
        ({"value": 4}, [4]),
        # nested dict — the calculator bug we just fixed
        ({"value": {"product": 391}}, [391]),
        # list of dicts
        ({"value": [{"k": "a"}, {"k": "b"}]}, ["a", "b"]),
        # mixed nesting
        ({"value": {"msg": "nice day", "temp": 72}}, ["nice day", 72]),
    ],
)
def test_collect_outputs_flattens_globals(raw, expected):
    outs = collect_outputs(_payload(globals_=[raw]))
    assert set(outs) == set(expected)


def test_collect_outputs_walks_element_outputs():
    payload = _payload(elements=[{"outputs": {"result": {"age": 47}}}])
    assert collect_outputs(payload) == [47]


def test_collect_outputs_walks_globals_dict():
    # Actual debug response shape: `variables.globals` is a dict, not the
    # `globalVariables` array the SDK types describe. End-node output
    # expressions land here.
    payload = {
        "variables": {
            "globals": {
                "summary": {"temperature": 52.5, "message": "bring a jacket"},
            }
        }
    }
    outs = collect_outputs(payload)
    assert "bring a jacket" in outs
    assert 52.5 in outs


def test_collect_outputs_empty():
    assert collect_outputs(_payload()) == []


# ── assert_flow_has_node_type ───────────────────────────────────────────────


def test_assert_flow_has_node_type_matches_substring(tmp_path, monkeypatch):
    root = _write_flow(tmp_path, ["core.action.http", "core.action.script"])
    monkeypatch.chdir(root)
    assert_flow_has_node_type(["core.action.http"])  # exact
    assert_flow_has_node_type(["http"])  # substring, case-insensitive


def test_assert_flow_has_node_type_matches_resource_node(tmp_path, monkeypatch):
    root = _write_flow(tmp_path, ["uipath.core.api-workflow.abc-123"])
    monkeypatch.chdir(root)
    assert_flow_has_node_type(["uipath.core.api-workflow"])


def test_assert_flow_has_node_type_fails_when_absent(tmp_path, monkeypatch):
    root = _write_flow(tmp_path, ["core.action.script"])
    monkeypatch.chdir(root)
    with pytest.raises(SystemExit, match="type hint 'core.action.http'"):
        assert_flow_has_node_type(["core.action.http"])


def test_assert_flow_has_node_type_empty_hints_is_noop(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no project needed when hints are empty
    assert_flow_has_node_type([])


# ── assert_output_value ─────────────────────────────────────────────────────


def test_assert_output_value_exact_int_in_nested_dict():
    # The calculator scenario: flow produced {"product": 391}, expect 391.
    payload = _payload(elements=[{"outputs": {"product": 391}}])
    assert_output_value(payload, 391)


def test_assert_output_value_string_substring():
    payload = _payload(globals_=[{"value": "It's a nice day today"}])
    assert_output_value(payload, "nice day")


def test_assert_output_value_fails_when_absent():
    payload = _payload(globals_=[{"value": 42}])
    with pytest.raises(SystemExit, match="expected 391"):
        assert_output_value(payload, 391)


# ── assert_output_int_in_range ──────────────────────────────────────────────


def test_assert_output_int_in_range_returns_match():
    payload = _payload(globals_=[{"value": {"roll": 4}}])
    assert assert_output_int_in_range(payload, 1, 6) == 4


def test_assert_output_int_in_range_fails_when_out_of_range():
    payload = _payload(globals_=[{"value": {"roll": 9}}])
    with pytest.raises(SystemExit, match=r"No integer in \[1, 6\]"):
        assert_output_int_in_range(payload, 1, 6)


# ── assert_outputs_contain ──────────────────────────────────────────────────


def test_assert_outputs_contain_all_required():
    payload = _payload(
        globals_=[{"value": "700 Bellevue Way NE, Suite 2000, Bellevue WA 98004"}]
    )
    assert_outputs_contain(payload, ["700 Bellevue Way", "Suite 2000", "WA 98004"])


def test_assert_outputs_contain_any_when_one_branch_wins():
    payload = _payload(globals_=[{"value": {"message": "nice day"}}])
    assert_outputs_contain(payload, ["nice day", "bring a jacket"], require_all=False)


def test_assert_outputs_contain_fails_when_missing():
    payload = _payload(globals_=[{"value": "hello"}])
    with pytest.raises(SystemExit, match="missing"):
        assert_outputs_contain(payload, ["world"])
