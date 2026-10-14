# UI Verification Guide — where a UI check goes, in every build

A UI activity waits for its target up to its timeout and fails with "element not found"; that failure is the check. The rules below decide every other check a genome states, extracted or authored.

## Verification — a property of the activity, not another activity

Every composite pattern ([ui-target-migration-guide.md § Composite interactions](ui-target-migration-guide.md)) owes a verify sub-step. **A verify sub-step is normally not a separate activity.** UI Automation activities carry post-action verification natively (`VerifyOptions` on Click, Hover, Keyboard Shortcuts and Type Into), and that is where a migration's verification belongs. Reaching for a Check Element / Check App State activity instead is the single largest source of activity-count inflation in a migrated project, and each one drags in a target that must be guessed, reviewed and healed like any other. A migrated project whose Check-activity count approaches its Click count, or that has hundreds of Check activities and no `VerifyOptions`, has this defect everywhere, not once.

Decide each check the genome states with one question: **does the outcome change what the automation does next?**

| Outcome | Build |
|---|---|
| No — the step simply has to have worked; not working is a failure: a substep's "confirm…" or stated post-condition | `VerifyOptions` on the activity itself. No extra activity, no extra target for an appearance check that reuses one. A page that must have loaded is the first activity that targets it |
| Yes — the automation genuinely branches, retries or takes another route: an alternative path, a skipped step, a popup that may appear within some time and is dismissed if it does, a record found instead of created | a Check activity, whose branches hold the alternative work |

**A test project's checkpoints are the exception.** Test Manager records a testing verify activity as an assertion of the case's result, with its title, its message and its screenshots, and records nothing of a `VerifyOptions`. So in a test project each source checkpoint is a verify activity of the testing package ([test-execution-guide.md § Result parity](test-execution-guide.md) rule 2), and a post-condition that is no checkpoint stays `VerifyOptions`.

Mapping a source's own verification steps (a source expresses "the value was accepted", "the page arrived", "the field now reads X" as its own check steps; the natural-looking one-Check-per-check translation is almost always wrong — those checks are post-conditions of the step before them):

| Source records | UiPath |
|---|---|
| typed value must be accepted / field must now read X — plain text box | Type Into `VerifyOptions`: **Auto** (target-less — confirms the text landed) or **Expected text** (target-less, wildcards allowed). Neither needs a target, so neither needs a migrated element |
| typed value must be accepted — prompt / type-ahead field, where the accepted entry replaces the typed text with a chip or selected option | Type Into `VerifyOptions` with a **target and mode** (`VerifyExecutionTypeIntoOptions` extends `VerifyExecutionOptions`): mode `Appears`, target = the field's value display scoped to the field ([selector-translation-guide.md](selector-translation-guide.md) rule 16). Target-less Auto fails here because the text is gone |
| a confirmation, banner, next page or row must appear after a click | Click `VerifyOptions`, mode `Appears`, target = the thing that appears |
| a spinner, dialog or row must be gone | mode `Disappears` |
| a field or label must change value | mode `TextChanges` |
| the step is a checkpoint with no follow-up behaviour | still `VerifyOptions` — a failed verify raises, which is the checkpoint |
| an outcome after an activity without `VerifyOptions` (Select Item, Check/Uncheck, a navigation, a process start) | the check the UIA package guide's *Execution Verification Policy* prescribes there, at the source's budget for that check |
| the source branches on the result (retry, alternate path, optional dialog) | a Check activity — this is control flow, not verification |

**The genome's checkpoints and step post-conditions are the request for verification.** The UIA package guide tells an author not to add `VerifyOptions` unless the user asks; in a migration the genome is that ask. A test-suite source asks through the Source Map's Checkpoints row: every checkpoint becomes an assertion of its test case ([test-execution-guide.md § Result parity](test-execution-guide.md) rule 2). A source without that row (an RPA bot) asks through its steps: a post-condition a Workflow substep states on an action (the field must read back the typed value, the page must appear) is verified on that action per the table above, never with a read activity and a comparison beside it. A secure-text field's check is target-less Auto — Expected text would put the secret in plain text. Nothing else gets one.

**A checkpoint followed by a read has no verify slot of its own.** Get Text and Get Attribute carry no `VerifyOptions`; when the source asserts a control is shown and then reads it (`expect(row).toBeVisible()` then `row.innerText()`), the read is the checkpoint: the read activity targets that element with the source's timeout, its success is the "shown" assertion, and its value is compared where the source compared, under the checkpoint id ([test-execution-guide.md § Result parity](test-execution-guide.md) rule 3). No Check activity is spent on it — a Check is still reserved for a genuine branch.

Mechanics that decide whether it behaves: `Retry` defaults to **true** and re-runs the action itself, not only the check, until the activity's own `Timeout`. Set it to false: the check a genome or its source states waits for the outcome without repeating the action, and a second submit, save or type into a field that was not emptied changes data. Keep it true only where the source or the genome repeats the action until the check passes. The verify `Timeout` (default 10s) is how long each check waits — set it to the source's budget for that check: the check's own timeout, else the framework default the source guide names, never left at the activity's default when the two differ. A verify target is *observed, never acted on*, so configure it with a neutral activity type (`None`), **not** `CheckElement` — a `CheckElement` type applies the state-attribute rules meant for Check Element itself. Reuse an existing Object Repository element for the observed thing whenever one exists rather than minting a near-duplicate.

Three consequences a migration gets wrong easily:

- **The verify observes the element that shows the outcome, scoped to where the outcome shows.** After a pick, that is the field's value display under the field's form item — not the option's text leaf, which also lives in the still-open list and makes the check pass before anything was accepted (the shared-text trap, [selector-translation-web-guide.md § Rule 16](selector-translation-web-guide.md)), and not a bare `tag='DIV'`. After a click that changes the page, it is the new page's header or the grid that renders. The verify target is one Object Repository element per widget type (parametrised by field label and value) or per field; it is never re-derived per step.
- **A plain text box's acceptance check is target-less; a prompt's is not.** Type Into Auto/Expected-text verification confirms the value landed in a text box with no element at all. A prompt replaces the typed text, so its check is a targeted `Appears` on the value display (table above).
- **The `IfNotExists`-branch idiom is control flow wearing a verification costume.** A Check whose "not found" branch clicks the suggestion is a legitimate retry path — but the *acceptance* check that follows the click is verification and belongs on the click. Do not let one genuine branch pull every check in the sequence into its own activity.

## Failure handling

Error Handling entries are built where the behaviour differs — the step's workflow-level catch or the process catch, rethrowing with the entry's message and classification — never as a Check activity and a throw before each UI action. A failure is logged once, at Error, where it is handled (the test case's or the process's catch), naming the step: a workflow that catches only to log and rethrow logs it again at every level it passes. The UIA package guide's *Unnecessary Check App State* pitfall states the same rule from the package side.

## Anti-patterns

1. Spending a Check Element / Check App State activity — and a guessed target — on a check the acting activity's own `VerifyOptions` performs, or verifying a pick against the option's text leaf instead of the field's value display (§ Verification).
