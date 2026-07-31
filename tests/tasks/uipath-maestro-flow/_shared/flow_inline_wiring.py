"""Shared helpers for flow-file-first inline-agent checks (uipath-maestro-flow).

Grades the `.flow` file as the source of truth per the self-contained-flow
storage contract (flow-workbench PR #2636): the `uipath.agent.autonomous`
node embeds the full agent definition in `inputs` (string `systemPrompt` /
`userPrompt` = the embed trigger), and the UUID sidecar directory is a
DERIVED artifact. These checks therefore read ONLY the `.flow`:

  - no helper requires the `<GUID>/` sidecar directory to exist,
  - no helper forbids it either (debug/eval/pack may legitimately
    materialize it).

Successor to `tests/tasks/uipath-agents/_shared/inline_wiring.py`, which
graded the sidecar files. Per-kind resource helpers (`find_wired_resource`,
`assert_resource_inputs`, `assert_resource_source_uuid`) are added in the
M2-M8 milestones as each kind's shapes are pinned.

Import pattern in a check script:

    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from _shared.flow_inline_wiring import (  # noqa: E402
        load_json,
        find_autonomous_agent_node,
        assert_embedded_agent,
        assert_prompt_tokens,
        assert_agent_output_vars,
        assert_agent_input_vars,
        assert_edge,
        assert_definition_present,
    )
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

AUTONOMOUS_NODE_TYPE = "uipath.agent.autonomous"

# Lowercase UUID — the canvas mints inputs.source via crypto.randomUUID() and
# the agent-storage watcher/folder-cleanup gate on AGENT_FOLDER_UUID_REGEX;
# uppercase or non-UUID sources break packaging identity (sanitized folder
# name != raw source).
# Deliberately does NOT pin the version/variant nibbles: authoring guidance
# says UUIDv4, but grading tolerates any UUID version so hydrated/migrated
# sources (whose GUIDs predate the v4 guidance) don't false-FAIL. Do not
# "fix" this to v4-only.
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)

# The manifest inputDefaults an agent must NOT be left on (same bar and same
# placeholder set as check_inline_agent.py, applied to the embedded node
# instead of agent.json).
SCAFFOLD_MODEL = "gpt-4o-2024-11-20"
PLACEHOLDER_PROMPTS = {
    "",
    "you are an agentic assistant.",
    "you are an assistant.",
    "triage the inbound email.",
    "you are a classifier.",
    "what is the current date?",
}
MIN_SYSTEM_PROMPT_LEN = 40

# Derived-artifact token form. `.flow` prompts hold canvas-form
# `{{ $vars.* }}` / `{{ $metadata.* }}` tokens; `{{input.<flat>}}` exists only
# in the DERIVED agent.json (and `{{ $agent.<flat> }}` only in derived
# resource files). An agent porting sidecar content verbatim brings these
# along — the single most emphasized anti-pattern in the M1 docs.
DERIVED_TOKEN_RE = re.compile(r"\{\{\s*(input|\$agent)\.")
VARS_TOKEN_RE = re.compile(r"\{\{\s*\$(vars|metadata)\.")


def load_json(path: Path) -> dict:
    """Load a JSON file. Exit with FAIL on missing or invalid JSON."""
    path = Path(path)
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def find_autonomous_agent_node(flow: dict) -> dict:
    """Return the first `uipath.agent.autonomous` node in the flow."""
    nodes = flow.get("nodes") or []
    matches = [n for n in nodes if n.get("type") == AUTONOMOUS_NODE_TYPE]
    if not matches:
        sys.exit(f"FAIL: flow has no node of type {AUTONOMOUS_NODE_TYPE!r}")
    node = matches[0]
    if not node.get("id"):
        sys.exit(f"FAIL: {AUTONOMOUS_NODE_TYPE} node has no id")
    return node


def assert_embedded_agent(
    node: dict,
    *,
    require_model_override: bool = True,
) -> dict:
    """Assert the agent node is self-contained (flow-file-first) and real.

    Checks, all against node `inputs` (never the sidecar):
      1. Embed trigger — `systemPrompt` AND `userPrompt` are strings.
         (The storage predicate flips on either one, but an authored agent
         must carry both.)
      2. Real-prompt bar — system prompt is not a known scaffold placeholder
         and is at least MIN_SYSTEM_PROMPT_LEN chars.
      3. `model` is a non-empty string; with `require_model_override`, it is
         also not the manifest scaffold default.
      4. `source` is a lowercase UUID (derived folder name, watcher regex,
         packaging identity).
      5. Never-author guards — no instance `model` block on the node, no
         `contentTokens` and no `derivedInputDefinition` in `inputs`. These
         are the sidecar/BPMN-emission artifacts an agent trained on the old
         pattern copies in. (`derivedInputDefinition` can leak into a `.flow`
         only via a canvas save after debug/publish — never in a CLI-only
         sandbox — so a hit here is always hand-authored.)

    Returns the node's `inputs` dict for follow-up assertions. Exits with a
    FAIL line naming every failing property.
    """
    inputs = node.get("inputs") or {}
    errs = []

    if "model" in node:
        errs.append(
            "node has an instance 'model' block — never authored; node model "
            "semantics live in definitions[], the agent model in inputs.model"
        )
    if "contentTokens" in inputs:
        errs.append(
            "inputs.contentTokens is a derived agent.json artifact — prompts "
            "in the .flow are plain strings with {{ $vars.* }} tokens"
        )
    if "derivedInputDefinition" in inputs:
        errs.append(
            "inputs.derivedInputDefinition is a BPMN-emission artifact — "
            "never hand-write it"
        )

    for key in ("systemPrompt", "userPrompt"):
        if not isinstance(inputs.get(key), str):
            errs.append(
                f"inputs.{key} is not a string — node is a legacy shell, "
                "not a self-contained agent"
            )

    system_prompt = inputs.get("systemPrompt")
    if isinstance(system_prompt, str):
        stripped = system_prompt.strip()
        if stripped.lower() in PLACEHOLDER_PROMPTS:
            errs.append(f"systemPrompt is a scaffold placeholder: {stripped[:60]!r}")
        elif len(stripped) < MIN_SYSTEM_PROMPT_LEN:
            errs.append(
                f"systemPrompt too short ({len(stripped)} chars < "
                f"{MIN_SYSTEM_PROMPT_LEN}): {stripped[:60]!r}"
            )

    model = inputs.get("model")
    if not isinstance(model, str) or not model:
        errs.append("inputs.model is missing or empty")
    elif require_model_override and model == SCAFFOLD_MODEL:
        errs.append(f"inputs.model not overridden from scaffold default ({model})")

    source = inputs.get("source")
    if not isinstance(source, str) or not UUID_RE.match(source):
        errs.append(
            f"inputs.source is not a lowercase UUID: {source!r}"
        )

    if errs:
        sys.exit(f"FAIL ({node.get('id')}): " + "; ".join(errs))
    return inputs


def assert_prompt_tokens(node: dict, *, require_vars_ref: bool = False) -> None:
    """Assert the node's prompts use the canvas token form, not derived forms.

    `.flow` prompts are plain strings with `{{ $vars.* }}` / `{{ $metadata.* }}`
    tokens. Fails on `{{input.<flat>}}` (derived agent.json namespace) and
    `{{ $agent.<flat> }}` (derived resource-file namespace) — `uip maestro
    flow validate` cannot catch these because prompts are opaque strings to it.

    With `require_vars_ref`, additionally require at least one `$vars.` /
    `$metadata.` reference across the two prompts — use in tasks that wire
    flow data into the agent.
    """
    inputs = node.get("inputs") or {}
    errs = []
    saw_vars_ref = False
    for key in ("systemPrompt", "userPrompt"):
        prompt = inputs.get(key)
        if not isinstance(prompt, str):
            continue
        m = DERIVED_TOKEN_RE.search(prompt)
        if m:
            errs.append(
                f"{key} uses derived-artifact token form {m.group(0)!r}…}}}} — "
                "flow prompts reference flow data as {{ $vars.<nodeId>.output.<field> }}"
            )
        if VARS_TOKEN_RE.search(prompt):
            saw_vars_ref = True
    if require_vars_ref and not saw_vars_ref:
        errs.append(
            "no {{ $vars.* }} / {{ $metadata.* }} reference in either prompt — "
            "the task expects flow data wired into the agent"
        )
    if errs:
        sys.exit(f"FAIL ({node.get('id')}): " + "; ".join(errs))


def assert_agent_output_vars(
    node: dict,
    expected: dict[str, str],
    *,
    require_description: bool = False,
) -> None:
    """Assert `inputs.agentOutputVariables` declares the expected typed fields.

    `expected` maps output id -> JSON-schema type (e.g. {"answer": "string"}).
    Extra declared outputs are allowed. Typed outputs surface flat at
    `$vars.<nodeId>.output.<field>` — never under `.content.`.
    """
    inputs = node.get("inputs") or {}
    declared = inputs.get("agentOutputVariables")
    if not isinstance(declared, list):
        sys.exit(
            f"FAIL ({node.get('id')}): inputs.agentOutputVariables is not a list"
        )
    by_id = {v.get("id"): v for v in declared if isinstance(v, dict)}
    errs = []
    for out_id, out_type in expected.items():
        entry = by_id.get(out_id)
        if entry is None:
            errs.append(f"missing output variable {out_id!r} (have {sorted(by_id)})")
            continue
        if entry.get("type") != out_type:
            errs.append(
                f"output {out_id!r} has type {entry.get('type')!r}, expected {out_type!r}"
            )
        if require_description and not entry.get("description"):
            errs.append(f"output {out_id!r} has no description")
    if errs:
        sys.exit(f"FAIL ({node.get('id')}): " + "; ".join(errs))


def assert_agent_input_vars(node: dict) -> None:
    """Assert `inputs.agentInputVariables` follows the authoring contract.

    `agentInputVariables` are DERIVED, not authored: the authoring contract is
    to write `[]` and let tooling scan the cluster's `$vars.*`/`$metadata.*`
    refs. Derived entries persist in the `.flow` after canvas/debug touch, so
    a non-empty list is acceptable ONLY when every entry looks derived (has a
    string `id` and a `binding` starting with `=`). Hand-authored freeform
    entries (no binding) fail.
    """
    inputs = node.get("inputs") or {}
    declared = inputs.get("agentInputVariables")
    if not isinstance(declared, list):
        sys.exit(
            f"FAIL ({node.get('id')}): inputs.agentInputVariables is not a list "
            "— author it as [] (entries are derived by tooling)"
        )
    errs = []
    for i, entry in enumerate(declared):
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            errs.append(f"entry [{i}] has no string id: {entry!r}")
            continue
        binding = entry.get("binding")
        if not (isinstance(binding, str) and binding.startswith("=")):
            errs.append(
                f"entry {entry['id']!r} has no '=…' binding — hand-authored "
                "agentInputVariables entries are pruned by tooling; author [] "
                "and reference flow data via {{ $vars.* }} prompt tokens"
            )
    if errs:
        sys.exit(f"FAIL ({node.get('id')}): " + "; ".join(errs))


def assert_edge(
    flow: dict,
    *,
    source_id: str,
    source_port: str,
    target_id: str,
    target_port: str,
) -> None:
    """Assert that an edge wires source_id:source_port -> target_id:target_port."""
    edges = flow.get("edges") or []
    matches = [
        e for e in edges
        if e.get("sourceNodeId") == source_id
        and e.get("sourcePort") == source_port
        and e.get("targetNodeId") == target_id
        and e.get("targetPort") == target_port
    ]
    if not matches:
        sys.exit(
            f"FAIL: no edge wires source node {source_id!r} port "
            f"{source_port!r} to target node {target_id!r} port "
            f"{target_port!r}."
        )


def assert_definition_present(flow: dict, node: dict) -> dict:
    """Assert `definitions[]` has the node's manifest and return it.

    Keying is `(nodeType, version)` matched from the instance's
    `(type, typeVersion)` — an exact match on both, since multiple versions
    of one nodeType legally coexist. A resource node without a matching
    definition does not project (it silently vanishes from the derived agent
    and the package), and `uip maestro flow validate` rejects it.
    """
    node_type = node.get("type")
    type_version = node.get("typeVersion")
    for definition in flow.get("definitions") or []:
        if (
            definition.get("nodeType") == node_type
            and definition.get("version") == type_version
        ):
            return definition
    sys.exit(
        f"FAIL: definitions[] has no entry for ({node_type!r}, "
        f"{type_version!r}) — the node would not hydrate, validate, or "
        "project into the derived agent"
    )
