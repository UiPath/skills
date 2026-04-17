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

Drift checks always resolve the **effective policy for the currently authenticated user** via `get-by-user`. The full USER → GROUP → TENANT → GLOBAL inheritance chain is applied server-side, so the orchestrator does not select a principal.

| Context | Target |
|---|---|
| Tenant context | `UIPATH_TENANT_ID` from `~/.uipath/.auth`. No prompt. |
| Group / user context | Not applicable in check mode — `get-by-user` resolves to whichever layer (incl. GROUP / USER) overrides for the authenticated session. |

The pack's `deploymentLevel` is still captured for the report (it describes *where* the pack expected the policy to land), but it does not drive the CLI call.

## Step 5 — Walk clauses and diff against effective policy

Iterate `clause-map.json` clause-first. Expected values come from the policy file referenced by each contribution; live values come from `get-by-user`. Two in-memory caches live for the duration of a single run:

```
policyFileCache  : map<relativePath, parsedPolicyJson>       # parse each policy file once
cliCache         : map<"{licenseType}|{productIdentifier}", CliResult>   # one CLI call per unique (license, product)
```

For each in-scope clause (from Step 3), sequentially:

```
clauseResult = {
    clauseId, name, category, obligationLevel,
    status: unknown,
    contributions: []
}

for contribution in clause.contributions:
    policyFile = policyFileCache.load(contribution.uipolicyFile)

    # V1 scope — only AITL product policies are diffed
    if policyFile.policyKind != "product"
       or policyFile.policy.productIdentifier != "AITrustLayer":
        clauseResult.contributions.append({
            product: policyFile.policy?.productIdentifier or policyFile.accessPolicy?.accessPolicyType,
            status: "skipped",
            reason: "out-of-version-scope",
            properties: []
        })
        continue

    product = policyFile.policy.productIdentifier
    license = policyFile.policy.licenseTypeIdentifier
    expectedFormData = policyFile.formData
    key = "{license}|{product}"

    # Cache hit? Reuse. Otherwise call the CLI once.
    # The CLI always returns an effective deployed policy for a valid (license, product, tenant) —
    # there is no "not deployed" branch at the fetch level.
    if key not in cliCache:
        cliCache[key] = invoke plugin [plugins/ai-trust-layer/impl.md](plugins/ai-trust-layer/impl.md)
                        with (license, product, UIPATH_TENANT_ID)
        # → returns CliResult { policyName, deployment, data }

    live = cliCache[key]

    properties = []
    for propertyPath in contribution.properties:
        expected = jsonPath(expectedFormData, propertyPath)
        actual   = jsonPath(live.data,        propertyPath)
        properties.append({
            path: propertyPath,
            expected, actual,
            match: deepEqual(expected, actual)
        })
    # A missing path (actual == null) counts as a mismatch — it's drift, not a
    # special "not-applied" case. The tenant is non-compliant either way.

    clauseResult.contributions.append({
        product,
        status: "checked",
        effectivePolicyName: live.policyName,
        effectiveDeployment: live.deployment,
        properties
    })

clauseResult.status = aggregate(clauseResult.contributions)
```

### Value comparison rules (AITL)

Consult the quirks table in [plugins/ai-trust-layer/impl.md](plugins/ai-trust-layer/impl.md) before equality-checking. In particular: `allow-llm-model-auto-routing` is a `"yes"`/`"no"` string (not boolean), `traces-ttl`/`traces-ttl-effective` are duration strings, `pii-*` values are enums, and arrays like `pii-entity-table` are order-independent and matched by `identifier`.

For drifted (`match: false`) properties, enrich with `classificationType` if it's available in the policy reference data.

### `aggregate(contributions)` — first match wins

1. Any `checked` contribution has a property with `match == false` → **`drifted`**
2. At least one `checked` contribution (rule 1 didn't fire) → **`compliant`**
3. All contributions `skipped` → **`skipped`** (clause excluded from compliant / drifted counts)

`skipped` contributions never drive the clause status — they're recorded for audit but ignored in the decision. A missing property path is treated as drift under rule 1.

### Dispatch table (V1)

| `productIdentifier` | Plugin |
|---|---|
| `AITrustLayer` | [plugins/ai-trust-layer/impl.md](plugins/ai-trust-layer/impl.md) |
| Any other | **SKIP** per contribution (record `out-of-version-scope`) |

### Caching invariants

- `cliCache` is **per-run only** — do not persist across invocations.
- Key is `{licenseType}|{productIdentifier}`. `tenantIdentifier` is not in the key because it's constant per run (from `~/.uipath/.auth`).
- Twenty clauses pointing at the same `(license, product)` pair must produce **exactly one** `get-by-user` call.

## Step 6 — Terminal summary

Print a human-readable summary:

```
Compliance Check: iso-27001-2022 v1.0.0 → tenant DefaultTenant

  ✓ A.8.11  Data Masking                    compliant
  ✗ A.8.12  Data Leakage Prevention         drifted (2 properties)
  ✗ A.5.3   Segregation of Duties           drifted (3 properties)

Result: 1/3 compliant, 2 drifted
Skipped (V1 scope): Development, Robot, StudioWeb
Report: ./compliance-report-iso-27001-2022-20260416T143000Z.json
```

Order: drifted clauses first (by obligation level: Mandatory > ConditionalMandatory > Recommended > Optional), then compliant.

## Step 7 — Write JSON report

Write to `./compliance-report-{packId}-{timestamp}.json` per [report-format.md](report-format.md).

Include ALL clauses (compliant, drifted) and ALL skipped policies.

Do NOT commit or stage the report file.

## Step 7b — Generate HTML report

Generate a self-contained HTML report for auditor review using the template at `assets/templates/compliance-report-template.html`.

1. Read the HTML template file.
2. Populate it by replacing the `{{PLACEHOLDER}}` tokens with actual data from the compliance check.
3. Generate the clause status table rows and drift detail blocks from the clause results.
4. Write to `./compliance-report-{packId}-{timestamp}.html` alongside the JSON report.

See [html-report-guide.md](html-report-guide.md) for the full placeholder reference and row generation instructions.

The HTML report is a **fixed-format, self-contained file** with no external dependencies. It renders identically regardless of who runs the skill or what tools they have installed. The auditor opens it in any browser.

Do NOT commit or stage the HTML report file.

## Step 8 — Remediation handoff

If any clause has `status: "drifted"`:

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
| CLI call fails | 5 | Halt. Surface the error. Write partial report. |
| Unknown clause ID in scope filter | 3 | Halt. Surface the unknown ID. |
