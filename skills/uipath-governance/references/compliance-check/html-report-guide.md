# HTML Report Generation Guide

Generate an auditor-facing HTML compliance report from the template at `assets/templates/compliance-report-template.html`.

The template is the **single source of truth** for layout and CSS. It ships with the skill and must not be modified at runtime. Rendering is pure data substitution: the skill reads the template, replaces placeholders, and writes a new HTML file. Do not inject additional `<style>` blocks, change class names, or alter the document structure — the template already contains everything.

The output is a **self-contained, single-file HTML document** with inline CSS, no external dependencies (no CDN fonts, no JavaScript, no images). It renders identically in any modern browser and prints cleanly.

## How to generate

1. Read the template file verbatim: `assets/templates/compliance-report-template.html`
2. Load the property reference: `assets/uipath_policy_reference_classified.json` — used to resolve property path → human-readable description (see [Control label lookup](#control-label-lookup) below)
3. Replace every scalar `{{PLACEHOLDER}}` token (see [Scalar placeholders](#scalar-placeholders) below)
4. Replace the three HTML-comment anchors with generated blocks:
   - `<!-- {{CLAUSE_ROWS}} -->` → concatenated `<tr>` rows, one per clause
   - `<!-- {{DRIFT_DETAILS}} -->` → concatenated drift blocks, one per drifted clause
   - `<!-- {{SKIPPED_POLICIES_BLOCK}} -->` → skipped-policies `<div>` or the empty string
5. Write the populated HTML to `./compliance-report-{packId}-{timestamp}.html`

### Substitution invariants

- Every scalar placeholder in the template must be replaced. No `{{…}}` may survive in the final file.
- HTML-escape every user-sourced string before substituting (pack names, clause names/categories, effective policy name, value fields). `&`, `<`, `>`, `"`, `'` must be encoded.
- Do not replace the three anchor comments with anything but the exact HTML fragments described below.
- If there are no drifted clauses, replace `<!-- {{DRIFT_DETAILS}} -->` with `<p class="empty-note">No drifted clauses.</p>`.
- If `skippedPolicies` is empty, replace `<!-- {{SKIPPED_POLICIES_BLOCK}} -->` with the empty string.

## Scalar placeholders

Every token below appears literally in `compliance-report-template.html`. Replace each with the value from the compliance result. Values other than numeric counts must be HTML-escaped.

| Placeholder | Source | Example |
|---|---|---|
| `{{PACK_NAME}}` | `report.pack.packName` | `ISO/IEC 42001:2023 — AI Trust Layer Controls` |
| `{{PACK_VERSION}}` | `report.pack.version` | `1.0.0` |
| `{{TENANT_NAME}}` | `UIPATH_TENANT_NAME` | `appsdevDefault` |
| `{{GENERATED_AT}}` | `report.generatedAt`, formatted as `YYYY-MM-DD HH:MM UTC` | `2026-04-17 15:24 UTC` |
| `{{OVERALL_STATUS}}` | Derived (see below) | `Non-Compliant` |
| `{{OVERALL_BADGE_CLASS}}` | Derived (see below) | `badge-fail` |
| `{{TOTAL_CLAUSES}}` | `report.summary.totalClauses` | `21` |
| `{{COMPLIANT_COUNT}}` | `report.summary.compliant` | `3` |
| `{{DRIFTED_COUNT}}` | `report.summary.drifted` | `18` |
| `{{COMPLIANT_PCT}}` | `round(compliant / total * 100)` (integer) | `14` |
| `{{DRIFTED_PCT}}` | `round(drifted / total * 100)` (integer) | `86` |

### Overall status logic

| Condition | `{{OVERALL_STATUS}}` | `{{OVERALL_BADGE_CLASS}}` |
|---|---|---|
| All in-scope clauses compliant | `Compliant` | `badge-pass` |
| At least one Mandatory or ConditionalMandatory clause drifted | `Non-Compliant` | `badge-fail` |
| All clauses drifted | `Non-Compliant` | `badge-fail` |
| Only non-mandatory (Recommended / Optional) clauses drifted | `Partially Compliant` | `badge-partial` |

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

## Generating the skipped policies block

Replace `<!-- {{SKIPPED_POLICIES_BLOCK}} -->` with either:

- The empty string, if `report.skippedPolicies` is empty.
- A single `<div>` block following this structure:

```html
<div class="skipped-policies">
  <h2 style="margin-top:0">Skipped Policies</h2>
  <p class="empty-note">The following policy files were recorded but not diffed (out of V1 scope):</p>
  <ul>
    <li><code>{{FILE}}</code> — {{PRODUCT}} ({{REASON}})</li>
    <!-- repeated per skipped entry -->
  </ul>
</div>
```

## Output path

Write the HTML file to: `./compliance-report-{packId}-{timestamp}.html`

Same directory as the JSON report. Do NOT commit or stage.
