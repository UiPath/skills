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
    assert_node_types,
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


def _exec(element_type=None, extension_type=None, status="Completed"):
    return {
        "elementType": element_type,
        "extensionType": extension_type,
        "status": status,
    }


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


def test_collect_outputs_empty():
    assert collect_outputs(_payload()) == []


# ── assert_node_types ───────────────────────────────────────────────────────


def test_assert_node_types_matches_element_type():
    payload = {"elementExecutions": [_exec(element_type="ScriptTask")]}
    assert_node_types(payload, ["script"])  # substring, case-insensitive


def test_assert_node_types_matches_extension_type():
    payload = {
        "elementExecutions": [
            _exec(element_type="ServiceTask", extension_type="api-workflow")
        ]
    }
    assert_node_types(payload, ["api-workflow"])


def test_assert_node_types_requires_completed_status():
    payload = {"elementExecutions": [_exec(element_type="ScriptTask", status="Failed")]}
    with pytest.raises(SystemExit, match="node-type hint 'script'"):
        assert_node_types(payload, ["script"])


def test_assert_node_types_fails_when_hint_absent():
    payload = {"elementExecutions": [_exec(element_type="HttpRequest")]}
    with pytest.raises(SystemExit, match="node-type hint 'agent'"):
        assert_node_types(payload, ["agent"])


def test_assert_node_types_empty_hints_is_noop():
    assert_node_types({}, [])  # no raise


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
