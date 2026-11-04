# Preview: Decisions and Reasons Widget (Decision Capture in a Coded Web App)

This guidance is in preview. It applies only when the request asks for a standalone Coded Web App (not an Action Center task) in which a reviewer confirms or corrects a proposal and the decision is captured. A request for an ordinary Coded Web App, with no mention of capturing decisions, reviewing a proposal or reasons, is built on the normal path in this skill and gets none of this guide. A reviewer working inside an Action Center task is a Coded Action App and is out of scope here.

The widget enforces the capture principles: the proposal is split into parts the reviewer weighs, nothing is pre-selected, the proposed outcome is marked Recommended, overriding a part costs one tap, the reviewer can add a part the proposal missed, and free-text is never the main input. For a Coded Web App:

1. There is no task schema and no backend that turns task data into a Decision. The app builds the Decision itself.
2. The app calls the generic `decisions.create` from `@uipath/uipath-typescript` on submit.
3. There are no implicit signals. The app does not attach `@uipath/intrinsic-signals`, does not mark elements with `data-signal-*`, and never sends `implicitSignals`.

Lifecycle commands (scaffold, OAuth client, build, `uip codedapp pack`, `publish`, `deploy`) follow [create-web-app.md](../create-web-app.md) and [pack-publish-deploy.md](../pack-publish-deploy.md). The SKILL.md Critical Rules still apply.

## Layers

| Layer | Lives in | The one contract it owns |
|---|---|---|
| Skill | This guide | The app follows the principles and maps the widget result to one decision request |
| Widgets | `@uipath/ui-widgets-decisions-and-reasons` (`/preview` entry) | The review components and their `ReviewPayload` |
| SDK | `@uipath/uipath-typescript` (`/traces`) | `Decisions.create(traceId, decisions, folderKey)` |
| Read | Decision Ledger, `Decisions.query`, `uip traces decisions` | Decisions filtered by `platform` = `CodedApp` |

## Steps

1. Decide that the path applies: the request names a standalone web app and a reviewer who decides. If the reviewer works inside Action Center, build a Coded Action App instead ([create-action-app.md](../create-action-app.md)).
2. Scaffold the app with [create-web-app.md](../create-web-app.md). Add `Traces.Api` to the OAuth scopes in Step 4 of that flow; `Decisions.create` needs it. See [oauth-scopes.md](../oauth-scopes.md).
3. Install the widget package from the public registry: `npm install @uipath/ui-widgets-decisions-and-reasons --@uipath:registry=https://registry.npmjs.org`. Import the stylesheet once: `@uipath/ui-widgets-decisions-and-reasons/DecisionsAndReasons.css`.
4. Pick the widget format from "Pick the widget format" and import it from `@uipath/ui-widgets-decisions-and-reasons/preview`. Confirm the export name in the installed package's `dist/preview.d.ts`; use only names it exports.
5. Build the page: the widget fed by the app's own proposal data, `onComplete` calling `submitDecision` (below). Reuse the SDK instance from `useAuth()`, never a second `UiPath`.
6. Build (`npm run build`) and fix type errors without loosening types. Run the app against sample proposal data and look at it: nothing pre-selected, a changed weight, a decision that re-fills final details, and the submitted request (log it once in the browser console while checking, then remove the log). Do not report done before this.
7. Pack, publish and deploy with [pack-publish-deploy.md](../pack-publish-deploy.md).

## Pick the widget format

Choose by the reviewer's job. Each format renders the guided layout and returns the same `ReviewPayload`.

| Format | Reviewer's job |
|---|---|
| `CaseAssessment` | Weighs reasons for and against a case and picks a resolution |
| `SourceComparison` | Compares what the sources say against the proposed value |
| `ExtractionValidation` | Checks extracted fields against a document |
| `TriageRouting` | Chooses a label or route for an incoming item |
| `DraftEditing` | Edits an agent-drafted text before it goes out |
| `FactWeighing` | Weighs each fact on a Fraud, Not relevant or Legitimate scale against the agent's read, picks an outcome, picks reason chips and writes a rationale |

Use the widget's own controls. Never rebuild them by hand, and never replace them with free-text boxes.

## Map the widget result to a decision request

Each Decision carries the reviewer's outcome and, per part, what was proposed against what was kept.

| Decision field | Source |
|---|---|
| `decisionId` | App-generated: 16 lowercase hex characters (see "Identifiers"). A GUID is rejected. |
| `data` | One entry per reason or fact and per final-details field (table below), keyed by its `id` |
| `actor` | `{ identity: <signed-in reviewer>, kind: 'Human' }`. Use `payload.reviewerId` when the host provides one, otherwise the signed-in user's identity. |
| `acceptedOutcome` | The outcome the reviewer clicked, which is `onComplete`'s first argument |
| `rejectedOutcomes` | The labels of the other outcomes the widget offered |
| `decisionTimestamp` | `new Date().toISOString()` at submit |
| `explicitEvidences` | The titles of the reasons in `payload.decidingReasons`, then `payload.rationaleText` |
| `processInstanceMetadata` | Optional. `processName` set to the app's name |
| `platform` | `'CodedApp'` |

`data` entries:

| Part | `proposedValue` | `finalValue` | `proposedBy` |
|---|---|---|---|
| A reason or fact | `proposedWeight` (or the proposed verdict for a fact) | `weight` (or the reviewer's verdict) | `{ identity: <reason.source or payload proposer>, kind: 'Agent' }`; for a reason with `added: true`: `{ identity: <reviewer>, kind: 'Person' }` |
| A final-details field | `byDecision[<proposed outcome>]` | `value` | the proposer's identity, kind `'Agent'` or `'Automation'` as the use case says |

`disposition` comes from the matching `record` row's `howMuch`:

| `howMuch` | `disposition` |
|---|---|
| Kept | `Accepted` |
| Lightly edited | `LightlyEdited` |
| Rewritten | `Rewritten` |
| Rejected | `Rejected` |
| Untouched | `Ignored` |
| Added | `Accepted` |

Write this as one pure function in one file, for example `src/decisions/buildDecision.ts`, that takes the widget payload, the outcome, the offered outcomes, the proposer and the reviewer and returns a `DecisionCreateInput`. Import `DecisionCreateInput` from `@uipath/uipath-typescript/traces`; never declare the request shape by hand.

## Identifiers

| Value | Format | How the app gets it |
|---|---|---|
| `decisionId` | 16 lowercase hex characters | Generated per submit: 8 bytes from `crypto.getRandomValues`, each as two hex digits |
| `traceId` | 32 lowercase hex characters | Generated once per review session the same way with 16 bytes, so a resubmit of the same review reuses it and updates the same decision |
| `folderKey` | Orchestrator folder GUID | Read from the app's configuration (a Vite env value the developer sets); never hardcoded and never invented |

`decisions.create` validates all three and throws `ValidationError` on a malformed value.

## Submit

```typescript
import { Decisions } from '@uipath/uipath-typescript/traces';

const decisions = new Decisions(sdk);

const submitDecision = async (outcome: string, payload: ReviewPayload) => {
  const decision = buildDecision(payload, outcome, offeredOutcomes, proposer, reviewer);
  const [ack] = await decisions.create(traceId, [decision], folderKey);
  return ack.feedbackId;
};
```

Resolve the widget's `onComplete` promise only after `create` resolves, so the widget does not show a completed state for a decision that failed. On failure show one plain sentence in the page, keep the reviewer's choices, and allow resubmit.

## Read it back

Decisions from this path appear in the Decision Ledger filtered to Platform = CodedApp. To check from code: `decisions.query({ platform: 'CodedApp', traceId })`.

## Critical Rules

1. Apply this guide only to a standalone Coded Web App. A reviewer inside Action Center uses a Coded Action App.
2. Every capture principle above holds: parts the reviewer weighs, nothing pre-selected, the proposal marked Recommended, an optional why, and no free-text boxes as the main input.
3. Build the request with `DecisionCreateInput` from `@uipath/uipath-typescript/traces` and send it with `decisions.create`. Never call the Decisions endpoint with `fetch`.
4. `platform` is `'CodedApp'`.
5. `decisionId` is 16 lowercase hex characters generated by the app. Never a GUID.
6. Never send `implicitSignals`, never import `@uipath/intrinsic-signals`, and never add `data-signal-*` attributes in this path.
7. Never hardcode `folderKey` or a tenant, folder or user identifier. Read the folder from configuration.
8. Add `Traces.Api` to the OAuth scopes in `uipath.json` and on the External Application.
9. The reviewer's outcome is `acceptedOutcome`; the other offered outcomes are `rejectedOutcomes`. Never add a separate `decision` data entry.
10. Never write raw cursor paths, keystrokes or typed text into any `data` entry.
11. Use a format name only if the installed package exports it.

## Anti-patterns

- Building a task schema or `action-schema.json` for a standalone web app.
- Hand-rolling the weight menus, reason chips or outcome cards instead of the widget.
- Declaring a local `Decision` type that duplicates the SDK's.
- A GUID or a timestamp-based string as `decisionId`.
- Marking elements for intrinsic signals or sending `implicitSignals`.
- Completing the widget before `decisions.create` resolves.
- Asking the developer "do you want decision capture?" instead of reading the request.
