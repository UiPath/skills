# Partial Apply — When and How to Route Here

Enter this plugin when the user explicitly scoped their request to a subset of the pack's recommended settings.

## Strong signals → route silently to partial apply

- Named a specific product domain: "AI Trust Layer", "Studio", "Robot", "Assistant", "Studio Web", "Integration Service"
- Named a specific ISO clause: "A.6.2.8", "clause 6.1.4", "A.9.2"
- Named a traceable category keyword:

| User phrase | Product(s) | What to look up in catalog |
|---|---|---|
| "traceability" / "audit logging" / "trace retention" | AITrustLayer, Robot | Clauses mentioning trace in controls |
| "guardrails" / "prompt injection" / "sensitive data" / "PII" | AITrustLayer | Clauses with guardrail controls |
| "model governance" / "allowed models" / "LLM providers" | AITrustLayer | Clauses with model toggle controls |
| "publishing controls" / "release notes" / "workflow analyzer" | Development | Clauses with analyzer/publish controls |
| "healing agent" / "self-healing" | Robot | Clauses with healing agent controls |
| "connector" / "integration service" | Integration Service | Clauses with connector controls |
| "high-impact" / "critical controls" | All products | Filter by `impact: "High"` in catalog |

## Identifying clauseIds and products from catalog data

From `catalog.clauses[]`:
- Match user's content words against `clause.clauseName`, `controls[].displayName`, `controls[].description`, `controls[].configLocation`
- The matching `clause.clauseId` → use in `synthesize-formdata.mjs --clause-ids`
- The matching `editorialPolicy.productIdentifier` → use in `synthesize-formdata.mjs --product`

## Controls that require user-supplied values

Some controls have `notEmpty: true` in their required operator — the standard says "this must be configured" but the specific values are org-specific. `synthesize-formdata.mjs` logs a `⚠` warning for these.

Common examples:

| Control | What to ask the user |
|---|---|
| Allowed Models List (AITL-003) | "Which AI model providers should be approved for your org?" |
| BYOM endpoint (AITL-004) | "What is your Azure OpenAI or Bedrock endpoint URL?" |
| Allowed URLs — UIAutomation (RBT-UIA-001) | "Which URLs should UIAutomation be allowed to access? (comma-separated)" |
| Forbidden URLs (RBT-UIA-002) | "Which URLs should UIAutomation be blocked from?" |
| Allowed Applications (RBT-UIA-003) | "Which applications should UIAutomation be allowed to interact with?" |
| Forbidden Applications (RBT-UIA-004) | "Which applications should be blocked?" |

When `synthesize-formdata.mjs` logs `⚠` warnings, check this table and collect values from the user before merging (see impl.md Step 1b).

## Ambiguous signals → ask before proceeding

When the user's phrase matches controls across 3+ product domains, present numbered options:

```
I found settings matching '<phrase>' in:
  1. <product 1> — <N> controls [<control names>]
  2. <product 2> — <N> controls [<control names>]
  3. <product 3> — <N> controls [<control names>]
Which did you mean? (enter numbers like "1,3" or "all")
```

Wait for user response. Do NOT guess and proceed. Do NOT silently configure more than the user asked for.

## Scope expansion note

After identifying target clauses and products, always show:

```
You asked for: <user's phrase>
I matched: <N> recommended settings across <M> product(s)
Note: The full ISO 42001 pack covers <total> recommended settings across <total products>.
Configuring this selection will NOT apply settings for the other products.
```

## Org-scope partial apply

When the user adds an org-level signal ("apply the traceability settings organization-wide"), partial logic uses the `organization` scope for `synthesize-formdata.mjs` synthesis (note: synthesize operates on catalog data which is org-agnostic), but `aops-policy create` targets the tenant logged into. For true org-scope partial apply, recommend applying the full pack at org scope (`state enable organization`) and refining individual tenant policies in the admin console afterward.

## See also

`assets/examples/partial-apply-example.md` — worked example of the full flow.
