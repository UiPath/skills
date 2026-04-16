# HTML Report Generation Guide

Generate an auditor-facing HTML compliance report from the template at `assets/templates/compliance-report-template.html`.

The output is a **self-contained, single-file HTML document** with inline CSS, no external dependencies (no CDN fonts, no JavaScript, no images). It renders identically in any modern browser and prints cleanly.

## How to generate

1. Read the template file: `assets/templates/compliance-report-template.html`
2. Replace all `{{PLACEHOLDER}}` tokens with actual values
3. Generate the clause rows and drift detail blocks
4. Write the populated HTML to `./compliance-report-{packId}-{timestamp}.html`

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
| Some compliant, some drifted/not-deployed | `Non-Compliant` | `badge-fail` |
| All drifted or not-deployed | `Non-Compliant` | `badge-fail` |
| Only non-mandatory clauses drifted | `Partially Compliant` | `badge-partial` |

### Summary placeholders

| Placeholder | Source |
|---|---|
| `{{TOTAL_CLAUSES}}` | Total number of in-scope clauses |
| `{{COMPLIANT_COUNT}}` | Count of clauses with `status: "compliant"` |
| `{{DRIFTED_COUNT}}` | Count of clauses with `status: "drifted"` |
| `{{NOT_DEPLOYED_COUNT}}` | Count of clauses with `status: "not-deployed"` |
| `{{COMPLIANT_PCT}}` | `(compliant / total) * 100` |
| `{{DRIFTED_PCT}}` | `(drifted / total) * 100` |
| `{{NOT_DEPLOYED_PCT}}` | `(notDeployed / total) * 100` |

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
| `not-deployed` | `pill-not-deployed` | `Not Deployed` |

### Row ordering

Order rows: drifted first (sorted by obligation: Mandatory > ConditionalMandatory > Recommended > Optional), then not-deployed, then compliant.

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
        <th>Property</th>
        <th>Expected</th>
        <th>Actual</th>
        <th style="width: 70px">Match</th>
      </tr>
    </thead>
    <tbody>
      <!-- One row per property -->
      <tr>
        <td><code>{{PROPERTY_PATH}}</code></td>
        <td><span class="val-expected">{{EXPECTED_VALUE}}</span></td>
        <td><span class="val-actual">{{ACTUAL_VALUE}}</span></td>
        <td><span class="{{MATCH_CLASS}}">{{MATCH_ICON}}</span></td>
      </tr>
    </tbody>
  </table>
</div>
```

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
