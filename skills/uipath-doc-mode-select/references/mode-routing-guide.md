# Mode Routing Guide

Maps a selected mode to the skill that owns building it. This skill selects; the target owns node
schemas, configuration fields, and CLI invocation.

## Registry before labels

The Add-node canvas label and the wire type are different strings. Summarize is
`uipath.pattern.deep-rag`; Extract is an `uipath.ixp.*` node. Before naming any node:

```bash
uip maestro flow registry search "<keyword>" --output json
uip maestro flow registry get <node-type> --output json
```

Tenant-specific nodes (IxP models, connectors) appear only after `uip login` and
`uip maestro flow registry pull`. An empty search is not proof of absence until you are authenticated
and have pulled.

## Handoff map

| Mode selected | Owner | Build guide |
|---|---|---|
| Extract, inside a Flow | `uipath-maestro-flow` | [/uipath:uipath-maestro-flow — plugins/ixp/planning.md](../../uipath-maestro-flow/references/author/plugins/ixp/planning.md) |
| Extract — taxonomy, labelling, model training, publishing | `uipath-ixp` | [/uipath:uipath-ixp — SKILL.md](../../uipath-ixp/SKILL.md) |
| Summarize, as a fixed Flow step | `uipath-maestro-flow` | [/uipath:uipath-maestro-flow — plugins/summarize/planning.md](../../uipath-maestro-flow/references/author/plugins/summarize/planning.md) |
| Summarize, as an agent-chosen action over attachments | `uipath-agents` | [/uipath:uipath-agents — deeprag/planning.md](../../uipath-agents/references/lowcode/capabilities/built-in-tools/deeprag/planning.md) |
| Analyze files | `uipath-agents` | [/uipath:uipath-agents — analyze-attachments.md](../../uipath-agents/references/lowcode/capabilities/built-in-tools/analyze-attachments.md) |
| Batch transform, per-row LLM work over a CSV | `uipath-agents` · `uipath-maestro-flow` | [/uipath:uipath-agents — batch-transform/planning.md](../../uipath-agents/references/lowcode/capabilities/built-in-tools/batch-transform/planning.md) · [/uipath:uipath-maestro-flow — plugins/batch-transform/planning.md](../../uipath-maestro-flow/references/author/plugins/batch-transform/planning.md) |
| Persistent index, semantic search (PS) | `uipath-agents` | [/uipath:uipath-agents — context/index.md](../../uipath-agents/references/lowcode/capabilities/context/index.md) |
| Persistent index, agentic search (PA) | `uipath-agents` | `/uipath:uipath-agents — references/agentic-search/planning.md` |
| Index lifecycle from the CLI — create, ingest, search, delete | `uipath-platform` | [/uipath:uipath-platform — index-management.md](../../uipath-platform/references/context-grounding/index-management.md) |
| Agent node referencing a published agent | `uipath-maestro-flow` | [/uipath:uipath-maestro-flow — plugins/agent/planning.md](../../uipath-maestro-flow/references/author/plugins/agent/planning.md) |
| Agent defined inside the Flow | `uipath-maestro-flow` | [/uipath:uipath-maestro-flow — plugins/inline-agent/planning.md](../../uipath-maestro-flow/references/author/plugins/inline-agent/planning.md) |
| Agent lifecycle — scaffold, configure, evaluate, deploy | `uipath-agents` | [/uipath:uipath-agents — SKILL.md](../../uipath-agents/SKILL.md) |
| Classification or splitting | see [classify-split-guide.md](classify-split-guide.md) | — |
| Deterministic transformation, branch, or calculation | `uipath-maestro-flow` | [/uipath:uipath-maestro-flow — plugins/script/planning.md](../../uipath-maestro-flow/references/author/plugins/script/planning.md) · [transform](../../uipath-maestro-flow/references/author/plugins/transform/planning.md) · [decision](../../uipath-maestro-flow/references/author/plugins/decision/planning.md) |
| Planned human review | `uipath-maestro-flow` · `uipath-human-in-the-loop` | [/uipath:uipath-maestro-flow — plugins/hitl/planning.md](../../uipath-maestro-flow/references/author/plugins/hitl/planning.md) |
| Which UiPath product at all, or a PDD/SDD | `uipath-planner` | [/uipath:uipath-planner — product-selection-guide.md](../../uipath-planner/references/product-selection-guide.md) |

For the full node palette with real type IDs and selection heuristics, read
[/uipath:uipath-maestro-flow — planning-arch.md](../../uipath-maestro-flow/references/author/planning-arch.md)
§ Plugin Index and § Node Selection Heuristics. That table is maintained against the registry; this one
is only a routing index.

If a target skill is not installed, still deliver the mode, the decisive signal, and a concrete
node-and-binding specification, and name the missing dependency.

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
4. **Investigation with a completeness boundary.** Agentic search for candidate discovery → deterministic
   corpus enumeration and coverage reconciliation when the deliverable claims "all" → review → End. Search
   iteration alone never establishes completeness.
5. **Segment, then extract.** Classification and boundary resolution → per-segment Extract, preserving
   original page ranges → deterministic duplicate rules → End.
6. **Pure data processing.** Filter → Group by → Map or Transform → script only for unsupported exact
   operations → persist → End. No document mode and no agent.

Asynchronous work needs an explicit start/status/resume pattern and a durable store. No harness setting
grants persistence automatically. Give every loop and retry an explicit bound, and handle duplicate
effects on any retried state-changing action.
