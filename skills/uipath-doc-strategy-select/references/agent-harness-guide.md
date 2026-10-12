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

The harness is the `settings.mode` field on the agent, not a separate artifact — see
[/uipath:uipath-agents — agent-definition.md](../../uipath-agents/references/lowcode/agent-definition.md)
§ Settings, which owns the schema. The capability matrix below is published at
https://docs.uipath.com/agents/automation-cloud/latest/user-guide/advanced-agents — advanced is in
**preview**, Automation Cloud only, not Automation Suite. Verify availability in the target tenant
before committing to it.

An agent is a model plus a harness. The model reasons; the harness is the loop that drives it, the tools
it can call, and the memory it can write to.

| | Standard | Advanced |
|---|---|---|
| Execution model | Reason and act, one pass through the tools | Act, observe and adjust, repeated until done |
| Where intermediate work lives | The context window | A per-run file workspace — list, read, write, edit, delete, search, match |
| Long-run behavior | Context fills and the agent loses track | Completed tool output is offloaded and older history pruned (context compaction) |
| Delegation | None | Sub-agents run a slice of work in their own context and return only the result |
| Tool calling | One tool call per model turn | The agent writes JavaScript calling its own tools — fan out over a list, filter and aggregate in one step |
| Code | None | Persistent JavaScript sandbox: calculations, programmatic tool calls, dispatching sub-agents. No network, no filesystem |
| Reading files | Needs the Analyze files tool | Input and uploaded files land in the workspace automatically |
| Failure handling | — | Failed tool calls, schema mismatches and dead ends are detected and retried |

### Selecting advanced

Advanced suits work showing **two or more** of these signals. One alone is not enough.

1. The work runs long — dozens of tool calls rather than a handful.
2. The agent's intermediate work matters and should persist as files that can be opened afterwards.
3. Parts of the work are independent and benefit from being handled separately.
4. The material is larger than fits in a single prompt — long documents or large record sets.

Research, analysis and document-heavy workflows are the typical examples, as is any task where the agent
must gather evidence, weigh it against a set of criteria, and justify a conclusion. Standard remains
better for tasks that are short, predictable, and complete in a few tool calls.

### Selecting advanced does not deselect a tool

The harness is `settings.mode` on the agent; Summarize, Analyze files and Batch transform are tools that
agent calls. They sit on different axes, so they do not trade off. An agent on either harness can call
any of those tools, and a Flow can hold that agent as one node among deterministic ones.

The Fast Routing table still asks for **one** answer, because the question it answers is which capability
carries the workload. Answer AH when the shape is not known in advance and the agent has to plan its own
steps — then say in the placement which tools it is given. Answer a fixed strategy when one of them
already satisfies the contract, even if the step runs inside an autonomous agent.

### Before committing to advanced

- **Preview gaps.** Tool argument values cannot be configured — every parameter is supplied by the model.
  Guardrails are not supported. Some Integration Service activities are unavailable. Custom sub-agents
  cannot be defined; only the built-in general-purpose sub-agent exists. An advanced agent cannot be
  cloned as a coded agent.
- **Moving an existing agent to advanced is destructive and one-way.** It permanently discards any Static
  and Argument values configured on its tools, and switching back does not restore them.
- **Cost follows call count.** Billing is per LLM call against the same units as standard, but a single
  advanced run makes more calls than a comparable standard run. Say so when you select it.

### What does not select advanced on its own

Each of these is either one signal (and the rule needs two), or no signal at all:

- **A long document, or many documents** — this is signal 4 only. Pair it with a second signal, or keep
  the bounded read and stay standard.
- **A long-running *process*** — a multi-day wait on a third party is elapsed time, not tool calls.
  Signal 1 is dozens of agent tool calls in one run. A Flow that waits is a Flow concern.
- a persistent index;
- many Flow nodes, or a multi-stage pipeline — stages in a graph are not the agent's own tool calls;
- a regulated industry or a high-stakes decision;
- coded rather than low-code authoring — an independent axis, decided in
  [/uipath:uipath-agents — coded-vs-lowcode-guide.md](../../uipath-agents/references/coded-vs-lowcode-guide.md);
- `Extract · Advanced` — an extraction strategy, unrelated to the harness.

A Flow can orchestrate several standard agents and deterministic nodes. Where that fits, it is the
simpler and cheaper design; prefer it and explain any departure.

### What the harness does not give you for free

Advanced self-corrects *within* a run — failed tool calls, schema mismatches and dead ends are detected
and retried. That is not the same as process durability. **Checkpointing across a run boundary, resume
after a crash, scheduled evaluation, and durable state all still require explicit implementation and
bindings**, on either harness. Persist long-running job state in a suitable store and implement polling
with a supported start/status pattern and a bounded loop.

The distinction that matters when routing: *"the agent needs dozens of tool calls to finish one item"*
is signal 1 and counts toward advanced. *"a case sits for eleven days waiting on a supplier"* is
orchestration and counts toward neither.

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
dependent lookups, one retrieval cannot answer it — see
[search-strategy-guide.md](search-strategy-guide.md); no strategy here covers that shape yet.

## Handing off

Once the harness and attachments are chosen, the configuration belongs to `uipath-agents`:

- [/uipath:uipath-agents — SKILL.md](../../uipath-agents/SKILL.md) § Task Navigation
- [/uipath:uipath-agents — lowcode/agent-definition.md](../../uipath-agents/references/lowcode/agent-definition.md) — `agent.json` settings
- [/uipath:uipath-agents — context/context.md](../../uipath-agents/references/lowcode/capabilities/context/context.md) — context variants
- [/uipath:uipath-agents — memory/memory.md](../../uipath-agents/references/lowcode/capabilities/memory/memory.md)
- [/uipath:uipath-agents — escalation/escalation.md](../../uipath-agents/references/lowcode/capabilities/escalation/escalation.md)
- [/uipath:uipath-agents — autonomous-agent-prompting-guide.md](../../uipath-agents/references/lowcode/prompting/autonomous-agent-prompting-guide.md)

For an agent embedded in a Flow, the node and its artifact ports are owned by
[/uipath:uipath-maestro-flow — plugins/inline-agent/planning.md](../../uipath-maestro-flow/references/inline-agent.md).

Cases that turn on this decision: [AH1–AH3](case-library-guide.md#ah-advanced-harness).
