# Reference Resolution

How to resolve reference fields — fields whose values must be looked up from another resource before create/update operations.

> Full command syntax and options: [uip-commands.md — Integration Service](../uip-commands.md#integration-service-is). Domain-specific usage patterns are shown inline below.

## Contents
- Reference Fields (CRITICAL)
- Simple Reference Fields (no dependencies)
- Field Dependency Chains
- Inferring References Without Describe
- Validate Required Fields Before Executing

---

## Reference Fields (CRITICAL)

Some fields in the describe response have a `reference` section — their value must be looked up from another resource. For each reference field: list the `referencedObject`, collect the `lookupValue` from results, and present options to the user.

A reference field in the describe output:

```json
{
  "field": "departmentId",
  "referencedObject": "departments",
  "lookupValue": "id",
  "hint": "Resolve by executing: is resources execute list ... \"departments\" ..."
}
```

### Resolution workflow

```bash
# 1. Describe → discover reference fields
uip is resources describe "<connector-key>" "<resource>" \
  --connection-id "<id>" --operation Create --output json

# 2. Resolve each reference field by listing its referenced object
uip is resources execute list "<connector-key>" "<referenced-object>" \
  --connection-id "<id>" --output json

# 3. Execute with resolved IDs
uip is resources execute create "<connector-key>" "<resource>" \
  --connection-id "<id>" --body '{"fieldName": "<resolved-id>"}' --output json
```

**Present options to the user** when multiple matches exist. Use the resolved IDs (not display names) in `--body` or `--query`.

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
