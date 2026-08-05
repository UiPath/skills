#!/usr/bin/env python3
"""Stale-shadow check for skill-flow-inline-agent-stale-shadow.

The sandbox starts with a self-contained inline agent in
`RefundSol/RefundTriage/RefundTriage.flow` whose derived sidecar
(`RefundTriage/9d41c7b2-…/agent.json`) is STALE — an older generation of the
same agent: weaker model, looser limits, no guardrail, one output instead of
two, and only one of the two prompt bindings. The `.flow` is the source of
truth; the sidecar is build output the canvas overwrites on the next save.

The prompt asks for a behaviour change in business terms. Grading is therefore
two-sided:

  1. The edit landed on the node — `riskTier` typed output plus a risk
     instruction in a prompt, surfaced as a flow output.
  2. Nothing regressed to the stale copy — model, limits, guardrail, both typed
     outputs and both `$vars` bindings still match the `.flow`, and no
     distinctive phrase of the stale prompts appears on the node.

Plus the standing contract: identity preserved, canvas token namespace, no
stored-file envelope keys in `inputs`, definition present at the instance
`(type, typeVersion)` with the inline serviceType, agent still on the
trigger→end sequence path.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.flow_inline_wiring import (  # noqa: E402
    load_json,
    find_flow_file,
    find_autonomous_agent_node,
    assert_embedded_agent,
    assert_prompt_tokens,
    assert_agent_input_vars,
    assert_agent_output_vars,
    assert_agent_sequence_wiring,
    assert_definition_present,
)

INLINE_AGENT_SERVICE_TYPE = "Orchestrator.StartInlineAgentJob"
FLOW_PATH = Path(os.getcwd()) / "RefundSol" / "RefundTriage" / "RefundTriage.flow"

# Fixture ground truth — the LIVE values in the `.flow`.
AGENT_GUID = "9d41c7b2-6e58-4a0d-8f13-27b5c9e0a48d"
LIVE_MODEL = "gpt-4.1-2025-04-14"
LIVE_MAX_TOKENS = 4096
LIVE_MAX_ITERATIONS = 8
LIVE_TEMPERATURE = 0.1
LIVE_PROMPT_MARKERS = ("manual-review", "payments playbook", "500")
LIVE_VARS_PATHS = (
    "$vars.start.output.requestDetails",
    "$vars.start.output.amountEur",
)

# Ground truth of the STALE sidecar — anything from this column appearing on the
# node means the agent re-synced from the derived artifact.
STALE_MODEL = "gpt-4o-mini-2024-07-18"
STALE_MAX_TOKENS = 16384
STALE_MAX_ITERATIONS = 25
STALE_TEMPERATURE = 0.9
STALE_PROMPT_MARKERS = ("refund clerk", "2000", "paid out immediately", "decide now")

STORED_ONLY_INPUT_KEYS = (
    "messages",
    "settings",
    "inputSchema",
    "outputSchema",
    "engine",
    "metadata",
    "projectId",
    "type",
)
NEW_OUTPUT = "riskTier"


def check_not_regressed(inputs: dict) -> None:
    errs = []
    model = inputs.get("model")
    if model == STALE_MODEL:
        errs.append(
            f"inputs.model was reset to the stale sidecar's {STALE_MODEL!r} — "
            f"the live flow runs {LIVE_MODEL!r}; the `.flow` wins over the "
            "derived copy"
        )
    elif model != LIVE_MODEL:
        errs.append(
            f"inputs.model is {model!r}, expected the flow's own {LIVE_MODEL!r} "
            "— the request did not ask for a model change"
        )

    for key, live, stale in (
        ("maxTokenPerResponse", LIVE_MAX_TOKENS, STALE_MAX_TOKENS),
        ("maxIterations", LIVE_MAX_ITERATIONS, STALE_MAX_ITERATIONS),
        ("temperature", LIVE_TEMPERATURE, STALE_TEMPERATURE),
    ):
        value = inputs.get(key)
        if value == stale:
            errs.append(
                f"inputs.{key} was reset to the stale sidecar's {stale!r} "
                f"(flow value: {live!r})"
            )
        elif value != live:
            errs.append(f"inputs.{key} is {value!r}, expected the flow's {live!r}")

    guardrails = inputs.get("guardrails")
    if not isinstance(guardrails, list) or not guardrails:
        errs.append(
            "inputs.guardrails is empty — the stale sidecar has no guardrails, "
            "the live flow has a prompt-injection block; dropping it is a "
            "silent security regression"
        )
    else:
        entry = next(
            (
                g for g in guardrails
                if isinstance(g, dict) and g.get("validatorType") == "prompt_injection"
            ),
            None,
        )
        if entry is None:
            errs.append(
                "no guardrail with validatorType 'prompt_injection' left on the "
                f"node (have {[g.get('validatorType') for g in guardrails if isinstance(g, dict)]})"
            )
        else:
            if (entry.get("action") or {}).get("$actionType") != "block":
                errs.append(
                    "prompt-injection guardrail no longer blocks "
                    f"(action.$actionType {(entry.get('action') or {}).get('$actionType')!r})"
                )
            scopes = (entry.get("selector") or {}).get("scopes")
            if not isinstance(scopes, list) or "Llm" not in scopes:
                errs.append(
                    f"prompt-injection guardrail selector.scopes is {scopes!r}, "
                    "expected to include 'Llm'"
                )

    if errs:
        sys.exit("FAIL (regressed to the stale sidecar): " + "; ".join(errs))
    print(
        f"OK: settings and guardrail still match the flow — model {LIVE_MODEL}, "
        f"maxTokenPerResponse {LIVE_MAX_TOKENS}, maxIterations "
        f"{LIVE_MAX_ITERATIONS}, prompt-injection block on Llm"
    )


def check_prompts(inputs: dict) -> None:
    both = f"{inputs.get('systemPrompt') or ''}\n{inputs.get('userPrompt') or ''}"
    lowered = both.lower()
    errs = []

    stale_hits = [m for m in STALE_PROMPT_MARKERS if m in lowered]
    if stale_hits:
        errs.append(
            f"prompt text pulled in from the stale sidecar: {stale_hits} — the "
            "derived copy is older than the flow; never author from it"
        )
    if not any(m in lowered for m in LIVE_PROMPT_MARKERS):
        errs.append(
            "no distinctive phrase of the flow's own system prompt survived "
            f"(looked for any of {list(LIVE_PROMPT_MARKERS)}) — the live "
            "instructions were overwritten"
        )
    missing = [p for p in LIVE_VARS_PATHS if p not in both]
    if missing:
        errs.append(
            f"lost flow-data binding(s) {missing} — the stale sidecar only "
            "referenced the request text, the flow also reads the amount"
        )
    if "risk" not in lowered:
        errs.append(
            "neither prompt instructs the agent about the fraud-risk tier — the "
            "requested change did not land on the node"
        )
    if errs:
        sys.exit("FAIL (prompts): " + "; ".join(errs))
    print("OK: live prompts kept, both bindings intact, risk instruction added")


def check_no_stored_scaffolding(node: dict) -> None:
    inputs = node.get("inputs") or {}
    leaked = [k for k in STORED_ONLY_INPUT_KEYS if k in inputs]
    if leaked:
        sys.exit(
            f"FAIL ({node.get('id')}): stored-file keys leaked into node "
            f"inputs: {leaked} — the sidecar's envelope (messages/settings/"
            "schemas/engine/metadata) has no place in the node"
        )
    print("OK: no sidecar envelope keys leaked into node inputs")


def check_flow_output(flow: dict, agent_id: str) -> None:
    globals_ = (flow.get("variables") or {}).get("globals") or []
    out_ids = {
        g.get("id") for g in globals_
        if isinstance(g, dict) and g.get("direction") == "out"
    }
    missing = [g for g in ("handlingPath", "summary", NEW_OUTPUT) if g not in out_ids]
    if missing:
        sys.exit(
            f"FAIL: missing 'out' global(s) {missing} (have {sorted(out_ids)}) — "
            f"{NEW_OUTPUT} must be surfaced alongside the existing flow outputs"
        )

    mappings = []
    for node in flow.get("nodes") or []:
        if node.get("type") != "core.control.end":
            continue
        for out_id, spec in (node.get("outputs") or {}).items():
            expression = ((spec or {}).get("source") or {}).get("expression")
            if isinstance(expression, str):
                mappings.append((out_id, expression))

    wrapped = [(o, e) for o, e in mappings if "output.content." in e]
    if wrapped:
        sys.exit(
            f"FAIL: end-node mapping uses the '.content.' wrapper: {wrapped} — "
            f"typed agent outputs surface flat at $vars.{agent_id}.output.<field>"
        )
    for expected in ("handlingPath", "summary", NEW_OUTPUT):
        if not any(expected in e and agent_id in e for _, e in mappings):
            sys.exit(
                f"FAIL: no end-node output maps {expected!r} from the agent "
                f"(expected $vars.{agent_id}.output.{expected}; have {mappings})"
            )
    print(f"OK: {NEW_OUTPUT} mapped out alongside handlingPath and summary")


def main() -> None:
    flow = load_json(find_flow_file(FLOW_PATH))
    node = find_autonomous_agent_node(flow)

    inputs = assert_embedded_agent(node)
    print(f"OK: {node['id']} is still self-contained")

    if inputs.get("source") != AGENT_GUID:
        sys.exit(
            f"FAIL ({node['id']}): inputs.source is {inputs.get('source')!r}, "
            f"expected the existing {AGENT_GUID!r} — the agent's identity is "
            "the derived folder name and the packaging identity; an edit keeps it"
        )
    print(f"OK: identity preserved (inputs.source still {AGENT_GUID})")

    assert_prompt_tokens(node, require_vars_ref=True)
    check_prompts(inputs)
    check_not_regressed(inputs)
    check_no_stored_scaffolding(node)

    assert_agent_input_vars(node)
    assert_agent_output_vars(
        node,
        {"handlingPath": "string", "summary": "string", NEW_OUTPUT: "string"},
    )
    print(
        "OK: typed outputs kept (handlingPath, summary) and extended with "
        f"{NEW_OUTPUT}"
    )

    definition = assert_definition_present(flow, node)
    service_type = (definition.get("model") or {}).get("serviceType")
    if service_type != INLINE_AGENT_SERVICE_TYPE:
        sys.exit(
            f"FAIL: definitions[] entry for {node.get('type')!r} has "
            f"model.serviceType {service_type!r}, expected "
            f"{INLINE_AGENT_SERVICE_TYPE!r}"
        )
    print(f"OK: definition present with serviceType {INLINE_AGENT_SERVICE_TYPE!r}")

    assert_agent_sequence_wiring(flow, node)
    check_flow_output(flow, node["id"])
    print("OK: agent still on the trigger→end sequence path")


if __name__ == "__main__":
    main()
