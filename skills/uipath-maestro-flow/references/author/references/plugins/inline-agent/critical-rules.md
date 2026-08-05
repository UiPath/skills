# Critical Rules and Anti-Patterns — Inline Agents

Canonical rules for authoring inline agents in `.flow` files. Capability files cross-reference back here; they do not restate rules. Mirrors the standalone low-code rules in the `uipath-agents` skill, adapted to flow-file embedding — for standalone agent projects, use that skill instead.

## Critical Rules (15)

1. **The flow file is the source of truth.** The full agent definition lives in the `uipath.agent.autonomous` node's `inputs` (a string `systemPrompt`/`userPrompt` is the embed trigger). The GUID subdirectory is a derived artifact — never create or edit it. Sole exception: `<GUID>/evals/` is authored via `uip maestro flow eval`. See [impl.md § 1](impl.md#1-the-contract--the-node-is-the-agent-definition).

2. **No `uip agent` lifecycle verbs.** Never run `uip agent init` / `refresh` / `validate` (with or without `--inline-in-flow`) — there is no agent project to scaffold or regenerate. The only sanctioned `uip agent` verbs are the tenant-level discovery reads: `uip agent model list --output json` (model discovery) and `uip agent guardrails list|catalog|llm-as-judge-models --output json` (validator discovery, [capabilities/guardrails.md](capabilities/guardrails.md)).

3. **Validate after every bulk of edits** — `uip maestro flow format "<FILE>.flow"` then `uip maestro flow validate "<FILE>.flow" --output json`. Format back-fills layout and `variables.nodes[]`; validate is the authoring gate for embedded-agent semantics.

4. **Use `--output json`** on all `uip` commands when parsing output.

5. **Definitions verbatim, exact version match.** Every node instance `(type, typeVersion)` needs a `definitions[]` entry `(nodeType, version)` copied verbatim from `uip maestro flow registry get`. A resource node without its definition silently vanishes from the derived agent and the package. The canvas rebuilds `definitions[]` on save — never hand-edit an entry; re-fetch instead. See [impl.md § 3](impl.md#3-manifest-and-definitions-contract).

6. **Prompts are plain strings with `{{ $vars.<nodeId>.output.<field> }}` / `{{ $metadata.* }}` tokens.** Never `{{input.<flat>}}` or `{{ $agent.<flat> }}` (derived-file namespaces), never `contentTokens`, never ExpressionValue objects. `flow validate` cannot catch a wrong namespace — the runtime renders the literal token.

7. **Author `agentInputVariables: []`** — entries are derived by tooling from `$vars`/`$metadata` refs across the cluster. Leave derived entries alone; never hand-populate.

8. **Mint `inputs.source` yourself: lowercase UUIDv4, unique per node** (`python3 -c "import uuid; print(uuid.uuid4())"`). It is the derived folder name and packaging identity. Never copy-paste a UUID between nodes; never omit it (the canvas would mint a fresh one, orphaning derived artifacts).

9. **Declare typed `agentOutputVariables[]`** — one `{id, type, description?}` entry per field, not a single `content` blob. Fields surface flat at `$vars.<nodeId>.output.<field>` — no `.content.` wrapper.

10. **Instance `outputs` = the `error` entry only; never an instance `model` block.** ServiceType, version, and context templates come from `definitions[]`; identity lives at `inputs.source`.

11. **Always override the model.** Discover with `uip agent model list --output json` and select per [model-selection-guide.md](model-selection-guide.md); set `maxTokenPerResponse` ≤ the model's cap. Never ship a copied example or manifest-default model name.

12. **One artifact edge per resource node:** agent `sourcePort ∈ {tool, context, escalation}` → resource `targetPort: "input"`, depth 1, one agent per resource. Resource nodes carry full config in their own `inputs` + their own `inputs.source` UUID.

13. **Guardrails live ONLY on the agent node's `inputs.guardrails[]`** — read [capabilities/guardrails.md](capabilities/guardrails.md) before writing any guardrail JSON (discriminator fields cannot be guessed) and run `uip agent guardrails list --output json` before any `builtInValidator`. `flow validate` is silent on guardrail content — the reference is the only gate. Default `[]` when none are requested.

14. **Legacy shells are migrated in the `.flow`, never edited in the sidecar.** A node whose `systemPrompt`/`userPrompt` is absent or non-string is a legacy shell — embed per [impl.md § 11](impl.md#11-legacy-flows--detect-and-migrate); leave the sidecar in place.

15. **Do not publish or deploy without user consent** — ask before `uip solution upload`, `uip solution publish`, or `uip solution deploy`.

## What NOT to Do (13)

1. **Do not create or edit sidecar files** (`<GUID>/agent.json`, `resources/**`, `features/**`, `flow-layout.json`) — derived; edits are shadowed on open and overwritten on save.
2. **Do not hand-write `bindings_v2.json`, `entry-points.json`, or `.agent-builder/`** — packaging artifacts.
3. **Do not use `{{input.*}}` / `{{ $agent.* }}` in `.flow` prompts** — flow prompts use `{{ $vars.* }}` / `{{ $metadata.* }}` only.
4. **Do not write `contentTokens` or `derivedInputDefinition` into node `inputs`** — derived agent.json / BPMN-emission artifacts.
5. **Do not hand-populate `agentInputVariables[]`** — derived; hand entries without a live `$vars` ref are pruned.
6. **Do not skip validation after a bulk of related edits** — always `flow format` + `flow validate` before moving to a new capability or publishing.
7. **Do not copy-paste UUIDs between nodes** — every `inputs.source` (agent and each resource) is unique.
8. **Do not put a `model` block on any inline-agent-related node instance** — agent node and every `uipath.agent.resource.*` node carry identity at `inputs.source` only.
9. **Do not use Flow CLI `node add` / `edge add` / `variable` commands for inline-agent graph edits** — author directly with `Edit` / `Write`.
10. **Do not read a `.content.` wrapper on typed outputs** — `$vars.<node>.output.content.<field>` resolves to undefined and yields a null flow output; typed fields are flat.
11. **Do not work around the debug/pack synthesis gap by hand-writing the sidecar** — surface the gap per [impl.md § 9](impl.md#9-validate); a canvas open/save derives it.
12. **Do not invoke other skills automatically.** Standalone agent projects belong to the `uipath-agents` skill; tell the user rather than switching.
13. **Do not omit guardrail discriminators (`$guardrailType`/`$actionType`/`$ruleType`/`$selectorType`/`$parameterType`), lowercase scope values, or write `guardrail.policies` on any derived resource** — `flow validate` catches none of these; [capabilities/guardrails.md](capabilities/guardrails.md) is the gate. Fresh UUID per guardrail `id`.
