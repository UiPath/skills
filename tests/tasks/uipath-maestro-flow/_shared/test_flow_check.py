"""Unit tests for flow_check helpers. Run with ``pytest`` from any directory.

These exercise the assertion helpers against hand-crafted ``uip maestro flow debug``
payload shapes so regressions in the eval logic are caught without burning a
real tenant run (as happened with the nested-output flattening bug).
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flow_check import (  # noqa: E402
    assert_flow_has_any_node_type,
    assert_flow_has_exact_node_type,
    assert_flow_has_node_type,
    assert_flow_uses_connector_target,
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


def _write_flow(tmp_path, node_types, *, project_type: str = "Flow"):
    """Create a minimal project.uiproj + .flow file tree and return its root.

    ``project_type`` is written into the project.uiproj manifest so
    _find_project's manifest-based filtering (MST-9734) can distinguish
    Flow projects from sibling agent / coded / process projects in the
    same solution.
    """
    import json

    proj = tmp_path / "MyFlow"
    proj.mkdir()
    (proj / "project.uiproj").write_text(json.dumps({"ProjectType": project_type}))
    flow = {
        "nodes": [
            node if isinstance(node, dict) else {"id": f"n{i}", "type": node}
            for i, node in enumerate(node_types)
        ]
    }
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


# ── assert_flow_has_any_node_type (weather connector collision, 2026-06-05) ─


def test_assert_flow_has_any_node_type_accepts_connector_only(tmp_path, monkeypatch):
    """Regression lock for the 2026-06-05 bellevue/multi-city failure: the agent
    built the open-meteo call with the curated tenant connector instead of a raw
    HTTP node, so the AND-matcher's `core.action.http` gate failed before
    run_debug. The any-of gate accepts the connector shape."""
    root = _write_flow(
        tmp_path, ["uipath.connector.custom-codereval-openmeteoapis.getcurrentweather"]
    )
    monkeypatch.chdir(root)
    assert_flow_has_any_node_type(
        ["core.action.http", "custom-codereval-openmeteoapis"]
    )


def test_assert_flow_has_any_node_type_accepts_raw_http(tmp_path, monkeypatch):
    """The raw-HTTP shape (e.g. a green run authored as `core.action.http.v2`)
    still satisfies the same any-of gate — backward compatibility."""
    root = _write_flow(tmp_path, ["core.action.http.v2"])
    monkeypatch.chdir(root)
    assert_flow_has_any_node_type(
        ["core.action.http", "custom-codereval-openmeteoapis"]
    )


def test_assert_flow_has_any_node_type_fails_when_none_present(tmp_path, monkeypatch):
    """Neither acceptable shape present → FAIL, and the message names the hints
    and the node types seen."""
    root = _write_flow(tmp_path, ["core.action.script"])
    monkeypatch.chdir(root)
    with pytest.raises(SystemExit) as exc:
        assert_flow_has_any_node_type(
            ["core.action.http", "custom-codereval-openmeteoapis"]
        )
    msg = str(exc.value)
    assert msg.startswith("FAIL:")
    assert "core.action.http" in msg  # hints named
    assert "custom-codereval-openmeteoapis" in msg
    assert "core.action.script" in msg  # types seen


def test_assert_flow_has_any_node_type_empty_hints_is_noop(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no project needed when hints are empty
    assert_flow_has_any_node_type([])


# ── assert_flow_has_exact_node_type (MST-10349) ─────────────────────────────


def test_assert_flow_has_exact_node_type_matches_generic_transform(
    tmp_path, monkeypatch
):
    """Generic chained transform node passes the exact helper."""
    root = _write_flow(tmp_path, ["core.action.transform"])
    monkeypatch.chdir(root)
    assert_flow_has_exact_node_type(["core.action.transform"])


def test_assert_flow_has_exact_node_type_rejects_filter_variant(
    tmp_path, monkeypatch
):
    """A flow whose only transform node is the standalone `.filter` variant
    FAILS the exact helper but PASSES the substring helper — this is exactly
    the difference MST-10349 relies on to reject the variant nodes."""
    root = _write_flow(tmp_path, ["core.action.transform.filter"])
    monkeypatch.chdir(root)
    # Old substring helper still accepts the variant ...
    assert_flow_has_node_type(["core.action.transform"])
    # ... but the exact helper rejects it.
    with pytest.raises(SystemExit, match="exact type 'core.action.transform'"):
        assert_flow_has_exact_node_type(["core.action.transform"])


def test_assert_flow_has_exact_node_type_empty_is_noop(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no project needed when types are empty
    assert_flow_has_exact_node_type([])


# ── assert_flow_uses_connector_target ──────────────────────────────────────


def test_assert_flow_uses_connector_target_accepts_native_connector_node(
    tmp_path, monkeypatch
):
    root = _write_flow(
        tmp_path, ["uipath.connector.uipath-salesforce-slack.ConversationsInfo"]
    )
    monkeypatch.chdir(root)
    assert_flow_uses_connector_target("uipath-salesforce-slack")


def test_assert_flow_uses_connector_target_accepts_http_proxy_binding(
    tmp_path, monkeypatch
):
    root = _write_flow(
        tmp_path,
        [
            {
                "id": "getChannelInfo",
                "type": "core.action.http.v2",
                "inputs": {
                    "detail": {
                        "connectionId": "7aa668d3-12eb-45a6-96d0-59617fd834d7",
                        "connectionFolderKey": "5da18ec0-7de1-4e57-aaf1-ddc8a369c199",
                        "bodyParameters": {
                            "authentication": "connector",
                            "targetConnector": "uipath-salesforce-slack",
                        },
                    }
                },
            }
        ],
    )
    monkeypatch.chdir(root)
    assert_flow_uses_connector_target("uipath-salesforce-slack")


def test_assert_flow_uses_connector_target_rejects_manual_http(tmp_path, monkeypatch):
    root = _write_flow(
        tmp_path,
        [
            {
                "id": "manualRequest",
                "type": "core.action.http.v2",
                "inputs": {
                    "detail": {
                        "connectionId": "ImplicitConnection",
                        "connectionFolderKey": "ImplicitConnection",
                        "bodyParameters": {
                            "authentication": "anonymous",
                            "targetConnector": "uipath-salesforce-slack",
                        },
                    }
                },
            }
        ],
    )
    monkeypatch.chdir(root)
    with pytest.raises(SystemExit, match="uipath-salesforce-slack"):
        assert_flow_uses_connector_target("uipath-salesforce-slack")


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


# ── _find_project (manifest-based Flow filtering, MST-9734) ─────────────────

from flow_check import _find_project, _is_flow_project, find_project_dir  # noqa: E402


def _make_proj(root, name, project_type):
    """Create <root>/<name>/project.uiproj declaring the given ProjectType."""
    import json as _json

    p = root / name
    p.mkdir()
    (p / "project.uiproj").write_text(_json.dumps({"ProjectType": project_type}))
    return p


def test_find_project_picks_flow_when_sibling_agent_exists(tmp_path, monkeypatch):
    """coded_agent / lowcode_agent shape: Flow project + sibling Agent project."""
    monkeypatch.chdir(tmp_path)
    solution = tmp_path / "CountLettersCoded"
    solution.mkdir()
    _make_proj(solution, "CountLetters", "Agent")
    _make_proj(solution, "CountLettersCoded", "Flow")
    found = _find_project("**/project.uiproj")
    # _find_project returns a path relative to cwd (glob default)
    assert found == os.path.join("CountLettersCoded", "CountLettersCoded")


def test_find_project_fails_when_no_flow_present(tmp_path, monkeypatch):
    """All siblings are Agent / Coded — no Flow project to operate on."""
    monkeypatch.chdir(tmp_path)
    solution = tmp_path / "AllAgents"
    solution.mkdir()
    _make_proj(solution, "AgentA", "Agent")
    _make_proj(solution, "AgentB", "Coded")
    with pytest.raises(SystemExit, match="No Flow project.uiproj found"):
        _find_project("**/project.uiproj")


def test_find_project_fails_when_multiple_flows(tmp_path, monkeypatch):
    """Two Flow projects in the same solution: still ambiguous."""
    monkeypatch.chdir(tmp_path)
    solution = tmp_path / "MultiFlow"
    solution.mkdir()
    _make_proj(solution, "FlowA", "Flow")
    _make_proj(solution, "FlowB", "Flow")
    with pytest.raises(SystemExit, match="Multiple Flow projects match"):
        _find_project("**/project.uiproj")


def test_find_project_fails_when_no_candidates(tmp_path, monkeypatch):
    """No project.uiproj at all — original failure message preserved."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match="No project.uiproj found matching"):
        _find_project("**/project.uiproj")


def test_is_flow_project_handles_malformed_manifest(tmp_path):
    """A bad sibling manifest must not crash discovery."""
    bad = tmp_path / "project.uiproj"
    bad.write_text("{not valid json")
    assert _is_flow_project(str(bad)) is False


def test_is_flow_project_handles_missing_file(tmp_path):
    missing = tmp_path / "does-not-exist.uiproj"
    assert _is_flow_project(str(missing)) is False


def test_find_project_dir_uses_central_filter(tmp_path, monkeypatch):
    """The public find_project_dir() helper goes through the same filter."""
    monkeypatch.chdir(tmp_path)
    solution = tmp_path / "Mixed"
    solution.mkdir()
    _make_proj(solution, "Helper", "Process")
    _make_proj(solution, "MainFlow", "Flow")
    assert find_project_dir() == os.path.join("Mixed", "MainFlow")


# ── raw-debug-payload capture on output-assertion failure ───────────────────
#
# When an output assertion fails, the helpers dump the raw `flow debug` response
# (stashed by run_debug) to stderr so a failing eval's task.json preserves the
# full runtime payload. This is the diagnostic for the chronic "Completed but
# Variables/Globals empty" flake (skill-flow-calculator 0.375), whose debug
# session is otherwise ephemeral and unrecoverable after the run.

import json as _json  # noqa: E402

import flow_check  # noqa: E402

# A debug response shaped like the flake: the run Completed and every node
# executed, yet the runtime returned an empty global-variable space.
_FLAKE_RAW = _json.dumps(
    {
        "Result": "Success",
        "Code": "FlowDebug",
        "Data": {
            "FinalStatus": "Completed",
            "Variables": {"Globals": {}, "GlobalVariables": [], "Elements": []},
            "elementExecutions": [
                {"elementId": "start", "elementType": "StartEvent", "status": "Completed"},
                {"elementId": "multiply", "elementType": "ScriptTask", "status": "Completed"},
                {"elementId": "end", "elementType": "EndEvent", "status": "Completed"},
            ],
            "incidents": [],
        },
    }
)


@pytest.fixture
def _reset_debug_raw():
    saved = flow_check._LAST_DEBUG_RAW
    yield
    flow_check._LAST_DEBUG_RAW = saved


def test_output_assert_failure_dumps_raw_capture(capsys, _reset_debug_raw):
    flow_check._LAST_DEBUG_RAW = _FLAKE_RAW
    # Empty Globals → no output equals 391 → fail, and the capture must fire.
    payload = {"variables": {"globals": {}}}
    with pytest.raises(SystemExit, match="expected 391"):
        assert_output_value(payload, 391)
    err = capsys.readouterr().err
    assert "FLOW_DEBUG_RAW_CAPTURE BEGIN" in err
    assert "FLOW_DEBUG_RAW_CAPTURE END" in err
    # The summary localizes the defect: Completed run, nodes ran, globals empty.
    assert '"finalStatus": "Completed"' in err
    assert '"globals": {}' in err
    assert "ScriptTask" in err  # elementExecutions surfaced
    assert _FLAKE_RAW in err  # full raw payload preserved verbatim


def test_output_assert_success_emits_no_capture(capsys, _reset_debug_raw):
    flow_check._LAST_DEBUG_RAW = _FLAKE_RAW  # stale buffer must not leak on success
    payload = _payload(elements=[{"outputs": {"product": 391}}])
    assert_output_value(payload, 391)  # passes
    assert "FLOW_DEBUG_RAW_CAPTURE" not in capsys.readouterr().err


def test_capture_noop_when_no_debug_raw(capsys, _reset_debug_raw):
    flow_check._LAST_DEBUG_RAW = None  # e.g. a static check that never ran debug
    with pytest.raises(SystemExit, match="expected 391"):
        assert_output_value(_payload(globals_=[{"value": 42}]), 391)
    assert "FLOW_DEBUG_RAW_CAPTURE" not in capsys.readouterr().err


def test_capture_summary_survives_cli_preamble(capsys, _reset_debug_raw):
    """The capture must parse via the tolerant _parse_json, like run_debug — so a
    CLI banner before the JSON still yields the structured SUMMARY, not
    `<unparsable>`. Guards the same preamble case run_debug already handles."""
    flow_check._LAST_DEBUG_RAW = (
        "Tool factory already registered for project type 'Flow', skipping.\n"
        "[ManifestClient] fetchDynamicNodes ok: total=59\n" + _FLAKE_RAW
    )
    with pytest.raises(SystemExit, match="expected 391"):
        assert_output_value({"variables": {"globals": {}}}, 391)
    err = capsys.readouterr().err
    assert '"finalStatus": "Completed"' in err  # structured summary recovered
    assert "<unparsable>" not in err


# ── _get_ci / PascalCase tolerance (CLI #2266 contract) ─────────────────────
#
# `uip … --output json` PascalCases its Data keys when the CLI carries PR #2266
# and the command does not opt out via `preserveDataKeys` (flow/case debug DO
# opt out — see uipath-cli debug.ts — but a checker must not depend on which
# CLI build the eval image happens to run). These tests pin that every runtime
# read tolerates BOTH casings, so a future re-introduction of #2266-style
# normalization cannot silently break the maestro-flow debug checkers again.

from flow_check import _get_ci  # noqa: E402


def test_get_ci_reads_camelcase_and_pascalcase():
    assert _get_ci({"finalStatus": "Completed"}, "finalStatus", "FinalStatus") == "Completed"
    assert _get_ci({"FinalStatus": "Completed"}, "finalStatus", "FinalStatus") == "Completed"


def test_get_ci_first_candidate_wins_and_default():
    assert _get_ci({"Status": "x"}, "status", "Status") == "x"
    assert _get_ci({}, "status", "Status", default="<none>") == "<none>"
    assert _get_ci("not-a-dict", "status", default=None) is None


def test_collect_outputs_handles_pascalcase_payload():
    """The exact #2266 shape: every Data key PascalCased. collect_outputs must
    still recover the declared output value (it was silently dropped before)."""
    pascal = {
        "Variables": {
            "GlobalVariables": [{"Name": "result", "Value": "warm"}],
            "Elements": [{"Outputs": {"message": "bring a jacket"}}],
        }
    }
    out = collect_outputs(pascal)
    assert "warm" in out
    assert "bring a jacket" in out


def test_collect_outputs_pascalcase_matches_camelcase():
    """Casing must not change the extracted output set."""
    camel = {
        "variables": {
            "globalVariables": [{"name": "result", "value": 42}],
            "elements": [{"outputs": {"x": "done"}}],
        }
    }
    pascal = {
        "Variables": {
            "GlobalVariables": [{"Name": "result", "Value": 42}],
            "Elements": [{"Outputs": {"x": "done"}}],
        }
    }
    assert sorted(map(str, collect_outputs(camel))) == sorted(map(str, collect_outputs(pascal)))
