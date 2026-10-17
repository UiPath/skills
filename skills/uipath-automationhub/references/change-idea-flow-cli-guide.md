# Change an Automation's Idea Flow — `uip ah` CLI flow

Moves an existing automation into another idea flow and places it in a phase/status of that flow — the CLI equivalent of the **Change Idea Flow** action on the automation profile page. Its most common use: **convert an idea into a Business Process.**

> **Use this flow only after the preflight in [`cli-commands.md`](cli-commands.md) passed.** All commands: append `--output json`. The flow-type values, the `SubmissionType` mapping and what happens to the data are domain facts in [`api-endpoints.md`](api-endpoints.md) → **Idea flow types**.

## When to use

- An automation landed in the **wrong idea flow** — typically a Business Process that was submitted as a CoE-driven or Employee-driven idea (a known publish failure mode; [`publish-process-cli-guide.md`](publish-process-cli-guide.md) Step 7 detects it).
- The user asks to **convert** an idea into a Business Process, or to move an automation into any other flow.

Never delete and re-create the automation to "fix" its flow — that loses its id, documents, comments and history.

## Step 1: Pick the target flow by its TYPE

```bash
uip ah idea-flows list --output json
```

Each entry carries `Id`, `Name`, `Type` and `Phases`. Select the target by **`Type`** (`business-process` for a Business Process) — **never by `Name`, and never by an id you remember**: names are tenant-editable and ids differ per tenant (the Business Process flow is `7` on one tenant and `8` on another).

- Exactly one entry of that type → take its `Id`.
- Several → list their names + ids and ask the user which one.
- None → that flow is not enabled on this tenant; say so and stop.
- No entry carries `Type` → the server predates this capability; see [Not available yet](#not-available-yet).
- The target type is `change-request` → **stop**: an automation cannot be moved into a Change Request flow, because a Change Request needs a parent automation (the CLI also rejects it).

## Step 2: Pick the phase and status from that same entry

The target entry's `Phases` map holds, per phase, its statuses — each with `PhaseVariable`, `StatusVariable` and `StatusValue`. Pass **`--phase <PhaseVariable>` and `--status <StatusVariable>` copied from one status entry** — normally the target flow's first phase and its starting status, unless the user named one.

> ⚠️ **Casing trap:** the CLI output PascalCases the *keys* of the `Phases` map (`DOCUMENTATION` prints as `Documentation`). Never pass a map key — always the `PhaseVariable` / `StatusVariable` values (`DOCUMENTATION`, `NOT_STARTED`).

Never hardcode them and never reuse the source flow's: phases differ between tenants even for the same flow type (one tenant's Business Process flow starts at `IDEA`/`ASSESSMENT`, a newer one at `DOCUMENTATION` / `NOT_STARTED`).

## Step 3: Warn about data, then confirm

Before converting, tell the user what happens to the automation's data, and get a confirm:

- Answers carry over for assessment types **both** flows use (migrated to the target flow's assessment version).
- Assessments the target flow doesn't use are **not shown** there.
- Any **parent-automation link** (from a Change Request) is cleared.

If the user has data that only exists in the source flow's assessments, say so explicitly — they may want to copy it first.

## Step 4: Change the flow

```bash
uip ah automations change-idea-flow <automation-id> --idea-flow <id> --phase <PHASE_VARIABLE> --status <STATUS_VARIABLE> --output json
```

`--idea-flow` also accepts the flow type or name; pass the `Id` from Step 1 so an ambiguous name can't pick the wrong flow.

- `Result: Success` → `Data` carries `AutomationId`, `IdeaFlowId`, `IdeaFlow`, `IdeaFlowType`, `Phase`, `Status`.
- **Exit 3, ambiguous `--idea-flow`** → `Data.Candidates` lists the matching flows; pick by `Type` (ask if still ambiguous) and retry with that flow's id.
- **Exit 3, invalid phase/status** → `Data.ValidPairs` (and `Instructions`) list the target flow's valid pairs; pick one and retry with corrected values.
- **Exit 3, Change Request target** → Step 1's rule; stop.
- **Exit 4, `Retry: RetryWillNotFix` (timeout)** — the call is slow (~20 s or more; the CLI makes a single attempt with a 120 s timeout) and the change may still have landed. **Never re-run it blindly:** run `uip ah automations get <automation-id> --output json` first (Step 5). If the flow already changed, it succeeded.
- **403** → the user lacks the **Change idea flow** permission (by default only account owner, system admin and program manager have it) or permission to submit into the target flow. Do not retry; tell the user an admin must grant it or perform the change.

## Step 5: Verify

```bash
uip ah automations get <automation-id> --output json
```

`Data.SubmissionType` must match the target type (mapping in [`api-endpoints.md`](api-endpoints.md) → **Idea flow types**; `business-process` = `8`) and `Phase` / `PhaseStatus` the values you sent. Report the automation's name, id, new flow and phase/status.

## Not available yet

The capability needs an Automation Hub server with **RPANAV-19226** and a `uip` that ships `automations change-idea-flow`. If the CLI rejects the subcommand as unknown, `idea-flows list` carries no `Type`, or the server answers **404** for the route, tell the user that changing an automation's idea flow isn't available on this tenant/CLI yet (they can use **Change Idea Flow** on the automation profile page in the browser). **Do not** fall back to UI automation or Playwright, and do not re-create the automation instead.
