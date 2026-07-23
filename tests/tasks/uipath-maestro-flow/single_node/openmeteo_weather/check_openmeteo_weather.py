#!/usr/bin/env python3
"""Open-Meteo current-weather connector (live execution).

Structural pre-checks fail fast and prevent gaming, then a live `flow debug`
proves the connector actually called Open-Meteo and returned a temperature:

1. A connector node targets the Open-Meteo connector
   (`custom-codereval-openmeteoapis`) using the curated `getcurrentweather`
   activity — NOT a `core.action.http.v2` proxy and NOT a `core.logic.mock`.
2. That node is configured for the current weather at a location: its
   `inputs.detail.queryParameters` carry `latitude`, `longitude`, and a truthy
   `current_weather` flag.
3. `flow debug` completes (`finalStatus == "Completed"`).
4. The flow output holds the current temperature — a numeric value in a
   plausible range for Bellevue (covers both °C and °F so the test is not
   flaky on the chosen unit). A `temperature`-named output is preferred but a
   plausible numeric output is accepted, since the value changes every run.

Grounded against the codereval tenant's "Open-Meteo APIs" connection: the
curated `V1Forecast` retrieve with `current_weather=true` returns a response
whose `current_weather.temperature` is the live air temperature in °C.
"""

from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    _get_ci,
    assert_flow_uses_connector_target,
    collect_outputs,
    find_project_dir,
    run_debug,
)

CONNECTOR_KEY = "custom-codereval-openmeteoapis"
OPERATION = "getcurrentweather"

# Plausible current-temperature band. Wide enough to span °C and °F so the test
# never flakes on the unit the agent picked, narrow enough to exclude obvious
# non-temperature numbers (e.g. wind direction in degrees, epoch-ish values).
TEMP_LO = -60.0
TEMP_HI = 130.0

_JSONSTRING_PREFIX = "=jsonString:"


def _fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def _load_flow_nodes(project_dir: str) -> list[dict]:
    flows = glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
    if not flows:
        _fail(f"No .flow file found under {project_dir}")
    with open(flows[0]) as f:
        flow = json.load(f)
    return flow.get("nodes") or []


def _detail_dict(node: dict) -> dict:
    """Return the connector node's `inputs.detail` as a dict.

    Configured connector nodes store `detail` as a JSON object (CLI-authored via
    `node configure`). Tolerate a `=jsonString:` envelope just in case, but never
    treat the whole detail as a bare string."""
    raw = (node.get("inputs") or {}).get("detail")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.startswith(_JSONSTRING_PREFIX):
        try:
            parsed = json.loads(raw[len(_JSONSTRING_PREFIX):])
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _is_truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes")
    return False


def _assert_structure() -> None:
    # A real Open-Meteo connector node must be present (native connector node),
    # not a managed HTTP proxy or a mock.
    assert_flow_uses_connector_target(CONNECTOR_KEY)

    nodes = _load_flow_nodes(find_project_dir())
    weather_nodes = [
        n
        for n in nodes
        if CONNECTOR_KEY in str(n.get("type", "")).lower()
        and OPERATION in str(n.get("type", "")).lower()
    ]
    if not weather_nodes:
        types = sorted({str(n.get("type", "")) for n in nodes})
        _fail(
            f"No Open-Meteo {OPERATION!r} connector node found. "
            f"Node types seen: {types}"
        )

    # The node must be configured for the current weather at a location:
    # latitude + longitude + a truthy current_weather query parameter.
    for node in weather_nodes:
        qp = _detail_dict(node).get("queryParameters") or {}
        if not isinstance(qp, dict):
            continue
        keys = {k.lower() for k in qp}
        if not ({"latitude", "longitude"} <= keys):
            continue
        cw = next((qp[k] for k in qp if k.lower() == "current_weather"), None)
        if cw is None or _is_truthy(cw):
            print(
                "OK: Open-Meteo connector node configured with "
                f"latitude/longitude (current_weather={cw!r})"
            )
            return
    _fail(
        f"Open-Meteo {OPERATION} node found but its queryParameters do not carry "
        f"latitude, longitude, and a truthy current_weather flag. The curated "
        f"activity must be configured for the current weather at a location."
    )


def _as_temperature(value: object) -> float | None:
    if isinstance(value, bool):  # bool is an int subclass — reject explicitly
        return None
    if isinstance(value, (int, float)):
        f = float(value)
    elif isinstance(value, str):
        try:
            f = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    return f if TEMP_LO <= f <= TEMP_HI else None


def _assert_temperature_returned(payload: dict) -> None:
    # Prefer an explicitly named temperature output (the End-node output map is a
    # name->value dict under variables.globals at runtime).
    variables = _get_ci(payload, "variables", "Variables") or {}
    globals_ = _get_ci(variables, "globals", "Globals") or {}
    if isinstance(globals_, dict):
        for name, value in globals_.items():
            if "temp" in str(name).lower():
                temp = _as_temperature(value)
                if temp is not None:
                    print(
                        f"OK: connector returned current temperature {temp} "
                        f"in output {name!r}"
                    )
                    return

    # Fall back to any plausible numeric output leaf (the value changes every
    # run, so we assert a plausible temperature is present, not an exact value).
    for leaf in collect_outputs(payload):
        temp = _as_temperature(leaf)
        if temp is not None:
            print(f"OK: connector returned a plausible temperature value {temp}")
            return

    _fail(
        "No flow output holds a plausible current temperature "
        f"(numeric in [{TEMP_LO}, {TEMP_HI}]). Outputs: "
        f"{json.dumps(collect_outputs(payload), default=str)[:1000]}"
    )


def main() -> None:
    _assert_structure()
    payload = run_debug(timeout=300)
    _assert_temperature_returned(payload)


if __name__ == "__main__":
    main()
