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
graded the sidecar files. Per-kind resource helpers grow in the M2-M8
milestones as each kind's shapes are pinned (M2: `find_wired_resource`,
`assert_resource_source_uuid`, `assert_resource_inputs`,
`assert_tool_type_key_uuid`, `assert_cluster_vars_ref`; M3:
`assert_no_derived_resource_fields`, `assert_bindings_rows`,
`assert_agent_sequence_wiring`, `find_flow_file`,
`assert_builtin_identity`; M4: `assert_context_inputs`).

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
import os
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
# Single stale-default sentinel: if the manifest/CLI default model changes,
# this check silently weakens — re-pin at the M11 final sweep (roadmap).
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
    entries (no binding) fail. An ABSENT key is accepted as equivalent to []
    — tooling derives regardless of whether the empty list is spelled out.
    """
    inputs = node.get("inputs") or {}
    declared = inputs.get("agentInputVariables")
    if declared is None:
        return
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


# ---------------------------------------------------------------------------
# Resource-node helpers (M2+: capability tasks — tools/context/escalation)
# ---------------------------------------------------------------------------

# Raw `$vars.` / `$metadata.` reference — matches braced prompt tokens AND
# structured raw refs (e.g. a variable-mode per-argument
# `argumentPath: "$vars.start.output.index"`); the cluster ref scanner
# (agent-cluster-rewrite) catches both forms.
RAW_VARS_RE = re.compile(r"\$(vars|metadata)\.")

# Node-type key suffix for process-family tools: the registry mints one node
# type per callable target, `uipath.agent.resource.tool.<family>.<key>`,
# where <key> is the target's resource key GUID. Case-insensitive: the key is
# registry-owned (unlike the author-minted inputs.source, which must be
# lowercase).
TYPE_KEY_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def find_wired_resource(flow: dict, agent_node: dict, *, type_prefix: str, source_port: str) -> dict:
    """Find the resource node with the given type prefix wired to the agent.

    Asserts (1) at least one node's `type` starts with `type_prefix` and
    (2) one of them is attached via the single artifact edge — agent
    `source_port` (source) -> resource `input` (target). Returns the wired
    resource node.
    """
    nodes = flow.get("nodes") or []
    candidates = [n for n in nodes if str(n.get("type", "")).startswith(type_prefix)]
    if not candidates:
        sys.exit(f"FAIL: flow has no node with type prefix {type_prefix!r}")
    agent_id = agent_node.get("id")
    edges = flow.get("edges") or []
    for node in candidates:
        for e in edges:
            if (
                e.get("sourceNodeId") == agent_id
                and e.get("sourcePort") == source_port
                and e.get("targetNodeId") == node.get("id")
                and e.get("targetPort") == "input"
            ):
                return node
    sys.exit(
        f"FAIL: no artifact edge wires agent {agent_id!r} port {source_port!r} "
        f"to the 'input' port of a {type_prefix!r} node — unwired candidate(s): "
        f"{[n.get('id') for n in candidates]}"
    )


# Derived resource.json `type` values (canvas-to-storage CANVAS_TO_STORAGE_TOOL_TYPE
# range). Used to value-gate the inputs.type contamination check so a legitimate
# tool argument that happens to be named "type" (a ValueSourceField OBJECT, or a
# string outside this set) never false-FAILs.
DERIVED_TOOL_TYPE_VALUES = {
    "process", "agent", "api", "integration", "internal",
    "clientSide", "ixp", "processOrchestration", "flow",
}


def assert_no_derived_resource_fields(node: dict) -> None:
    """Assert the tool node's `inputs` carry no derived resource.json fields.

    The deleted sidecar `resource.json`'s content is the likely legacy
    contamination: an agent trained on the old pattern copies its derived
    fields into the node. Projection owns these — they are never authored:

      - `$resourceType` (resource-file discriminator)
      - `type` when it holds a derived-type string (`"internal"`,
        `"process"`, …) — value-gated, see DERIVED_TOOL_TYPE_VALUES
      - `location` when it holds `"solution"`/`"external"`
      - `argumentProperties` (built from per-argument modes / file bindings)
      - `properties.toolType` (runtime discriminator — the flow surface
        encodes the tool in the node TYPE suffix instead)

    Graded tasks author NEW nodes, so a hit is always contamination (only
    canvas hydration of a legacy shell writes some of these back).
    """
    inputs = node.get("inputs") or {}
    errs = []
    if "$resourceType" in inputs:
        errs.append("inputs.$resourceType is a derived resource.json field — never authored")
    type_val = inputs.get("type")
    if isinstance(type_val, str) and type_val in DERIVED_TOOL_TYPE_VALUES:
        errs.append(
            f"inputs.type={type_val!r} is the derived resource.json type — "
            "never authored (the node's TYPE string already encodes the kind)"
        )
    location = inputs.get("location")
    if isinstance(location, str) and location in {"solution", "external"}:
        errs.append(f"inputs.location={location!r} is projection-owned — never authored")
    if isinstance(inputs.get("argumentProperties"), dict):
        errs.append(
            "inputs.argumentProperties is derived from per-argument modes — "
            "author ValueSourceField entries per argument instead"
        )
    props = inputs.get("properties")
    if isinstance(props, dict) and "toolType" in props:
        errs.append(
            "inputs.properties.toolType is the derived runtime discriminator — "
            "the tool is selected by the node type suffix, never authored"
        )
    if errs:
        sys.exit(f"FAIL ({node.get('id')}): " + "; ".join(errs))


def assert_bindings_rows(
    flow: dict,
    *,
    property_attributes: tuple[str, ...] = ("name", "folderPath"),
) -> list[dict]:
    """Assert the flow has top-level `bindings[]` rows for a process-family tool.

    Tolerant DIRECT assertion (deliberately weaker than `flow validate`,
    which enforces the full row set with actionable errors): at least one
    row whose `propertyAttribute` is in `property_attributes`. Exists so
    bindings coverage survives a CLI validate regression — do not tighten
    to exact row matching (the validate criterion owns that).
    """
    rows = flow.get("bindings") or []
    hits = [
        r for r in rows
        if isinstance(r, dict) and r.get("propertyAttribute") in property_attributes
    ]
    if not hits:
        sys.exit(
            "FAIL: no top-level bindings[] row with propertyAttribute in "
            f"{sorted(property_attributes)} — process-family tools require "
            "rows mirroring the definition's model.bindings.values[]"
        )
    return hits


def assert_agent_sequence_wiring(flow: dict, agent_node: dict) -> None:
    """Assert the agent node sits on the sequence path.

    At least one sequence edge INTO the agent's `input` port and one OUT of
    its `success` port — an agent wired only via artifact edges never runs.
    """
    agent_id = agent_node.get("id")
    edges = flow.get("edges") or []
    has_input = any(
        e.get("targetNodeId") == agent_id and e.get("targetPort") == "input"
        for e in edges
    )
    has_success = any(
        e.get("sourceNodeId") == agent_id and e.get("sourcePort") == "success"
        for e in edges
    )
    errs = []
    if not has_input:
        errs.append("no sequence edge into the agent's 'input' port")
    if not has_success:
        errs.append("no sequence edge out of the agent's 'success' port")
    if errs:
        sys.exit(
            f"FAIL ({agent_id}): " + "; ".join(errs) +
            " — the agent must be on the trigger→end sequence path"
        )


def find_flow_file(expected: Path) -> Path:
    """Return the graded `.flow` path, tolerating a relocated project.

    Prefer `expected` (the path the prompt names — separate lower-weight
    path criteria grade its exactness). When absent, fall back to the
    single `*.flow` under the working directory (skipping hidden dirs and
    node_modules) so the content checker still grades a correctly-authored
    flow at a wrong path. Zero or multiple candidates FAIL.
    """
    expected = Path(expected)
    if expected.is_file():
        return expected
    root = Path(os.getcwd())
    candidates = [
        p for p in root.rglob("*.flow")
        if not any(part.startswith(".") or part == "node_modules" for part in p.relative_to(root).parts)
    ]
    if len(candidates) == 1:
        print(f"NOTE: {expected} missing; grading sole flow file {candidates[0]}")
        return candidates[0]
    sys.exit(
        f"FAIL: {expected} does not exist and fallback found "
        f"{len(candidates)} .flow candidates: {[str(c) for c in candidates]}"
    )


def assert_resource_source_uuid(node: dict) -> str:
    """Assert the resource node's identity contract and return its source.

    `inputs.source` must be a lowercase UUID (it becomes the derived
    `resources/<source>/resource.json` id), and the node must not carry an
    instance `model` block (never authored — identity lives in `inputs`,
    node semantics in `definitions[]`).
    """
    errs = []
    if "model" in node:
        errs.append(
            "node has an instance 'model' block — never authored; identity "
            "lives at inputs.source, node semantics in definitions[]"
        )
    source = (node.get("inputs") or {}).get("source")
    if not isinstance(source, str) or not UUID_RE.match(source):
        errs.append(f"inputs.source is not a lowercase UUID: {source!r}")
    if errs:
        sys.exit(f"FAIL ({node.get('id')}): " + "; ".join(errs))
    return source


def assert_resource_inputs(
    node: dict,
    *,
    expected_properties: dict[str, str] | None = None,
    require_name: bool = True,
    require_description: bool = True,
) -> dict:
    """Assert the resource node carries its config in `inputs` (never a sidecar).

    - `expected_properties` maps `inputs.properties` keys to exact expected
      values (e.g. {"processName": "CalculatePay", "folderPath":
      "solution_folder"}). A missing/empty value fails — an empty
      `folderPath` breaks runtime process resolution.
    - `require_name` / `require_description`: non-empty string `inputs.name`
      (the tool name the LLM selects by) and `inputs.description`.

    Returns the node's `inputs` dict for follow-up assertions.
    """
    inputs = node.get("inputs") or {}
    errs = []
    if require_name and not (isinstance(inputs.get("name"), str) and inputs["name"].strip()):
        errs.append(f"inputs.name is missing or empty: {inputs.get('name')!r}")
    if require_description and not (
        isinstance(inputs.get("description"), str) and inputs["description"].strip()
    ):
        errs.append(
            "inputs.description is missing or empty — the LLM selects tools "
            "by description"
        )
    if expected_properties:
        props = inputs.get("properties")
        if not isinstance(props, dict):
            errs.append(f"inputs.properties is not an object: {props!r}")
        else:
            for key, expected in expected_properties.items():
                actual = props.get(key)
                if actual != expected:
                    errs.append(
                        f"inputs.properties.{key} should be {expected!r}, got {actual!r}"
                    )
    if errs:
        sys.exit(f"FAIL ({node.get('id')}): " + "; ".join(errs))
    return inputs


def assert_tool_type_key_uuid(node: dict) -> str:
    """Assert a process-family tool node's type ends in the target's key GUID.

    The registry mints `uipath.agent.resource.tool.<family>.<key>` per
    callable target — a non-UUID suffix means the type string was constructed
    by hand instead of discovered via `registry search`.
    """
    node_type = str(node.get("type", ""))
    key = node_type.rsplit(".", 1)[-1]
    if not TYPE_KEY_UUID_RE.match(key):
        sys.exit(
            f"FAIL ({node.get('id')}): node type {node_type!r} does not end in "
            "the target's resource-key GUID — discover the exact node type via "
            "`uip maestro flow registry search`, never construct it by hand"
        )
    return key


# Builtin tool node-type suffixes whose manifest declares model.source: true —
# identity is a minted inputs.source UUID (validator-enforced). The other
# builtins (summarize, batchtransform) declare no model.source: identity is a
# minted inputs.id, and their inputs.source is a FILE REFERENCE (empty string
# or a $vars file expression), never a UUID.
BUILTIN_SOURCE_IDENTITY_SUFFIXES = {"analyzefiles"}


def assert_builtin_identity(node: dict) -> str:
    """Assert a builtin tool node's identity contract and return the UUID.

    Dispatches on the node-type suffix (`…tool.builtin.<suffix>`):
    `analyzefiles` requires a lowercase-UUID `inputs.source`;
    `summarize`/`batchtransform` require a lowercase-UUID `inputs.id`.
    Also rejects an instance `model` block (never authored).
    """
    errs = []
    if "model" in node:
        errs.append(
            "node has an instance 'model' block — never authored; node "
            "semantics live in definitions[]"
        )
    suffix = str(node.get("type", "")).rsplit(".", 1)[-1]
    inputs = node.get("inputs") or {}
    if suffix in BUILTIN_SOURCE_IDENTITY_SUFFIXES:
        identity = inputs.get("source")
        if not isinstance(identity, str) or not UUID_RE.match(identity):
            errs.append(
                f"inputs.source is not a lowercase UUID: {identity!r} — "
                f"the {suffix} manifest declares model.source: true"
            )
    else:
        identity = inputs.get("id")
        if not isinstance(identity, str) or not UUID_RE.match(identity):
            errs.append(
                f"inputs.id is not a lowercase UUID: {identity!r} — "
                f"{suffix} has no model.source; identity is inputs.id "
                "(inputs.source is the file reference)"
            )
        source = inputs.get("source")
        if isinstance(source, str) and UUID_RE.match(source):
            errs.append(
                f"inputs.source holds a UUID ({source!r}) on a {suffix} node — "
                "source is the FILE REFERENCE here; the identity UUID belongs "
                "at inputs.id"
            )
    if errs:
        sys.exit(f"FAIL ({node.get('id')}): " + "; ".join(errs))
    return identity


# Context-index retrievalMode values — ALL-LOWERCASE by contract. The manifest
# schema discriminates on lowercase consts (`deeprag`, `batchtransform`); a
# camelCase value (`deepRAG`) matches none of the conditionals, silently falls
# into the semantic branch, and PASSES `flow validate` while misconfiguring
# retrieval — this checker is the only gate that catches casing drift.
VALID_CONTEXT_RETRIEVAL_MODES = {"semantic", "structured", "deeprag", "batchtransform"}


def assert_context_inputs(
    node: dict,
    *,
    expected_identity: dict[str, str] | None = None,
) -> dict:
    """Assert a context-index node carries the flat flow-form config in `inputs`.

    - `expected_identity` maps TOP-LEVEL `inputs` identity keys to exact
      expected values (e.g. {"indexName": "MyIndex", "folderPath":
      "Shared/Knowledge"}) — copied from the manifest's `inputDefaults`,
      never guessed. (Identity is flat on context nodes, unlike the
      process-tool `inputs.properties` nesting.)
    - `retrievalMode` must be in the all-lowercase VALID_CONTEXT_RETRIEVAL_MODES
      set (validate cannot catch casing drift — see the set's comment).
    - When `inputs.indexId` is present, it must equal the node type's `<id>`
      suffix (the registry mints one node type per index).
    - Never-author guards: no `$resourceType` / `contextType` / dict
      `settings` in `inputs` — those are the DERIVED resource.json shape
      (the flat fields collapse into a `settings` union at projection).

    Returns the node's `inputs` dict for follow-up assertions.
    """
    inputs = node.get("inputs") or {}
    errs = []

    if "$resourceType" in inputs:
        errs.append("inputs.$resourceType is a derived resource.json field — never authored")
    if "contextType" in inputs:
        errs.append(
            "inputs.contextType is a derived resource.json field — the node "
            "TYPE string already encodes the context kind"
        )
    if isinstance(inputs.get("settings"), dict):
        errs.append(
            "inputs.settings is the derived resource.json union — the flow "
            "form is FLAT (retrievalMode, query, threshold, … directly in inputs)"
        )

    mode = inputs.get("retrievalMode")
    if mode not in VALID_CONTEXT_RETRIEVAL_MODES:
        errs.append(
            f"inputs.retrievalMode must be one of "
            f"{sorted(VALID_CONTEXT_RETRIEVAL_MODES)} (all-lowercase), got {mode!r}"
        )

    if expected_identity:
        for key, expected in expected_identity.items():
            actual = inputs.get(key)
            if actual != expected:
                errs.append(f"inputs.{key} should be {expected!r}, got {actual!r}")

    index_id = inputs.get("indexId")
    if isinstance(index_id, str) and index_id:
        type_suffix = str(node.get("type", "")).rsplit(".", 1)[-1]
        if index_id.lower() != type_suffix.lower():
            errs.append(
                f"inputs.indexId {index_id!r} does not match the node type's "
                f"index-GUID suffix {type_suffix!r} — identity is copied from "
                "the manifest's inputDefaults, never guessed"
            )

    if errs:
        sys.exit(f"FAIL ({node.get('id')}): " + "; ".join(errs))
    return inputs


def assert_cluster_vars_ref(nodes: list[dict]) -> None:
    """Assert at least one `$vars.` / `$metadata.` ref across the nodes' inputs.

    Flow data can legitimately enter an agent cluster through a prompt token
    (`{{ $vars.* }}`) OR through a resource node's structured input (e.g. a
    variable-mode per-argument `argumentPath`) — the derivation scanner
    accepts both. Use in tasks whose prompt mandates wiring flow inputs in.
    """
    for node in nodes:
        blob = json.dumps(node.get("inputs") or {})
        if RAW_VARS_RE.search(blob):
            return
    sys.exit(
        "FAIL: no $vars./$metadata. reference in any cluster node's inputs "
        f"(checked {[n.get('id') for n in nodes]}) — the task expects flow "
        "data wired into the agent cluster"
    )
