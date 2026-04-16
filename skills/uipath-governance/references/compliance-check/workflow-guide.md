# Compliance Check Workflow

End-to-end orchestrator for checking a `.uipolicy` compliance pack against the live tenant state.

## References

- [Pack Resolution](pack-resolution.md) — how to resolve the input pack
- [Pack Format](pack-format.md) — `.uipolicy` archive structure
- [CLI Cheat Sheet](cli-cheatsheet.md) — read-only CLI commands
- [Report Format](report-format.md) — JSON compliance report schema
- **AITL Plugin:** [plugins/ai-trust-layer/impl.md](plugins/ai-trust-layer/impl.md)

## Step 0 — Preflight

```bash
uip login status --output json
```

Require `Data.Status == "Logged in"`. If not, halt and ask the user to run `uip login`.

Read auth context:

```bash
AUTH_FILE="$HOME/.uipath/.auth"
UIPATH_TENANT_ID=$(grep '^UIPATH_TENANT_ID=' "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_TENANT_NAME=$(grep '^UIPATH_TENANT_NAME=' "$AUTH_FILE" | cut -d'=' -f2-)
UIPATH_URL=$(grep '^UIPATH_URL=' "$AUTH_FILE" | cut -d'=' -f2-)
```

## Step 1 — Resolve the pack

Follow [pack-resolution.md](pack-resolution.md). Accept `--pack-file <path>`, `--pack-url <url>`, or `--pack-id <id> [--pack-version <v>]`.

After unzip, parse:
1. `manifest.json` — pack metadata and policy index
2. `clause-map.json` — clause-to-property mappings
3. Every `policies/*.json` — individual policy files

Validate per [pack-format.md](pack-format.md) validation rules. Halt on any validation failure.

## Step 2 — Partition policies by product

Iterate `manifest.policies[]`. Two buckets:

```
applicable  = [ p for p in manifest.policies
                if p.product == "AITrustLayer" ]
skipped     = [ p for p in manifest.policies
                if p.product != "AITrustLayer" or p.accessPolicyType is not None ]
```

Log the split to the user:

```
Pack: iso-27001-2022 v1.0.0
Applicable (AITL, 1 file): policies/ai-trust-layer.json
Skipped (out of V1 scope, 3 files):
  - policies/development.json (Development)
  - policies/robot.json (Robot)
  - policies/studio-web.json (StudioWeb)
```

If `applicable` is empty, write a report with all policies as `skipped` and exit.

## Step 3 — Determine scope

Default: ALL clauses in `clause-map.json` are in scope. Only narrow if the user's prompt explicitly signals it:

| Signal in prompt | Resulting clause filter |
|---|---|
| (none) | Every clause. Default. |
| "mandatory", "required" | `obligationLevel ∈ {Mandatory, ConditionalMandatory}` |
| Clause ID mentioned ("A.8.11") | Exactly those IDs. Unknown IDs halt. |
| Descriptive phrase ("data masking") | NL match on clause name + description. Confirm matches with user before proceeding. |

Filter clauses to those with at least one contribution to an `applicable` policy file.

## Step 4 — Resolve deployment target

For each applicable policy file, read `deploymentLevel` from the policy:

| `deploymentLevel` | Target |
|---|---|
| `tenant` | Use `UIPATH_TENANT_ID` from `~/.uipath/.auth`. No prompt needed. |
| `group` | If user named a group, use it. Otherwise, list groups via Identity Directory Search (see [cli-cheatsheet.md](cli-cheatsheet.md)) and ask user to select. |
| `user` | If user named a user, use it. Otherwise, list users and ask user to select. |

## Step 5 — Fetch and diff (per applicable policy)

For each applicable policy file, sequentially:

1. Read the policy file from the pack to get `expectedFormData = policyFile.formData`.
2. **Dispatch to the product plugin:**
   - `productIdentifier == "AITrustLayer"` → [plugins/ai-trust-layer/impl.md](plugins/ai-trust-layer/impl.md)
   - Any other `productIdentifier` → skip (should not reach here due to Step 2 partition, but guard defensively)
3. Collect the plugin's return: `{ status, policyId, properties[] }`.

### Dispatch table (V1)

| `productIdentifier` | Plugin |
|---|---|
| `AITrustLayer` | [plugins/ai-trust-layer/impl.md](plugins/ai-trust-layer/impl.md) |
| Any other | **SKIP** (record `out-of-version-scope`) |

## Step 6 — Map results to clauses

For each clause in `clause-map.json` that is in scope:

1. Find all contributions to applicable policy files.
2. For each contribution, look up the property results from the plugin's return.
3. Determine clause status:
   - If the plugin returned `status: "not-deployed"` → clause is `not-deployed`
   - If ALL contributing properties have `match: true` → clause is `compliant`
   - If ANY contributing property has `match: false` → clause is `drifted`
4. For drifted properties, enrich with `classificationType` if available from the policy reference data.

## Step 7 — Terminal summary

Print a human-readable summary:

```
Compliance Check: iso-27001-2022 v1.0.0 → tenant DefaultTenant

  ✓ A.8.11  Data Masking                    compliant
  ✗ A.8.12  Data Leakage Prevention         drifted (2 properties)
  ✗ A.5.3   Segregation of Duties           not-deployed

Result: 1/3 compliant, 1 drifted, 1 not-deployed
Skipped (V1 scope): Development, Robot, StudioWeb
Report: ./compliance-report-iso-27001-2022-20260416T143000Z.json
```

Order: drifted clauses first (by obligation level: Mandatory > ConditionalMandatory > Recommended > Optional), then not-deployed, then compliant.

## Step 8 — Write JSON report

Write to `./compliance-report-{packId}-{timestamp}.json` per [report-format.md](report-format.md).

Include ALL clauses (compliant, drifted, not-deployed) and ALL skipped policies.

Do NOT commit or stage the report file.

## Step 8b — Generate HTML report

Generate a self-contained HTML report for auditor review using the template at `assets/templates/compliance-report-template.html`.

1. Read the HTML template file.
2. Populate it by replacing the `{{PLACEHOLDER}}` tokens with actual data from the compliance check.
3. Generate the clause status table rows and drift detail blocks from the clause results.
4. Write to `./compliance-report-{packId}-{timestamp}.html` alongside the JSON report.

See [html-report-guide.md](html-report-guide.md) for the full placeholder reference and row generation instructions.

The HTML report is a **fixed-format, self-contained file** with no external dependencies. It renders identically regardless of who runs the skill or what tools they have installed. The auditor opens it in any browser.

Do NOT commit or stage the HTML report file.

## Step 9 — Remediation handoff

If any clause has `status: "drifted"` or `status: "not-deployed"`:

```
Some clauses are not compliant. Would you like me to re-apply the
drifted policies using the compliance applier skill?
```

If the user says yes, instruct them to invoke the `uipath-compliance-applier` skill with the same pack. The governance skill does NOT mutate tenant state — it hands off.

If everything is compliant:

```
All checked clauses are compliant. No action needed.
```

## Error handling

| Error | Step | Action |
|---|---|---|
| Not logged in | 0 | Halt. Ask user to `uip login`. |
| Malformed pack | 1 | Halt. Surface the validation error. |
| No applicable policies | 2 | Write report with all skipped. Exit cleanly. |
| Plugin returns error | 5 | Halt. Surface the error. Write partial report. |
| Unknown clause ID in scope filter | 3 | Halt. Surface the unknown ID. |
