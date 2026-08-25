# Query — Control and Clause Lookup

**Preview gate:** Compliance Standards is a preview feature. Append the disclaimer to user-facing output; on any compliance-packs **403**, stop (org not enrolled). See [preview-gate.md](../preview-gate.md).

Pure information — no state commands, no mutations. Uses `catalog get` data only.

## When to use

- "What does clause A.6.2.8 recommend?"
- "Which ISO 42001 controls address prompt injection?"
- "What's the recommended setting for trace retention?"
- "Show me all High-impact controls"
- "What does the AI Trust Layer traceability section require?"

## Command (if not already fetched)

```bash
# Read the session dir written by catalog get; run catalog get if not yet fetched this session.
SESSION_TEMP=$(cat "$HOME/.uipath-compliance-current-session" 2>/dev/null) || {
  SESSION_TEMP=$(mktemp -d)
  echo "$SESSION_TEMP" > "$HOME/.uipath-compliance-current-session"
}
uip gov compliance-packs catalog get iso-42001-2023 --output json > "$SESSION_TEMP/catalog.json"
```

## Filter from catalog

**By clauseId:** match `clauses[].clauseId` exactly ("A.6.2.8", "6.1.4")

**By topic:** match user content words against:
- `clause.clauseName`
- `editorialPolicies[].controls[].displayName`
- `editorialPolicies[].controls[].description`
- `editorialPolicies[].controls[].configLocation`

**By impact:** `controls[].impact == "High"` for "high-impact" / "critical" / "priority"

## Present matched controls

For each matched clause:

```
<clauseName>  (<clauseId>)
<N> settings  ·  <highCount> High  ·  <medCount> Medium  ·  <lowCount> Low

┌──────────────────────────────┬─────────────────────────┬────────┬──────────────────────────────────────┐
│ Setting                      │ Recommendation          │ Impact │ Where to configure                   │
├──────────────────────────────┼─────────────────────────┼────────┼──────────────────────────────────────┤
│ <controlDisplayName>         │ <recommendedSetting>    │ High   │ <configLocation>                     │
│ <controlDisplayName>         │ <recommendedSetting>    │ Medium │ <configLocation>                     │
└──────────────────────────────┴─────────────────────────┴────────┴──────────────────────────────────────┘
[repeat per matched clause]

Current posture on <tenantName>: <appliedControlCount> / <checkableControlCount> settings Applied
→ 'Check my ISO 42001 posture'  to see all gaps
→ 'Apply <clauseName> settings'  to configure these
```

**Data sources:**
- `controls[].displayName` → Control column
- `controls[].recommendedSetting` → Recommendation column
- `controls[].impact` → Impact column
- `controls[].configLocation` → Where to configure column
- Current posture line: read from `SESSION_TEMP/coverage.json` **only if it already exists**. Sum `Data.Clauses[].controls[]` where `status == "deployed"` over the count of all `controls[]` entries (checkable settings). If `controls[]` is absent (older CLI), fall back to counting `Data.Clauses[]` where `Status == "fully-deployed"` over total clauses, and label it "clauses" not "settings". Never run `state coverage` here. If the file does not exist, omit the posture line entirely.

**Terminology:** "settings" for configured items. Plain-English clause name in headline, clause ID as secondary reference in parentheses.

## Auth failure handling

**403 / Forbidden** (not 401) → org not enrolled in the Compliance Standards preview; stop and show the opt-in message. See [preview-gate.md](../preview-gate.md).

If `catalog get` returns an auth error (401 / `RetryWillNotFix`):
1. Report the error to the user.
2. Stop. Do NOT suggest or write example `state` commands (coverage, enable, disable, get) anywhere — not in the response, not in output files, not as comments.
3. The query flow is read-only; if catalog data is unavailable, there is nothing to query.
