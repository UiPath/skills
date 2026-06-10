# Query — Control and Clause Lookup

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
<N> controls  ·  <highCount> High  ·  <medCount> Medium  ·  <lowCount> Low

┌──────────────────────────────┬─────────────────────────┬────────┬──────────────────────────────────────┐
│ Control                      │ Recommendation          │ Impact │ Where to configure                   │
├──────────────────────────────┼─────────────────────────┼────────┼──────────────────────────────────────┤
│ <controlDisplayName>         │ <recommendedSetting>    │ High   │ <configLocation>                     │
│ <controlDisplayName>         │ <recommendedSetting>    │ Medium │ <configLocation>                     │
└──────────────────────────────┴─────────────────────────┴────────┴──────────────────────────────────────┘
[repeat per matched clause]

Current posture on <tenantName>: <inPlaceCount> / <totalCount> controls configured
→ 'Check my ISO 42001 posture'  to see all gaps
→ 'Apply <clauseName> controls'  to configure these
```

**Data sources:**
- `controls[].displayName` → Control column
- `controls[].recommendedSetting` → Recommendation column
- `controls[].impact` → Impact column
- `controls[].configLocation` → Where to configure column
- Current posture line: from `state coverage` if SESSION_TEMP/coverage.json exists, otherwise omit the line

**Terminology:** "controls" NOT "settings". Plain-English clause name in headline, clause ID as secondary reference in parentheses.
