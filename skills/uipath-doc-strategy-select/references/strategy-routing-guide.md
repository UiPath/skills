# Strategy Routing Guide

Maps a selected strategy to the skill that owns building it. This skill selects; the target owns node
schemas, configuration fields, and CLI invocation.

## Registry before labels

The Add-node canvas label and the wire type are different strings. Summarize is
`uipath.pattern.deep-rag`; Extract is an `uipath.ixp.*` node. Before naming any node:

```bash
uip maestro flow registry search "<keyword>" --output json
uip maestro flow registry get <node-type> --output json
```

Tenant-specific nodes (IxP models, connectors) appear only after `uip login`. Registry reads are cached
for 30 minutes, so an empty search is not proof of absence until you have run
`uip maestro flow registry pull --force` once and searched again.

**The registry cannot confirm the Extract document node.** `uipath.ixp.extract-document-builder` is in
no tenant manifest — Studio Web adds it to the canvas client-side behind a tenant feature flag — so
`registry search` reports `AvailableOnTenant: false` on every tenant, enabled or not, even after login
and pull, and `registry get` answers `Node not found`. `nodes create` and `validate` also succeed on a
tenant that cannot run it. The registry check holds for wire types and tenant-published IxP models only.
The tenant check for this node is:

```bash
uip maestro flow extraction check --output json
```

`Data.Status` `Available` means the tenant can run it. `FeatureDisabled`, `ModelUnavailable` and
`ServiceUnavailable` mean it cannot — route to a published IXP model instead (§ Which Extract node,
rule 4). `Unknown` or a non-zero exit settles nothing: report it, never treat it as unavailable.
Interpreting the result and acting on it belongs to `uipath-maestro-flow`.

## Handoff map

| Strategy selected | Owner | Build guide |
|---|---|---|
| Extract, inside a Flow — default: a published IXP model | `uipath-maestro-flow` | [/uipath:uipath-maestro-flow — ixp.md](../../uipath-maestro-flow/references/ixp.md) |
| Extract, inside a Flow — the Extract document node: named by the user, already in the flow, or IXP not enabled | `uipath-maestro-flow` | [/uipath:uipath-maestro-flow — extract-document-node.md](../../uipath-maestro-flow/references/extract-document-node.md) · [taxonomy](../../uipath-maestro-flow/references/extract-document-taxonomy.md) |
| Extract — no trained model yet: taxonomy, labelling, training, deployment | `uipath-ixp` | [/uipath:uipath-ixp — SKILL.md](../../uipath-ixp/SKILL.md) |
| Summarize, as a fixed Flow step | `uipath-maestro-flow` | [/uipath:uipath-maestro-flow — summarize.md](../../uipath-maestro-flow/references/summarize.md) |
| Summarize, as an agent-chosen action over attachments | `uipath-agents` | [/uipath:uipath-agents — deeprag/planning.md](../../uipath-agents/references/lowcode/capabilities/built-in-tools/deeprag/planning.md) |
| Analyze files | `uipath-agents` | [/uipath:uipath-agents — analyze-attachments.md](../../uipath-agents/references/lowcode/capabilities/built-in-tools/analyze-attachments.md) |
| Batch transform, per-row LLM work over a CSV | `uipath-agents` · `uipath-maestro-flow` | [/uipath:uipath-agents — batch-transform/planning.md](../../uipath-agents/references/lowcode/capabilities/built-in-tools/batch-transform/planning.md) · [/uipath:uipath-maestro-flow — batch-transform.md](../../uipath-maestro-flow/references/batch-transform.md) |
| Persistent index, semantic search (PS) | `uipath-agents` | [/uipath:uipath-agents — context/index.md](../../uipath-agents/references/lowcode/capabilities/context/index.md) |
| Index lifecycle from the CLI — create, ingest, search, delete | `uipath-platform` | [/uipath:uipath-platform — index-management.md](../../uipath-platform/references/context-grounding/index-management.md) |
| Agent node referencing a published agent | `uipath-maestro-flow` | [/uipath:uipath-maestro-flow — agent.md](../../uipath-maestro-flow/references/agent.md) |
| Agent defined inside the Flow | `uipath-maestro-flow` | [/uipath:uipath-maestro-flow — inline-agent.md](../../uipath-maestro-flow/references/inline-agent.md) |
| Agent lifecycle — scaffold, configure, evaluate, deploy | `uipath-agents` | [/uipath:uipath-agents — SKILL.md](../../uipath-agents/SKILL.md) |
| Deterministic transformation, branch, or calculation | `uipath-maestro-flow` | [/uipath:uipath-maestro-flow — script.md](../../uipath-maestro-flow/references/script.md) · [transform](../../uipath-maestro-flow/references/transform.md) · [branch](../../uipath-maestro-flow/references/branch.md) |
| Planned human review | `uipath-maestro-flow` · `uipath-human-in-the-loop` | [/uipath:uipath-maestro-flow — hitl.md](../../uipath-maestro-flow/references/hitl.md) |
| Which UiPath product at all, or a PDD/SDD | `uipath-planner` | [/uipath:uipath-planner — product-selection-guide.md](../../uipath-planner/references/shared/product-selection-guide.md) |

For the full node palette with real type IDs and selection heuristics, read
[/uipath:uipath-maestro-flow — author.md](../../uipath-maestro-flow/references/author.md)
§ Plugin Index and § Node Selection Heuristics. That table is maintained against the registry; this one
is only a routing index.

If a target skill is not installed, still deliver the strategy, the decisive signal, and a concrete
node-and-binding specification, and name the missing dependency.

## Which Extract node — published model or Extract document

Both are EX. `uipath-maestro-flow` owns this choice; the rules below mirror its default so an agent with
both skills loaded gets one answer.

1. **New flow: default to a published IXP model** — node type `uipath.ixp.<project>.<version>-<folder>`,
   built per `ixp.md`. This covers a new document type with no trained model too: hand off to
   `uipath-ixp` to build and deploy the project, then wire the Flow against the deployed model.
2. **New flow: use the Extract document node** (`uipath.ixp.extract-document-builder`) only when the user
   asks for it by name.
3. **Existing flow: keep the extraction node it has.** A Flow already holding an Extract document node
   (`uip maestro flow nodes list <file> --output json` shows the types), or a request about the taxonomy
   that node carries, stays on the Extract document node.
4. **Each falls back to the other.** IXP not enabled in the environment (`uip ixp` returns
   `not_supported`: Automation Suite, or a tenant without the IXP service) → stop IXP work and offer the
   Extract document node. Extract document not available on the tenant (§ Registry before labels) → a
   published IXP model whose taxonomy covers the requested fields. Neither available → stop and say so;
   never put a `mock()` or fixed-value script where extraction should run.
5. **Never pick the Extract document node to skip a training cycle.** Setup cost is not a routing signal.
   A recurring document type whose fields need calibrated review needs the trained model's field
   evaluation regardless.

Extract document facts that change the handoff — detail lives in the owning guides:

- **Taxonomy, not JSON Schema.** The node carries its taxonomy inline at `inputs.schemaDocument`: an
  object with `prompt` and `outputSchema`, where every field group and field holds a stable id
  (`x-uipath-field-group-id` / `x-uipath-field-id`). A bare JSON-Schema object with `properties` alone
  is not valid.
- **Author with the CLI.** `uip maestro flow nodes create` adds the node; `uip maestro flow nodes schema set`
  writes the taxonomy and mints the ids. Do not hand off to the SDK `dynamicExtract()` factory — it
  demands a published model identity the node never reads, and emits the schema without ids.
- **No IXP model or deployment.** The node requires only `fileRef`. It runs through a processor that the
  authoring commands provision; carry into the handoff what `nodes create` reported about that processor
  ([Making it actually extract](../../uipath-maestro-flow/references/extract-document-node.md#making-it-actually-extract)).
- **Tenant-gated and invisible to the registry** — run the extraction check in § Registry before labels.
- **Model settings, test documents and evaluations are out of CLI reach.** Extraction strategy, model
  choice, language, layout parsing, attribution, sample documents, annotation and evaluators are set in
  the Studio Web designer. Do not promise them as part of the build.

**Published model: deploying is not publishing.** The published-model node addresses the model by
`{FolderKey, DeploymentName}`, so the trained version must be deployed to an Orchestrator folder
(`uip ixp deployments create --folder-key`). `uip ixp projects publish` pins a version inside the project
and does not supply that folder identity. Treat "is there a project for this?" as a question about
deployment, and route the deployment itself to `uipath-ixp`.

## Flow-owned versus agent-owned placement

Several capabilities exist at both levels. The choice is whether the step is fixed and visible in the
graph, or whether the agent decides at runtime when to invoke it.

| Capability | Flow-owned | Agent-owned | Decide by |
|---|---|---|---|
| Summarize | `Document → Summarize` (`uipath.pattern.deep-rag`) | agent tool | A fixed visible stage vs an agent-selected evidence action |
| HTTP request | `Connector → HTTP Request` | agent tool | A known orchestration call vs an agent-selected request |
| Batch transform | `Data → Batch transform` | agent tool | A fixed batch stage vs an agent-selected transformation |
| Analyze files | no standalone node | agent tool only | Always agent-owned |

A fixed step duplicated inside the agent adds nondeterminism without adding capability. Duplicate only
when the agent genuinely must decide whether to run it.

## Extract strategy

Extract strategy is an extraction setting. It is not the agent harness — `Extract · Advanced` and the
advanced harness are unrelated axes.

| Strategy signal | Evaluate when |
|---|---|
| Short, clean forms with simple fields | Start at the lowest supported strategy |
| Digitization, tables, scans, routine structured capture | Standard capture with digitization settings validated on representative scans |
| Dense repeated entities, cross-page assembly, schema decomposition | Escalate only when measured density requires it |
| Irregular or sparse targets needing adaptive reads | Last resort; cost it explicitly |

Choose the lowest strategy that meets measured field quality, and confirm each option exists in the
target before promising it. Structural errors point at digitization and layout; semantic errors point at
field definitions. Count entities and output values, not just pages — a truncated entity group looks
like a clean result.

## Composition patterns

Logical plans, not executable syntax. Resolve IDs, expressions, and bindings with the owning skill.

1. **Field extraction with review.** Document entry → Extract → Decision on validated review criteria →
   Human review when needed → bind corrected fields → persist → End. Configure the non-review branch and
   the rejection outcome too.
2. **Structure detection then deterministic processing.** Agent with Analyze files returns the header and
   column mapping → script validates it against the file and parses rows → Loop over relevant items. Known
   exact mappings never enter the agent.
3. **Grounded question answering.** Agent with a persistent-index context, semantic search → structured
   answer plus unresolved list → Decision → planned human clarification if required → End.
4. **Enumeration with a completeness boundary.** Deterministic corpus enumeration and coverage
   reconciliation whenever the deliverable claims "all" → review → End. A retrieval result is never
   a coverage test.
5. **Pure data processing.** Filter → Group by → Map or Transform → script only for unsupported exact
   operations → persist → End. No document strategy and no agent.

Asynchronous work needs an explicit start/status/resume pattern and a durable store. No harness setting
grants persistence automatically. Give every loop and retry an explicit bound, and handle duplicate
effects on any retried state-changing action.
