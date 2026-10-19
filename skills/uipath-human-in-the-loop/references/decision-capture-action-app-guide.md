# Guided Decision Experience

Read this before designing any Coded Action App schema. It decides whether the guided decision experience is on (see "Decide the toggle from what the developer wants") and, when it is, what to add.

The guided decision experience is an **opt-in toggle on a Coded Action App the author already needs**. With the toggle off, the app is an ordinary action app. With it on, the skill:

1. **Adds a fixed set of decision fields** to the app's `action-schema.json`, beside the author's own fields.
2. **Switches the UI to the guided layout**: the reviewer confirms or corrects what was proposed, sets a weight on each reason, picks rationale chips, and, only when departing from the proposal, picks a lesson for next time.

The author's own fields keep their names, types and directions. Downstream steps read them as `$vars.<nodeId>.output.<fieldId>`, so renaming one breaks the flow.

Nothing in the app builds the Decision. When the task completes, the backend turns the task data into a Decision and persists it. The toggle only shapes what the task data contains.

Lifecycle commands (scaffold, `uip codedapp pack`, `publish -t Action`, `deploy --folder-key`) come from the `uipath-coded-apps` skill. Read its `references/create-action-app.md` and `references/pack-publish-deploy.md` before running them. Everything in its Critical Rules still applies, especially: never call `sdk.initialize()` in an action app.

## Decide the toggle from what the developer wants

Never open with a yes/no question. Read the request and set the toggle yourself:

| Signal in the request | Toggle |
|---|---|
| Asks to capture, record or learn from a decision, or names the Decision Ledger | On |
| An agent, automation or model proposes a value, label, route or verdict that a reviewer confirms or corrects | On |
| The reviewer picks between named resolutions backed by reasons (approve/deny, triage, route, accept/reject a vendor) | On |
| The reviewer only enters data nothing proposed, or only acknowledges (sign a form, upload a file) | Off |

When the toggle is on and the user did not ask for it by name, say in one line what you turned on and why, for example: "The agent proposes a route that reviewers correct, so I turned on the guided decision experience: reviewers confirm with one click, and each correction teaches the next run. Say so if you want a plain form." Then proceed without waiting. When it is off but a proposal is close to the surface, mention it once in the final report as a one-line option.

QuickForm has no guided layout. If the user wants the guided experience on a QuickForm, say so and offer a Coded Action App instead.

## Fields the toggle adds

Proposals can come from an agent, an automation or a person, so the fields say "proposed", never "agent".

| Section | Field | Type | Holds |
|---|---|---|---|
| `inputs` | `proposedOutcome` | string | The outcome the process proposes; equals one outcome name |
| `inputs` | `proposalConfidence` | number | 0 to 100 |
| `inputs` | `rationaleOptions` | string[] | Rationale chips the process proposes for this task |
| `inputs` | `instructionOptions` | string[] | Lessons the process proposes, model-written, one sentence each |
| `inOuts` | `evidence` | array | The reasons. Proposed in, reviewer's weights and flags out (item shape below) |
| `outputs` | `rationale` | string[] | The chips the reviewer kept, plus any they added |
| `outputs` | `instructionText` | string | The lesson the reviewer picked or edited; empty string when none |
| `outputs` | `instructionScope` | string | `this-task`, `similar-tasks` or `all-tasks` |

`evidence` item:

| Field | Type | Holds |
|---|---|---|
| `id` | string | Stable id |
| `title` | string | Short, specific claim |
| `description` | string | The fact behind it, with the concrete value, date or clause |
| `supports` | string | The outcome name it argues for |
| `weight` | string | `High`, `Medium`, `Low` or `Not relevant`. Proposed in, reviewer's choice out |
| `notRelevantWhy` | string | `Wrong`, `Outdated` or `Other`; set only when `weight` is `Not relevant` |
| `notRelevantNote` | string | Free text, only when `notRelevantWhy` is `Other` |

**Outcomes are the decision.** The author's outcome buttons stay as they are and the reviewer's click is the decision. If the app has a single `Submit` outcome, ask the user for the real choices (Approve, Deny, ...) and make each one an outcome. Rename an existing outcome only with the user's yes, and update every flow port that reads it.

Every field the process proposes and the reviewer may change belongs in `inOuts` under one name. The toggle never moves an author's field; it tells the user when a field they want corrected is an `input` and asks before moving it.

## What the backend records

When the task completes with `completeTask('<OUTCOME_NAME>', data)`:

| Task data | Decision |
|---|---|
| The outcome clicked | `AcceptedOutcome` |
| Every field in `data` | `Data.<field>`: `inOuts` values carry the proposed value in and the final value out; `outputs` values carry the final value only |
| `rationale` | Rationale in the Decision Ledger |
| `instructionText`, `instructionScope` | Instruction in the Decision Ledger |
| The user who completed the task | `Actor` |

## Critical Rules

1. Set the toggle from the request's signals (table above), state it in one line when you turned it on unasked, and never block on a question about it.
2. Never rename, retype or redirect the author's own fields or outcomes without the user's yes.
3. Return every `inOuts` value in exactly the shape it arrived in. Never add keys, counters or UI state. Anything added appears in the Decision as a change the reviewer made.
4. Treat every input and `inOuts` value as possibly absent. Render an empty state, and never return a field the task did not receive.
5. Never write computed or telemetry fields (`signals`, `action`, timings) into task data.
6. Reasons, rationale options and lessons are model-written by the process that creates the task, never rule-generated or templated in the app.
7. Never pre-select `proposedOutcome`.

## The guided layout

Build it with Apollo Wind components (`@uipath/apollo-wind`). The author's own fields render first, unchanged; the guided sections follow.

| Section | Reviewer sees | Reviewer does |
|---|---|---|
| Decision | One card per outcome; the proposed one carries "Proposed · `proposalConfidence`%". Once picked, a chip says "As proposed" or "Override". | Clicks one card |
| Reasons | One row per `evidence` item: title, description, "Supports <outcome>", and a weight menu with bar marks (High, Medium, Low, Not relevant). Reasons are true unless the reviewer says otherwise. | Picks a weight. Choosing Not relevant reveals "Why is it not relevant?" with Wrong, Outdated and Other; Other opens a short note. |
| Rationale | `rationaleOptions` as chips, plus "Add your own" | Taps chips. Optional when the reviewer kept everything; required once they depart. |
| Teach | Shown only when the reviewer departed. `instructionOptions` as cards, and "Applies to": This task, Similar tasks, All tasks | Taps one lesson, optionally edits it, picks the scope |
| What changed | A side panel listing each change as it happens: Decision `Route → Close`, Reason `High → Not relevant · Wrong`, Rationale `2 chips`, Lesson | Reads it before recording |

Rules:

- Every control whose value differs from the proposal shows "Proposed: <value>" under it.
- With no change, the single button reads "Agree · <proposedOutcome>" and completes in one click.
- With any change, the button reads "Record decision". It is disabled until an outcome is picked, every Not relevant reason has a why, at least one rationale chip is picked, and a lesson is picked. The note under it names what is missing.
- After completion, the screen shows the filed state read-only.
- Honour `task.isReadOnly`: render the saved values, never complete.
- Keep the app's types in one file (`src/decision/types.ts`) derived from `action-schema.json`. Never declare the same type twice.

## Steps

1. Decide the toggle from the request (above). Off: stop here and build the app on the normal path.
2. Read the author's existing `action-schema.json`, or design it from the use case on the normal path first.
3. Show the user one table: their fields unchanged, the added decision fields, their outcomes as the decision choices, and any field you recommend moving to `inOuts`. Proceed without waiting; record the table in the final report.
4. Add the fields from "Fields the toggle adds" to `action-schema.json`.
5. Build the guided layout. Write `sample-task-data.json` with realistic values for every field, including 3 to 6 reasons covering more than one outcome, 4 to 6 rationale options and 2 lesson options.
6. Build (`npm run build`) and fix type errors. Do not loosen types to silence them.
7. Run the app against `sample-task-data.json` and look at it: the untouched state, a changed state, and the filed state. Do not report done before this.
8. Follow `uipath-coded-apps` for pack, publish (`-t Action`) and deploy.

## Anti-patterns

- Asking "do you want decision capture?" instead of reading the request.
- Turning it on for pure data entry, where nothing was proposed.
- Free-text boxes as the main input. The reviewer taps; typing is the fallback.
- Renaming the author's fields to fit the decision fields.
- A single `Submit` outcome with the choice stored in a field.
- Templated lessons ("Field X is Y") built in the app.
