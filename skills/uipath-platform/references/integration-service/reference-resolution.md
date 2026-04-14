# Reference Resolution

How to resolve reference fields — fields whose values must be looked up from another resource before create/update operations.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

## Contents
- Reference Fields (CRITICAL)
- Search References (filterPattern)
- Field Dependency Chains
- Inferring References Without Describe
- Validate Required Fields Before Executing

---

## Reference Fields (CRITICAL)

Some fields in the describe `requestFields` have a `reference` section — their value must be looked up from another resource before executing.

### Reference structure

```json
{
  "name": "channel",
  "type": "string",
  "displayName": "Channel name/ID",
  "required": true,
  "reference": {
    "objectName": "curated_channels?types=public_channel,private_channel",
    "lookupNames": ["name", "id"],
    "lookupValue": "id",
    "path": "/curated_channels?fields=id,name"
  }
}
```

| Property | Meaning |
|---|---|
| **`reference.objectName`** | The resource to list (use as `<object>` in `execute list`). May include query params. |
| **`reference.lookupNames`** | Fields to match the user's input against (e.g., match "general" against `name`) |
| **`reference.lookupValue`** | The field to extract as the resolved value (e.g., `id`) |
| **`reference.path`** | The API path — use `reference.objectName` for the list call |
| **`reference.filterPattern`** | Search endpoint pattern — substitute the user's input into `{filter}` and pass as `--query`. See [Search References](#search-references-filterpattern). |
| **`reference.childPath`** | Scoped child path — used for drill-down references (e.g., folder subfolders) |

### Resolution workflow

```bash
# 1. Describe → find fields with "reference" in requestFields
uip is resources describe "<connector-key>" "<resource>" \
  --connection-id "<id>" --operation Create --output json

# 2. For each reference field, list the referenced object
#    Use reference.objectName as the object name (including any query params)
uip is resources execute list "<connector-key>" "<reference.objectName>" \
  --connection-id "<id>" --output json

# 3. Match the user's input against reference.lookupNames in the results
#    Extract reference.lookupValue as the resolved ID

# 4. Execute with resolved IDs (not display names)
uip is resources execute create "<connector-key>" "<resource>" \
  --connection-id "<id>" --body '{"channel": "<resolved-id>"}' --output json
```

### Example: Resolving a Slack channel (list reference)

User says: "Send a message to #general"

1. **Describe** returns `channel` field with `reference.objectName: "curated_channels?types=public_channel,private_channel"`
2. **List** the referenced object:
   ```bash
   uip is resources execute list "uipath-salesforce-slack" \
     "curated_channels?types=public_channel,private_channel" \
     --connection-id "<id>" --output json
   ```
3. **Match** "general" against `lookupNames` (`name` field) in results → find `{ "name": "general", "id": "C02CAP3LAAG" }`
4. **Use** the `lookupValue` (`id`) → `"C02CAP3LAAG"` in the `--body`

**Present options to the user** when multiple matches exist. Always use the resolved `lookupValue` (not display names) in `--body` or `--query`.

---

## Search References (filterPattern)

Some reference fields point to **search endpoints** that require user input as a query parameter. These have a `filterPattern` property with a `{filter}` placeholder.

### Search reference structure

```json
{
  "name": "productId",
  "displayName": "Product ID",
  "description": "ID of the product to which the ticket is mapped",
  "required": false,
  "reference": {
    "objectName": "search_products",
    "lookupNames": ["productCode", "id"],
    "lookupValue": "id",
    "path": "/search_products",
    "filterPattern": "productCode={filter}"
  }
}
```

### How to detect

If `reference.filterPattern` exists, the reference is a **search endpoint** — a plain `list` call without the filter will return no results or an error.

### Resolution workflow (search)

1. **Get the user's search input** — the value they want to look up (e.g., product name, code)
2. **Substitute into filterPattern** — replace `{filter}` with the user's input
3. **Pass as `--query`** when listing the referenced object:

```bash
# filterPattern: "productCode={filter}"
# User input: "Widget Pro"
uip is resources execute list "<connector-key>" "search_products" \
  --connection-id "<id>" --query "productCode=Widget Pro" --output json
```

4. **Match results** against `lookupNames` and extract `lookupValue` as usual

### Example: Resolving a Zoho Desk product

User says: "Create a ticket for product Widget Pro"

1. **Describe** returns `productId` with `reference.filterPattern: "productCode={filter}"`
2. **Search** with user input:
   ```bash
   uip is resources execute list "uipath-zoho-desk" "search_products" \
     --connection-id "<id>" --query "productCode=Widget Pro" --output json
   ```
   → `{ "productCode": "WP-100", "id": "1892000000056007" }`
3. **Use** the `lookupValue` (`id`) → `"1892000000056007"` in `--body`

> **If the user doesn't provide a search term**, ask them. Search references cannot be resolved without user input — do NOT call the search endpoint with an empty filter.

---

## Field Dependency Chains

Some reference fields **depend on other fields** — the child field's valid values are scoped by the parent field's selection. Dependencies are expressed in `reference.path` templates containing `{otherField}` variables that must be substituted.

### How to detect dependencies

Check if `reference.path` contains `{fieldName}` template variables. If so, that field depends on the referenced field. Resolve the parent first.

**CRITICAL: If a parent field value is NOT in the user's prompt, you MUST ask the user for it BEFORE attempting to resolve any child fields.** Do not resolve child fields without a scoped parent — the results will be wrong or ambiguous.

### Dependency chain example

A resource has two reference fields with a dependency chain:

```
Field A → no template variables in path    → resolve first (list resource, pick value)
Field B → path contains {Field A}          → resolve after A (list scoped by A's value)
```

**Wrong** — listing Field B's resource globally returns duplicates from all scopes.

**Correct** — resolve Field A first, then list Field B's resource scoped to Field A's resolved value:

```bash
# Step 1: Resolve Field A (no dependencies)
uip is resources execute list "<connector-key>" "<resource-a>" \
  --connection-id "<id>" --output json
# → pick value

# Step 2: Resolve Field B scoped to Field A's value
uip is resources execute list "<connector-key>" "<resource-a>/<resolved-value>/sub-resource" \
  --connection-id "<id>" --output json
# → only values valid for this scope
```

### General rule

When resolving reference fields:
1. **Sort fields by dependency** — fields with no `{template}` in their reference path come first
2. **Resolve parent fields** — list the parent resource, pick the value
3. **Substitute into child path** — replace `{parentField}` in the child's reference path with the resolved value
4. **Resolve child fields** — list the scoped resource using the substituted path

This pattern applies across all connectors wherever child fields are scoped by parent selections.

---

## Inferring References Without Describe

When describe metadata is unavailable (see [resources.md — Describe Failures](resources.md#describe-failures)), infer reference fields from naming conventions:

- Fields ending in **`Id`** (e.g., `PromotionId`, `AccountId`) typically reference the object with the matching base name (`Promotion`, `Account`).
- List the inferred object to resolve the ID: `is resources execute list "<connector-key>" "<base-name>" --connection-id "<id>" --output json`
- Match the user's value by `Name` or `DisplayName` in the results.

---

## Validate Required Fields Before Executing

After resolving references, **check every required field** from the describe response against what the user provided. This is a hard gate — do NOT execute until all required fields have values.

**Process:**
1. Collect all fields where `required: true` from the describe output
2. For each required field, check if the user's prompt contains a value for it
3. If any required field is missing, **ask the user** before proceeding:
   - List the missing fields with their `displayName` and `description`
   - For reference fields, explain what kind of value is expected
   - Wait for the user's response before continuing
4. Only after all required fields are accounted for, proceed to execute

> **Do NOT guess or skip missing required fields.** A missing required field will cause a runtime error. It is always better to ask than to assume.
