# Full Apply — Configure All Recommended Settings

**Preview gate:** Compliance Standards is a preview feature. Append the disclaimer to user-facing output; on any compliance-packs **403**, stop (org not enrolled). See [preview-gate.md](../preview-gate.md).

Turns on the entire compliance standard in one command: in **Enforce** it writes the standard's settings to the tenant's Automation Ops policies and blocks at runtime; in **Observe** it only reports what it would block. Also used to switch an active standard between the two.

`<packId>` / `<packName>` below = the standard being applied — `Data.PackId` / `Data.PackName` from the session `catalog.json`, resolved via [`../catalog/impl.md` § Pack ID lookup](../catalog/impl.md#pack-id-lookup).

**Note:** This configures settings recommended by <packName>. Your organization's auditor determines compliance status — UiPath does not certify compliance.

## Pre-condition

Coverage (posture analysis) has been run and presented ([`../coverage/impl.md`](../coverage/impl.md)).

## Step 1 — Which flow the service follows

```bash
TENANT_ID=$(grep '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
uip gov compliance-packs settings get --output json
```

- `Data.ModeSelectionEnabled == true` — **modes on**: several standards can be active at once, each in Enforce or Observe, and Enforce needs the admin's answer on every conflict. Follow Steps 2–6.
- `Data.ModeSelectionEnabled == false` — **modes off**: one standard at a time, nothing to choose. Skip Step 2 and the conflict steps; confirm with the impact table (Step 5) and enable with `--mode enforce` only.
- `settings` is an unknown command — the `uip` CLI predates modes, and its `state enable` takes no `--mode`. Follow modes off, but call `state enable` WITHOUT `--mode`, and suggest updating `uip`.
- Any other failure — 403 → preview gate; otherwise stop and report it. Do not guess which flow applies.

## Step 2 — Observe or Enforce (modes on)

"apply", "configure", "enforce", "turn on the settings" → **Enforce**. "observe", "monitor", "report only", "try it first", "dry run" → **Observe**. Anything else — ask, then END YOUR REPLY:

```
How should <packName> run on <tenantName>?

1. Enforce — writes its recommended settings to your Automation Ops policies and blocks what it doesn't allow.
2. Observe — reports what it would block. Changes no settings.

Reply with the number.
```

**Observe** needs no conflict answers: go to [Step 5](#step-5--review-gate) with the Observe confirmation, then enable with `--mode audit`.

## Step 3 — Fresh coverage (Enforce, modes on)

Run coverage now, even if the posture was shown a turn ago — the service rejects a `CoverageVersion` once the tenant changes, and the choices must answer the data the admin sees.

```bash
SESSION_TEMP=$(cat "$HOME/.uipath-compliance-current-session")
uip gov compliance-packs state coverage tenant $TENANT_ID <packId> --output json \
  > "$SESSION_TEMP/coverage.json"
```

Keep `Data.CoverageVersion`. Then by `Data.ConflictStatus`:
- `"evaluated"` — `Summary.ConflictCount` is exact. 0 → no questions, go to Step 4's check for other standards, then Step 5.
- `"unavailable"` — run coverage once more. Still unavailable → stop: "Couldn't check for conflicts with your existing policies, so <packName> can't be enforced safely right now. Try again in a few minutes." Never enforce without knowing the conflicts.
- `"not-applicable"` — nothing to resolve.

## Step 4 — Ask about every conflict (Enforce, modes on)

List each conflict once — the same `ConflictId` can appear under several clauses. A conflict whose `Policies[]` has more than one entry differs per license type: ask per entry. Ask, then END YOUR REPLY:

```
Your existing policies disagree with <packName> on <N> settings. For each one, keep your current value or use the standard's:

1. <ControlDisplayName>  (<clauseName>)
   Standard: <PackValueDisplay>  ·  yours: <Current>
2. <ControlDisplayName>  (<clauseName>)
   Standard: <PackValueDisplay>
   a. <PolicyName> · <license display names>: yours <Current>
   b. <PolicyName> · <license display names>: yours <Current>

Reply per number, e.g. "1 keep, 2a standard, 2b keep" — or "standard for all" / "keep all".
```

Render `Current` and names as in [coverage § Conflicts and apply plan](../coverage/impl.md#conflicts-and-apply-plan--before-enforcing). When `OwnerPackIds` names another standard, add "— set by <other standard>; using <packName>'s value makes <other standard> show it as changed."

Rules:
- **Every conflict needs the admin's answer.** A reply that skips some → ask again for only those, and END YOUR REPLY. The service gives the standard's value to any conflict left out, so a missing answer silently overwrites the admin's setting. Never fill a gap yourself.
- **Only two choices exist.** A value of the admin's own (neither theirs nor the standard's) is not possible here — say so, and offer the two.
- "standard for all" / "keep all" are answers — the admin gave them. Never assume one.

**Another standard already enforced.** Run `uip gov compliance-packs state list tenant $TENANT_ID --output json`. If another standard is `Active` with `Mode` `"enforce"` (or `null`), add to the review: "<other standard> is also enforced. Where both set the same setting, the service writes a value both accept — this can change a value you chose to keep for <other standard>, without asking."

## Step 5 — Review gate

**Enforce** — build the impact table from `catalog.clauses[].editorialPolicies[].controls[]`, for settings the posture shows as not yet Applied. Group by impact. List settings needing user-supplied values (flagged by `synthesize-formdata` notEmpty warnings) with a plain-English prompt.

```
Enforce <packName> on <tenantName>?

┌──────────┬─────────────────────────────────────────────────────┐
│ Impact   │ Settings                                            │
├──────────┼─────────────────────────────────────────────────────┤
│ High     │ <comma-separated displayNames of High settings,     │
│ (<N>)    │ truncated to first 3 + "N more">                    │
├──────────┼─────────────────────────────────────────────────────┤
│ Medium   │ <comma-separated displayNames, first 3 + "N more">  │
│ (<N>)    │                                                     │
├──────────┼─────────────────────────────────────────────────────┤
│ Low (<N>)│ <comma-separated displayNames>                      │
└──────────┴─────────────────────────────────────────────────────┘

Your choices on conflicting settings:          (omit when there were none)
  Keep yours:        <ControlDisplayName>, ...
  Use the standard:  <ControlDisplayName>, ...

What changes in Automation Ops:                (from Data.ApplyPlan; omit when absent)
  · <product> · <license>: updates the standard's policy <PolicyName>
  · <product> · <license>: creates <PolicyName>, a copy of your <SourcePolicyName> — yours is not changed

<the other-standard warning from Step 4, when it applies>

⚠ <N> settings need values from you:
  • <controlDisplayName>  — <plain-English prompt for the value>
(omit the ⚠ section if no settings need user-supplied values)

Proceed? (y/n)
```

**Observe:**

```
Turn on <packName> in Observe on <tenantName>?
It reports what it would block and changes no settings. You can switch it to Enforce later.
Proceed? (y/n)
```

Ask, then END YOUR REPLY. Proceed only on an explicit `y` in the user's next message; halt on anything else.

## Step 6 — Apply

**Enforce, modes on** — write the answers to a file (inline JSON breaks on Windows shells), one entry per conflict:
- choice: `"keep"` for keep, `"pack"` for the standard's value.
- One answer for the whole conflict → one entry, no `licenseTypeIdentifier`.
- Per-license answers → one entry per identifier in that `Policies[]` entry's `LicenseTypeIdentifiers`, each with `"licenseTypeIdentifier"`.

```bash
cat > "$SESSION_TEMP/conflict-resolutions.json" <<'JSON'
[
  {"conflictId": "<ConflictId>", "choice": "keep"},
  {"conflictId": "<ConflictId>", "choice": "pack", "licenseTypeIdentifier": "<LicenseTypeIdentifier>"}
]
JSON
COVERAGE_VERSION=$(grep -o '"CoverageVersion": *"[^"]*"' "$SESSION_TEMP/coverage.json" | sed 's/.*"\([^"]*\)"$/\1/')
uip gov compliance-packs state enable tenant $TENANT_ID <packId> --mode enforce \
  --coverage-version "$COVERAGE_VERSION" \
  --conflict-resolutions-file "$SESSION_TEMP/conflict-resolutions.json" --output json
```

```powershell
# Windows PowerShell
$coverageVersion = (Get-Content "$tmpDir\coverage.json" -Raw | ConvertFrom-Json).Data.CoverageVersion
uip gov compliance-packs state enable tenant $tenantId <packId> --mode enforce `
  --coverage-version $coverageVersion `
  --conflict-resolutions-file "$tmpDir\conflict-resolutions.json" --output json
```

No conflicts → leave out `--conflict-resolutions-file`.

**Enforce, modes off** — `uip gov compliance-packs state enable tenant $TENANT_ID <packId> --mode enforce --output json`

**Observe** — `uip gov compliance-packs state enable tenant $TENANT_ID <packId> --mode audit --output json`

## Change the mode of an active standard (modes on)

- **Observe → Enforce** — Steps 3–6 (Enforce). Observe wrote nothing, so the conflicts are the same as for a first enforce.
- **Enforce → Observe** — confirm, then END YOUR REPLY:
  ```
  Switch <packName> to Observe on <tenantName>?
  Its settings come off your Automation Ops policies and your own policies go back. It stops blocking and only reports.
  A policy another enforced standard also uses stays in place.
  Proceed? (y/n)
  ```
  On `y`: `state enable … --mode audit`.

## Verify

```bash
uip gov compliance-packs state get tenant $TENANT_ID <packId> --output json
```

`Data.Active` must be `true`; with modes on, `Data.Mode` must be the mode you sent (`"enforce"` / `"audit"`).

## Report

```
<packName> settings configured on <tenantName> ✓          (Observe: "<packName> is on in Observe on <tenantName> ✓ — reporting only")

SUMMARY
┌───────────────────────────────────┬───────────┐
│ Settings before                   │ <N> / <T> │
│ Settings after                    │ <T> / <T> │
│ High impact settings configured   │ <N>       │
└───────────────────────────────────┴───────────┘

Kept your value: <ControlDisplayName>, ...       (omit when none)

⚠ Manual configuration needed:
┌──────────────────────┬──────────────────────────────────────────────┐
│ Control              │ Where                                        │
├──────────────────────┼──────────────────────────────────────────────┤
│ <controlDisplayName> │ <configLocation from catalog>                │
└──────────────────────┴──────────────────────────────────────────────┘
(omit the ⚠ table if no SKIPped controls)

Applied by: <UIPATH_USER from ~/.uipath/.auth>  ·  <tenantName>  ·  <date>
Note: compliance status is determined by your auditor, not this tool.
```

## Org-scope deployment (all tenants)

When the user says "apply to all tenants", "organization-wide", or "entire org", configure each tenant individually.

> **Note:** `state enable organization` is exposed by the CLI but is not implemented on the backend — calling it has no effect. The correct approach is to iterate over all tenants in the org and call `state enable tenant` for each one.

### Step 1 — Discover all tenants in the org

```bash
uip login tenant list --output json > "$SESSION_TEMP/tenants.json"
```

Parse `Data[].TenantName` and `Data[].TenantId` for the list of tenants. Run `settings get` and settle Observe or Enforce once (Steps 1–2 above) — the answer is per org.

### Step 2 — Run posture analysis per tenant

For each tenant, run coverage to understand current state:

```bash
uip gov compliance-packs state coverage tenant <tenantId> <packId> --output json
```

Aggregate results: note how many tenants have gaps vs are already fully Applied. Enforce with modes on: each tenant has its own policies, so its own conflicts and `CoverageVersion` — ask Step 4's questions per tenant that has conflicts, naming the tenant. Never reuse one tenant's answers for another.

### Step 3 — Confirmation

```
<Enforce | Turn on in Observe> <packName> across all tenants in <UIPATH_ORGANIZATION_NAME>?

Tenants to configure:
  <tenantName1> — <N> settings Not Applied
  <tenantName2> — <N> settings Not Applied
  <tenantName3> — already fully Applied (will skip)

<totalTenantsToConfig> tenants will be configured. Your auditor determines compliance status.
Continue? (y/n)
```

Require `y`. Halt on anything else. Skip tenants where `NewCount == 0` (all settings already Applied).

### Step 4 — Enable per tenant

For each tenant with gaps, call enable individually with the mode, and in Enforce with modes on that tenant's `--coverage-version` and answers file:

```bash
for each tenant with NewCount > 0:
  uip gov compliance-packs state enable tenant <tenantId> <packId> --mode <enforce|audit> [--coverage-version <that tenant's> --conflict-resolutions-file <that tenant's>] --output json
```

### Step 5 — Verify

```bash
for each configured tenant:
  uip gov compliance-packs state get tenant <tenantId> <packId> --output json
```

### Report

```
<packName> settings configured across <N> tenants in <UIPATH_ORGANIZATION_NAME> ✓

┌──────────────────┬──────────────────┐
│ Tenant           │ Status           │
├──────────────────┼──────────────────┤
│ <tenantName1>    │ Applied ✓        │
│ <tenantName2>    │ Applied ✓        │
│ <tenantName3>    │ Already Applied  │
└──────────────────┴──────────────────┘

Applied by: <user>  ·  <date>
Note: compliance status is determined by your auditor, not this tool.
```

## Error handling

`state enable` failures carry the service's own code in `Context.ErrorCode`; branch on it first.

| Error | Action |
|---|---|
| Any compliance-packs call → **403 / Forbidden** | Org not enrolled in the Compliance Standards preview — stop, do not retry, run no further compliance commands. Show the opt-in message. See [preview-gate.md](../preview-gate.md). |
| `Context.ErrorCode: coverage_stale` | The tenant's policies changed after the coverage run; nothing was written. Re-run Step 3, show the conflicts again (say which are new or changed), get the answers again (Step 4), and repeat the review gate. Never resend the old answers without asking. |
| `Context.ErrorCode: coverage_version_required` | Step 3 was skipped. Run it, then Steps 4–6. |
| `Context.ErrorCode: invalid_conflict_resolutions` | An entry names a `ConflictId` or license type not in the current coverage, or repeats one. Rebuild the file from `coverage.json` and the admin's answers. If it fails again, stop and report. |
| `Context.ErrorCode: conflict_resolutions_not_applicable` | This enable writes nothing to Automation Ops, so there is nothing to resolve. Run it again without `--conflict-resolutions-file`. |
| `Context.ErrorCode: another_pack_already_enabled` (`ErrorCode: confirmation_required`) | Modes off: another standard is active and only one is allowed. Name it (from `state list`) and ask: "Replace <other standard> with <packName>? <other standard> will be turned off." END YOUR REPLY. On `y`, run the same enable with `--replace-active`. |
| `ValidationError` naming `--mode` | The CLI needs `--mode`. Add it (Step 2). |
| `state enable` → **409** with `"Retry": "RetryAfter10Seconds"` | Another operation holds the per-pack lock (e.g. a concurrent enable/disable) — transient. Wait ~10 seconds and retry, up to 3 attempts. Halt and report only if it persists. |
| `state enable` → other 4xx | Halt. Report the error in plain English. Do NOT retry. |
| `state enable` → 5xx AND `"Retry": "RetryWillNotFix"` | Halt. Report the error in plain English. Do NOT retry — the server explicitly flagged retrying as futile. |
| `state enable` → 5xx (transient, no `RetryWillNotFix`) | Retry once after a short pause. If it fails again, halt and report. |
| `Data.Active != true` after enable | Unexpected — ask user to run `state get` manually and report the output. |
