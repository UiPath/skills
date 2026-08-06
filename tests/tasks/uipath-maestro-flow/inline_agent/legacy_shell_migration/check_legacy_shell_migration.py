#!/usr/bin/env python3
"""Brownfield check for skill-flow-inline-agent-legacy-shell.

The sandbox starts with a LEGACY-SHELL inline agent: the
`uipath.agent.autonomous` node in `BillingSol/DisputeAnalyst/DisputeAnalyst.flow`
carries only structural `inputs` (`source` + the two variables arrays) and its
definition lives in the stored sidecar
`DisputeAnalyst/e5715a3f-…/agent.json`. The prompt asks for a behaviour change
(cite the SOP section, add a `sopSection` output) using NO pattern words.

Grades the migration, not just the edit:

  1. The node is now self-contained — string prompts, model, UUID `source`, no
     never-author artifacts (instance `model` block, `contentTokens`,
     `derivedInputDefinition`).
  2. Identity preserved — `inputs.source` is still the sidecar's GUID (it is
     the derived folder name and the packaging identity; minting a fresh UUID
     orphans the stored artifact).
  3. Stored content was PORTED, not reinvented — the sidecar's model,
     `maxTokens`→`maxTokenPerResponse`, `maxIterations` (and `temperature` /
     `mode` when present) land on the node, and a distinctive phrase of the
     stored system prompt survives.
  4. Reverse token mapping — the stored `{{input.<flat>}}` tokens became
     `{{ $vars.<dotted.path> }}`; the derived namespaces never appear in the
     `.flow`.
  5. The guardrail travelled with the definition (verbatim array, same
     validator/action/scope) — losing a security control during a migration is
     the expensive brownfield failure.
  6. No stored-file scaffolding leaked into `inputs` (`messages`, `settings`,
     `inputSchema`, `engine`, `metadata`, …).
  7. The requested edit landed ON THE NODE — `sopSection` typed output plus a
     section instruction in a prompt — and is surfaced as a flow output.
  8. The graph still holds: definition present at the instance
     `(type, typeVersion)` with the inline-agent serviceType, agent on the
     trigger→end sequence path.
"""

from __future__ import annotations

import os
import re
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
FLOW_PATH = (
    Path(os.getcwd()) / "BillingSol" / "DisputeAnalyst" / "DisputeAnalyst.flow"
)

# Fixture ground truth (see fixture/BillingSol/DisputeAnalyst/…): the stored
# sidecar the agent must migrate FROM.
SIDECAR_GUID = "e5715a3f-0d31-4ad8-9c70-91df180760e6"
STORED_MODEL = "gpt-4.1-mini-2025-04-14"
STORED_MAX_TOKENS = 8192
STORED_MAX_ITERATIONS = 12
STORED_TEMPERATURE = 0.2
STORED_MODE = "standard"
# Phrases unique to the stored system prompt — at least one must survive, which
# is what distinguishes a port from a from-scratch rewrite. Deliberately
# excludes domain-generic words ("refund", "dispute") a rewrite would plausibly
# reinvent.
STORED_PROMPT_MARKERS = (
    "needs-review",
    "accounts-receivable",
    "contact the customer",
)
# The two flat input keys the stored prompt referenced, with the dotted paths
# they must reverse-map to.
REVERSE_TOKEN_PATHS = (
    "$vars.start.output.disputeDescription",
    "$vars.start.output.invoiceNumber",
)
# Stored-file keys that must never appear in node `inputs`.
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
NEW_OUTPUT = "sopSection"


def check_ported_settings(inputs: dict) -> None:
    errs = []
    model = inputs.get("model")
    if model != STORED_MODEL:
        errs.append(
            f"inputs.model is {model!r}, expected the stored settings.model "
            f"{STORED_MODEL!r} — the migration ports the agent's model, it "
            "does not pick a new one"
        )
    if inputs.get("maxTokenPerResponse") != STORED_MAX_TOKENS:
        errs.append(
            f"inputs.maxTokenPerResponse is "
            f"{inputs.get('maxTokenPerResponse')!r}, expected "
            f"{STORED_MAX_TOKENS} (stored settings.maxTokens — renamed on the "
            "node)"
        )
    if inputs.get("maxIterations") != STORED_MAX_ITERATIONS:
        errs.append(
            f"inputs.maxIterations is {inputs.get('maxIterations')!r}, "
            f"expected the stored {STORED_MAX_ITERATIONS}"
        )
    # The fixture stores a NON-default temperature — omitting it falls back to
    # the manifest default and changes behaviour, so it is required like the
    # other numeric settings. `mode` stays tolerant-on-presence: the stored
    # value IS the default, so an omission is behaviour-neutral.
    if inputs.get("temperature") != STORED_TEMPERATURE:
        errs.append(
            f"inputs.temperature is {inputs.get('temperature')!r}, expected "
            f"the stored {STORED_TEMPERATURE} — dropping it resets the agent "
            "to the manifest default"
        )
    if "mode" in inputs and inputs["mode"] != STORED_MODE:
        errs.append(
            f"inputs.mode is {inputs['mode']!r}, expected the stored "
            f"{STORED_MODE!r}"
        )
    if errs:
        sys.exit("FAIL (ported settings): " + "; ".join(errs))
    print(
        f"OK: stored settings ported — model {STORED_MODEL}, "
        f"maxTokenPerResponse {STORED_MAX_TOKENS}, "
        f"maxIterations {STORED_MAX_ITERATIONS}"
    )


def check_ported_prompts(inputs: dict) -> None:
    system_prompt = inputs.get("systemPrompt") or ""
    user_prompt = inputs.get("userPrompt") or ""
    both = f"{system_prompt}\n{user_prompt}"
    lowered = both.lower()

    if not any(marker in lowered for marker in STORED_PROMPT_MARKERS):
        sys.exit(
            "FAIL: no distinctive phrase of the stored system prompt survived "
            f"(looked for any of {list(STORED_PROMPT_MARKERS)}) — the node's "
            "prompts read as a rewrite, not as the migrated definition"
        )
    # Brace spacing is free-form (`{{ $vars.x }}` / `{{$vars.x}}`); the dotted
    # path itself is not.
    missing_paths = [p for p in REVERSE_TOKEN_PATHS if p not in both]
    if missing_paths:
        sys.exit(
            "FAIL: stored `{{input.<flat>}}` tokens were not reverse-mapped — "
            f"missing {missing_paths} in the node prompts. "
            "`{{input.start__output__disputeDescription}}` becomes "
            "`{{ $vars.start.output.disputeDescription }}`"
        )
    if "section" not in lowered:
        sys.exit(
            "FAIL: neither prompt instructs the agent about the SOP section it "
            "applied — the requested behaviour change did not land on the node"
        )
    print("OK: prompts ported with reverse-mapped tokens and the new instruction")


def check_guardrail(inputs: dict) -> None:
    guardrails = inputs.get("guardrails")
    if not isinstance(guardrails, list) or not guardrails:
        sys.exit(
            "FAIL: inputs.guardrails is empty or missing — the stored "
            "definition carries a PII-detection guardrail; it projects "
            "verbatim onto the node and must survive the migration"
        )
    errs = []
    entry = next(
        (
            g for g in guardrails
            if isinstance(g, dict) and g.get("validatorType") == "pii_detection"
        ),
        None,
    )
    if entry is None:
        sys.exit(
            "FAIL: no guardrail with validatorType 'pii_detection' on the node "
            f"(have {[g.get('validatorType') for g in guardrails if isinstance(g, dict)]})"
        )
    if entry.get("$guardrailType") != "builtInValidator":
        errs.append(
            f"$guardrailType is {entry.get('$guardrailType')!r}, expected "
            "'builtInValidator'"
        )
    action = entry.get("action") or {}
    if action.get("$actionType") != "block":
        errs.append(
            f"action.$actionType is {action.get('$actionType')!r}, expected "
            "'block' (the stored action)"
        )
    scopes = (entry.get("selector") or {}).get("scopes")
    if not isinstance(scopes, list) or "Agent" not in scopes:
        errs.append(f"selector.scopes is {scopes!r}, expected to include 'Agent'")
    param_ids = {
        p.get("id") for p in entry.get("validatorParameters") or []
        if isinstance(p, dict)
    }
    for required in ("entities", "entityThresholds"):
        if required not in param_ids:
            errs.append(
                f"validatorParameters lost {required!r} (have {sorted(param_ids)})"
            )
    if errs:
        sys.exit("FAIL (guardrail): " + "; ".join(errs))
    print("OK: stored PII guardrail ported verbatim (validator, action, scope, params)")


def check_no_stored_scaffolding(node: dict) -> None:
    inputs = node.get("inputs") or {}
    leaked = [k for k in STORED_ONLY_INPUT_KEYS if k in inputs]
    if leaked:
        sys.exit(
            f"FAIL ({node.get('id')}): stored-file keys leaked into node "
            f"inputs: {leaked} — the sidecar's envelope (messages/settings/"
            "schemas/engine/metadata) has no place in the node; only the "
            "mapped fields move"
        )
    print("OK: no sidecar envelope keys leaked into node inputs")


def check_flow_output(flow: dict, agent_id: str) -> None:
    globals_ = (flow.get("variables") or {}).get("globals") or []
    out_ids = {
        g.get("id") for g in globals_
        if isinstance(g, dict) and g.get("direction") == "out"
    }
    if NEW_OUTPUT not in out_ids:
        sys.exit(
            f"FAIL: no 'out' global named {NEW_OUTPUT!r} (have {sorted(out_ids)}) "
            "— the new agent output was not surfaced as a flow output"
        )

    mappings = []
    for node in flow.get("nodes") or []:
        if node.get("type") != "core.control.end":
            continue
        for out_id, spec in (node.get("outputs") or {}).items():
            expression = ((spec or {}).get("source") or {}).get("expression")
            if isinstance(expression, str):
                mappings.append((out_id, expression))

    wrapped = [
        (out_id, expr) for out_id, expr in mappings
        if re.search(r"output\.content\.", expr)
    ]
    if wrapped:
        sys.exit(
            f"FAIL: end-node mapping uses the '.content.' wrapper: {wrapped} — "
            "typed agent outputs surface flat at "
            f"$vars.{agent_id}.output.<field>"
        )
    hit = [
        (out_id, expr) for out_id, expr in mappings
        if NEW_OUTPUT in expr and agent_id in expr
    ]
    if not hit:
        sys.exit(
            f"FAIL: no end-node output maps {NEW_OUTPUT!r} from the agent "
            f"(expected an expression referencing $vars.{agent_id}.output."
            f"{NEW_OUTPUT}; have {mappings})"
        )
    print(f"OK: {NEW_OUTPUT} surfaced as a flow output via {hit[0][1]!r}")


def main() -> None:
    flow_path = find_flow_file(FLOW_PATH)
    flow = load_json(flow_path)
    node = find_autonomous_agent_node(flow)

    inputs = assert_embedded_agent(node)
    print(
        f"OK: {node['id']} is now self-contained — the legacy shell was "
        "migrated into the node"
    )

    if inputs.get("source") != SIDECAR_GUID:
        sys.exit(
            f"FAIL ({node['id']}): inputs.source is {inputs.get('source')!r}, "
            f"expected the existing {SIDECAR_GUID!r} — the agent's identity is "
            "the derived folder name and the packaging identity; a migration "
            "keeps it"
        )
    print(f"OK: identity preserved (inputs.source still {SIDECAR_GUID})")

    assert_prompt_tokens(node, require_vars_ref=True)
    check_ported_prompts(inputs)
    check_ported_settings(inputs)
    check_guardrail(inputs)
    check_no_stored_scaffolding(node)

    assert_agent_input_vars(node)
    assert_agent_output_vars(
        node,
        {"determination": "string", "rationale": "string", NEW_OUTPUT: "string"},
    )
    print(
        "OK: typed outputs kept (determination, rationale) and extended with "
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
