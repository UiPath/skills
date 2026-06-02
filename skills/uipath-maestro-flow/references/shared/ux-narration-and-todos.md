# UX — Narration and Todos

Two **opt-in** rules govern how this skill communicates with the user during work. They are **off by default** — the agent works quietly. Engage them only when the user requests narration / progress tracking or signals a preference for verbosity. When engaged, they apply across every capability (Author, Operate, Diagnose, Evaluate), every journey, and every action type (`uip` CLI, shell builtins, Read/Write/Edit, Glob/Grep).

> Inherits from [SKILL.md](../../SKILL.md). The rules below are the canonical source — capability indexes and journey docs reference this file.

## When to engage

Engage narration + todos when **any** of these hold:

- User explicitly asks: "narrate", "walk me through it", "show your steps", "keep a todo list", "track progress", "tell me what you're doing", "verbose", "be detailed", "explain as you go".
- User expresses a standing preference for verbosity (in-session, or via a recalled memory / preference).
- User asks a question that only makes sense with running commentary ("what are you doing right now?", "where are we?").

**Default — silent mode.** When none of the above hold, do the work quietly. Surface only: decisions (`AskUserQuestion`), failures, consent gates (`flow debug`), and the final result. No per-step narration line; no user-facing `TodoWrite` list. The agent MAY still keep todos privately on large journeys for its own tracking, but it is not required and is not a user-facing contract.

## The two rules

These apply **only once engaged** (see When to engage):

1. **Narrate every logical step in plain English** — one short line before each step explaining what the agent is doing and why, in terms of the user's request. The user should never need to know `bash`, `uip` flags, or `.flow` JSON internals to follow along.
2. **Maintain a granular `TodoWrite` list** for any journey above the trivial threshold — one todo per logical step, kept current as work proceeds. Standard journeys typically land at 10+ items; complex flows go higher. The count emerges from the journey's actual logical steps — do not target a number.

## What is a "logical step"

A logical step is the smallest user-meaningful **outcome** — usually 1–5 actions across any mix of tools grouped under one intent.

| Step intent | Actions inside |
| --- | --- |
| Discover and add the Slack node | `registry search` + `registry get` + `flow node add` + Edit to wire outputs |
| Confirm project layout | `ls` + `cat <project>.flow` + `Glob` for nested files |
| Update a script body | `Read` of `.flow` + `Edit` on the script node's `inputs.code` |
| Validate the flow | `flow validate` (one call, but still a step) |
| Triage a fault | `instance asset` + `incident list` + `incident get` |

Bash plumbing inside a step is invisible to the user — the step's narration line covers it.

## Narration cadence

| Situation | Rule |
| --- | --- |
| Start of a logical step | **Narrate.** One short line, plain English, user terms. |
| Multiple actions within the same step | No additional narration — the step's opening line covers them |
| Step transitions (one outcome done, next starting) | Narrate the next step |
| Decision point | Brief one-liner before `AskUserQuestion` ("This decision affects which connection binding I generate — choose one:") |
| Failure / retry | Always narrate — explain what failed and what's being tried next. Failures surface even in silent mode. |
| Trivial probe (`uip --version`, repeated `login status` in same minute) | Skip |
| Non-`uip` shell commands (`ls`, `cat`, `mkdir`, `cd`) used as plumbing inside a step | Skip — covered by the step's opening narration |
| File reads/edits inside a step | Skip — covered by the step's opening narration |

## Narration line format

- **Length:** ≤ ~15 words. Single sentence or fragment.
- **Voice:** system voice. Not first person ("I'm checking…" → "Checking…").
- **Terms:** user terms. "looking up the Slack node schema" — not "running `registry get core.action.slack.send`".
- **Carry information:** every line tells the user something they couldn't have inferred from the prior line. No ceremony, no recap of flags or JSON paths.
- **Reference user intent when scope is non-obvious.** "Adding the Slack node" beats "Adding a node"; "Editing the flow JSON to wire the new variable" beats "Editing the file".

## Phrasing register

Reference table — adapt to context. Add subject (what's being acted on) when scope is ambiguous.

| Logical step | Narration |
| --- | --- |
| Login probe | "Checking whether you're logged in to the UiPath tenant…" |
| Solution scaffold | "Scaffolding a new solution at `<path>` so the Flow project has a parent." |
| Flow init | "Initializing the Flow project. This creates the `.flow` file you'll edit." |
| Verify project layout | "Confirming the solution/project layout is correct before continuing." |
| Registry discovery | "Looking up `<node-type>` in the registry so I can wire its inputs correctly…" |
| Node add (multi-step) | "Adding the `<node-type>` node and copying its registry definition into the file…" |
| Edit flow JSON | "Editing the flow JSON to add the `<thing>`." |
| Edge wiring | "Wiring `<from>` → `<to>` so data flows in the right order." |
| Variable mapping | "Mapping output variables on the End node — every reachable End needs them." |
| Script body update | "Updating the script body in the `<nodeId>` node." |
| Resource refresh | "Syncing connection and resource declarations into the solution before upload…" |
| Validate | "Running validate. This catches missing edges, bad expressions, and wiring mistakes." |
| Format | "Formatting the layout. Studio Web renders nodes correctly only after format normalizes their sizes." |
| Studio Web upload | "Pushing to Studio Web. This is the safe path — no execution, just the visual editor." |
| Pack for Orchestrator | "Packing the solution for Orchestrator deploy…" |
| Orchestrator publish | "Publishing the package to Orchestrator…" |
| Debug consent | "Running debug end-to-end. Real systems will be hit (emails sent, Slack posts, API calls)." |
| Process run | "Triggering the deployed process now…" |
| Job status | "Checking the job's current status…" |
| Job traces | "Pulling traces — verbose execution timeline." |
| Instance pause | "Pausing the running instance…" |
| Instance resume | "Resuming the instance from where it paused…" |
| Instance cancel | "Cancelling the instance…" |
| Instance retry | "Retrying the faulted instance from the last successful checkpoint…" |
| Incident fetch | "Fetching the incident record — this is the structured error report from the failed run." |
| Variable inspection | "Reading the runtime variable state at the moment of failure…" |
| Flow correlation | "Mapping the faulting element ID back to a node in your `.flow` file…" |
| Traces (last resort) | "Pulling traces. Last resort — the previous steps weren't enough." |

## Threshold for `TodoWrite`

This table applies only once narration/todos are engaged (see [When to engage](#when-to-engage)). In silent mode there is no user-facing narration or todo list regardless of journey size.

| Journey size | Narration | TodoWrite |
| --- | --- | --- |
| Single edit (1–2 actions, no decisions) | Yes — 1 line | No |
| Small edit (3–5 actions or 1 decision) | Yes — line per logical step | Optional, agent's call |
| Standard journey (greenfield, brownfield with multiple nodes, ship, run, full diagnose) | Yes — line per logical step | **Required** — granular |
| Complex flow (10+ nodes, multiple resource bindings, planning phase) | Yes — denser cadence | **Required** — granular, with sub-todos |

## Todo granularity

A todo is a **state-changing outcome the user cares about**. One logical step ≈ one todo. Multiple actions across multiple tools can map to one todo.

**Counts as a todo:**
- Solution scaffolded
- Flow project initialized
- Node added and wired
- Edges connected
- Variables defined and mapped
- Validate green
- Format applied
- Resources refreshed
- Uploaded to Studio Web
- Incident fetched and read
- Root cause classified

**Does NOT count as a todo (invisible plumbing):**
- Single `registry get` for schema lookup
- `ls` / `cat` / `Glob` to confirm a path
- Reading a file before editing it
- Re-running the same `validate` after a one-character fix (same todo, just not yet checked)
- Parsing JSON output

## Pivot rules

If the user redirects scope mid-journey ("skip the connector — use HTTP instead"):

1. Narrate the pivot — "Switching from connector to HTTP node. Updating todos."
2. Update `TodoWrite`:
   - Mark obsolete in-flight todos as cancelled and drop them from the list.
   - Insert new todos for the new direction at the right spot.
   - Leave completed todos in place — they're history, not work.
3. Continue from the new in-progress todo.

## Anti-patterns

- **Never narrate every command.** "Running `registry search`… running `registry get`… running `flow node add`…" — three lines for one logical step is noise. One step, one line.
- **Never narrate every Read/Edit.** Reading the `.flow` before editing it is plumbing. The step's opening line covers it.
- **Never recap flag-level or JSON-structure-level detail.** The user does not care that you used `--output json` or that `inputs.detail.bodyParameters` is the field name. Speak in user terms.
- **Never narrate or spin up a user-facing todo list when the user hasn't asked for verbosity.** Silent by default. Surfacing every step unprompted is noise.
- **When engaged, never skip narration on a step transition.** Silent transitions leave the user lost.
- **Never create a todo per bash call.** Todos are user-meaningful outcomes, not the agent's internal action log.
- **When engaged, never skip `TodoWrite` on a standard journey.** Above the trivial threshold, the granular list is mandatory.
- **Never use first-person filler.** "Let me…", "I'll go ahead and…", "I'm going to…" — drop. Lead with the verb.
- **Never repeat the prior line's content.** If the previous narration said "Adding the Slack node and wiring its inputs", the next line is *not* "Adding the Slack node now" — it's the next step.
