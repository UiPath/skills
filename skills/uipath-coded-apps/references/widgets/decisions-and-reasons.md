# Preview: Decision Capture with the Decisions and Reasons Widget

Build a coded app in which a reviewer confirms or corrects a proposal, and every part of that review lands in one Decision. The widget renders the review and returns a `ReviewPayload`; this guide covers picking the widget, feeding it, and writing the payload into a Decision without losing anything.

Lifecycle commands (scaffold, OAuth client, build, `uip codedapp pack`, `publish`, `deploy`) follow [create-web-app.md](../create-web-app.md), [create-action-app.md](../create-action-app.md) and [pack-publish-deploy.md](../pack-publish-deploy.md). The SKILL.md Critical Rules still apply.

## Packages

| Package | Entry | Owns |
|---|---|---|
| `@uipath/ui-widgets-decisions-and-reasons` `^1.0.1-beta.0` | `/preview`, plus `/DecisionsAndReasons.css` | Review formats, primitives, `useDecisionCapture`, `ReviewPayload` |
| `@uipath/uipath-typescript` `^1.8.4` | `/traces` | `Decisions` service and `DecisionCreateInput`. 1.8.4 is the first version with `Decisions` |

Install both from the public registry:

```bash
npm install @uipath/ui-widgets-decisions-and-reasons@^1.0.1-beta.0 @uipath/uipath-typescript@^1.8.4 --@uipath:registry=https://registry.npmjs.org
```

Import the stylesheet once in the app entry: `import '@uipath/ui-widgets-decisions-and-reasons/DecisionsAndReasons.css';`. Before using any export name below, confirm it in `node_modules/@uipath/ui-widgets-decisions-and-reasons/dist/preview.d.ts`.

## Steps

1. Scaffold the app. Add `Traces.Api` to the OAuth scopes when the app writes the Decision itself (see "Write the Decision"); every `Decisions` method needs it. See [oauth-scopes.md](../oauth-scopes.md).
2. Install the packages and import the stylesheet (above).
3. Pick the format by the reviewer's job ("Pick the format").
4. Map the app's proposal data to the format's props ("Feed the widget"). Write `sample-proposal.json` with realistic data: 3 or 4 reasons from more than one source, at least one reason against the recommended outcome, and final details with a value for every outcome.
5. Write the payload into a Decision ("Write the Decision"), in one pure function in `src/decisions/buildDecision.ts`.
6. Build (`npm run build`) and fix type errors without loosening types.
7. Run the app against the sample data and check, in the browser: no outcome selected on load, the recommended outcome marked, a changed weight, an outcome change that re-fills the final details, an added reason, and the built Decision (log it once in the console while checking, then remove the log). Every reason and every final-details field must appear in `data`. Do not report done before this.
8. Pack, publish and deploy.

## Pick the format

Every format returns the same `ReviewPayload`.

| Export | Reviewer's job |
|---|---|
| `CaseAssessment` | Weighs the reasons in a case and picks its outcome (claims, refunds, exceptions). Supports task tags, default reasons and Next time |
| `SourceComparison` | Compares extracted values against a system of record, field by field, with verdicts and citations |
| `ExtractionValidation` | Confirms or corrects values extracted from a document, with confidence and line items |
| `TriageRouting` | Confirms or changes the category, priority and team that were proposed |
| `DraftEditing` | Accepts, edits or rewrites proposed text |
| `FactWeighing` | Weighs each fact on a five-point scale from fraud to legitimate, beside the proposer's read |

No format fits: compose one from the primitives (`ReviewShell`, `OutcomePicker`, `ReasonsSection`, `ProposalInput`, `NextTimeSection`, `ChangesSummary`) around `useDecisionCapture`, wrapped in `CaptureProvider`. The hook builds the same payload. Never rebuild weight menus, reason chips or outcome cards by hand, and never replace them with free-text boxes.

## Feed the widget

Props shared by every format (`ReviewProps`):

| Prop | Set it to |
|---|---|
| `title`, `subtitle`, `facts`, `excerpt` | The case the reviewer is looking at, from the app's data |
| `proposedBy` | The proposer's display name (an agent, an automation or a team). It also becomes `proposedBy.identity` in the Decision |
| `outcomes` | Every outcome the reviewer can choose: `{ id, label, description }`. Mark the proposed one `recommended: true`. Add `requiresReason` with `reasons` where a reason must go with that choice, and `requiresCoverage` where every field needs a verdict first |
| `reasonOptions` | The reason chip vocabulary, in the process's own words |
| `show` | Optional pieces: `confidence`, `citation`, `qcLane`, `nextTime`, `comparison`, `record` |
| `reviewerId` | The signed-in reviewer's identity (email or user name). It becomes `actor.identity` |
| `saved` | A previously saved draft, so a reopened review resumes where it stopped |
| `onChange(payload)` | Save the draft (optional) |
| `onComplete(outcome, payload)` | Write the Decision. Return the promise, so the widget shows completed only after the write resolves |

The format's own props type (`CaseAssessmentProps`, `SourceComparisonProps`, ...) names the items it reviews: `reasons`, `fields` or `labels`. Each reason carries its `source` and, when known, `confidence`. Each final-details field carries `byOutcome`, the proposed value for each outcome, so the field re-fills when the reviewer changes the outcome.

Never pre-select an outcome. The proposal is marked Recommended and the reviewer picks.

## Write the Decision

Where the Decision is written depends on where the app runs.

| App | Who writes the Decision | The app does |
|---|---|---|
| Coded Action App (Action Center task) | Action Center, when the task completes | `onComplete` calls `completeTask(outcome, payload)`. Declare `reasons` and `fields` as `inOuts` and the other payload keys as `outputs` in `action-schema.json`, because Action Center drops undeclared keys. Never call `decisions.create` |
| Coded Web App | The app | `onComplete` builds a `DecisionCreateInput` from the payload and calls `decisions.create` |

The rest of this section is for a Coded Web App.

### Decision

| Field | Value |
|---|---|
| `decisionId` | 16 lowercase hex characters, new per submit (see "Identifiers") |
| `data` | One entry per reason, per final-details field and per fact (tables below) |
| `actor` | `{ identity: payload.reviewerId, kind: 'Human' }` |
| `acceptedOutcome` | `onComplete`'s first argument, the outcome id the reviewer clicked |
| `rejectedOutcomes` | The ids of every other outcome passed in `outcomes` |
| `decisionTimestamp` | `new Date().toISOString()` at submit |
| `explicitEvidences` | The titles of the reasons whose ids are in `payload.decidingReasons`, then each of `payload.taskTags`, then `payload.rationaleText` when not empty |
| `processInstanceMetadata` | `{ processName: <app or process name> }`, plus `processKey` and `instanceId` when the app knows them |
| `platform` | `'CodedApp'` |

### `data`: one entry per reason

Key: `reason.<reason.id>`. `payload.reasons` includes the reasons the reviewer added and the whys they picked (`added: true`); each gets its own entry.

| Field | Value |
|---|---|
| `proposedValue` | `reason.proposedWeight`; `null` when `reason.added` |
| `finalValue` | `reason.weight` |
| `disposition` | `added`: `Accepted`. `weight === proposedWeight`: `Accepted`. `weight === 'Not relevant'`: `Rejected`. Otherwise `Rewritten` |
| `proposedBy` | `added`: `{ identity: payload.reviewerId, kind: 'Person' }`. Otherwise `{ identity: reason.source ?? proposedBy, kind: 'Agent' }`, or `'Automation'` when an automation proposed it |

### `data`: one entry per final-details field

Key: `field.id`.

| Field | Value |
|---|---|
| `proposedValue` | `field.byDecision[acceptedOutcome]`, falling back to the recommended outcome's entry |
| `finalValue` | `field.value` |
| `disposition` | `Accepted` when `finalValue` equals `proposedValue`, otherwise `Rewritten` |
| `proposedBy` | `{ identity: proposedBy, kind: 'Agent' }`, or `'Automation'` as the use case says |

### `data`: one entry per fact (`FactWeighing`)

`FactWeighing` returns a `FactWeighingPayload`: the `ReviewPayload` plus `facts` and `rationale`. Key each fact `fact.<fact.id>`.

| Field | Value |
|---|---|
| `proposedValue` | `fact.agentRead` |
| `finalValue` | `fact.weight` |
| `disposition` | `Accepted` when `fact.setBy === 'model'` or `weight` equals `agentRead`, otherwise `Rewritten` |
| `proposedBy` | `{ identity: proposedBy, kind: 'Agent' }` |

Append `rationale.text` to `explicitEvidences` when not empty.

### `data`: Next time

When `payload.nextTimeId` is not empty, add key `nextTime`: `proposedValue` `null`, `finalValue` `{ text: payload.nextTimeText, scope: payload.nextTimeScope, conditions: payload.nextTimeConditions }`, `disposition` `Accepted`, `proposedBy` `{ identity: proposedBy, kind: 'Agent' }`.

These dispositions match how the Decisions backend classifies Action Center tasks (a changed value is `Rewritten`, an unchanged one `Accepted`), so `decisions.query({ hasOverrides: true })` finds overrides from both kinds of app.

Import `DecisionCreateInput` and `DecisionFieldData` from `@uipath/uipath-typescript/traces`. Never declare the request shape by hand.

### Identifiers

| Value | Format | How the app gets it |
|---|---|---|
| `decisionId` | 16 lowercase hex characters | 8 bytes from `crypto.getRandomValues`, each as two hex digits, per submit |
| `traceId` | 32 lowercase hex characters | 16 bytes the same way, once per review, so a resubmit of the same review reuses it |
| `folderKey` | Orchestrator folder GUID | The `<meta name="uipath:folder-key">` tag the platform injects at deploy, so a deploy into another folder writes there. A Vite env value only for local runs where the tag is missing |

`decisions.create` validates all three and throws `ValidationError` on a malformed value.

### Submit

```typescript
import { Decisions } from '@uipath/uipath-typescript/traces';
import type { ReviewPayload } from '@uipath/ui-widgets-decisions-and-reasons/preview';

const decisions = new Decisions(sdk);
const folderKey =
  document.querySelector('meta[name="uipath:folder-key"]')?.getAttribute('content') ??
  import.meta.env.VITE_UIPATH_FOLDER_KEY;

const submitDecision = async (outcome: string, payload: ReviewPayload) => {
  const decision = buildDecision({ payload, outcome, outcomes, proposedBy, processName });
  const [ack] = await decisions.create(traceId, [decision], folderKey);
  return ack.feedbackId;
};
```

Pass `submitDecision` as `onComplete`. Reuse the SDK instance from `useAuth()`, never a second `UiPath`. On failure show one plain sentence in the page, keep the reviewer's choices, and allow resubmit with the same `traceId`.

### Read it back

`decisions.query({ platform: 'CodedApp', traceId })` returns the written Decision. In the Decision Ledger, filter Platform to CodedApp.

## Critical Rules

1. Use a format from the widget package, or compose one from its primitives and `useDecisionCapture`. Never hand-build weight menus, reason chips or outcome cards, and never make a free-text box the main input.
2. Never pre-select an outcome. Mark the proposed outcome `recommended: true`.
3. Every outcome the reviewer can choose is in `outcomes`. The clicked one is `acceptedOutcome`, the others are `rejectedOutcomes`. Never add a `decision` entry to `data`.
4. Every reason in `payload.reasons`, including added ones, every field in `payload.fields` and, for `FactWeighing`, every fact in `payload.facts` gets its own `data` entry with `proposedValue`, `finalValue`, `disposition` and `proposedBy`.
5. A part the reviewer added has `proposedBy.kind` `'Person'` and the reviewer's identity. Everything else names its real proposer.
6. In a Coded Web App, build the request with `DecisionCreateInput` from `@uipath/uipath-typescript/traces` and send it with `decisions.create`. Never call the Decisions endpoint with `fetch`.
7. In a Coded Action App, complete the task with the payload and let Action Center write the Decision. Never also call `decisions.create`, which writes a second Decision.
8. `platform` is `'CodedApp'` for a Coded Web App.
9. `decisionId` is 16 lowercase hex characters generated by the app, never a GUID.
10. Read `folderKey` from the `uipath:folder-key` meta tag. Never hardcode a folder, tenant or user identifier, and never bake the folder into the build.
11. Resolve `onComplete` only after the write resolves.
12. Leave `implicitSignals` unset. Never write raw cursor paths, keystrokes or typed text into any `data` entry.
13. Use an export name only if the installed `dist/preview.d.ts` exports it.

## Anti-patterns

- Writing only the outcome and dropping the reasons or final details from `data`.
- Mapping every part to `Accepted` regardless of what the reviewer changed.
- One `data` entry holding the whole payload as a blob.
- Declaring a local `Decision` type that duplicates the SDK's.
- A GUID or a timestamp-based string as `decisionId`.
- Completing the widget before `decisions.create` resolves.
- Asking the developer "do you want decision capture?" instead of reading the request.
