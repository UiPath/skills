# Preview: Decision Capture (Guided Decision Experience)

This guidance is in preview. It applies only when the request asks for decision capture or describes a reviewer confirming or correcting a proposal (see the toggle below). A request to build an ordinary Coded Action App, QuickForm or validation task, with no mention of capturing decisions, reviewing a proposal or reasons, is built on the normal path and gets none of the fields, outputs or layout in this guide.

Read this before designing any Coded Action App, QuickForm or document-validation task where a reviewer confirms or corrects something a process proposed. It decides whether the guided decision experience is on (see "Decide the toggle from what the developer wants") and, when it is, what to build.

The experience is an **opt-in toggle on a task the author already needs**. Off: an ordinary form. On, the skill:

1. **Adds a fixed set of decision fields** to the task schema, beside the author's own.
2. **Switches the UI to one light layout** for the surface: the proposal shown as parts the reviewer can re-weight or edit, nothing pre-selected, one optional reason only after a change, and a quiet record of the rest.

The author's own fields keep their names, types and directions. Downstream steps read them as `$vars.<nodeId>.output.<fieldId>`, so renaming one breaks the flow.

Nothing in the app builds the Decision. When the task completes, the backend turns the task data into a Decision and persists it. The toggle only shapes what the task data contains.

Lifecycle commands (scaffold, `uip codedapp pack`, `publish -t Action`, `deploy --folder-key`) come from the `uipath-coded-apps` skill. Read its `references/create-action-app.md` and `references/pack-publish-deploy.md` before running them. Its Critical Rules still apply, especially: never call `sdk.initialize()` in an action app.

## Decide the toggle from what the developer wants

Never open with a yes/no question. Read the request and set the toggle yourself:

| Signal in the request | Toggle |
|---|---|
| Asks to capture or record a decision, or names the Decision Ledger | On |
| An agent, automation or model proposes a value, label, route or verdict that a reviewer confirms or corrects | On |
| The reviewer picks between named resolutions backed by reasons (approve/deny, triage, route, accept/reject) | On |
| The request does not mention capturing decisions, reviewing a proposal or reasons, or the reviewer only enters data nothing proposed, or only acknowledges (sign a form, upload a file) | Off |

When the toggle is on and the user did not ask for it by name, say in one line what you turned on and why, then proceed without waiting. When it is off but a proposal is close to the surface, mention it once in the final report as a one-line option.

## Pick the surface

| Surface | Use when | Layout |
|---|---|---|
| Coded Action App | The reviewer weighs reasons and picks one of a few resolutions | "Coded Action App layout" below |
| QuickForm | The task is a few select fields the developer wants built fast | "QuickForm" below |
| Document validation | The reviewer checks many extracted fields against a document | "Document validation" below |

## Capture principles

All UI text is plain English; never "teach", "train" or "lesson". Capture reads as normal review work.

1. Show the proposal's reasoning as parts the reviewer can change. Never an empty explain-yourself box.
2. Agreeing costs nothing. Correcting costs at most one tap more. A changed part shows "Proposed: <old>".
3. Never pre-select the outcome. Mark the proposal "Recommended". Pre-fill every other part.
4. Ask why only after a change, in one optional step. A skipped why stays absent and never blocks completion. Only the decision is required.
5. Keep the detailed capture quiet. Source, version, how much each part changed, whether the reviewer looked at it, scope, order of changes and time on task are written to the task outputs and never shown to the reviewer.
6. Every correction counts for future cases by default. "Just this claim" (or the use case's equivalent) is a scope choice on Next time, never an extra toggle per change.
7. The reasons are the rationale. There is no separate rationale section, textarea or note box. The reviewer states their own reasoning by adding a reason, and the app generates the rationale text from the deciding reasons and the decision without showing it.

## Coded Action App layout

One column of cards, in this order. Build with Apollo Wind (`@uipath/apollo-wind`).

| Card | Reviewer sees | Reviewer does |
|---|---|---|
| Context | Read-only facts (3 lines) and "Proposed by <name and version> · <involvement>" | Reads |
| Reasons | At most 4 proposed. Each: title, one-line detail, "Supports <outcome>", and a weight menu with bar marks: High, Medium, Low, Not relevant. The menu footer reads "From <source and version> · <confidence>%". Not relevant opens "Why is it not relevant?" with Wrong, Outdated, Other; Other opens one short note. The why is optional. A "+ Add a reason" row at the bottom takes a one-line title and the outcome it supports, and starts at High. | Opens a menu, sets a weight, optionally adds a reason |
| Decision | One card per outcome, none selected, the proposal marked Recommended. Under it, "Final details": the `fields` entries, pre-filled from the proposal and re-filled to follow the chosen decision until the reviewer edits one, then the author's own editable fields at their proposed value. An edited field shows "Proposed: <value>". | Picks a card, edits a field |
| Next time | Shown once something changed. One or two drafted rules built from the changes, each with its basis line. Picking one reveals "Applies to": Just this claim, Claims like this (with 2 or 3 condition chips), Always. | Picks a draft, a scope, conditions |
| What changed | One row per change, each ending with how much it changed (Kept, Lightly edited, Rewritten, Rejected, Added). The decision row also carries its scope. | Reads |
| Complete | One button, "Complete as <decision>". Disabled only until a decision is picked. | Presses it |

Rules:

- Weight is the only per-reason control. There are no per-reason Confirm buttons, verdict controls, confidence pills or evidence accordions. Evidence detail goes in the reason's one-line detail; longer evidence opens in the platform's own task view, never in an iframe.
- Generate `rationaleText` in the app from `reasons` and the decision: reasons weighted High that support the decision (or the top two when none is High), then reasons weighted Not relevant. For a partial outcome every live reason counts. Never show it, and never offer a field to edit it.
- A reason the reviewer adds is a reason like any other: it has a weight menu, can be removed, and counts toward the rationale. It is recorded with `howMuch` = `Added` and `source` = `Reviewer`, and its item carries `added: true`.
- A reason counts as looked at when the reviewer opens its weight menu or clicks its text, even if the weight is kept. "Kept after looking" and "Untouched" stay separate.
- How much a value changed: Kept (looked at, same), Untouched (never looked at, same), Lightly edited (text edit under about 30% of the characters, or a weight moved one step), Rewritten (more than that), Rejected (cleared, set to Not relevant, or the outcome differs from the proposal).
- Honour `task.isReadOnly`: render the saved values and never complete.
- Keep the app's types in one file derived from `action-schema.json`.

## Fields the toggle adds (Coded Action App)

Proposals can come from an agent, an automation or a person, so the fields say "proposed", never "agent".

| Section | Field | Type | Holds |
|---|---|---|---|
| `inputs` | `proposedOutcome` | string | The outcome the process recommends; equals one outcome name |
| `inputs` | `proposedBy` | string | Name and version of the proposer |
| `inputs` | `involvement` | string | `Sign-off`, `Added judgment` or `Peer review` |
| `inputs` | `nextTimeOptions` | array | `{ "id", "text", "basis" }` rules drafted by the process, 1 or 2 |
| `inputs` | `conditionOptions` | array | `{ "id", "label" }` conditions that define "claims like this", 2 or 3 |
| `inOuts` | `reasons` | array | The reasons: proposed in, weights and why out (item shape below) |
| `inOuts` | `fields` | array | Only the final details whose right value depends on the decision: `{ "id", "label", "kind", "byDecision", "value" }`. `byDecision` maps each outcome name to the proposed value; `value` is the reviewer's final value |
| `inOuts` | the author's own fields | as declared | A value the process proposes that does not depend on the decision (a cost center, a priority) stays its own `inOuts` field under its own name, never an entry in `fields` |
| `outputs` | `rationaleText` | string | The rationale generated from the deciding reasons and the decision |
| `outputs` | `decidingReasons` | string[] | Ids of the reasons that carried the decision |
| `outputs` | `nextTimeId`, `nextTimeText` | string | The drafted rule picked; empty when none |
| `outputs` | `nextTimeScope` | string | `this-claim`, `similar-claims` or `all-claims`; name the scopes after the use case |
| `outputs` | `nextTimeConditions` | string[] | The condition labels chosen when the scope is `similar-claims` |
| `outputs` | `changes` | string[] | One line per change, ending with how much it changed |
| `outputs` | `record` | array | One row per part: `{ "part", "proposed", "submitted", "howMuch", "source", "lookedAt", "scope" }` |
| `outputs` | `timeOnTaskSeconds` | number | Open to completion |
| `outputs` | `changeLog` | array | `{ "step", "what", "atSecond", "lookedAt" }` in the order the changes happened; `lookedAt` lists what the reviewer had opened |
| `outputs` | `reviewerId` | string | Only when the host provides one; otherwise absent and the backend records the completing user |

`reasons` item:

| Field | Type | Holds |
|---|---|---|
| `id` | string | Stable id |
| `title` | string | Short, specific claim |
| `detail` | string | The fact behind it, with the concrete value, date or clause |
| `supports` | string | The outcome name it argues for |
| `proposedWeight` | string | `High`, `Medium`, `Low` or `Not relevant`, as proposed |
| `weight` | string | The reviewer's weight; starts equal to `proposedWeight` |
| `source` | string | Name and version of what produced it, shown only in the menu footer |
| `sourceConfidence` | number | 0 to 100, shown only in the menu footer |
| `notRelevantWhy` | string | `Wrong`, `Outdated` or `Other`; only when `weight` is `Not relevant` and answered |
| `notRelevantNote` | string | Free text, only when `notRelevantWhy` is `Other` |
| `added` | boolean | `true` only for a reason the reviewer added; absent otherwise |

**Outcomes are the decision.** The author's outcome buttons stay as they are and the reviewer's click is the decision. Add no `decision` output. If the app has a single `Submit` outcome, ask the user for the real choices (Approve, Deny, ...) and make each one an outcome. Rename an existing outcome only with the user's yes, and update every flow port that reads it.

## QuickForm

QuickForm renders only what a field declares, so the guided experience here uses select controls only: `dropdown`, `radioGroup` and `checkbox`. The proposal is each field's `defaultValue`, set by the process.

Every select field gets one optional reason field through a rule:

| Part | Value |
|---|---|
| Id | `why_<fieldId>` |
| Control | `dropdown`, direction `output`, options Wrong, Outdated, Other |
| Rule | `{ "conditions": [{ "when": "<fieldId>", "isNot": "<defaultValue>" }], "effects": { "visible": true } }` |

The Why field is hidden until the value differs from the proposal, is never required, and sits directly under its field. Write this as a function that takes the developer's schema and returns it with the Why fields added (`withReasonCapture`), so the developer writes only the select fields. Skip input-direction fields.

Rules:

- Outcomes are plain buttons, none pre-selected. The first is not primary.
- Read-only context goes in `input` fields. The runtime form shows only a field's label, control, options and default value, so put the proposer in the label, for example "Category (proposed by <name and version>)".
- QuickForm cannot compare proposed and submitted values itself. The backend compares the values the task was created with against the values it completed with.

## Document validation

For many extracted fields (a taxonomy of dozens, possibly hundreds) next to a document.

| Part | Reviewer sees |
|---|---|
| Document | The document on one side |
| Groups | Fields in collapsed groups, each with its field count (for example Header, Vendor, Buyer, Line items, Tax, Totals, Payment). Line items are a table. |
| Filter | One chip, "<n> need a look", that shows only the fields the process flagged |
| Editing | A value is plain text until clicked, then an inline input. No per-field confidence text, no Confirm. |
| Reason | When a value is edited, one optional chip row under that field only: Extraction misread, Not in the document, Rule doesn't fit, Other (one short note) |
| What changed | Only the edited fields: group, field, from, to, reason |
| Validate | One button |

Schema: `inputs.fields` (array of `{ "id", "group", "label", "value", "needsLook" }`), `outputs.editedFields` (array of `{ "id", "from", "to", "reason" }`, edited fields only). Untouched fields are never written to the outputs.

## What the backend records

When the task completes with `completeTask('<OUTCOME_NAME>', data)`:

| Task data | Decision |
|---|---|
| The outcome clicked | `AcceptedOutcome` |
| Every field in `data` | `Data.<field>`: `inOuts` carry the proposed value in and the final value out; `outputs` carry the final value only |
| `rationaleText`, `decidingReasons` | Rationale in the Decision Ledger |
| `nextTimeId`, `nextTimeText`, `nextTimeScope`, `nextTimeConditions` | Instruction in the Decision Ledger |
| `record`, `changeLog`, `timeOnTaskSeconds` | `Data.<field>`, the quiet record of how the decision was reached |
| The user who completed the task | `Actor` |

Interaction signals Action Center already captures (changes of mind, abandoned overrides) are never rebuilt in the app. The app does record its own `record`, `changeLog` and `timeOnTaskSeconds`, because they describe parts of the form the platform cannot see.

## Critical Rules

1. Set the toggle from the request's signals, state it in one line when you turned it on unasked, and never block on a question about it.
2. Never rename, retype or redirect the author's own fields or outcomes without the user's yes. A proposed value that does not depend on the decision stays its own `inOuts` field under its own name; only decision-dependent details go in `fields`.
3. Return every `inOuts` value in exactly the shape it arrived in, adding only the keys this guide names. Never add counters or UI state beyond `record`, `changeLog` and `timeOnTaskSeconds`.
4. Treat every input and `inOuts` value as possibly absent. Render an empty state, and never return a field the task did not receive.
5. Never pre-select the outcome. Mark the proposal "Recommended" and pre-fill every other part.
6. Require only a decision. Never require free text, a why or an added reason; every optional prompt is answered by a tap and a skipped prompt stays absent from the data.
7. Reasons, drafted rules and conditions are written by the process that creates the task, never templated in the app. The generated `rationaleText` is the one text the app builds, from the reasons and the decision, and it is never shown or edited.
8. Show source, version and confidence only in a reason's weight-menu footer and in the collapsed record. Never put them on the row.
9. Never add per-reason Confirm buttons, confidence pills, verdict controls, evidence accordions, side panels or a chip bank of rationale options.
10. Never use "teach", "train" or "lesson" in UI text, labels or field names you add.
11. Record how much each part changed with the vocabulary above, and keep "looked at" separate from "changed".
12. Name the Next time scopes after the use case, and show the condition chips only for the "like this" scope.
13. A QuickForm Why field is optional, rule-driven and added to every select field by one function, not written by hand per field.
14. Document validation writes only edited fields to the outputs.

## Task kinds

Guidance, not a contract. Use it to pick what to propose on screen and which part of the Decision matters most for the request.

| Task kind | Surface | Automation proposes | Human typically does | The one thing to record |
|---|---|---|---|---|
| Approval gate | Coded Action App | Approve or deny, with reasons | Change | The outcome and why it changed |
| Exception escalation | Coded Action App | A resolution for a case it could not settle | Choose | The chosen resolution and the reason that decided it |
| Write-back validation | Document validation | The values to write to the system of record | Overwrite | Each overwritten value, proposed and final |
| Data enrichment | Document validation | Likely values for the missing fields | Add | Each added value, proposed and final |
| Agentic output review | Coded Action App | A drafted email, root-cause note or summary | Overwrite | The final text beside the draft |
| IT ticket or access triage | QuickForm | Category, priority and queue | Change | Each changed select and its why |
| Financial transaction approval | Coded Action App | The amount to release or the override | Split | The final details beside the proposal |
| Customer communication approval | Coded Action App | A drafted reply | Reject | Why it was rejected: draft, rule or data |

## Steps

1. Decide the toggle from the request. Off: stop here and build the task on the normal path.
2. Pick the surface (table above). Read the author's existing schema, or design it from the use case on the normal path first.
3. Show the user one table: their fields unchanged, the added decision fields, their outcomes as the decision choices, and any field you recommend moving to `inOuts`. Proceed without waiting; record the table in the final report.
4. Add the fields from this guide to the schema.
5. Build the layout. For a Coded Action App write `sample-task-data.json` with realistic values for every field: 3 or 4 reasons covering more than one outcome, each with a source, the final details with `byDecision` values for every outcome, one or two drafted rules and 2 or 3 conditions.
6. Build (`npm run build`) and fix type errors. Do not loosen types to silence them.
7. Run the app against the sample data and look at it: the untouched state with no outcome selected, a changed-weight state with a Not relevant reason, a decision change that re-fills the final details, Add a reason, Next time with a scope, and What changed. Check that `record`, `changeLog` and `timeOnTaskSeconds` are in the data passed to `completeTask`. Do not report done before this.
8. Follow `uipath-coded-apps` for pack, publish (`-t Action`) and deploy.

## Anti-patterns

- Asking "do you want decision capture?" instead of reading the request.
- Turning it on for pure data entry, where nothing was proposed.
- Free-text boxes as the main input.
- A separate Rationale card, rationale textarea or "Add a note" box next to the reasons.
- Making an override ask more than agreeing does.
- Blocking Complete on a why or an added reason.
- Source, version or confidence on every row, Confirm buttons, or an evidence accordion per reason.
- A separate rationale chip bank that restates the reasons.
- Final fields that ignore the chosen decision.
- Renaming the author's fields to fit the decision fields, or a single `Submit` outcome with the choice in a field.
- Pre-selecting the proposed outcome, or a separate "Agree" button that skips the outcome cards.
- A hand-written Why field per QuickForm select, or a required one.
- Writing untouched document fields to the outputs.
- Showing the record to the reviewer. It goes to the outputs; a record drawer is for demos only.
