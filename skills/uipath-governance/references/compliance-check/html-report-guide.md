# HTML Report Generation Guide

Generate an auditor-facing HTML compliance report from the template at `assets/templates/compliance-report-template.html`.

The output is a **self-contained, single-file HTML document** with inline CSS, no external dependencies (no CDN fonts, no JavaScript, no images). It renders identically in any modern browser and prints cleanly.

## How to generate

1. Read the template file: `assets/templates/compliance-report-template.html`
2. Load the property reference: `assets/uipath_policy_reference_classified.json` — used to resolve property path → human-readable description (see [Property description + classification lookup](#property-description--classification-lookup) below)
3. Replace all `{{PLACEHOLDER}}` tokens with actual values
4. Generate the clause rows and drift detail blocks
5. Write the populated HTML to `./compliance-report-{packId}-{timestamp}.html`

## Placeholder reference

### Header placeholders

| Placeholder | Source | Example |
|---|---|---|
| `{{PACK_NAME}}` | `manifest.packName` | `ISO/IEC 42001:2023 — AI Trust Layer Controls` |
| `{{PACK_VERSION}}` | `manifest.version` | `1.0.0` |
| `{{PACK_ID}}` | `manifest.packId` | `iso-42001-2023-aitl` |
| `{{STANDARD_NAME}}` | `clauseMap.standardName` | `ISO/IEC 42001:2023` |
| `{{TENANT_NAME}}` | From `~/.uipath/.auth` `UIPATH_TENANT_NAME` | `appsdevDefault` |
| `{{DEPLOYMENT_LEVEL}}` | From the policy file's `deploymentLevel` | `tenant` |
| `{{GENERATED_AT}}` | ISO 8601 timestamp | `2026-04-16 14:56 UTC` |
| `{{OVERALL_STATUS}}` | Derived from results (see below) | `Non-Compliant` |
| `{{OVERALL_BADGE_CLASS}}` | CSS class for the badge (see below) | `badge-fail` |

### Overall status logic

| Condition | `{{OVERALL_STATUS}}` | `{{OVERALL_BADGE_CLASS}}` |
|---|---|---|
| All clauses compliant | `Compliant` | `badge-pass` |
| Some compliant, some drifted | `Non-Compliant` | `badge-fail` |
| All drifted | `Non-Compliant` | `badge-fail` |
| Only non-mandatory clauses drifted | `Partially Compliant` | `badge-partial` |

### Summary placeholders

| Placeholder | Source |
|---|---|
| `{{TOTAL_CLAUSES}}` | Total number of in-scope clauses |
| `{{COMPLIANT_COUNT}}` | Count of clauses with `status: "compliant"` |
| `{{DRIFTED_COUNT}}` | Count of clauses with `status: "drifted"` |
| `{{COMPLIANT_PCT}}` | `(compliant / total) * 100` |
| `{{DRIFTED_PCT}}` | `(drifted / total) * 100` |

## Generating clause rows

Replace the `<!-- {{CLAUSE_ROWS}} -->` comment with one `<tr>` per clause. Use this structure:

```html
<tr>
  <td><span class="clause-id">{{CLAUSE_ID}}</span></td>
  <td>
    <div class="clause-name">{{CLAUSE_NAME}}</div>
    <div class="clause-category">{{CLAUSE_CATEGORY}}</div>
  </td>
  <td><span class="obligation-tag {{OBLIGATION_TAG_CLASS}}">{{OBLIGATION_LEVEL}}</span></td>
  <td><span class="status-pill {{STATUS_PILL_CLASS}}">{{STATUS}}</span></td>
  <td><span class="drift-count">{{DRIFT_PROPERTY_COUNT}}</span></td>
</tr>
```

### Obligation tag classes

| `obligationLevel` | `{{OBLIGATION_TAG_CLASS}}` |
|---|---|
| `Mandatory` | `tag-mandatory` |
| `ConditionalMandatory` | `tag-conditional` |
| `Recommended` | `tag-recommended` |
| `Optional` | `tag-optional` |

### Status pill classes

| `status` | `{{STATUS_PILL_CLASS}}` | Display text |
|---|---|---|
| `compliant` | `pill-compliant` | `Compliant` |
| `drifted` | `pill-drifted` | `Drifted` |

### Row ordering

Order rows: drifted first (sorted by obligation: Mandatory > ConditionalMandatory > Recommended > Optional), then compliant.

## Generating drift details

Replace the `<!-- {{DRIFT_DETAILS}} -->` comment with one block per **drifted** clause. Use this structure:

```html
<div class="drift-detail">
  <div class="drift-detail-header">
    <span class="clause-id">{{CLAUSE_ID}}</span>
    <span class="clause-name">{{CLAUSE_NAME}}</span>
  </div>
  <table>
    <thead>
      <tr>
        <th>Control</th>
        <th>Expected</th>
        <th>Actual</th>
        <th style="width: 70px">Match</th>
      </tr>
    </thead>
    <tbody>
      <!-- One row per property -->
      <tr>
        <td><div class="control-desc">{{CONTROL_LABEL}}</div></td>
        <td><span class="val-expected">{{EXPECTED_VALUE}}</span></td>
        <td><span class="val-actual">{{ACTUAL_VALUE}}</span></td>
        <td><span class="{{MATCH_CLASS}}">{{MATCH_ICON}}</span></td>
      </tr>
    </tbody>
  </table>
</div>
```

### Control label lookup

Do NOT label rows with the raw property path when a description is available. Resolve each path against the reference at `assets/uipath_policy_reference_classified.json` and use the field's `description` as the label. Do **not** render the raw property path or the `classification_type` — they add noise the auditor doesn't need.

**Reference file layout:**

```jsonc
{
  "AITrustLayer": {
    "_product_name": "AITrustLayer",

    "global-control-toggle": {
      "type": "boolean",
      "description": "Master switch. Must be true for all sub-controls to take effect…"
    },

    "container": {
      "type": "object",
      "fields": {
        "pii-in-flight-agents": {
          "type": "boolean",
          "description": "Scan and redact PII in data sent to/from Agents at runtime."
        }
      }
    },

    "pii-entity-table": {
      "type": "array",
      "item_schema": {
        "pii-entity-confidence-threshold": {
          "description": "Minimum confidence score for detection…"
        }
      }
    }
  }
}
```

Top-level keys starting with `_` (e.g. `_product_name`, `_section_pii`) are metadata and must be ignored during lookup.

**Traversal algorithm** — given a product (e.g. `AITrustLayer`) and a dotted path (e.g. `container.pii-in-flight-agents`):

```
node = reference[product]
for segment in path.split("."):
    if segment in node:
        node = node[segment]
    elif node.fields and segment in node.fields:
        node = node.fields[segment]
    elif node.item_schema and segment in node.item_schema:
        node = node.item_schema[segment]
    else:
        node = null
        break
```

**Rendering rules:**

| Situation | `{{CONTROL_LABEL}}` |
|---|---|
| Description found | `node.description` verbatim |
| No description (unmapped path, or product missing from reference) | Fall back to the raw path wrapped in `<code>…</code>` so it's still intelligible to the auditor |

### Match display

| `match` | `{{MATCH_CLASS}}` | `{{MATCH_ICON}}` |
|---|---|---|
| `true` | `val-match` | `&#x2713;` (checkmark) |
| `false` | `val-mismatch` | `&#x2717;` (cross) |

### Value formatting

- Booleans: render as `true` or `false` (lowercase)
- Strings: render as-is
- `null` (missing from tenant): render as `null`
- Arrays: render as `[array]` with a note — the drift detail table is for scalar leaf properties

## Generating skipped policies section

If `skippedPolicies` is non-empty, include the skipped policies section. Otherwise omit it entirely.

## Output path

Write the HTML file to: `./compliance-report-{packId}-{timestamp}.html`

Same directory as the JSON report. Do NOT commit or stage.
