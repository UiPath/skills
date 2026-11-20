"""check_multi_city_weather grades the flow's declared output, not the whole debug payload."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.check_multi_city_weather import assert_result_output, read_flow_out_vars  # noqa: E402

CITIES = [
    {"name": "Seattle", "latitude": 47.6062, "longitude": -122.3321},
    {"name": "Phoenix", "latitude": 33.4484, "longitude": -112.074},
    {"name": "New York", "latitude": 40.7128, "longitude": -74.006},
]
RESULTS = [
    {"city": "Seattle", "temperature": 48.2, "verdict": "cold"},
    {"city": "Phoenix", "temperature": 71.6, "verdict": "warm"},
    {"city": "New York", "temperature": 52.0, "verdict": "cold"},
]


def payload(results):
    """A debug payload shaped like the 2026-11-12 nightly's: per-iteration
    script outputs and the inout `cities` list carry every city name."""
    return {
        "variables": {
            "globals": {"results": results, "resultsValue": results, "cities": CITIES},
            "elements": [
                {"elementId": "recordCold", "outputs": {"output": RESULTS[0]}},
                {"elementId": "recordWarm", "outputs": {"output": RESULTS[1]}},
                {"elementId": "recordCold", "outputs": {"output": RESULTS[2]}},
            ],
        }
    }


def test_passes_when_the_output_holds_every_city():
    assert assert_result_output(payload(RESULTS), ["results"]) == "results"


def test_fails_when_the_loop_writes_were_dropped():
    """The case the old whole-payload check graded as a pass."""
    with pytest.raises(SystemExit):
        assert_result_output(payload([]), ["results"])


def test_fails_without_a_declared_output():
    with pytest.raises(SystemExit):
        assert_result_output(payload(RESULTS), [])


def test_any_declared_output_may_hold_the_results():
    p = payload(RESULTS)
    p["variables"]["globals"]["summary"] = "3 cities checked"
    assert assert_result_output(p, ["summary", "results"]) == "results"


def test_reads_only_out_globals(tmp_path):
    flow = tmp_path / "MultiCityWeather.flow"
    flow.write_text(json.dumps({"variables": {"globals": [
        {"id": "results", "direction": "out", "type": "array"},
        {"id": "resultsValue", "direction": "inout", "type": "array"},
        {"id": "cities", "direction": "inout", "type": "array"},
    ]}}))
    assert read_flow_out_vars(str(flow)) == ["results"]
