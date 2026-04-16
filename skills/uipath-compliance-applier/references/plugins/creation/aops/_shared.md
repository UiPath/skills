# Creation · AOps · Shared Recipe

Uniform CLI recipe for creating an AOps product policy. Every `{product}/impl.md` under this folder follows this flow; per-product files only layer product-unique quirks.

## Input (from orchestrator)

```jsonc
{
  "policyKind":         "product",
  "productIdentifier":  "<e.g. AITrustLayer>",
  "policyName":         "<deterministic>",
  "formData":           { /* synthesized */ },
  "priority":           1,
  "availability":       365,
  "description":        "<pass-through from policy file>",
  "licenseTypeIdentifier": "NoLicense"
}
```

## Recipe

1. **Write `formData` to a temp file** (bare object, not wrapped in `{ "data": … }`):
   ```bash
   dataFile="$(mktemp -d)/formData.json"
   printf '%s' '<formData-json>' > "$dataFile"
   ```

2. **Create**:
   ```bash
   uip admin aops-policy create \
     --name "<policyName>" \
     --product-name "<productIdentifier>" \
     --data-file "$dataFile" \
     --description "<description>" \
     --priority <priority> \
     --availability <availability> \
     --output json
   ```
   Parse `Data.identifier` → `policyId`.

3. **Return** to orchestrator:
   ```jsonc
   { "status": "success", "policyId": "<guid>", "warnings": [] }
   ```

**No assignment here.** Creation is Phase 1 only. Deployment is handled by [../../deployment/aops/impl.md](../../deployment/aops/impl.md).

## Error map (common to all products)

| HTTP | Action |
|---|---|
| `400` | Halt run. Surface error message verbatim — it typically names the offending leaf. |
| `401 / 403` | Halt run. Ask user to `uip login`. |
| `409` | Halt run. Duplicate name — V1 rule: do NOT fall back to `update`. |
| `5xx` | Retry once after 3s sleep. Halt on second failure. |

Product-specific quirks and error-message patterns live in each `{product}/impl.md`.
