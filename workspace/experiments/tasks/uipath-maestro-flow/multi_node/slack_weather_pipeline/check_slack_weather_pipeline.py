#!/usr/bin/env python3
"""Slack weather pipeline: Slack connector + HTTP + decision all ran, and the
mapped `weatherVerdict` output holds one of the two allowed verdicts.

The behavior grade scopes to the named `weatherVerdict` output global rather
than sweeping every runtime global and element output. A whole-payload sweep is
a false pass here: the Slack channel description and the raw HTTP response body
both land in element outputs, so a flow that never mapped a verdict into a flow
output can still make the verdict text "present" somewhere in the debug dump.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    _fail_with_capture,
    assert_flow_has_api_node_targeting,
    assert_flow_uses_connector_target,
    assert_output_nonempty,
    run_debug,
)

ALLOWED_VERDICTS = ("warm office today", "cold office today")


def main():
    # Must have a real Slack-backed connector call and a weather-API node —
    # proves the pipeline isn't shortcutting by hardcoding the city or skipping
    # the Slack read. The Slack call may be represented as an HTTP v2 proxy node.
    # The weather call may be a raw HTTP node OR the curated Open-Meteo
    # connector (the skill's node-selection ladder may pick either) — but it
    # must actually TARGET open-meteo: a bare core.action.http hint would be
    # satisfied by the Slack HTTP proxy node above, letting a flow with no
    # weather node at all pass the structural gate.
    assert_flow_uses_connector_target("uipath-salesforce-slack")
    assert_flow_has_api_node_targeting(["open-meteo", "openmeteoapis"])

    payload = run_debug(timeout=240)

    value = assert_output_nonempty(payload, "weatherVerdict")
    text = str(value).lower()
    hits = [v for v in ALLOWED_VERDICTS if v in text]
    if len(hits) != 1:
        found = "both verdicts" if len(hits) > 1 else "neither verdict"
        _fail_with_capture(
            f"weatherVerdict must contain exactly one of {list(ALLOWED_VERDICTS)}; "
            f"found {found}. weatherVerdict={value!r}"
        )

    print(
        "OK: Slack connector target + weather-API node + decision all executed, "
        f"weatherVerdict carries {hits[0]!r}"
    )


if __name__ == "__main__":
    main()
