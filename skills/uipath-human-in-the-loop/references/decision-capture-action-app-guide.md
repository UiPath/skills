# Guided Decision Experience

Read this before designing any Coded Action App schema. It decides whether the guided decision experience is on (see "Decide the toggle from what the developer wants") and, when it is, what to add.

The guided decision experience is an **opt-in toggle on a Coded Action App the author already needs**. With the toggle off, the app is an ordinary action app. With it on, the skill:

1. **Adds a fixed set of decision fields** to the app's `action-schema.json`, beside the author's own fields.
2. **Switches the UI to a light capture layout**: the normal form, every field opening at its proposed value, a one-tap reason only where the reviewer changed something, and a deeper section only when the case calls for it.

The author's own fields keep their names, types and directions. Downstream steps read them as `$vars.<nodeId>.output.<fieldId>`, so renaming one breaks the flow.

Nothing in the app builds the Decision. When the task completes, the backend turns the task data into a Decision and persists it. The toggle only shapes what the task data contains.

Lifecycle commands (scaffold, `uip codedapp pack`, `publish -t Action`, `deploy --folder-key`) come from the `uipath-coded-apps` skill. Read its `references/create-action-app.md` and `references/pack-publish-deploy.md` before running them. Everything in its Critical Rules still applies, especially: never call `sdk.initialize()` in an action app.

## Decide the toggle from what the developer wants

Never open with a yes/no question. Read the request and set the toggle yourself:

| Signal in the request | Toggle |
|---|---|
| Asks to capture or record a decision, or names the Decision Ledger | On |
| An agent, automation or model proposes a value, label, route or verdict that a reviewer confirms or corrects | On |
| The reviewer picks between named resolutions backed by reasons (approve/deny, triage, route, accept/reject a vendor) | On |
| The reviewer only enters data nothing proposed, or only acknowledges (sign a form, upload a file) | Off |

When the toggle is on and the user did not ask for it by name, say in one line what you turned on and why, for example: "The agent proposes a route that reviewers correct, so I turned on the guided decision experience: reviewers confirm with one click, and a change asks for one tap of reason. Say so if you want a plain form." Then proceed without waiting. When it is off but a proposal is close to the surface, mention it once in the final report as a one-line option.

QuickForm has no guided layout. If the user wants the guided experience on a QuickForm, say so and offer a Coded Action App instead.

## Capture depth scales to stakes

Three levels. The reviewer never chooses the level; the developer does.

| Level | When | What the reviewer sees |
|---|---|---|
| Default | Every task in an app with the toggle on | The normal form. Each field opens at the proposed value. A changed field shows "Proposed: <value>" and one row of one-tap reason chips. Untouched fields ask nothing. At most 3 reason prompts per task. |
| Override | The reviewer picks an outcome other than `proposedOutcome` | Agreeing stays one click. A different outcome adds "How sure are you?" (Low, Medium, High) and one row of one-tap reason chips. No free text is required. |
| In-depth | `proposalConfidence` is below the developer's threshold, or `highStakes` is `true` | The default and override behavior, plus the in-depth section below, with a visible line saying why it is there. |

The in-depth trigger is set by the developer, never by the reviewer:

- The threshold lives in one constant (`IN_DEPTH_CONFIDENCE_BELOW` in `src/decision/depth.ts`). Use the number the user gave; when they gave none, use 70 and say so in the final report.
- `highStakes` is an input the process sets from the case data (an amount over a limit, a regulated customer, a deny that blocks a payment). Ask the user which condition makes a case high-stakes when the request does not say; when it never applies, still add the field.
- The in-depth section shows one line naming the cause: "More detail is asked here because the proposal is at <proposalConfidence>% (threshold <n>%)" or "More detail is asked here because this is a high-stakes case". When both hold, name both.

The in-depth section:

- The proposed reasons (`evidence`), each with Keep, Edit or Strike. Strike on a reason asks "Why?" with Wrong, Outdated or Other.
- One "Decided it" marker on the single reason that decided the outcome.
- "+ Add a factor" with a weight, for a reason the process did not propose.
- One "What would have changed your decision?" with `counterfactualOptions` as one-tap answers.

## Fields the toggle adds

Proposals can come from an agent, an automation or a person, so the fields say "proposed", never "agent".

| Section | Field | Type | Holds |
|---|---|---|---|
| `inputs` | `proposedOutcome` | string | The outcome the process proposes; equals one outcome name |
| `inputs` | `proposalConfidence` | number | 0 to 100 |
| `inputs` | `highStakes` | boolean | `true` when the developer's high-stakes condition holds for this task |
| `inputs` | `rationaleOptions` | string[] | Reason chips the process proposes for this task, used for the outcome and for changed fields |
| `inputs` | `counterfactualOptions` | string[] | One-tap answers to "What would have changed your decision?", model-written, case-specific, 2 to 4 |
| `inputs` | `instructionOptions` | string[] | Kept for the merged contract. Optional; never rendered as its own step |
| `inOuts` | `evidence` | array | The reasons. Proposed in, reviewer's weights and flags out (item shape below) |
| `outputs` | `rationale` | string[] | The chips the reviewer tapped for the outcome |
| `outputs` | `fieldReasons` | object | Per changed field: `{ "<fieldId>": { "reason": "<chip>", "note": "<optional>" } }`. Only fields the reviewer changed and answered |
| `outputs` | `reviewerConfidence` | string | `Low`, `Medium` or `High`. Present only when the reviewer overrode the outcome and answered |
| `outputs` | `decisiveReasonId` | string | The `evidence` id marked "Decided it". In-depth only |
| `outputs` | `addedFactors` | array | Factors the reviewer added: `{ "title", "weight" }`. In-depth only |
| `outputs` | `counterfactual` | string | The one-tap answer picked. In-depth only |
| `outputs` | `instructionText` | string | Kept for the merged contract. Optional; empty string when unused |
| `outputs` | `instructionScope` | string | Kept for the merged contract. Optional; `this-task`, `similar-tasks` or `all-tasks` |

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

`fieldReasons`, `reviewerConfidence`, `decisiveReasonId`, `addedFactors` and `counterfactual` travel as `Data.<field>`.

Interaction signals (time on task, changes of mind, abandoned overrides) are captured out of the box by Action Center and the coded-action-app SDK. Never build them into the app and never write them into task data.

## Critical Rules

1. Set the toggle from the request's signals (table above), state it in one line when you turned it on unasked, and never block on a question about it.
2. Never rename, retype or redirect the author's own fields or outcomes without the user's yes.
3. Return every `inOuts` value in exactly the shape it arrived in. Never add keys, counters or UI state. Anything added appears in the Decision as a change the reviewer made. The decision fields in the table above are the only additions.
4. Treat every input and `inOuts` value as possibly absent. Render an empty state, and never return a field the task did not receive.
5. Never write computed or telemetry fields (`signals`, `action`, timings) into task data.
6. Reasons, reason chips and counterfactual options are model-written by the process that creates the task, never rule-generated or templated in the app.
7. Never pre-select `proposedOutcome`.
8. Never require free text. Every prompt is answered by a tap, and a skipped prompt stays absent from the data, never filled in by default.
9. Ask for at most 3 reasons per task. Fields changed past the third are recorded without a prompt.
10. Show the in-depth section only when the developer's trigger holds (`proposalConfidence` below the threshold, or `highStakes` is `true`), and always with the line that says why. Never let the reviewer open or close it.
11. Never use "teach", "train" or "lesson" in the UI text, labels or field names you add. Capture reads as normal review work.

## The capture layout

Build it with Apollo Wind components (`@uipath/apollo-wind`). The author's own form renders first and unchanged; each field opens at its proposed value.

| Section | Reviewer sees | Reviewer does |
|---|---|---|
| Decision | One card per outcome; the proposed one carries "Proposed · `proposalConfidence`%". Once picked, a chip says "As proposed" or "Override". | Clicks one card |
| Override | Only after a different outcome is picked: "How sure are you?" (Low, Medium, High) and one row of reason chips from `rationaleOptions` | Taps a confidence and a chip; both can be skipped |
| Changed fields | Under each field whose value differs from the proposal: "Proposed: <value>" and one row of reason chips (first 3 changed fields only) | Taps a chip, or ignores the row |
| Reasons | One row per `evidence` item with title, description, "Supports <outcome>" and a weight menu. Reasons are true unless the reviewer says otherwise. | Picks a weight. Not relevant reveals "Why is it not relevant?" with Wrong, Outdated and Other; Other opens a short note. |
| In-depth | Only when triggered, headed by the line that says why: proposed reasons with Keep, Edit or Strike, a "Decided it" marker, "+ Add a factor" with a weight, and "What would have changed your decision?" | Taps; typing is the fallback for a factor's title only |

Rules:

- Every control whose value differs from the proposal shows "Proposed: <value>" under it.
- With no change, the single button reads "Agree · <proposedOutcome>" and completes in one click.
- With any change, the button reads "Record decision". It is disabled only until an outcome is picked and every Not relevant reason has a why. Confidence, chips and the in-depth answers never block it.
- A changed field never asks twice, and an untouched field never asks.
- After completion, the screen shows the filed state read-only.
- Honour `task.isReadOnly`: render the saved values, never complete.
- Keep the app's types in one file (`src/decision/types.ts`) derived from `action-schema.json`. Never declare the same type twice.

## Steps

1. Decide the toggle from the request (above). Off: stop here and build the app on the normal path.
2. Read the author's existing `action-schema.json`, or design it from the use case on the normal path first.
3. Show the user one table: their fields unchanged, the added decision fields, their outcomes as the decision choices, the in-depth trigger (threshold and high-stakes condition), and any field you recommend moving to `inOuts`. Proceed without waiting; record the table in the final report.
4. Add the fields from "Fields the toggle adds" to `action-schema.json`.
5. Build the capture layout. Write `sample-task-data.json` with realistic values for every field, including 3 to 6 reasons covering more than one outcome, 4 to 6 reason chips and 2 to 4 counterfactual options. Add a second sample with `proposalConfidence` below the threshold to exercise the in-depth section.
6. Build (`npm run build`) and fix type errors. Do not loosen types to silence them.
7. Run the app against `sample-task-data.json` and look at it: the untouched state, a changed-field state, an override state, the in-depth state, and the filed state. Do not report done before this.
8. Follow `uipath-coded-apps` for pack, publish (`-t Action`) and deploy.

## Anti-patterns

- Asking "do you want decision capture?" instead of reading the request.
- Turning it on for pure data entry, where nothing was proposed.
- Free-text boxes as the main input. The reviewer taps; typing is the fallback.
- Making an override ask more than agreeing does: a form, an essay, or a required explanation.
- Showing the in-depth section on every task, or letting the reviewer decide whether to open it.
- Renaming the author's fields to fit the decision fields.
- A single `Submit` outcome with the choice stored in a field.
- Templated reasons or counterfactual options ("Field X is Y") built in the app.
- Counting time on task, hesitation or abandoned overrides in the app.
