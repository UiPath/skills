# Change an Automation's Idea Flow — `uip ah` CLI flow

Moves an existing automation into another idea flow and places it in a phase/status of that flow — the CLI equivalent of the **Change Idea Flow** action on the automation profile page. Its most common use: **convert an idea into a Business Process.**

> **Use this flow only after the preflight in [`cli-commands.md`](cli-commands.md) passed.** All commands: append `--output json`. The flow-type values, the `SubmissionType` mapping and what happens to the data are domain facts in [`api-endpoints.md`](api-endpoints.md) → **Idea flow types** and the PATCH section.

## When to use

- An automation landed in the **wrong idea flow** — typically a Business Process that was submitted as a CoE-driven or Employee-driven idea (a known publish failure mode; [`publish-process-cli-guide.md`](publish-process-cli-guide.md) Step 7 detects it).
- The user asks to **convert** an idea into a Business Process, or to move an automation into any other flow.

This command **only changes flows.** Moving an automation to another phase/status of the flow it is already in (e.g. "move this to Assessment") is `uip ah phases set`, which this skill doesn't cover yet — tell the user so; never use `change-idea-flow` as a phase setter.

Never delete and re-create the automation to "fix" its flow — that loses its id, documents, comments and history.

## Step 1: Pick the target flow by its TYPE

```bash
uip ah automations change-idea-flow --help    # unknown command → the installed uip is too old; see Not available yet
uip ah idea-flows list --limit 1000 --output json
```

Check the CLI first: an older `uip` drops `Type` from `idea-flows list` even when the server sends it, so a missing `Type` says nothing about the server until you know the CLI has `change-idea-flow`. Pass `--limit` — the list defaults to 20 entries, and `--output-filter` requires it.

Each entry carries `Id`, `Name`, `Type` and `Phases`. Select the target by **`Type`** (`business-process` for a Business Process) — **never by `Name`, and never by an id you remember**: names are tenant-editable and ids differ per tenant (the Business Process flow is `7` on one tenant and `8` on another).

- Exactly one entry of that type → take its `Id`.
- Several → **normal**, not an edge case: every flow an admin creates from a default (duplicate, copy, upload) keeps that default's type. List their names + ids and ask the user which one.
- None → that flow is not enabled on this tenant; say so and stop.
- No entry carries `Type` (with a CLI that has `change-idea-flow`) → the server predates this capability; see [Not available yet](#not-available-yet).
- The target type is `change-request` → **stop**: an automation cannot be moved into a Change Request flow, because a Change Request needs a parent automation (the CLI also rejects it).

## Step 2: Check the automation isn't already there

```bash
uip ah automations get <automation-id> --output json
```

(Named by the user? Resolve the id with `uip ah automations list --search <name> --output json` first.) Nothing stops a move into the flow the automation is already in — the server re-saves it, sets the status directly and, if the status changes, notifies followers — so check first:

- `Data.SubmissionType` already equals the target type's number ([`api-endpoints.md`](api-endpoints.md) → **Idea flow types**) and only one flow has that type → tell the user it is already in that flow and **stop**. If they wanted another phase, that is `uip ah phases set` (see above).
- It matches but several flows share the type → `SubmissionType` can't tell them apart; ask the user whether they mean a different flow of that type before going on.

## Step 3: Pick the phase and status from the target entry

The target entry's `Phases` map holds, per phase, its statuses — each with `PhaseVariable`, `StatusVariable` and `StatusValue`. Pass **`--phase <PhaseVariable>` and `--status <StatusVariable>` copied from one status entry** — normally the target flow's first phase and its starting status, unless the user named one.

> ⚠️ **Casing trap:** the CLI output PascalCases the *keys* of the `Phases` map (`DOCUMENTATION` prints as `Documentation`). Never pass a map key — always the `PhaseVariable` / `StatusVariable` values (`DOCUMENTATION`, `NOT_STARTED`).

Never hardcode them and never reuse the source flow's: phases differ between tenants even for the same flow type (one tenant's Business Process flow starts at `IDEA`/`ASSESSMENT`, a newer one at `DOCUMENTATION` / `NOT_STARTED`).

## Step 4: Warn about what changes, then confirm

Before converting, tell the user what the move does, and get a confirm:

- **Answers** carry over for assessment types **both** flows use. They migrate to the target flow's assessment version only when the saved version is the source flow's default; a manually changed version is left as it is.
- Assessments the target flow doesn't use are **hidden, not deleted** — the answers stay on the record.
- Any **parent-automation link** (from a Change Request) is cleared.
- It counts as a **phase change** whenever the phase/status changes (it almost always does): followers and upvoters get the usual emails/notifications, and user tasks are created.
- The change shows in the automation's **history** (as changed overview answers — flow, phase and status).
- Collaborators and their roles are **not** changed.

If the user has data that only exists in the source flow's assessments, say so explicitly — they may want to copy it first.

## Step 5: Change the flow

```bash
uip ah automations change-idea-flow <automation-id> --idea-flow-id <Id> --phase <PHASE_VARIABLE> --status <STATUS_VARIABLE> --output json
```

Pass the ids from Steps 1–2 so nothing ambiguous can pick the wrong record. (`<automation>` also takes the exact name, and `--idea-flow <type|name>` is the alternative to `--idea-flow-id` — the two can't be combined.)

**Only exit 3 is fixed by retrying with corrected values.** Anything else: don't retry — re-read in Step 6 and report.

- `Result: Success` → `Data` carries `AutomationId`, `AutomationName` (when named), `IdeaFlowId`, `IdeaFlow`, `IdeaFlowType`, `Phase`, `Status`. Go to Step 6 — a success envelope alone is not proof (see there).
- **Exit 3, `Data.Candidates`** → a name matched several records. The candidates are **automations** when the `<automation>` name was ambiguous, **flows** (with `Type`) when `--idea-flow` was. Ask the user which one and retry with its id.
- **Exit 3, `Data.ValidPairs`** → the phase/status isn't in the target flow; pick a pair from that list (or `Instructions`) and retry.
- **Exit 3, Change Request target** → Step 1's rule; stop.
- **Exit 1, `ErrorCode: not_supported`** → the server can't change flows yet; see [Not available yet](#not-available-yet).
- **Exit 4, `Retry: RetryWillNotFix` (timeout)** — the call is slow (~20 s or more; the CLI makes a single attempt with a 120 s timeout) and the change may still have landed. **Never re-run it blindly:** read back with Step 6. Changed → it succeeded. Unchanged or half moved → report what `get` shows to the user; don't retry.
- **Any other exit 1** — `Message` carries the server's text and status:
  - `(403 Forbidden)` is more than a missing permission: the **Change idea flow** action may not be enabled at the automation's **current** phase/status (configurable per status) or the user's role lacks it (by default only account owner, system admin and program manager have it), the user may lack the right to submit into the target flow, or may have no tenant roles. `Message` says which; relay it. An admin, or the profile page's **Change Idea Flow** action, is the way forward.
  - `404` → unknown automation; `400` naming the automation's current status → that status no longer exists in its flow, which only the UI can fix; `500` → server error.
  - In every case: the server commits the new flow id **before** the full re-save, so a failure can leave the automation **half moved** (in the new flow, but with phase and type not updated). Run Step 6 and report what it shows alongside the error.

## Step 6: Verify

```bash
uip ah automations get <automation-id> --output json
```

`Data.SubmissionType` must match the target type (mapping in [`api-endpoints.md`](api-endpoints.md) → **Idea flow types**; `business-process` = `8`), `Data.PhaseKey` must equal the `--phase` you sent, and `Data.PhaseStatusKey` must equal `<PHASE>_<STATUS>` (e.g. `DOCUMENTATION_NOT_STARTED`). Don't compare `Phase` / `PhaseStatus`: those are display names. For a `custom` target, skip the `SubmissionType` check (see the mapping) and rely on the phase keys. `SubmissionType` confirms the type, not which flow of that type.

The server can answer **200 even when the save failed**, so this read-back is the only reliable check. If anything doesn't match, **don't re-run the command**: report what `get` shows and point the user to **Change Idea Flow** on the automation's profile page. Otherwise report the automation's name, id, new flow and phase/status.

## Not available yet

The capability needs an Automation Hub server with **RPANAV-19226** and a `uip` that ships `automations change-idea-flow` with `--idea-flow-id`. If the CLI rejects the subcommand or `--idea-flow-id` as unknown, tell the user to update `uip` — and **don't** conclude anything about the server from that CLI's `idea-flows list` (an older `uip` hides `Type`). Only with an up-to-date CLI: if `idea-flows list` carries no `Type`, or the command fails with `ErrorCode: not_supported`, tell the user that changing an automation's idea flow isn't available on this tenant yet (they can use **Change Idea Flow** on the automation profile page in the browser). **Do not** fall back to UI automation or Playwright, and do not re-create the automation instead.
