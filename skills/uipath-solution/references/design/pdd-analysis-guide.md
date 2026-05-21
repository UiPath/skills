# PDD Analysis Guide

How to extract structured information from Process Design Documents in any format.

## Supported Input Formats

| Format | How to Read | Notes |
|---|---|---|
| PDF | Use the Read tool with `pages` parameter. Read in chunks of up to 20 pages. | Screenshots are visible as images — see "Handling Screenshots" below. |
| Word (.docx) | Read the file directly. | Tables may render differently — verify structure. |
| Markdown | Read the file directly. | Easiest format — structure is already parseable. |
| Pasted text | Process from the conversation context. | Ask the user to paste section by section if the PDD is large. |

## Handling Screenshots

When you encounter screenshots in the PDD:

1. **Note** the application name and screen shown.
2. **Extract** visible field names, button labels, and navigation elements — these become data field references and process step descriptions.
3. **Do NOT extract** selectors, XPath, CSS, coordinates, colors, or visual layout details — these are determined at development time, not from static images.
4. **Reference** the screenshot content in the relevant process step's "Remarks" field if useful.
5. **DO extract concrete data values** shown in the screenshot — sample IDs, names, dates, expected outputs, error messages. These are oracles for the test strategy, not selectors. See "Extract Canonical Examples" below.

## Extract Canonical Examples

**Mandatory step. Run this on every PDD before falling back to `[SME REVIEW]` for test data.** PDDs almost always carry concrete example values somewhere — most agents miss them because the values live in screenshots, inline strings, or example tables rather than in a dedicated "Test Data" section.

### Where to look

Scan every one of these surfaces for concrete values:

| Surface | What to look for | Example signals |
|---|---|---|
| **Screenshots of input data** | Sample IDs, names, codes, dates, free-form values shown filled into a form or list | `PRO1037`, `Jeanine Frederick`, `Romania`, `01/15/2024` |
| **Screenshots of expected output** | Hash values, computed outputs, status fields, post-state values | `bde2c5964a3cfbc9b839aef9aa2a2764829d5497` (SHA1), `Confirmed`, `Approved` |
| **Inline strings in step descriptions** | Quoted literals — anything inside backticks, double quotes, or single quotes that names a value rather than a column | `"the value 'WI5' in the Type column"`, `'PRO1037'` |
| **Example tables in the Appendix** | Rows where each cell is a concrete value rather than a placeholder | `Vendor: ACME`, `Amount: 1250.00`, `Currency: EUR` |
| **Validation rule examples** | Concrete inputs paired with expected pass/fail outcomes | `Hash must be 40 lowercase hex chars; e.g., bde2c5964a3...` |
| **"For example" callouts in prose** | Sentences like "for example, ID PRO1037 produces hash X" | `e.g.`, `for example`, `such as` |
| **Error message screenshots** | Verbatim error strings the automation must match | `"Hash mismatch — expected ..., got ..."` |

### What to extract

For every concrete value found, capture:

| Field | Description |
|---|---|
| **Source location** | PDD page or section (e.g., "page 9 screenshot, Login screen") |
| **Data role** | Input / Expected output / Validation rule / Error message |
| **Field name** | Maps to a field in §5 Data Definitions |
| **Value** | The literal value, quoted exactly as it appears in the PDD |

### Where to write the extracted values

Write the canonical examples into the SDD's §17 Testing Strategy → Canonical Test Case table. Use the field/value rows of that table to capture the input set, and add a separate Expected Output subsection for the output values. The values feed:

- **§4 Business Rule test oracles** — every business rule with a concrete example becomes a test assertion using these values (e.g., `BR-04: SHA1(input) == '<canonical hash>'`).
- **§17 Happy Path Assertions** — the canonical case is the first row of happy-path tests.
- **§17 Output validation tests** — the canonical output value is the oracle for output-format regex checks (see template §4 prompt block).

### Canonical examples are NOT `[SME REVIEW]` items

A canonical example present anywhere in the PDD is **fact**, not user-supplied data. Do not mark it as `[SME REVIEW]`. The `[SME REVIEW]` fallback applies only when:

- The entire PDD has been scanned (all screenshots, all tables, all step descriptions, all appendices) AND
- No concrete value can be derived for the field.

If scanning finds at least one concrete value, treat it as the canonical case — the gap-detection row "Test data / canonical case" only fires when extraction returns empty.

### Output writing checklist

Before declaring Phase 1 extraction complete:

- [ ] Every screenshot has been visually inspected for concrete values (not just labels and buttons).
- [ ] Every inline-quoted string in step descriptions has been captured.
- [ ] Every example table in the PDD body or appendix has been read row by row.
- [ ] At least one canonical input set + expected output is recorded for the §17 Canonical Test Case (or the `[SME REVIEW]` fallback applies because the PDD genuinely has no examples).
- [ ] Hash / regex / format-shaped values are paired with the BR they validate (e.g., "SHA1 output: `bde2c596...`" → BR-04 SHA1 format rule).

## Reading Strategy

PDD templates vary — section numbers and names differ across organizations. Use the Table of Contents to identify where each topic lives, then read in this priority order:

1. **Start with the Table of Contents** (usually in the first few pages of a PDF). This reveals the PDD structure and tells you which sections exist.
2. **Read the Process Overview first.** This gives you the high-level picture: what the process does, how often, how many items, how many apps.
3. **Read the Detailed Process Steps next.** This is the core — every step the robot needs to perform.
4. **Read Exception and Error sections.** These define the failure modes.
5. **Read Application Details and Credentials last.** These are supporting information.

## Extraction Rules by PDD Topic

PDD section numbers below are typical but not guaranteed. Match by topic name, not number.

### Introduction

Extract:
- **Process name** — the official name used in the PDD title and overview
- **Objective** — what the automation achieves (faster processing, error reduction, etc.)
- **Department/function** — who owns the process
- **Key contacts** — SME / Process Owner, Solution Architect, Business Analyst, Developer(s), Project Manager (only roles the PDD explicitly names). **Destination:** §1 Delivery Team table in the RPA SDD. Omit rows for roles the PDD does not name; do not invent.
- **Master project / process full name** — if the PDD names the Master Project explicitly (e.g., a "Process Full Name" cell such as `PurchaseOrders_DataExtraction`), capture it verbatim. **This literal name becomes the project-name prefix** used in Level 2.5 sub-project naming — it overrides any PascalCase short-name derived from the process title.

Watch for:
- The PDD may describe the project initiative context (e.g., "part of a larger digital transformation"). Capture this as context but do not let it expand the SDD scope.

### Process Overview

Extract into a structured table:
- Process full name
- Function and department
- Short description (operation, activity, outcome)
- Required roles
- Schedule (frequency, business hours)
- Volume (items per day, peak periods)
- Average handling time (manual vs. automated target)
- FTE count
- Exception rate estimate
- Input data description
- Output data description

Watch for:
- **In scope vs. out of scope** — these define the SDD boundary. Anything out of scope must not appear in the workflow inventory.
- Vague volume descriptions like "7-15 items" — capture the range, use the upper bound for capacity planning.

### Detailed Process Map

Extract:
- **Step numbering scheme** — usually 1.1, 1.2, ..., 1.5.A, 1.5.B, etc.
- **High-level flow** — the sequence of major steps
- **Loop boundaries** — where the per-item processing starts and ends
- **Decision points** — any branching logic in the flow

Watch for:
- The process map may be a flowchart image. Read the image to understand the flow, then verify against the detailed process steps section.
- Some PDDs use swimlane diagrams showing which application each step uses. This is valuable for the application scope mapping.

### Detailed Process Steps

This is the most important section. For each step, extract:

| Field | Description |
|---|---|
| Step number | The PDD's numbering (1.1, 1.5.A, etc.) |
| Action description | What the robot does in this step |
| Application | Which application is used |
| Expected result | What should be true after the step completes |
| Remarks | Error handling notes, edge cases, business rules |

Watch for:
- **Embedded business rules** — rules are often buried in the "Remarks" column or in step descriptions rather than in a dedicated section. Extract and number them (BR-01, BR-02, etc.).
- **Data field references** — step descriptions mention specific field names, variable names, or data values. Collect these for the data model definitions.
- **Value mappings** — when a step says "map X to Y" or shows a conversion table, capture the full mapping.
- **Implicit ordering constraints** — some steps must happen before others but the PDD doesn't explicitly say so. Note these for the workflow decomposition.

### Business Exceptions

Extract into a table:

| Field | Description |
|---|---|
| Exception ID | B1, B2, etc. (assign IDs if the PDD doesn't) |
| Exception name | Short descriptive name |
| Trigger step | Which process step encounters this exception |
| Trigger condition | How to detect the exception (parameters, UI state, data condition) |
| Action | What the robot must do (skip, retry, escalate, notify) |

Watch for:
- PDDs often have a "catch-all" row: "for any other exception, send email to X". Preserve this as the default handler.
- Some exceptions are actually business rules in disguise (e.g., "amount over threshold" is both an exception and a rule). Cross-reference with extracted business rules.

### System Errors

Extract into a table with the same structure as business exceptions, plus:

| Field | Description |
|---|---|
| Severity | If specified (Sev-1, Sev-2, etc.) |
| Retry policy | Number of retries, backoff strategy |

Watch for:
- If the PDD has only generic errors ("application unresponsive — retry 2 times"), expand with `[DEFAULT]` entries for common system errors: selector not found, browser crash, network timeout, credential expiry.

### Application Details

Extract into a table:

| Field | Description |
|---|---|
| Application name | Official name and version |
| Language | System language |
| Login method | How authentication works |
| Interface type | Web, desktop, terminal, API |
| Access method | Browser type, URL, application path |
| Comments | Special behaviors, routing, SPA details |

Watch for:
- URLs may be environment-specific (localhost for dev, internal DNS for prod). Note both if available.
- SPA details (hash routing, pushState) affect how the robot navigates. Capture these.
- **Email protocol** — when email is an application, extract the protocol signal: IMAP, Exchange/EWS, O365 Graph API, POP3, SMTP. Look for keywords like "IMAP", "Exchange", "O365", "Graph API", "dedicated mailbox". If not specified, mark as `[SME REVIEW]` — do not default to O365.
- **FTP/SFTP** — note whether the PDD specifies FTP, SFTP, or cloud storage (S3, Azure Blob). Capture host/path if mentioned.

### Development Details

Extract:
- **Prerequisites** — UiPath Studio version, packages, screen resolution, test environment setup
- **Credentials** — asset names, types, values (training only), notes
- **Password policies** — rotation, complexity, storage requirements

Watch for:
- Training credentials that should not be hardcoded in the automation. Note them as Orchestrator assets.

### Appendix

Extract:
- **Canonical test data** — apply the "Extract Canonical Examples" procedure above. The appendix is one of several surfaces; also scan screenshots, inline strings, and example tables elsewhere in the PDD.
- **Selector references** — if provided (rare in traditional PDDs, common in agent-ready PDDs)
- **Value mapping tables** — additional mappings not covered in the detailed process steps

### Reporting Requirements

Extract:
- **Report type** — Excel, email summary, dashboard data, PDF
- **Report frequency** — real-time, daily, weekly, per-run
- **Report content** — what data appears in the report (success counts, error details, processing times, item-level outcomes)
- **Report recipients** — who receives the report
- **Monitoring tool** — where the report is visualized (Excel, Power BI, Orchestrator Insights, custom dashboard)

Watch for:
- Reporting requirements are often in a separate section or table near the end of the PDD. They are easy to miss.
- If the PDD mentions reporting, this is a signal for a dedicated Reporting project in the project decomposition decision (see [RPA Product Guide](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals) Level 2.5 Part A).
- If the PDD has no reporting section but mentions logging or monitoring, mark reporting as `[DEFAULT]` — Orchestrator logs only.

### Project Decomposition Signals

While extracting data, watch for signals that indicate the process should be split into multiple projects. These feed into Level 2.5 Part A of the [RPA Product Guide](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals):

1. **Distinct processing stages** — does the process have clearly separate phases (e.g., "collect emails" → "extract data" → "generate output")? Note stage boundaries.
2. **Per-item transactional processing** — are items processed independently where one failure should not block others? Note where per-item processing starts/ends.
3. **Document Understanding with human validation** — does the process use DU extraction followed by Action Centre / human review? This is a common split point.
4. **Multiple output channels** — does the process produce output to multiple unrelated systems (e.g., XML to MQ + files to FTP + report to email)?
5. **Reporting** — does the PDD specify reporting requirements? This often warrants a dedicated project.
6. **Queue mentions** — does the PDD mention queues, batches, or "items to process"? This suggests queue-based architecture.

Capture these signals as a structured list in your internal model. They will be used during product selection.

## Gap Detection Checklist

After extraction, verify these items exist. Flag missing ones:

| Item | If Missing |
|---|---|
| Business exceptions section | `[DEFAULT]` — create placeholder rows for common exceptions based on application types (invalid credentials, malformed input data, missing required fields, data validation failure). Mark each as `[DEFAULT]`. |
| System errors section | `[DEFAULT]` — create placeholder rows for common infrastructure errors (application unresponsive, element not found, timeout, unhandled exception). Mark each as `[DEFAULT]`. |
| Process schedule/frequency | `[DEFAULT]` — assume on-demand trigger |
| Volume/throughput | `[SME REVIEW]` — needed for capacity planning |
| Retry counts on errors | `[DEFAULT]` — 3 retries with exponential backoff |
| Element/activity timeouts | `[DEFAULT]` — 30s page loads, 10s element waits |
| Max items per run | `[DEFAULT]` — 50 items safety cap |
| Notification recipients for errors | `[SME REVIEW]` — needed for error escalation |
| Amount/value thresholds | `[SME REVIEW]` — business decision |
| Data retention requirements | `[SME REVIEW]` — compliance decision |
| Credential rotation policy | `[DEFAULT]` — assume Orchestrator asset management |
| Test data / canonical case | Run "Extract Canonical Examples" first. Only mark `[SME REVIEW]` if scanning every screenshot, every inline-quoted string, and every example table genuinely returns zero concrete values. Most PDDs carry at least one example. |
| Reporting requirements | `[DEFAULT]` — Orchestrator logs only (no dedicated report) |
| Email protocol (when email is used) | `[SME REVIEW]` — needed for package selection (IMAP vs O365 vs Exchange) |
