# Decision Capture Action App

Read this only when the user explicitly asks to capture, record or persist a decision (or to feed the Decision Ledger). For any other human review step, use the QuickForm or Coded Action App paths in [SKILL.md](../SKILL.md) Step 3.

A decision capture action app is a Coded Action App designed so that every completed task persists as a complete **Decision**. The app author writes only `action-schema.json` and the UI. The Decision is built from the completed task, so the schema decides what the Decision contains.

The app is instructional. On one screen the reviewer:

1. **Corrects**: changes what the agent proposed (the outcome, a priority from High to Low, a reason's relevance). Every changed control shows the agent's value.
2. **Explains**: writes why the final values are right (`rationaleText`).
3. **Instructs**: tells the agent what to do next time (`instructionText`), for example "Route claims under $500 with a receipt straight to Approve".

Lifecycle commands (scaffold, `uip codedapp pack`, `publish -t Action`, `deploy --folder-key`) come from the `uipath-coded-apps` skill. Read its `references/create-action-app.md` and `references/pack-publish-deploy.md` before running them. Everything in its Critical Rules still applies, especially: never call `sdk.initialize()` in an action app.

## The Decision model

A completed task becomes one Decision:

| Decision field | What it holds |
|---|---|
| `Data.<field>` | One entry per task field: `proposedValue` (the agent's value), `finalValue` (the reviewer's value), `disposition`, `proposedBy` |
| `AcceptedOutcome` | The outcome button the reviewer clicked |
| `RejectedOutcomes` | The other outcome buttons |
| `Actor` | The user who completed the task |
| `DecisionTimestamp` | When the task was completed |

How `action-schema.json` maps onto it:

| In `action-schema.json` | Becomes |
|---|---|
| `inOuts.<field>` | `Data.<field>` with the value sent in as `proposedValue` and the value returned as `finalValue`. This is the only way to record a correction. |
| `outputs.<field>` | `Data.<field>` with `finalValue` only. The Decision Ledger shows it as set by the reviewer, with nothing proposed. |
| `inputs.<field>` | Context only. Read-only for the reviewer. |
| `outcomes.<name>` | `AcceptedOutcome` when clicked, `RejectedOutcomes` otherwise |
| `outputs.rationaleText` | The Decision Ledger's Rationale |
| `outputs.instructionText` | The Decision Ledger's Instruction |

## Critical Rules

1. Every value the agent proposes and the reviewer may change goes in `inOuts`, under the same name in both directions. Never split a proposal into an input and a differently named output: the Decision then has no `proposedValue` for it.
2. Each resolution the reviewer can choose is its own outcome (`Approve`, `Deny`), so `AcceptedOutcome` is the decision. Never use a single `Submit` outcome with the choice hidden in a field.
3. `outputs` holds only `rationaleText`, `instructionText`, and values the reviewer produces from nothing. Anything the agent could have proposed goes in `inOuts` instead.
4. Return every `inOuts` value in exactly the shape it arrived in. Never add keys, counters or UI state to an item. Anything added appears in the Decision as a change the reviewer made.
5. Never write computed or telemetry fields (`signals`, `action`, timings) into task data. They become `Data` entries nobody decided.
6. Confirm the Decision preview table (Step 1) with the user before writing code.
7. Reasons are model-written English statements, never rule-generated. When the upstream agent produces reasons from raw metadata, a model writes the statement, its relevance and its verdict. Keyword matching, bucketing or templated strings ("Field X is Y") are not acceptable.

## Step 1: Design the Decision first

Ask the user these four questions in one message. Skip any the description already answers.

| Question | The answer becomes |
|---|---|
| What does the agent propose for each task? | `inOuts` fields, plus `agentRecommendedOutcome` and `confidenceScore` |
| What can the reviewer choose? | `outcomes`, one per resolution |
| What do reviewers correct most often? | The fields shown first, with the largest controls |
| What would a reviewer tell the agent after a correction? | The instruction prompt's placeholder text, as one concrete example |

Then write the **Decision preview** before touching code, and wait for a yes:

| Field | In or out | Agent proposes | Reviewer can change it to | Example Decision row |
|---|---|---|---|---|
| `priority` | inOut | `High` | `High`, `Normal`, `Low` | Priority: High → Low |
| `amount` | inOut | `250000` | any number | Amount: 250000 → 200000 (−50000) |
| `evidence` | inOut | 3 to 6 reasons | relevance and verdict per reason | Evidence: 2 of 4 edited |
| outcome | outcomes | `Approve` (recommended, 82%) | `Approve`, `Deny` | Accepted outcome: Deny |
| `rationaleText` | output | prefilled from `rationaleSuggestion` | free text | Rationale: "Receipt is missing" |
| `instructionText` | output | nothing | free text | Instruction: "Deny claims without a receipt" |

Use these definitions:

- **Outcomes**: 2 to 4 mutually exclusive resolutions. The name is what the reviewer clicks (`Approve`, `Deny`, `Approve partial`).
- **Agent recommendation**: `agentRecommendedOutcome` (equals one outcome name) and `confidenceScore` (0 to 100), both inputs. The UI badges the recommended button and never pre-selects it.
- **Evidence**: the reasons behind the proposal. Each item has `id`, `title` (a short, specific claim), `description` (the fact with its concrete value, date or clause), `tags` (0 to 3 short facts), `supports` (an outcome name), `relevance` (`high`, `medium`, `low`, `not-relevant`) and `verdict` (an outcome name). The reviewer can change `relevance` and `verdict`.
- **Rationale**: why the final values are right. The agent supplies `rationaleSuggestion` as an input. It prefills the field only while the field is empty.
- **Instruction**: what the agent should do differently on future tasks of this kind. The agent never prefills it.
- **Use-case fields**: domain values the agent proposes and the reviewer acts on. Keep the list short.

## Step 2: Write action-schema.json

For a new app, scaffold it with `uipath-coded-apps` first. For an existing app, keep its fields and move each agent-proposed value into `inOuts` (Critical Rule 1).

```json
{
  "inputs": {
    "type": "object",
    "properties": {
      "agentRecommendedOutcome": { "type": "string", "required": true, "description": "One of the outcome names" },
      "confidenceScore": { "type": "number", "required": true, "description": "0 to 100" },
      "rationaleSuggestion": { "type": "string", "required": false, "description": "Agent's draft rationale" }
    }
  },
  "inOuts": {
    "type": "object",
    "properties": {
      "priority": { "type": "string", "required": true, "description": "High, Normal or Low" },
      "evidence": {
        "type": "array", "required": true,
        "description": "Agent's reasons in; the reviewer's relevance and verdict per reason out",
        "items": { "type": "object", "properties": {
          "id": { "type": "string", "required": true },
          "title": { "type": "string", "required": true },
          "description": { "type": "string", "required": false },
          "tags": { "type": "array", "required": false, "items": { "type": "string" } },
          "supports": { "type": "string", "required": true, "description": "An outcome name" },
          "relevance": { "type": "string", "required": true, "description": "high, medium, low or not-relevant" },
          "verdict": { "type": "string", "required": true, "description": "An outcome name" }
        } }
      }
    }
  },
  "outputs": {
    "type": "object",
    "properties": {
      "rationaleText": { "type": "string", "required": true },
      "instructionText": { "type": "string", "required": false, "description": "Empty string when the reviewer gave none" }
    }
  },
  "outcomes": {
    "type": "object",
    "properties": {
      "Approve": { "type": "string" },
      "Deny": { "type": "string" }
    }
  }
}
```

`priority` stands in for the use case's own fields. Replace it with the fields from the Step 1 table.

## Step 3: Build the instructional UI

Build the UI in the app with Apollo Wind components (`@uipath/apollo-wind`). Do not add a dependency on a decision widget package, and do not copy a widget's source into the app.

Top to bottom:

| Part | Bound to | Renders as |
|---|---|---|
| Use-case fields | `inOuts` | One editable control per field, starting at the agent's value |
| Reasons | `evidence` | One row per reason: `title`, `description`, `tags`, a `supports` chip, a relevance select and a verdict select, both starting at the agent's values |
| Rationale | `rationaleSuggestion` in, `rationaleText` out | A textarea labeled "Why is this the right decision?", prefilled while empty |
| Instruction | `instructionText` out | A textarea labeled "What should the agent do next time?", empty on load |
| Outcome buttons | `outcomes`, `agentRecommendedOutcome`, `confidenceScore` | One button per outcome. The recommended one carries "Recommended · `confidenceScore`%". |

Capture rules. The backend builds the Decision from task data, so the UI's only job is to make honest corrections cheap:

- Every control opens at the agent's value. Agreeing with the agent takes one click on the recommended outcome.
- Every control whose value differs from the agent's shows "Agent proposed: <value>" under it.
- Fields from the "corrected most often" answer come first.
- The instruction textarea's placeholder is the example from Step 1.
- Outcome buttons are disabled until the rationale is non-empty.
- When the reviewer overrode the agent (clicks an outcome other than `agentRecommendedOutcome`, or changed any `inOuts` value), the instruction is required too. Otherwise it stays optional.
- On click, call `completeTask('<OUTCOME_NAME>', data)` where `data` holds every `inOuts` field in the shape it arrived in (Critical Rule 4), `rationaleText`, and `instructionText` (empty string when none).
- Treat every `inOuts` value as possibly absent: the process that creates the task may not send it. Render an empty state (`evidence ?? []`), and never return a field in `data` that the task did not receive.
- Honour `task.isReadOnly`: render the saved values, never complete.
- Keep the app's types in one file (`src/decision/types.ts`) derived from `action-schema.json`. Never declare the same type twice.

## Step 4: Sample data and verify

1. Write `sample-task-data.json` with a realistic case: the recommendation inputs, every `inOuts` field with the agent's proposed value, and 3 to 6 reasons covering more than one outcome.
2. Build (`npm run build`) and fix type errors. Do not loosen types to silence them.
3. Check `action-schema.json` against the Critical Rules: proposals in `inOuts`, one outcome per resolution, `rationaleText` and `instructionText` in `outputs`, nothing else in `outputs` the agent could have proposed.
4. Check the completion path in code: `completeTask` receives the clicked outcome name, and `data` adds no keys to any `inOuts` value.
5. Follow `uipath-coded-apps` for pack, publish (`-t Action`) and deploy.

## Anti-patterns

- A single `Submit` outcome with the choice stored in a field. The Decision's `AcceptedOutcome` then reads "Submit" on every task.
- An agent value sent as an input and the reviewer's value returned as a differently named output. The Decision shows the output as set from nothing.
- Adding UI keys to evidence items before completing the task. The Decision shows them as reviewer edits.
- Pre-selecting the agent's recommended outcome.
