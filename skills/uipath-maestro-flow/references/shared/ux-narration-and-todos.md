# UX — Narration and Todos

Two **opt-in** rules govern communication during work. They are **off by default**. Engage them when the user requests narration/progress tracking or signals a verbosity preference. Once engaged, they apply across every capability (Author, Operate, Diagnose, Evaluate), journey, and action type (`uip` CLI, shell builtins, Read/Write/Edit, Glob/Grep).

> Inherits from [SKILL.md](../../SKILL.md). These rules are canonical; capability indexes and journey docs reference this file.

## When to engage

Engage narration and todos if any condition holds:

- The user explicitly asks to narrate, show steps, keep a todo list, track progress, explain as work proceeds, be verbose, or be detailed.
- The user has a standing verbosity preference in-session or in recalled memory.
- The user asks a question requiring running commentary, such as what is happening or where work stands.

Otherwise use **silent mode**: work quietly and surface only decisions, failures, consent gates (`flow debug`), and the final result. Do not provide per-step narration or a user-facing todo list. Private todos remain optional for large journeys.

## The two rules

Once engaged:

1. **Narrate every logical step in plain English.** Give one short line before each step explaining what is being done and why in user terms; do not require knowledge of `bash`, `uip` flags, or `.flow` JSON.
2. **Maintain a granular progress list** for every journey above the trivial threshold: one todo per logical step, kept current. Standard journeys usually have 10+ items; complex flows have more. Do not target a count; derive it from the actual steps.

### Logical steps

A logical step is the smallest user-meaningful outcome, usually 1–5 actions grouped by intent across tools. Examples include discovering and adding a node, confirming project layout, updating a script body, validating a flow, or triaging a fault. Bash plumbing inside a step is covered by its narration.

## Narration cadence

| Situation | Rule |
|---|---|
| Start of logical step | Narrate one short line in plain English. |
| Multiple actions within a step | Do not add narration. |
| Step transition | Narrate the next step. |
| Decision point | Give a brief line before asking the user; explain the decision's consequence. |
| Failure/retry | Always narrate what failed and what will be tried next, even in silent mode. |
| Trivial probe (`uip --version`, repeated `login status` in the same minute) | Skip. |
| Non-`uip` shell plumbing (`ls`, `cat`, `mkdir`, `cd`) | Skip; the step line covers it. |
| File reads/edits inside a step | Skip; the step line covers them. |

## Narration lines

Keep each line to approximately 15 words or fewer, as one sentence or fragment. Use system voice, not first person. Use user terms rather than commands, flags, or JSON internals. State the actual subject when scope is ambiguous, convey new information, and avoid ceremony, recaps, and repetition.

Use or adapt these patterns:

| Step | Narration |
|---|---|
| Login probe | “Checking whether you're logged in to the UiPath tenant…” |
<!--skill-flavor:flow-project-creation-narration:start-->
| Solution scaffold | “Scaffolding a new solution at `<path>` so the Flow project has a parent.” |
| Flow init | “Initializing the Flow project. This creates the `.flow` file you'll edit.” |
| Verify project layout | “Confirming the solution/project layout is correct before continuing.” |
<!--skill-flavor:flow-project-creation-narration:end-->
| Registry discovery | “Looking up `<node-type>` in the registry so I can wire its inputs correctly…” |
| Node add | “Adding the `<node-type>` node and copying its registry definition into the file…” |
| Edit flow JSON | “Editing the flow JSON to add the `<thing>`.” |
| Edge wiring | “Wiring `<from>` → `<to>` so data flows in the right order.” |
| Variable mapping | “Mapping output variables on the End node — every reachable End needs them.” |
| Script body update | “Updating the script body in the `<nodeId>` node.” |
| Resource refresh | “Syncing connection and resource declarations into the solution before upload…” |
| Validate | “Running validate. This catches missing edges, bad expressions, and wiring mistakes.” |
| Format | “Formatting the layout. Studio Web renders nodes correctly only after format normalizes their sizes.” |
| Studio Web upload | “Pushing to Studio Web. This is the safe path — no execution, just the visual editor.” |
| Pack for Orchestrator | “Packing the solution for Orchestrator deploy…” |
| Orchestrator publish | “Publishing the package to Orchestrator…” |
| Debug consent | “Running debug end-to-end. Real systems will be hit (emails sent, Slack posts, API calls).” |
| Process run | “Triggering the deployed process now…” |
| Job status | “Checking the job's current status…” |
| Job traces | “Pulling traces — verbose execution timeline.” |
| Instance pause | “Pausing the running instance…” |
| Instance resume | “Resuming the instance from where it paused…” |
| Instance cancel | “Cancelling the instance…” |
| Instance retry | “Retrying the faulted instance from the last successful checkpoint…” |
| Incident fetch | “Fetching the incident record — this is the structured error report from the failed run.” |
| Variable inspection | “Reading the runtime variable state at the moment of failure…” |
| Flow correlation | “Mapping the faulting element ID back to a node in your `.flow` file…” |
| Traces, last resort | “Pulling traces. Last resort — the previous steps weren't enough.” |

## Progress-list threshold

This applies only when narration/todos are engaged. In silent mode, journey size never creates a user-facing list.

| Journey | Narration | Progress list |
|---|---|---|
| Single edit: 1–2 actions, no decisions | One line | None |
| Small edit: 3–5 actions or one decision | One line per step | Optional |
| Standard: greenfield, multi-node brownfield, ship, or full diagnose | One line per step | Required and granular |
| Complex: 10+ nodes, multiple resource bindings, or planning phase | Denser cadence | Required, granular, with sub-todos |

## Todo rules

A todo represents a state-changing outcome the user cares about; roughly one logical step. Multiple tool actions may form one todo.

Valid todos include: solution scaffolded; Flow project created; node added and wired; edges connected; variables defined and mapped; validate green; format applied; resources refreshed; uploaded to Studio Web; incident fetched and read; root cause classified.

Do not create todos for registry lookup, `ls`/`cat`/`Glob` path checks, pre-edit reads, parsing JSON, or rerunning the same `validate` after a one-character fix. Keep such plumbing invisible.

## Pivots

When scope changes:

1. Narrate the pivot, for example: “Switching from connector to HTTP node. Updating todos.”
2. Mark obsolete in-flight todos cancelled and remove them; insert todos for the new direction in the correct position; retain completed todos as history.
3. Continue with the new in-progress todo.

## Anti-patterns

- Never narrate every command, Read, Edit, or shell action; narrate logical outcomes.
- Never recap flags or JSON structure.
- Never show narration or a user-facing todo list without an engagement trigger.
- When engaged, never omit narration at a step transition or the required list for a standard journey.
- Never create a todo per bash call.
- Never use first-person filler such as “Let me,” “I'll go ahead,” or “I'm going to.”
- Never repeat the previous narration; move to the next logical step.
