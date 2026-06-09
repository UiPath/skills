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
SESSION_TEMP="${SESSION_TEMP:-$(mktemp -d)}"  # Windows PS5+: if (-not $env:SESSION_TEMP) { $env:SESSION_TEMP = Join-Path $env:TEMP ('compliance-' + [guid]::NewGuid().ToString('N').Substring(0,8)) ; New-Item $env:SESSION_TEMP -ItemType Directory | Out-Null }
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
Clause A.6.2.8 — AI system recording of event logs
ISO 42001 recommends:

AI Trust Layer (3 recommended settings, 2 High):
  • Trace Data TTL — ≥30 days recommended [High]
    Admin > AI Trust Layer > Settings > Data Retention
  • Input/Output Logging — Enabled recommended [High]
    Admin > AI Trust Layer > Settings > Audit
  • Restrict Insights Trace — Per sensitivity [Medium]
    Admin > AI Trust Layer > Insights

Robot (2 recommended settings, 2 High):
  • UIAutomation Trace Retention — ≥30 days recommended [High]
  • Trace Masking — Per data type [High]
```

End with: "To check your current posture towards ISO 42001: 'Check my ISO 42001 posture'. To configure recommended settings: 'Apply ISO 42001 settings'."
