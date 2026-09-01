"""Unit tests for flow_check helpers. Run with ``pytest`` from any directory.

These exercise the assertion helpers against hand-crafted ``uip maestro flow debug``
payload shapes so regressions in the eval logic are caught without burning a
real tenant run (as happened with the nested-output flattening bug).
"""

import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import flow_check  # noqa: E402
from flow_check import (  # noqa: E402
    assert_flow_has_any_node_type,
    assert_flow_has_api_node_targeting,
    assert_flow_has_exact_node_type,
    assert_flow_has_node_type,
    assert_flow_uses_connector_target,
    assert_output_int_in_range,
    assert_output_value,
    assert_outputs_contain,
    collect_outputs,
    run_debug,
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


# ── assert_flow_has_api_node_targeting (slack-weather gate, PR #1301) ───────


_SLACK_PROXY_NODE = {
    "id": "readSlack",
    "type": "core.action.http.v2",
    "inputs": {
        "detail": {
            "bodyParameters": {
                "authentication": "connector",
                "targetConnector": "uipath-salesforce-slack",
            },
            "connectionId": "abc-123",
            "connectionFolderKey": "def-456",
        }
    },
}


def test_api_node_targeting_accepts_openmeteo_connector(tmp_path, monkeypatch):
    """The curated connector node targets the service via its own type string."""
    root = _write_flow(
        tmp_path,
        [_SLACK_PROXY_NODE, "uipath.connector.custom-codereval-openmeteoapis.getcurrentweather"],
    )
    monkeypatch.chdir(root)
    assert_flow_has_api_node_targeting(["open-meteo", "openmeteoapis"])


def test_api_node_targeting_accepts_manual_http_url(tmp_path, monkeypatch):
    """A manual HTTP node targets the service via its URL."""
    http_node = {
        "id": "getWeather",
        "type": "core.action.http.v2",
        "inputs": {"detail": {"url": "https://api.open-meteo.com/v1/forecast"}},
    }
    root = _write_flow(tmp_path, [_SLACK_PROXY_NODE, http_node])
    monkeypatch.chdir(root)
    assert_flow_has_api_node_targeting(["open-meteo", "openmeteoapis"])


def test_api_node_targeting_rejects_unrelated_proxy_only(tmp_path, monkeypatch):
    """Regression lock for the #1301 review finding: a Slack connector-proxy
    HTTP node satisfies a bare core.action.http type hint, so a flow with no
    weather node at all could pass the structural gate. The service-targeting
    gate must reject it."""
    root = _write_flow(tmp_path, [_SLACK_PROXY_NODE, "core.action.script"])
    monkeypatch.chdir(root)
    with pytest.raises(SystemExit) as exc:
        assert_flow_has_api_node_targeting(["open-meteo", "openmeteoapis"])
    msg = str(exc.value)
    assert msg.startswith("FAIL:")
    assert "open-meteo" in msg
    assert "core.action.http.v2" in msg  # API-capable types seen


def test_api_node_targeting_ignores_script_mentions(tmp_path, monkeypatch):
    """A Script node that merely mentions the service is not an API call."""
    script_node = {
        "id": "fake",
        "type": "core.action.script",
        "inputs": {"script": "// pretend to call open-meteo here\nreturn 72;"},
    }
    root = _write_flow(tmp_path, [script_node])
    monkeypatch.chdir(root)
    with pytest.raises(SystemExit):
        assert_flow_has_api_node_targeting(["open-meteo", "openmeteoapis"])


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


# ── assert_outputs_contain: input echoes must not satisfy the match ─────────
#
# `variables.globals` carries every global, `in` as well as `out`, and _leaves
# flattens nested objects — so a needle that is also an input used to be matched
# by the input's own value. Observed live on the file-attachment task: a flow
# whose End node mapped the output to a hardcoded literal still "passed" because
# the bound attachment object carried the random FullName the checker searched
# for. These pin the guard that subtracts inputs before matching.


@pytest.fixture
def _no_bound_inputs():
    """Isolate the run_debug stashes — they are process-global state."""
    saved_ids = flow_check._LAST_DEBUG_INPUT_IDS
    saved_dir = flow_check._LAST_DEBUG_PROJECT_DIR
    flow_check._LAST_DEBUG_INPUT_IDS = set()
    flow_check._LAST_DEBUG_PROJECT_DIR = None
    yield
    flow_check._LAST_DEBUG_INPUT_IDS = saved_ids
    flow_check._LAST_DEBUG_PROJECT_DIR = saved_dir


def _globals_payload(mapping):
    """Payload using the dict form the runtime actually returns."""
    return {"variables": {"globals": dict(mapping)}}


def test_trigger_scoped_input_echo_does_not_satisfy_match(_no_bound_inputs):
    # The exact live shape: attachment object under `<trigger>.output.<varId>`,
    # real output hardcoded to something else.
    payload = _globals_payload(
        {
            "start.output.inputDoc": {
                "ID": "1106735d-3076-4315-92ab-08defd736ffd",
                "FullName": "evidence-2ba9f1a197d0.txt",
                "MimeType": "application/octet-stream",
                "Metadata": {"size": "8"},
            },
            "fileName": "sample-report.txt",
        }
    )
    with pytest.raises(SystemExit, match="INPUT ECHO"):
        assert_outputs_contain(payload, "evidence-2ba9f1a197d0.txt")


def test_bound_input_id_echo_does_not_satisfy_match(_no_bound_inputs):
    # Plain (non-trigger) input, keyed by bare id — indistinguishable from an
    # output by shape alone, so the guard leans on what run_debug bound.
    flow_check._LAST_DEBUG_INPUT_IDS = {"webhookPayload"}
    payload = _globals_payload(
        {
            "webhookPayload": {"invoice": {"invoiceNumber": "MCS-2026-04872"}},
            "resolution": "unable to process",
        }
    )
    with pytest.raises(SystemExit, match="INPUT ECHO"):
        assert_outputs_contain(payload, "MCS-2026-04872")


def test_declared_input_echo_does_not_satisfy_match(tmp_path, _no_bound_inputs):
    # An `in` global with a defaultValue echoes even though no checker bound it.
    # Caught only with project_dir, since neither key shape nor the stash sees it.
    import json as _json

    proj = tmp_path / "MyFlow"
    proj.mkdir()
    (proj / "MyFlow.flow").write_text(
        _json.dumps(
            {
                "variables": {
                    "globals": [
                        {"id": "cities", "direction": "in", "defaultValue": ["Seattle"]},
                        {"id": "report", "direction": "out"},
                    ]
                }
            }
        )
    )
    payload = _globals_payload({"cities": ["Seattle"], "report": "no data"})

    # With no project known at all, key shape and the bind-stash see nothing...
    assert_outputs_contain(payload, "Seattle")
    # ...an explicit project_dir reports the vacuous match...
    with pytest.raises(SystemExit, match="INPUT ECHO"):
        assert_outputs_contain(payload, "Seattle", project_dir=str(proj))
    # ...and so does the project run_debug resolved, with no opt-in at the call
    # site. This is what closes the defaultValue case suite-wide.
    flow_check._LAST_DEBUG_PROJECT_DIR = str(proj)
    with pytest.raises(SystemExit, match="INPUT ECHO"):
        assert_outputs_contain(payload, "Seattle")


def test_real_output_still_passes_when_it_also_appears_in_input(_no_bound_inputs):
    # Subtracting inputs must not create false failures: when the flow genuinely
    # produces the value, matching it is legitimate even though an input echoes it.
    flow_check._LAST_DEBUG_INPUT_IDS = {"inputDoc"}
    payload = _globals_payload(
        {
            "start.output.inputDoc": {"FullName": "evidence-abc.txt"},
            "fileName": "evidence-abc.txt",
        }
    )
    assert_outputs_contain(payload, "evidence-abc.txt")


def test_element_outputs_are_never_subtracted(_no_bound_inputs):
    # Node results are genuine outputs regardless of the input-key filter.
    flow_check._LAST_DEBUG_INPUT_IDS = {"inputDoc"}
    payload = {
        "variables": {
            "globals": {"start.output.inputDoc": {"FullName": "evidence-xyz.txt"}},
            "elements": [{"outputs": {"echo": "evidence-xyz.txt"}}],
        }
    }
    assert_outputs_contain(payload, "evidence-xyz.txt")


def test_allow_input_echo_restores_whole_payload_match(_no_bound_inputs):
    payload = _globals_payload(
        {"start.output.inputDoc": {"FullName": "evidence-def.txt"}}
    )
    with pytest.raises(SystemExit):
        assert_outputs_contain(payload, "evidence-def.txt")
    assert_outputs_contain(payload, "evidence-def.txt", allow_input_echo=True)


def test_collect_outputs_still_includes_inputs(_no_bound_inputs):
    # collect_outputs is unchanged — billing_dispute_resolution uses it for a
    # "did the run produce anything at all" check that must stay permissive.
    payload = _globals_payload(
        {"start.output.inputDoc": {"FullName": "evidence-ghi.txt"}}
    )
    assert "evidence-ghi.txt" in collect_outputs(payload)


def test_input_echo_note_absent_for_an_ordinary_miss(_no_bound_inputs):
    # A needle that appears nowhere is a plain miss, not an input echo — the
    # remediation hint must not fire and misdirect the reader.
    payload = _globals_payload({"fileName": "sample-report.txt"})
    with pytest.raises(SystemExit) as exc:
        assert_outputs_contain(payload, "nowhere-to-be-found")
    assert "INPUT ECHO" not in str(exc.value)


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


# ── run_debug transient server-error retry ───────────────────────────────────


_TRANSIENT_504 = (
    '{\n  "Result": "Failure",\n'
    '  "Message": "Failed during poll-instance-status: HTTP 504 on GET /api/v1/debug-instances/x/element-executions",\n'
    '  "Context": {"HttpStatus": 504, "Stage": "poll-instance-status"},\n'
    '  "ErrorCode": "server_error",\n  "Retry": "RetryLater"\n}'
)
_COMPLETED = (
    '{\n  "Result": "Success",\n'
    '  "Data": {"finalStatus": "Completed", "variables": {"globalVariables": '
    '[{"name": "severity", "value": "Sev1"}]}}\n}'
)
# Verbatim envelope from `uip maestro flow debug --timeout 1`. The
# `RetryWillNotFix` label is wrong for a poll timeout, so we match the Message.
_POLL_TIMEOUT = (
    '{\n  "Result": "Failure",\n'
    '  "Message": "Debug polling timed out after 180s",\n'
    '  "Instructions": "Check that the flow project is valid, the selected folder '
    'is accessible, and Studio Web debug is available, then retry.",\n'
    '  "ErrorCode": "unknown_error",\n  "Retry": "RetryWillNotFix"\n}'
)


def _cp(returncode, stdout="", stderr=""):
    return subprocess.CompletedProcess(
        args=["uip", "maestro", "flow", "debug"], returncode=returncode, stdout=stdout, stderr=stderr
    )


def _stub_debug(monkeypatch, results):
    """Feed run_debug a queue of CompletedProcess results, stub sleep to be
    instant, and stub project discovery so no real tree is needed.

    A queued ``BaseException`` is raised rather than returned, which is how the
    ``subprocess.TimeoutExpired`` path is exercised. The last invocation's
    ``cmd`` / ``env`` / ``timeout`` are recorded for assertions."""
    calls = {"n": 0, "cmd": None, "env": None, "timeout": None}
    queue = list(results)
    monkeypatch.setattr(flow_check, "_find_project", lambda pattern: "/tmp/proj")
    monkeypatch.setattr(flow_check.time, "sleep", lambda *_: None)

    def fake_run(cmd, **kwargs):
        calls["n"] += 1
        calls["cmd"] = cmd
        calls["env"] = kwargs.get("env")
        calls["timeout"] = kwargs.get("timeout")
        result = queue.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result

    monkeypatch.setattr(flow_check.subprocess, "run", fake_run)
    return calls


def test_run_debug_retries_transient_504_then_completes(monkeypatch):
    calls = _stub_debug(monkeypatch, [_cp(1, _TRANSIENT_504), _cp(0, _COMPLETED)])
    payload = run_debug(inputs={"x": 1})
    assert calls["n"] == 2
    assert flow_check._get_ci(payload, "finalStatus") == "Completed"


def test_run_debug_does_not_retry_real_fault(monkeypatch):
    """A run that returns exit 0 but did not complete is a real flow fault —
    fail immediately, no retry."""
    faulted = '{\n  "Result": "Success",\n  "Data": {"finalStatus": "Faulted"}\n}'
    calls = _stub_debug(monkeypatch, [_cp(0, faulted)])
    with pytest.raises(SystemExit):
        run_debug()
    assert calls["n"] == 1


def test_run_debug_does_not_retry_nontransient_error(monkeypatch):
    """A non-5xx / non-RetryLater failure (e.g. bad input) is returned on the
    first attempt."""
    bad = '{\n  "Result": "Failure",\n  "ErrorCode": "invalid_argument",\n  "Retry": "RetryWillNotFix"\n}'
    calls = _stub_debug(monkeypatch, [_cp(1, bad)])
    with pytest.raises(SystemExit):
        run_debug()
    assert calls["n"] == 1


def test_run_debug_exhausts_retries_on_persistent_504(monkeypatch):
    calls = _stub_debug(monkeypatch, [_cp(1, _TRANSIENT_504)] * 3)
    with pytest.raises(SystemExit):
        run_debug(retries=3)
    assert calls["n"] == 3


@pytest.mark.parametrize(
    "cp,expected",
    [
        (_cp(0, _COMPLETED), False),                                   # success: never transient
        (_cp(1, _TRANSIENT_504), True),                                # RetryLater + server_error + 504
        (_cp(1, '{"Retry": "RetryLater"}'), True),                     # marker alone
        (_cp(1, '{"ErrorCode": "server_error"}'), True),               # marker alone
        (_cp(1, '{"Context": {"HttpStatus": 503}}'), True),            # 5xx via HttpStatus
        (_cp(1, '{"ErrorCode": "invalid_argument", "Retry": "RetryWillNotFix"}'), False),
        (_cp(1, '{"Context": {"HttpStatus": 404}}'), False),           # 4xx is not transient
        (_cp(1, _POLL_TIMEOUT), True),                                 # CLI poll-budget expiry
    ],
)
def test_is_transient_debug_error(cp, expected):
    assert flow_check._is_transient_debug_error(cp) is expected


# ── run_debug: completed but outputs unreadable (variables fetch failed) ─────

# Verbatim shape of the 2026-09-01 move-node/v2 payload: every element
# Completed, no `variables` key anywhere in Data.
_COMPLETED_NO_VARIABLES = (
    '{\n  "Result": "Success",\n  "Code": "FlowDebug",\n'
    '  "Data": {"jobKey": "j", "instanceId": "609c57fa", "finalStatus": "Completed",\n'
    '           "elementExecutions": [{"elementId": "end", "status": "Completed"}]},\n'
    '  "Instructions": "Debug completed with status: Completed"\n}'
)
# Shape emitted by the fixed CLI: still no `variables`, plus the structured reason.
_COMPLETED_VARIABLES_ERROR = (
    '{\n  "Result": "Success",\n  "Code": "FlowDebug",\n'
    '  "Data": {"instanceId": "609c57fa", "finalStatus": "Completed", "elementExecutions": [],\n'
    '           "variablesError": {"message": "pims API request failed: 403 Forbidden", '
    '"httpStatus": 403, "attempts": 4, "traceIds": ["t1"], '
    '"endpoint": "/api/v1/debug-instances/609c57fa/variables"}}\n}'
)
# A run whose flow declares no outputs: `variables` is PRESENT and empty. Real result.
_COMPLETED_EMPTY_VARIABLES = (
    '{\n  "Result": "Success",\n'
    '  "Data": {"finalStatus": "Completed", "variables": {"globals": {}, "elements": []}}\n}'
)
_CLI_STDERR = (
    "Polling for completion...\nStatus: Completed (9/9 elements completed)\n"
    "Fetching output variables...\n"
    "[WARN] Could not fetch variables: pims API request failed: 403 Forbidden on GET "
    "/api/v1/debug-instances/609c57fa/variables\n"
)


def test_run_debug_retries_completed_without_variables_then_returns_outputs(monkeypatch):
    """A Completed payload with no `variables` key is a failed fetch, not a
    result — retry the debug once; the second run's outputs are graded."""
    calls = _stub_debug(
        monkeypatch,
        [_cp(0, _COMPLETED_NO_VARIABLES, _CLI_STDERR), _cp(0, _COMPLETED)],
    )
    payload = run_debug()
    assert calls["n"] == 2
    assert flow_check.collect_outputs(payload) == ["Sev1"]


def test_run_debug_retries_variables_error_payload(monkeypatch):
    calls = _stub_debug(
        monkeypatch, [_cp(0, _COMPLETED_VARIABLES_ERROR), _cp(0, _COMPLETED)]
    )
    payload = run_debug()
    assert calls["n"] == 2
    assert flow_check.collect_outputs(payload) == ["Sev1"]


def test_run_debug_persistent_unreadable_outputs_fails_as_infra(monkeypatch, capsys):
    """Both attempts complete with unreadable outputs: fail with an INFRA
    message and the capture (RAW + the CLI's STDERR), never as
    'Outputs missing' — that verdict would blame the flow."""
    calls = _stub_debug(
        monkeypatch,
        [
            _cp(0, _COMPLETED_NO_VARIABLES, _CLI_STDERR),
            _cp(0, _COMPLETED_NO_VARIABLES, _CLI_STDERR),
        ],
    )
    with pytest.raises(SystemExit) as exc:
        run_debug()
    assert calls["n"] == flow_check._VARIABLES_UNREADABLE_ATTEMPTS == 2
    msg = str(exc.value)
    assert "could not be read" in msg
    assert "INFRA" in msg
    assert "Outputs missing" not in msg
    err = capsys.readouterr().err
    assert "FLOW_DEBUG_RAW_CAPTURE BEGIN" in err
    assert "STDERR (tail):" in err
    assert "Could not fetch variables" in err


def test_run_debug_does_not_retry_present_but_empty_variables(monkeypatch):
    """`variables` present and empty is a genuine 'no outputs' result — return
    it on the first attempt so the caller's assertion grades it."""
    calls = _stub_debug(monkeypatch, [_cp(0, _COMPLETED_EMPTY_VARIABLES)])
    payload = run_debug()
    assert calls["n"] == 1
    assert flow_check.collect_outputs(payload) == []


def test_run_debug_unreadable_retry_does_not_burn_the_transient_budget(monkeypatch):
    """The unreadable-outputs retry is its own budget (2), independent of the
    3 attempts reserved for 5xx/RetryLater."""
    calls = _stub_debug(
        monkeypatch,
        [_cp(1, _TRANSIENT_504), _cp(0, _COMPLETED_NO_VARIABLES), _cp(0, _COMPLETED)],
    )
    payload = run_debug()
    assert calls["n"] == 3
    assert flow_check.collect_outputs(payload) == ["Sev1"]


@pytest.mark.parametrize(
    "stdout,expected",
    [
        (_COMPLETED, None),
        (_COMPLETED_EMPTY_VARIABLES, None),
        ('{"Result": "Success", "Data": {"finalStatus": "Faulted"}}', None),  # not Completed: other path
        (_COMPLETED_NO_VARIABLES, "no `variables` key"),
        (_COMPLETED_VARIABLES_ERROR, "variablesError after 4 attempt(s)"),
    ],
)
def test_variables_unreadable_classifier(stdout, expected):
    reason = flow_check._variables_unreadable(flow_check._parse_json(stdout))
    if expected is None:
        assert reason is None
    else:
        assert expected in reason


def test_capture_includes_cli_stderr_tail(capsys, _reset_debug_raw, monkeypatch):
    monkeypatch.setattr(flow_check, "_LAST_DEBUG_STDERR", _CLI_STDERR)
    flow_check._LAST_DEBUG_RAW = _COMPLETED_NO_VARIABLES
    with pytest.raises(SystemExit):
        flow_check._fail_with_capture("boom")
    err = capsys.readouterr().err
    assert "STDERR (tail): Polling for completion..." in err
    assert "Could not fetch variables" in err


# ── run_debug timeout budget + diagnostics ───────────────────────────────────
#
# Regression cover for skill-flow-wiki-pageviews: the subprocess cap fired below
# the CLI's own poll budget, SIGKILLing it mid-run, so a correct artifact scored
# 0 with nothing left to diagnose from.


def test_run_debug_passes_derived_cli_timeout(monkeypatch):
    calls = _stub_debug(monkeypatch, [_cp(0, _COMPLETED)])
    run_debug(timeout=240)
    cmd = calls["cmd"]
    assert cmd[cmd.index("--timeout") + 1] == "180"  # 240 - 60 headroom
    assert calls["timeout"] == 240


def test_run_debug_cli_timeout_never_goes_below_floor(monkeypatch):
    calls = _stub_debug(monkeypatch, [_cp(0, _COMPLETED)])
    run_debug(timeout=45)
    cmd = calls["cmd"]
    assert cmd[cmd.index("--timeout") + 1] == str(flow_check._MIN_CLI_TIMEOUT_SECONDS)


def test_run_debug_sets_uip_log_level_for_instance_id(monkeypatch):
    """The only channel that emits jobKey / instanceId / Studio Web URL."""
    monkeypatch.delenv("UIP_LOG_LEVEL", raising=False)
    calls = _stub_debug(monkeypatch, [_cp(0, _COMPLETED)])
    run_debug()
    assert calls["env"]["UIP_LOG_LEVEL"] == "info"


def test_run_debug_keeps_operator_log_level(monkeypatch):
    monkeypatch.setenv("UIP_LOG_LEVEL", "debug")
    calls = _stub_debug(monkeypatch, [_cp(0, _COMPLETED)])
    run_debug()
    assert calls["env"]["UIP_LOG_LEVEL"] == "debug"


def test_run_debug_retries_poll_timeout_then_completes(monkeypatch):
    calls = _stub_debug(monkeypatch, [_cp(1, _POLL_TIMEOUT), _cp(0, _COMPLETED)])
    payload = run_debug()
    assert calls["n"] == 2
    assert flow_check._get_ci(payload, "finalStatus") == "Completed"


def test_run_debug_caps_poll_timeout_attempts(monkeypatch):
    """Stops at _POLL_TIMEOUT_ATTEMPTS even when `retries` allows more."""
    calls = _stub_debug(monkeypatch, [_cp(1, _POLL_TIMEOUT)] * 3)
    with pytest.raises(SystemExit):
        run_debug(retries=3)
    assert calls["n"] == flow_check._POLL_TIMEOUT_ATTEMPTS == 2


def test_run_debug_subprocess_timeout_fails_cleanly(monkeypatch):
    """A stall upstream of polling exits as a graded FAIL carrying the partial
    output, not as an uncaught TimeoutExpired traceback."""
    exc = subprocess.TimeoutExpired(
        cmd=["uip", "maestro", "flow", "debug"],
        timeout=240,
        output=b'{"partial": true}',
        stderr=b"Debug instance created - instanceId: abc-123\n",
    )
    calls = _stub_debug(monkeypatch, [exc])
    with pytest.raises(SystemExit) as excinfo:
        run_debug(timeout=240)
    assert calls["n"] == 1
    message = str(excinfo.value)
    assert "240s subprocess cap" in message
    assert "abc-123" in message  # without the instanceId the run is unrecoverable
    assert flow_check._LAST_DEBUG_RAW == '{"partial": true}'


@pytest.mark.parametrize(
    "raw,expected",
    [
        (b"bytes payload", "bytes payload"),  # TimeoutExpired hands back bytes
        ("str payload", "str payload"),  # CompletedProcess hands back str
        (None, ""),
        (b"\xff\xfe bad utf8", "�� bad utf8"),
    ],
)
def test_as_text_decodes_defensively(raw, expected):
    assert flow_check._as_text(raw) == expected
