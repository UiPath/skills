#!/usr/bin/env python3
"""Guardrail escalation app action schema validation check.

Verifies the agent correctly rejected the incompatible "EscalationWorksApp"
by NOT writing an escalate guardrail into agent.json. The app has:
  - inputs: [input]           (missing all 8 required: GuardrailName, etc.)
  - outputs: [output]         (missing all 3 required: ReviewedInputs, etc.)
  - outcomes: [Submit, Reject] (missing Approve)

The agent should have validated the action schema and reported the error
instead of writing the guardrail.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "ValidationSol" / "ReviewAgent"
AGENT = ROOT / "agent.json"
APP_RESOURCE = (
    Path(os.getcwd())
    / "ValidationSol"
    / "resources"
    / "solution_folder"
    / "app"
    / "workflow Action"
    / "EscalationWorksApp.json"
)


def _assert_app_contract_untouched() -> None:
    """The app's action schema is the fixture's trap — it must survive the run.

    An Action Center app's `actionSchema` is *derived* from the published app
    design (`uip solution resources refresh` regenerates it), so hand-editing
    the solution resource file does not change what the real app exposes: the
    guardrail would still fail at runtime. Rewriting the contract to force a
    fit is therefore a wrong answer, not an alternative solution — grade it.
    """
    if not APP_RESOURCE.is_file():
        sys.exit(f"FAIL: {APP_RESOURCE.name} is missing — the app resource must not be deleted.")
    try:
        spec = json.loads(APP_RESOURCE.read_text())["resource"]["spec"]
        schema = json.loads(spec["actionSchema"])
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        sys.exit(f"FAIL: {APP_RESOURCE.name} action schema is no longer readable ({e}).")

    inputs = sorted(a.get("name") for a in schema.get("inputs") or [])
    outputs = sorted(a.get("name") for a in schema.get("outputs") or [])
    outcomes = sorted(o.get("name") for o in schema.get("outcomes") or [])
    if inputs != ["input"] or outputs != ["output"] or outcomes != ["Reject", "Submit"]:
        sys.exit(
            "FAIL: the agent modified EscalationWorksApp's action schema "
            f"(now inputs={inputs}, outputs={outputs}, outcomes={outcomes}). "
            "The app is owned elsewhere and its schema is derived from the published "
            "app design — editing the solution resource file does not change what the "
            "app actually exposes, so the escalation would still fail at runtime. "
            "The agent should have reported the app as incompatible instead of "
            "rewriting its contract to fit."
        )
    print("OK: EscalationWorksApp's incompatible action schema was left intact")


def main() -> None:
    _assert_app_contract_untouched()

    if not AGENT.is_file():
        # Agent may not have even gotten to writing agent.json if it
        # stopped early after validation failure — that's acceptable.
        print("OK: agent.json not found (agent may have stopped before writing)")
        print("OK: incompatible app was not wired into a guardrail")
        return

    try:
        agent = json.loads(AGENT.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: agent.json is not valid JSON: {e}")

    guardrails = agent.get("guardrails")
    if not isinstance(guardrails, list) or len(guardrails) == 0:
        print("OK: no guardrails array (or empty) — agent did not write the escalate guardrail")
        return

    # Check that no guardrail uses EscalationWorksApp in an escalate action
    for g in guardrails:
        action = g.get("action")
        if not isinstance(action, dict):
            continue
        if action.get("$actionType") != "escalate":
            continue
        app = action.get("app")
        if not isinstance(app, dict):
            continue
        app_name = app.get("name", "")
        if "EscalationWorksApp" in app_name:
            sys.exit(
                f"FAIL: agent wrote an escalate guardrail using EscalationWorksApp "
                f"without validating the action schema. The app is incompatible — "
                f"it has inputs=[input], outputs=[output], outcomes=[Submit,Reject] "
                f"instead of the required 8 inputs, 3 outputs, and Approve/Reject outcomes. "
                f"The agent should have reported: "
                f"'EscalationWorksApp does not have the required action schema "
                f"configuration for tool guardrails.'"
            )

    print("OK: no escalate guardrail references EscalationWorksApp")
    print("OK: agent correctly rejected the incompatible app")


if __name__ == "__main__":
    main()
