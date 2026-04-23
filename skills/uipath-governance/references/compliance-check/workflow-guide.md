# Compliance Check Workflow

End-to-end orchestrator for checking a `.uipolicy` compliance pack against the live tenant state.

## Runtime output rules (read before Step 0)

These rules govern **what the user sees**, not what the tools do internally. Tool calls are plumbing. Your text output between tool calls is the only thing that renders.

1. **No step narration.** Do not emit headings like "Step 0 preflight…", "Now resolving pack…", "All 3 policies are AITL — applicable", "Let me verify…", or any variant. The step headings in this document are for *you*, not the user.
2. **No intermediate echoes.** Do not print manifest.json contents, clause listings, first-clause inspections, per-policy metadata tables, cached CLI responses, or partial drift tables. The final summary renders the result; intermediate state stays in tool output only.
3. **One visible block, at the end.** After the reports are written, emit exactly one terminal summary (format in Step 6). That is the user-visible output for the entire run.
4. **Consolidate shell work.** Preflight + unzip + structural existence checks go in one `Bash` call, not four. Each tool call is a permission prompt; chain them.
5. **Don't re-verify.** Do not run an extra tool call "to double-check" a drift finding after the diff is complete. The walk already produced the result.
6. **No inline script generation.** Do not write a from-scratch Python renderer during the run. Use `jq`/inline loops per the per-step instructions. The HTML template and property reference are the only authored data assets.
7. **Errors are the exception.** If a step fails, surface the exact failure (path, error message) and halt. That is the only other permitted user-visible output.

## References

- [Pack Resolution](pack-resolution.md) — how to resolve the input pack
- [Pack Format](pack-format.md) — `.uipolicy` archive structure
- [CLI Cheat Sheet](cli-cheatsheet.md) — read-only CLI commands
- [Report Format](report-format.md) — JSON compliance report schema
- **AITL Plugin:** [plugins/ai-trust-layer/impl.md](plugins/ai-trust-layer/impl.md)

## Step 0 + Step 1 — Preflight, auth context, unzip, structure check (one shell call)

Combine the login check, auth read, unzip, and archive existence checks into a **single** `Bash` call so the user sees one permission prompt, not four. Example:

```bash
set -eu
# Auth
uip login status --output json | jq -e '.Data.Status == "Logged in"' >/dev/null || { echo "NOT_LOGGED_IN" >&2; exit 1; }
AUTH="$HOME/.uipath/.auth"
UIPATH_TENANT_ID=$(grep '^UIPATH_TENANT_ID=' "$AUTH" | cut -d= -f2-)
UIPATH_TENANT_NAME=$(grep '^UIPATH_TENANT_NAME=' "$AUTH" | cut -d= -f2-)

# Pack — substitute the actual resolution from pack-resolution.md (file / url / id)
TMP=$(mktemp -d)/pack
mkdir -p "$TMP/extracted"
unzip -q "$PACK_SOURCE" -d "$TMP/extracted"

# Structure
test -f "$TMP/extracted/manifest.json"     || { echo "missing manifest.json" >&2; exit 1; }
test -f "$TMP/extracted/clause-map.json"   || { echo "missing clause-map.json" >&2; exit 1; }
test -d "$TMP/extracted/policies"          || { echo "missing policies/ dir" >&2; exit 1; }

# Export for downstream steps
printf 'TMP=%s\nUIPATH_TENANT_ID=%s\nUIPATH_TENANT_NAME=%s\n' "$TMP" "$UIPATH_TENANT_ID" "$UIPATH_TENANT_NAME" > /tmp/pack_tmp.env
```

If `NOT_LOGGED_IN` appears on stderr, halt and ask the user to run `uip login`.

Pack resolution options (`--pack-file <path>`, `--pack-url <url>`, or `--pack-id <id> [--pack-version <v>]`) are documented in [pack-resolution.md](pack-resolution.md). Substitute the appropriate `$PACK_SOURCE` above.

Parse `manifest.json`, `clause-map.json`, and every `policies/*.json` in a **subsequent single** call using `jq` — do not print any of their contents to the user. Validate per [pack-format.md](pack-format.md). Halt on any validation failure with the specific error path.

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

## Step 5 — Fetch effective policies (one CLI call per unique license + product)

Discover every unique `(licenseType, productIdentifier)` pair among the pack's AITL product policy files, call `uip admin aops-policy deployment get-by-user` once per pair, and write the responses to a cache file keyed by `"{licenseType}|{productIdentifier}"`. All of this goes in a single `Bash` call:

```bash
source /tmp/pack_tmp.env
CACHE=/tmp/cli-cache.json
echo '{}' > "$CACHE"

# Collect (license, product) pairs across all AITL product policy files
pairs=$(for f in "$TMP/extracted/policies"/*.json; do
    jq -r 'select(.policyKind == "product" and .policy.productIdentifier == "AITrustLayer")
           | "\(.policy.licenseTypeIdentifier)|\(.policy.productIdentifier)"' "$f"
done | sort -u)

while IFS='|' read -r license product; do
    [ -z "$license" ] && continue
    key="${license}|${product}"
    data=$(uip admin aops-policy deployment get-by-user "$license" "$product" "$UIPATH_TENANT_ID" --output json | jq '.Data')
    tmp=$(jq --arg k "$key" --argjson v "$data" '.[$k] = $v' "$CACHE") && echo "$tmp" > "$CACHE"
done <<< "$pairs"
```

Do **not** print the CLI responses. The cache file is the handoff to Step 6.

## Step 6 — Generate reports + terminal summary (one script call)

Invoke the skill's runner, which walks clauses, applies the aggregate rule, writes the JSON report per [report-format.md](report-format.md), renders the HTML report from [assets/templates/compliance-report-template.html](../../assets/templates/compliance-report-template.html) per [html-report-guide.md](html-report-guide.md), and prints the terminal summary:

```bash
source /tmp/pack_tmp.env
SKILL=/path/to/skills/uipath-governance       # $(dirname "$(dirname "$(realpath references/compliance-check/workflow-guide.md)")")
python3 "$SKILL/assets/scripts/run-compliance-check.py" \
    --pack-dir    "$TMP/extracted" \
    --cli-cache   /tmp/cli-cache.json \
    --tenant-id   "$UIPATH_TENANT_ID" \
    --tenant-name "$UIPATH_TENANT_NAME" \
    --out-dir     .
```

The script exits 0 whether or not drift is found (drift is a finding, not a failure). Non-zero exit means the walk itself failed (malformed pack, cache miss) — surface the stderr verbatim.

The script's stdout **is** the user-visible output for the entire run: terminal summary, then the two report file paths. Do not add extra commentary. Do not re-print findings from the JSON report.

### What the script does (reference only — do not re-implement)

- Parses `manifest.json`, `clause-map.json`, every `policies/*.json` into `policyFileCache`
- Walks clauses; for each contribution resolves the `(license, product)` pair and looks up the cached CLI response in `cliCache` (passed in via `--cli-cache`)
- Skips non-AITL / access contributions (`out-of-version-scope`)
- Per property path: `expected = jsonPath(formData, path)`, `actual = jsonPath(live.data, path)`, `match = deepEqual(expected, actual)`. A missing path (`actual == null`) is drift, not a special state.
- Aggregate rule (first match wins): any mismatch in a `checked` contribution → `drifted`; else any `checked` contribution → `compliant`; else all `skipped` → `skipped`
- AITL value quirks from [plugins/ai-trust-layer/impl.md](plugins/ai-trust-layer/impl.md) (e.g. `pii-entity-table` matched by `identifier`) are built into `deep_equal`
- Writes `compliance-report-{packId}-{timestamp}.json` and `compliance-report-{packId}-{timestamp}.html` into `--out-dir`

### Dispatch table (V1)

| `productIdentifier` | Handled by |
|---|---|
| `AITrustLayer` | `run-compliance-check.py` (diff + report) |
| Any other | Recorded as `out-of-version-scope` skip — no CLI call, no diff |

### Caching invariants

- `cliCache` is **per-run only** — do not persist across invocations (delete `/tmp/cli-cache.json` between runs or place it under a fresh `mktemp`).
- Key is `{licenseType}|{productIdentifier}`. `tenantIdentifier` is not in the key because it's constant per run.
- Twenty clauses pointing at the same `(license, product)` pair must produce **exactly one** `get-by-user` call (Step 5 enforces this by deduplicating pairs before the loop).

## Step 7 — Remediation handoff

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
| Not logged in | 0+1 | Halt. Ask user to `uip login`. |
| Malformed pack | 0+1 | Halt. Surface the path + validation error. |
| No applicable policies | 2 | Invoke Step 6 anyway — the script writes a report with all `skipped`. |
| CLI call fails | 5 | Halt. Surface stderr. |
| Unknown clause ID in scope filter | 3 | Halt. Surface the unknown ID. |
| `run-compliance-check.py` exit ≠ 0 | 6 | Halt. Surface stderr. Do not try to reimplement the walk inline. |
