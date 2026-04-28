# Policy CRUD — shared CLI recipes

Primitive operations on AOPS product policies. All three capabilities (Apply / Diagnose / Advise) call these recipes.

## Commands covered

| Operation | CLI |
|---|---|
| List | `uip gov aops-policy list [--product-name X] [--search Q] [--order-direction asc\|desc] --output json` |
| **Get (metadata + form data)** | `uip gov aops-policy get <policyIdentifier> --output json` — returns `{ name, identifier, description, priority, availability, product, data: {...} }` |
| Get tenant deployment map | `uip gov aops-policy deployment tenant get <tenantIdentifier> --output json` |
| Get template (schema + i18n) | `uip gov aops-policy template get <productIdentifier> --output json` |
| Get template defaults (form-data blueprint) | `uip gov aops-policy template get <productIdentifier> --output-form-data <path> --output json` |
| Get locale-resolved template reference | `uip gov aops-policy template get <productIdentifier> --output-template-locale-resource <path> --output json` |
| List license types | `uip gov aops-policy license-type list --output json` |
| Create | `uip gov aops-policy create ...` (recipe below) |
| Update | `uip gov aops-policy update ...` (recipe below) |
| Delete | `uip gov aops-policy delete <policyIdentifier> --output json` |

> **`policy get` is the single read path.** It combines `policyGetPolicyById` (metadata) with `policyGetFormDataByPolicyId` (values) into one response with the `data` field always populated. Use it for diagnosis, pre-update reads, and advise's current-state fetch.

All responses use `{ Result: "Success" | "Failure", Code, Data, Message }`. Parse accordingly.

### `list` response shape

```jsonc
{
  "Result": "Success",
  "Code": "AopsPolicyList",
  "Data": {
    "totalCount": 12,
    "result": [                           // ← the array lives under Data.result, NOT Data.policies
      { "name": "...", "identifier": "...", "product": { ... }, ... },
      ...
    ]
  }
}
```

Same shape applies to every paginated list command: `deployment tenant list`, `deployment group list`, `deployment user list`, `license-type list`. The array is always `Data.result[]`; pagination metadata is in `Data.totalCount` (and, where applicable, `Data.offset` / `Data.limit`). Never assume `Data.policies` / `Data.tenants` / etc. — those keys don't exist.

---

## CREATE recipe

Used by **Apply** (creating policies from a pack) and **Advise** (when no policy is deployed for a target product).

### Input contract

```jsonc
{
  "policyName":           "<deterministic or user-supplied>",
  "productIdentifier":    "<AITrustLayer | Robot | ...>",
  "description":          "<pass-through>",
  "priority":             1,
  "availability":         365,
  "licenseTypeIdentifier": "NoLicense",
  "formData":             { /* overrides — NOT a complete payload */ }
}
```

### Steps

1. **Fetch template defaults — the base for CREATE is always the product's template defaults.** CREATE never merges onto a deployed policy; that's the UPDATE path. (See [synthesis-algorithm.md #apply-always-creates-new-policies](plugins/compliance/synthesis-algorithm.md#apply-always-creates-new-policies--base-is-always-template-defaults) for why.)

   ```bash
   # Use the standard governance temp root (see check/impl.md Step 2 for the TMP_ROOT pattern).
   tmpDir="$TMP_ROOT/uipath-governance/create-$(date -u +%Y%m%dT%H%M%SZ)"
   mkdir -p "$tmpDir"

   # Use session-cache — templates are stable within a session (30 min TTL).
   # First call per product fetches via `uip`; subsequent calls across
   # Check / Impact / Advise / Apply skip the network round-trip entirely.
   node "$SKILL_DIR/assets/scripts/session-cache.mjs" fetch template-form-data "<productIdentifier>" \
     --out "$tmpDir/base.json" > /dev/null
   ```

   > **⚠ Discard stdout on direct `template get` calls.** If you ever bypass the cache and call `uip gov aops-policy template get --output-form-data <file>` directly, remember that it writes the blueprint to `<file>` AND prints a large JSON envelope to stdout. Redirect to `/dev/null` — a single direct call otherwise dumps 100 KB+ into your conversation context. The cache wrapper already handles this.

2. **Write the pack's overrides to a file** (bare object, not wrapped in `{ "data": ... }`):
   ```bash
   printf '%s' '<overrides-formData-json>' > "$tmpDir/overrides.json"
   ```

3. **Merge overrides onto the base using the deterministic script.** Do NOT hand-write the merge — the script encodes the contract (objects recurse, arrays replace wholesale, `null` in overrides clears).
   ```bash
   node "$SKILL_DIR/assets/scripts/merge-overrides.mjs" \
     --base      "$tmpDir/base.json" \
     --overrides "$tmpDir/overrides.json" \
     --out       "$tmpDir/formData.json" \
     --summary
   dataFile="$tmpDir/formData.json"
   ```
   The `--summary` flag prints the list of overridden paths — surface this (and the `baseLayer` choice) in the deploy/patch record for audit.

4. **Create:**
   ```bash
   uip gov aops-policy create \
     --name "<policyName>" \
     --product-name "<productIdentifier>" \
     --input "$dataFile" \
     --description "<description>" \
     --priority <priority> \
     --availability <availability> \
     --output json
   ```
   Parse `Data.identifier` → `policyId`.

### Error map

| HTTP | Action |
|---|---|
| `400` | Halt. Surface error — usually names the offending leaf. |
| `401 / 403` | Halt. Ask user to `uip login`. |
| `409` | Halt. Duplicate policy name — do NOT fall back to `update` (Apply contract). |
| `404` | Likely a missing / unreadable `--input` path. See [cli-known-issues.md](cli-known-issues.md). |
| `5xx` | Retry once after 3s. Halt on second failure. |

---

## UPDATE recipe

Used by **Diagnose** (applying approved fixes) and **Advise** (when a policy is already deployed for a target product).

### Input contract

```jsonc
{
  "policyIdentifier":    "<existing policy GUID>",
  "policyName":          "<current name>",
  "productIdentifier":   "<current product>",
  "description":         "<current description>",   // REQUIRED — see warning below
  "priority":            1,                          // REQUIRED — see warning below
  "availability":        365,                        // REQUIRED — see warning below
  "changes": [
    { "path": "allowed-llm-regions.europe", "to": true },
    { "path": "azure-openai-control-toggle", "to": true }
  ]
}
```

> **⚠ All metadata flags are required on UPDATE.** The CLI accepts `--description`, `--priority`, `--availability` as "optional" in `--help`, but the API returns **500** if any are omitted (see [cli-known-issues.md #2](cli-known-issues.md)). Always read the current values via `uip gov aops-policy get <id>` and pass them through unchanged unless the caller explicitly wants to update them.

### Steps

1. **Read the full current policy** — metadata + form data in one call:
   ```bash
   uip gov aops-policy get "<policyIdentifier>" --output json
   # Capture: Data.name, Data.product.name, Data.description, Data.priority, Data.availability, Data.data
   ```
   `Data.data` holds the full form-data object. The CLI fetches metadata (`policyGetPolicyById`) and form data (`policyGetFormDataByPolicyId`) in parallel and merges them.

2. **Merge the approved changes onto the live `Data.data`.** Always send the complete object back (UPDATE is full-replace). Use the deterministic merge script — base is the live policy data, overrides are the fields you're changing (e.g., Diagnose fixes, Advise plan, or a pack subset in the `apply-merge-existing` opt-in path).
   ```bash
   tmpDir="$TMP_ROOT/uipath-governance/update-$(date -u +%Y%m%dT%H%M%SZ)"
   mkdir -p "$tmpDir"
   # Extract live data from the GET response captured in Step 1.
   node -e 'const fs=require("fs"); fs.writeFileSync(process.argv[1], JSON.stringify(JSON.parse(fs.readFileSync(process.argv[2],"utf8")).Data.data));' \
     "$tmpDir/base.json" "$tmpDir/get-response.json"

   printf '%s' '<overrides-formData-json>' > "$tmpDir/overrides.json"

   node "$SKILL_DIR/assets/scripts/merge-overrides.mjs" \
     --base      "$tmpDir/base.json" \
     --overrides "$tmpDir/overrides.json" \
     --out       "$tmpDir/formData.json" \
     --summary
   dataFile="$tmpDir/formData.json"
   ```

3. **(formerly a separate step — now rolled into step 2 above.)**

4. **Update — pass ALL metadata flags, not just the ones you're changing:**
   ```bash
   uip gov aops-policy update \
     --identifier "<policyIdentifier>" \
     --name "<policyName>" \
     --product-name "<productIdentifier>" \
     --description "<description>" \
     --priority <priority> \
     --availability <availability> \
     --input "$dataFile" \
     --output json
   ```
   Even if you're only patching `formData`, pass through `--description`, `--priority`, `--availability`, and `--input` from Step 1. `update` is a full-replace — omitting any optional flag clears that field on the server.

### Error map

| HTTP | Action |
|---|---|
| `400` | Halt. Likely schema mismatch. Surface the error. |
| `401 / 403` | Halt. Permission — user may not have update rights. |
| `404` | Target identifier not found. (Missing `--input` paths now produce a clear filesystem error, not 404.) |
| `409` | Concurrent modification — another admin updated the policy. Tell user to retry. |
| `500` | Most often: missing `--description` / `--priority` / `--availability` flag. See [cli-known-issues.md #2](cli-known-issues.md). Re-run with all metadata flags from Step 1. |
| `503` / other 5xx with transient `Instructions` | Inspect the response's `Instructions` field. If it contains `template upgrade`, `connection timeout`, `backend temporarily unavailable`, or similar transient-condition wording, do NOT apply the default "retry in 3s, halt on second failure" policy — template upgrades take tens of seconds to minutes. Either (a) wait **30 seconds** before the first retry and **60 seconds** before a second, OR (b) surface to the user: `AOPS reports a transient condition: "<Instructions text>". I'll retry automatically in 30s, or reply 'retry now' / 'cancel'.` Pick (b) when the user is actively attached to the session; (a) is acceptable for scripted / headless runs. Only halt after a third failure or if the `Instructions` text changes to a non-transient error. Surface `Instructions` verbatim in the final report either way. |
| other `5xx` | Retry once after 3s. Halt on second failure. |

---

## Read-full-policy recipe

Used by **Diagnose** and **Advise** to read the live configuration of any deployed policy:

```bash
uip gov aops-policy get <policyIdentifier> --output json
```

The response includes both metadata and the full `data` (formData) in a single call. `Data.data` is the unwrapped formData object with every field and value — ready for correlation (diagnosis), plan construction (advise), or read-modify-write (update). No separate `form-data get` step is needed.

---

## TENANT-GET recipe

Returns the full deployment landscape for a tenant — every `(product, license)` slot and whether a custom policy is deployed.

```bash
uip gov aops-policy deployment tenant get "$UIPATH_TENANT_ID" --output json
```

Response shape:
```jsonc
{
  "Data": {
    "name": "DefaultTenant",
    "identifier": "<guid>",
    "tenantPolicies": [
      { "productIdentifier": "AITrustLayer", "licenseTypeIdentifier": "NoLicense",
        "policyIdentifier": "<guid>" },                  // custom policy deployed
      { "productIdentifier": "Robot", "licenseTypeIdentifier": "Attended",
        "policyIdentifier": null }                        // using global default
    ]
  }
}
```

**Filter to `policyIdentifier != null`** to get only custom-deployed policies. Used by Diagnose (to know what to inspect) and Advise (to know CREATE vs. UPDATE path).

## Product-specific quirks

Per-product CLI value conventions (like AITL's `"yes"/"no"` strings) live in `plugins/compliance/products/<product>.md`. The CRUD recipe itself is uniform across products.
