# Configure Policy Form Data — Form.io Parsing Guide

How to fetch a product's form template, walk the component tree, collect policy settings from the user using natural language, and produce a ready-to-submit policy data JSON.

## Prerequisites

- User must be logged in — see [aops-policy-commands.md — Authentication](./aops-policy-commands.md#authentication).
- `$PRODUCT_NAME` is known (resolved by [aops-policy-manage-guide.md — Step 1](./aops-policy-manage-guide.md#step-1--bootstrap-and-verify-product) for create, or from `policy get` for update).
- `$SESSION_DIR` is set. For the create flow, Step 1 below creates it; for the update flow, the caller ([aops-policy-manage-guide.md — Update Step 1](./aops-policy-manage-guide.md#step-1--identify-the-policy-and-create-the-session-directory)) creates it before invoking this guide.
- For every CLI subcommand mentioned below, see [aops-policy-commands.md](./aops-policy-commands.md).

---

## Overview

AOps policy settings are a JSON object defined by a **form.io schema** (`FormTemplateDto.template`), shipped with flat default values. This guide covers the interactive, field-by-field configuration workflow — using natural-language prompts, the locale file for labels, and the form-data file for defaults.

---

## Step 1 — Bootstrap: Load All Products and Their Templates (create flow only)

> **Applies only to the create flow.** The update flow already knows the product from the existing policy — skip directly to Step 2 and fetch only that product's template.

Create a session directory to isolate files for this configuration run:

```bash
SESSION_DIR="./aops-sessions/$(date +%Y%m%d-%H%M%S)-$(uuidgen | cut -c1-8 | tr '[:upper:]' '[:lower:]')"
mkdir -p "$SESSION_DIR"
```

This produces a path like `./aops-sessions/20260416-143022-a1b2c3d4`.

### 1.1 — Fetch every product's template, form data, and locale in one call

```bash
mkdir -p "$SESSION_DIR/products"
uip gov aops-policy template list --output-dir "$SESSION_DIR/products" --output json
```

For the full flag reference, see [aops-policy-commands.md — template list](./aops-policy-commands.md#uip-gov-aops-policy-template-list). The command writes three files per product into `$SESSION_DIR/products/<PRODUCT_NAME>/`:

- `form-template.json` — raw form.io DTO returned by the governance API. Its top-level `.product` object carries `{name, label}` and is the authoritative product catalog entry.
- `form-data.json` — fillable blueprint with defaults for every field. Display-only components (`hidden`, `button`, `submit`, `htmlelement`, `content`) are omitted. Fields without an explicit default get a type-appropriate default: `false` for checkbox, `[]` for editgrid, `{}` for selectboxes, and `null` for text/select.
- `form-template-locale-resource.json` — locale-resolved reference. Every product-scoped locale key is replaced with its English string; a sibling `<prop>-key` preserves the original key for traceability. `defaultData.data` is a flat per-field map `{value, type, label, description?, tooltip?}`, and select/selectboxes option labels live under `template.components[...].values[].label`.

Per-product fetch failures are collected by the CLI and do not abort the run; the command only exits non-zero if every product fails.

> **Product catalog is implicit.** There is no `products.json` — each `form-template.json`'s top-level `product` object IS the catalog entry. The caller enumerates products via the `Glob` tool on `$SESSION_DIR/products/*/form-template.json` and reads `.product.{name, label}` from each file.

After Step 1, the session directory looks like:

```text
$SESSION_DIR/
└── products/
    ├── <PRODUCT_NAME_1>/
    │   ├── form-template.json   # .product.{name,label,...} is the catalog entry
    │   ├── form-data.json
    │   └── form-template-locale-resource.json
    ├── <PRODUCT_NAME_2>/
    │   └── ...
```

Once `$PRODUCT_NAME` is confirmed by the caller, proceed to Step 2 using `$SESSION_DIR/products/$PRODUCT_NAME/` as the working directory.

---

## Step 2 — Load Form Template, Form Data, and Locale

For the **create flow**, the bootstrap (Step 1) already produced all three files under `$SESSION_DIR/products/$PRODUCT_NAME/`. No new CLI call is needed — read the files directly.

For the **update flow**, the product is known from the existing policy. `$SESSION_DIR` is already set by the caller (see [aops-policy-manage-guide.md — Update Step 1](./aops-policy-manage-guide.md#step-1--identify-the-policy-and-create-the-session-directory)) — do NOT create a new session directory here, or `$SESSION_DIR/existing-policy-data.json` will end up in a different folder. Only create the per-product subfolder and fetch that product's template. For flags, see [aops-policy-commands.md — template get](./aops-policy-commands.md#uip-gov-aops-policy-template-get):

```bash
PRODUCT_DIR="$SESSION_DIR/products/$PRODUCT_NAME"
mkdir -p "$PRODUCT_DIR"

uip gov aops-policy template get "$PRODUCT_NAME" \
  --output-form-data "$PRODUCT_DIR/form-data.json" \
  --output-template-locale-resource "$PRODUCT_DIR/form-template-locale-resource.json" \
  --output json \
  | jq '.Data.template' > "$PRODUCT_DIR/form-template.json"
```

Either way, the three working files are:

| File | Source | Purpose |
|------|--------|---------|
| `$SESSION_DIR/products/$PRODUCT_NAME/form-template.json` | Written by `template list`, or extracted via `jq '.Data.template'` on `template get` | Form.io schema — defines field types, options, validation, and structure |
| `$SESSION_DIR/products/$PRODUCT_NAME/form-data.json` | Written by CLI (`template list`, or `template get --output-form-data`) | Flat key-value object with default values for every policy field |
| `$SESSION_DIR/products/$PRODUCT_NAME/form-template-locale-resource.json` | Written by CLI (`template list`, or `template get --output-template-locale-resource`) | Per-field object with `value`, `type`, `label`, and `description` — locale-resolved from the form template |

Read `$SESSION_DIR/products/$PRODUCT_NAME/form-template.json` for the form.io schema used in Step 3.

**Choose the working `$POLICY_DATA` blueprint based on the flow:**

- **Create flow:** read `$SESSION_DIR/products/$PRODUCT_NAME/form-data.json` as `$POLICY_DATA`. Every field not explicitly changed keeps its product default.
- **Update flow:** read `$SESSION_DIR/existing-policy-data.json` (extracted by the caller via `jq '.Data.data'` on `policy get`) as `$POLICY_DATA`. Every field not explicitly changed keeps the value from the existing policy — NOT the product default. Using `form-data.json` as the update blueprint would silently wipe every non-default setting the user previously configured. If a key appears in `form-data.json` but not in the existing policy data (schema drift — new field added to the template after the policy was created), fill the gap from `form-data.json` and flag the new field to the user in the final review.

Read `$SESSION_DIR/products/$PRODUCT_NAME/form-template-locale-resource.json` as your field metadata map. Each entry looks like:

```json
{
  "gemini-control-toggle": {
    "value": true,
    "type": "checkbox",
    "label": "Gemini",
    "description": "Disabling models will impact genAI features across products..."
  }
}
```

Use `label` as the display name and `description` as the hint when prompting the user. Use `type` to determine the prompt style (Step 5). Use `value` as the pre-populated default.

---

## Step 3 — Traverse the Component Tree

The form.io schema has a root `components[]` array. Components nest recursively. Use a depth-first traversal.

### Container types — recurse, do not prompt

| `type` | Children field | Notes |
|--------|---------------|-------|
| `panel` | `components[]` | Announce the panel title as a section header |
| `tabs` | `components[]` — each child has its own `components[]` | Announce each tab label as a sub-section |
| `columns` | `columns[]` — each column has `components[]` | Recurse silently, no header |
| `fieldset` | `components[]` | Recurse silently, no header |
| `well` | `components[]` | Recurse silently, no header |
| `editgrid` | `components[]` (row template) + data is an array | See [editgrid handling](#step-6--editgrid-repeating-rows) below |

### Display-only types — skip entirely

`htmlelement`, `content`, `button`, `submit`

### Input types — prompt the user

`checkbox`, `radio`, `select`, `selectboxes`, `textfield`, `textarea`, `number`, `currency`, `email`, `url`, `phoneNumber`, `datetime`

---

## Step 4 — Use Locale Resource for Labels

The `$SESSION_DIR/products/$PRODUCT_NAME/form-template-locale-resource.json` file already contains resolved, human-readable `label` and `description` for every field — this work is done by the CLI. No additional i18n key lookup is needed.

For each field in `form-template-locale-resource.json`:

- Use `label` as the display name shown to the user
- Use `description` as the hint (if present), appended as `(hint: <DESCRIPTION>)`
- Use `type` to determine the prompt style (Step 5)
- Use `value` as the pre-populated default

Iterate `form-template-locale-resource.json` in form-template order — the CLI writes its entries in the same order as the form template component tree, so a straight iteration gives the user-facing ordering.

---

## Step 5 — Choose Interaction Mode

Decide the interaction mode from the user's original request. **Prefer Mode A whenever the user supplied any intent** — only fall back to Mode B when the user's request has no configurable signal at all.

| Situation | Mode | Action |
|-----------|------|--------|
| User supplied intent keywords (*"disable Gemini and Claude"*, *"restrict to US and EU"*, etc.) | A | Grep locale resource + auto-fill matched fields |
| User named only the product (*"create a policy for Studio"*) | B | Paginated field-by-field prompting |
| User explicitly asked *"show me every field"* | B | Paginated field-by-field prompting |
| Mode A left required fields unset or some intent phrases unmapped | A → B for those fields only | See Mode A fallback below |

### Mode A — Intent-based auto-fill (preferred — default)

If the user's original prompt describes how to configure the policy, or names specific fields to change, do NOT prompt field-by-field.

0. **Recipe lookup first.** Before grepping the locale file, check [aops-governance-recipes-guide.md](./aops-governance-recipes-guide.md) for a recipe whose intent keywords match the user's ask. If a recipe matches, apply its product + field mapping directly to `$POLICY_DATA` — the recipes give you the correct `key` and value without locale-string guessing. Only proceed to step 1 below for intents not covered by any recipe, or for recipe-matched intents whose parameter values (e.g. `BlockedEmails`, `AllowedApplications`) still need to be extracted from the user's phrasing.
1. Use the **`Grep` tool** (Claude's built-in — NOT `Bash(grep …)`, which prompts for permission every call) against `$SESSION_DIR/products/$PRODUCT_NAME/form-template-locale-resource.json` to find `label` / `description` entries matching the user's stated intent. Set `-i: true` (case-insensitive) and `output_mode: "content"`. Use the `Read` tool on the same file if you need surrounding structure to resolve a `key`.
2. Apply those values directly to `$POLICY_DATA` (skip Step 6 editgrid prompts unless the user's intent referenced a grid). Leave every unmatched field at its default (create) or existing value (update).
3. **Required-field sweep.** For each field with `validate.required: true`, confirm `$POLICY_DATA` contains a non-empty value. If a required field is unset (create flow, default is empty) or cleared by the user's intent, drop to Mode B for that single field only — do not silently produce invalid data.
4. **Runtime-rule empty-parameter check.** For runtime analyzer rules (e.g. `RT-UIA-001`, `RT-OUT-001`) and workflow analyzer allow/block-list rules, enabling the rule without populating its parameter array (`AllowedApplications`, `BlockedApplications`, `AllowedURLs`, `BlockedURLs`, `BlockedEmails`, etc.) produces a no-op policy that enforces nothing. If the user's intent names the rule but does not specify the list contents, STOP and ask for the list explicitly rather than saving an empty array. Do not silently write a do-nothing policy.
5. Jump to **Step 7 — Build the Output JSON**. The remaining steps (Step 8 Save, Step 9 Summary) run in their numbered order.

Prompt the user only if a specific field they clearly referenced is ambiguous (e.g. they said "restrict Claude" but there are two Claude-related fields). Do not confirm unchanged defaults — silence means "keep defaults".

**Fallback — intent doesn't match any field.** If the `Grep` search returns no matches for an intent keyword in the locale resource (e.g. they said "block region X" but the product has no region field), stop and tell the user exactly which phrases could not be mapped. Do not silently drop them. Ask: *"I couldn't find fields for `<PHRASES>` under `<PRODUCT_LABEL>`. Would you like to (a) proceed without those settings, (b) pick a different product, or (c) enter field values manually?"*. If **some** intent phrases matched and others did not, apply the matches and ask the same three-way question only for the unmapped phrases — do not discard the partial auto-fill.

If the caller's final review is rejected and the user asks to adjust specific fields, fall back to Mode B for those fields only.

### Mode B — Paginated interactive prompting

If the user did not provide intent, prompt them **one page at a time**, up to 10 fields per page. Do not prompt field-by-field one at a time — this is too slow for forms with 20+ fields.

For each page:

1. Group prompts by the enclosing panel or tab title. Announce each group:
   ```text
   ── Feedback settings ──
   ```
2. Show up to 10 input fields with their label, hint (if present), default value, and expected answer format.
3. After the 10th field on the page, stop and ask: `Press Enter to accept all defaults on this page, or reply with any changes (e.g. "feedback-enabled: no, default-action: Warning").`
4. Parse the user's reply, update `$POLICY_DATA`, and move to the next page.
5. Continue until every input field has been shown.

For each input field, show:

- Humanized label (and hint if present)
- Current default value (or "not set" if absent)
- Expected answer format for the field type (see below)

### checkbox

```text
Feedback enabled [default: yes]
Enable or disable feedback? (yes / no, or press Enter to keep default)
```

Map answers: `yes`/`true`/`1`/`on` → `true`; `no`/`false`/`0`/`off` → `false`.

### radio

```text
Default action [default: Error]
Options:
  1. Error
  2. Warning
  3. Info
Choose an option by number or name, or press Enter to keep default:
```

Use the option's `value` (not its `label`) when writing to `$POLICY_DATA`.

### select

Same prompt shape as radio.

### selectboxes

```text
Allowed regions [defaults: US: yes, EU: yes, APAC: no]
For each region, enter yes or no (or press Enter to keep all defaults):
  US   [yes]:
  EU   [yes]:
  APAC [no]:
```

Result is an object: `{ "US": true, "EU": true, "APAC": false }`.

### textfield / textarea

```text
Rule code [default: RULE001]
Enter a value, or press Enter to keep default:
```

If `validate.required` is `true` and the user provides an empty value, re-prompt: `This field is required. Please enter a value:`.

### number / currency

```text
Priority [default: 10]
Enter an integer, or press Enter to keep default:
```

Reject non-numeric input and re-prompt.

### datetime

```text
Expiry date [default: none]
Enter a date (YYYY-MM-DD), or press Enter to keep default:
```

---

## Step 6 — editgrid (Repeating Rows)

An `editgrid` stores an array of row objects. Each row's shape is defined by the grid's child `components[]`.

1. **Show existing rows** from `$POLICY_DATA[KEY]` (from defaultData). Number them starting at 1.
2. **Ask the user** which rows they want to modify (by number), or none.
3. For each row chosen: prompt field-by-field using the grid's child components (same rules as above).
4. **Add rows:** If `disableAddingRemovingRows` is `false` (or absent), ask after existing rows: `Add a new row? (yes / no)`
   - If yes, collect all fields for the new row, then ask again (max 20 new rows).
5. **Remove rows:** If `disableAddingRemovingRows` is `false`, ask: `Remove any existing rows? Enter row numbers to remove, or press Enter to skip.`

**Preserve each row's `identifier` field** if the row template's `components[]` declares a field named `identifier` and the existing row has a non-empty value for it — that identifier binds deployment-time references to the row. Do NOT regenerate it on edit. If a brand-new row is added, generate a fresh identifier per the product's conventions (usually a short slug of the row's primary display field; check existing rows for pattern).

---

## Step 7 — Build the Output JSON

After collecting all answers, assemble `$POLICY_DATA`. The structure must be a flat key-value object — the same format as `$SESSION_DIR/products/$PRODUCT_NAME/form-data.json` produced by `template get --output-form-data`:

```json
{
  "feedback-enabled": true,
  "default-action": "Warning",
  "orchestrator-library-feed-enabled": false,
  "embedded-rules-config-rules": [
    {
      "identifier": "rule1",
      "is-enabled-embedded-rules-config-rules": true,
      "code-embedded-rules-config-rules": "RULE001"
    }
  ]
}
```

Rules:

- **Create flow:** include every key from `$SESSION_DIR/products/$PRODUCT_NAME/form-data.json` — defaults for unchanged fields.
- **Update flow:** include every key from `$SESSION_DIR/existing-policy-data.json` so no previously configured value is dropped. For any key present in `form-data.json` but absent from the existing policy data, add it using the form-data default (schema drift — new field added since the policy was created).
- Do not add keys that are not in the schema (`form-template.json`).
- Use the component's `key` as the JSON key — not the label.
- Preserve types: boolean fields must be `true`/`false` (not `"true"`/`"false"`).
- Do NOT wrap the object in `{ "data": {...} }` — the CLI `create --input` / `update --input` wraps it automatically.

---

## Step 8 — Save to File

Write the final `$POLICY_DATA` object to `$SESSION_DIR/aops-policy-data.json` (session-scoped, not product-scoped — only one policy is created per session). The format must be identical to `$SESSION_DIR/products/$PRODUCT_NAME/form-data.json` — a flat JSON object, no envelope.

Use the `Write` tool to serialize `$POLICY_DATA` directly to `$SESSION_DIR/aops-policy-data.json`. Do NOT wrap the object in `{ "data": {...} }` — the CLI wraps it automatically.

Sanity-check the saved file:

```bash
jq 'type' "$SESSION_DIR/aops-policy-data.json"                                       # must print "object"
jq 'keys | length' "$SESSION_DIR/aops-policy-data.json"                              # must match the schema-expected field count
diff <(jq -S 'keys' "$SESSION_DIR/aops-policy-data.json") \
     <(jq -S 'keys' "$SESSION_DIR/products/$PRODUCT_NAME/form-data.json")            # create flow: should be empty (same key set)
```

For the update flow, the third check should compare against `$SESSION_DIR/existing-policy-data.json` plus any schema-drift keys — not against `form-data.json`.

The file must exist before Step 9 runs, because the caller's final-review gate (and the subsequent CLI mutation) both consume it.

---

## Step 9 — Prepare Change Summary and Return to Caller

Build a summary of every value the user changed and hand it to the caller. **Do NOT prompt for yes/no here** — the caller ([aops-policy-manage-guide.md](./aops-policy-manage-guide.md)) owns the single final-review gate before the CLI mutation runs.

**Baseline for the diff depends on the flow:**

- **Create flow:** diff against product defaults from `form-data.json`.
- **Update flow:** diff against the existing policy's data from `$SESSION_DIR/existing-policy-data.json`. Also call out any schema-drift fields (new keys filled from product defaults).

```text
Policy data summary — changed from <defaults | existing policy>:

  feedback-enabled             false   (was: true)
  default-action               Warning (was: Error)
  orchestrator-library-feed-enabled  false   (was: true)

Unchanged fields: 14 fields kept at their defaults.
```

**Return control to caller.** At this point the configure guide's work is done. Hand two things back to the caller and stop without prompting:

1. **Path:** `$SESSION_DIR/aops-policy-data.json` (render as a clickable markdown link so the user can open it from the upcoming review gate).
2. **Change summary:** the block above, verbatim.

The caller ([aops-policy-manage-guide.md — Create Step 4](./aops-policy-manage-guide.md#step-4--final-review-before-create-single-confirmation-gate) for the create flow, [Update Step 5](./aops-policy-manage-guide.md#step-5--final-review-before-update-single-confirmation-gate) for the update flow) inlines both into the single review gate. If the caller's review is rejected and the user asks to adjust specific fields, the caller routes back to Step 5 (Mode B for those fields) or Step 7 (metadata-only re-serialization) here.

---

## Debug

| Error | Cause | Fix |
|-------|-------|-----|
| `template list` bootstrap fails or writes no product folders | Every per-product fetch failed | Stop. Show the CLI error. Verify `uip login status` and network; rerun the bootstrap |
| `template get` returns no `template` field (update flow) | Product fetch failed for this product | Stop. Show the CLI error. Verify the product name matches a catalog entry |
| `template.components` is empty or absent | Product has no configurable fields | Inform the user. Use `defaultData` as-is and skip to Step 8 |
| User provides invalid type for a field (e.g. text for `number`) | Type mismatch in Mode B answer | Re-prompt: `Invalid input. Expected <TYPE>. Please try again:` |
| User enters blank for a required field | `validate.required: true` and empty value | Re-prompt: `This field is required. Please enter a value:` |
| Mode A partial match (some intent phrases unmapped) | Some user keywords found no locale-resource hits | Apply the matched phrases; ask the three-way question (proceed without / pick different product / enter manually) for the unmapped phrases only |
| `$POLICY_DATA` keys diverge from `form-data.json` | Accidental extra key or missing schema key | Stop. Diff via the `jq keys` check in Step 8. Drop unknown keys; re-fill missing keys from the blueprint |
| User asks to skip all fields | No intent + no default override | Use the full default data object without changes and proceed to Step 8 |
