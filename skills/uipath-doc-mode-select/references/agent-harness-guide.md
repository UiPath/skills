# Agent Harness and Attachments Guide

Selecting the autonomous agent's harness, and deciding which optional capabilities to attach. This is a
selection guide; `uipath-agents` owns the configuration.

## Interaction type comes first

Autonomous, conversational, and voice agents are separate choices, not variants of one setting.

| Need | Type |
|---|---|
| Delegated work with a defined output contract | Autonomous |
| Multi-turn dialogue with a person | Conversational |
| Spoken interaction over a call | Voice |

The harness and attachment guidance below applies to **autonomous** agents. Do not infer autonomous-only
configuration for the other two — verify each type's own supported settings.

## Standard versus advanced harness

`settings.mode` accepts `"standard"` or `"advanced"`. The repository's configuration guidance defaults to
`"standard"`, and no feature matrix distinguishing the two is published here.

Treat that as the decision rule, not as a gap to fill by guessing:

1. **Start with standard** for bounded reasoning with known tools and a defined output contract.
2. **Select advanced only for a concrete required behavior** that you have verified is supported there
   and is unavailable or materially inadequate in standard, in the target environment.
3. **Record what the requirement is.** "Complex workload" is not a requirement. "Requires <behavior X>,
   which standard does not support in this tenant" is.
4. When the distinction is unknown, keep the required behavior in the specification and leave the harness
   label unresolved rather than picking advanced defensively.

### What does not select advanced

None of these is a harness requirement:

- a long document, or many documents;
- a persistent index, or an agentic search loop;
- many Flow nodes, or a multi-stage pipeline;
- a regulated industry or a high-stakes decision;
- coded rather than low-code authoring — that is an independent axis;
- `Extract · Advanced` — an extraction strategy, unrelated to the harness.

A Flow can orchestrate several standard agents and deterministic nodes. That is usually the simpler and
cheaper design; prefer it and explain any departure.

### What no harness setting grants

Checkpointing, retry and resume, parallelism, evaluation, and durability all require explicit
implementation and bindings. Persist long-running job state in a suitable store and implement polling
with a supported start/status pattern and a bounded loop. Do not assume the harness provides them.

## Optional attachments

Attach only what the workload needs. Each addition widens the agent's decision space and its failure
surface.

| Attachment | Add when | Specify | Avoid |
|---|---|---|---|
| **Context** | Reusable grounded knowledge is required | Index binding, access scope, freshness and ingestion checks, retrieval settings, and a call cap | A standalone "persistent index" node — it does not exist; confusing it with conversation state |
| **Tools** | The agent must decide when and how to invoke a supported capability | Binding, inputs and outputs, a usage boundary, timeout and failure handling | Duplicating a fixed Flow step inside the agent without a reason |
| **Memory** | Justified state must survive beyond the current run | What is retained, its scope, ownership, retention, and update behavior | Storing every document by default; treating memory as a database or a policy authority |
| **Escalations** | The agent needs an exceptional handoff when evidence or judgment is unresolved | Trigger, recipient binding, payload, and the supported continuation | Assuming a model's self-rating is calibrated; replacing every planned review with an escalation |

Two distinctions that are routinely collapsed:

- **A persistent index is not memory.** It is reusable grounded knowledge, read the same way on every
  run. Memory is retained state that changes across runs.
- **A planned review is not an escalation.** Scheduled human checkpoints belong in Human nodes in the
  Flow. An escalation is the agent's exception path.

## Every tool and context handle needs a cap

An agent given a grounding tool and no call limit re-queries with new phrasings until the runtime
terminates it (`AGENT_RUNTIME.TERMINATION_MAX_ITERATIONS`; in a Flow, a failed node with incident
`170002`). Raising `settings.maxIterations` moves the failure rather than fixing it.

State a numeric cap and a fallback per grounding tool. When the workload genuinely needs several
dependent lookups, that is agentic search — bound it deliberately per
[search-mode-guide.md](search-mode-guide.md), do not leave it uncapped.

## Handing off

Once the harness and attachments are chosen, the configuration belongs to `uipath-agents`:

- [/uipath:uipath-agents — SKILL.md](../../uipath-agents/SKILL.md) § Task Navigation
- [/uipath:uipath-agents — lowcode/agent-definition.md](../../uipath-agents/references/lowcode/agent-definition.md) — `agent.json` settings
- [/uipath:uipath-agents — context/context.md](../../uipath-agents/references/lowcode/capabilities/context/context.md) — context variants
- [/uipath:uipath-agents — memory/memory.md](../../uipath-agents/references/lowcode/capabilities/memory/memory.md)
- [/uipath:uipath-agents — escalation/escalation.md](../../uipath-agents/references/lowcode/capabilities/escalation/escalation.md)
- [/uipath:uipath-agents — autonomous-agent-prompting-guide.md](../../uipath-agents/references/lowcode/prompting/autonomous-agent-prompting-guide.md)

For an agent embedded in a Flow, the node and its artifact ports are owned by
[/uipath:uipath-maestro-flow — plugins/inline-agent/planning.md](../../uipath-maestro-flow/references/author/plugins/inline-agent/planning.md).

Cases that turn on this decision: [AH1–AH3](case-library-guide.md#ah-advanced-harness).
