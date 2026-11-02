# PDD Analysis Guide

Extract a structured model from any business-process artifact: steps, applications, exceptions, business rules, data, as-is/to-be, and the need profile.

## Accepted process-knowledge sources

Any business-process artifact is valid input for an SDD; extract the same structured model from it:

| Source | Ingestion and notes |
|---|---|
| **PDD** (`.pdf` / `.docx` / `.md` / `.txt`) | Use [Supported Input Formats](#supported-input-formats); richest source. |
| **Confluence / wiki / SharePoint page** | User exports to md/pdf or pastes it; `WebFetch` a reachable page; or use a session-connected Atlassian / Glean / Microsoft-365 connector (best-effort). Often an SOP or process write-up. |
| **BPMN model** (`.bpmn` XML, Signavio/Camunda export, or diagram image) | `Read` XML/text or the diagram image; mine tasks, gateways, events, and lanes. It often encodes the *to-be*. |
| **Meeting / Zoom transcript** | `Read` the file or pasted content, or use a session-connected transcript connector (best-effort); expect heavy gaps. |
| **SOP / work instructions / requirements doc / email thread** | Use its file format (`Read` / `docx-extract`); scope varies. |

For less-structured sources, run heavier Phase 1 gap-detection and `AskUserQuestion` to fill missing steps, applications, exceptions, rules, and to-be. Never invent business rules; flag gaps `[SME REVIEW]`.

## Supported Input Formats

| Format | Required handling |
|---|---|
| Markdown (`.md`) | `Read` directly. |
| Plain text (`.txt`) | `Read` directly; for very large files use `Read` offset/limit or [sdd-generation-guide.md Step 1](sdd-generation-guide.md#step-1-read-the-pdd). |
| PDF (`.pdf`) | Use `Read` with `pages`, in chunks of up to 20 pages. Read extracted text and visually inspect screenshots/scanned pages (see [Handling Screenshots](#handling-screenshots)). |
| Word (`.docx`) | Run `Bash` → `scripts/docx-extract.sh` (pandoc); do **NOT** Read directly. Then Read the markdown and extracted media. Parse complex raw HTML `<table>` output. Legacy `.doc` is unsupported by pandoc: ask the user to save as `.docx`/PDF or paste it. See [sdd-generation-guide.md Step 1](sdd-generation-guide.md#step-1-read-the-pdd). |
| Pasted text | Process conversation context; ask the user to paste section by section if large. |

File ingestion needs only `Read` (Markdown, `.txt`, PDF, images/media) and `Bash` (runs `docx-extract.sh` → pandoc); remote pages use `WebFetch`. Session-connected MCP connectors (Atlassian / Glean / Microsoft 365 / transcript) are best-effort; if absent, ask the user to export or paste content.

## Handling Screenshots

For every screenshot: (1) note the application and screen; (2) extract visible field names, button labels, and navigation elements as data-field references and step descriptions; (3) do **not** extract selectors, XPath, CSS, coordinates, colors, or visual-layout details; (4) reference useful content in the process step's "Remarks" field; (5) extract concrete values (sample IDs, names, dates, expected outputs, and error messages) as test oracles; see [Extract Canonical Examples](#extract-canonical-examples); (6) for unreadable `.emf`/`.wmf`, do not guess—ask for a PNG export or mark every dependent extraction `[SME REVIEW]`, naming the file.

## Extract Canonical Examples

**Mandatory: run this on every PDD before falling back to `[SME REVIEW]` for test data.** Scan every screenshot, inline string, example table, validation example, prose callout, error-message screenshot, step description, appendix, and other listed surface for concrete inputs, outputs, statuses, hashes, dates, IDs, and exact errors.

| Surface | What to look for | Example signals |
|---|---|---|
| **Screenshots of input data** | Sample IDs, names, codes, dates, free-form values shown filled into a form or list | `PRO1037`, `Jeanine Frederick`, `Romania`, a `MM/DD/YYYY` date |
| **Screenshots of expected output** | Hash values, computed outputs, status fields, post-state values | `bde2c5964a3cfbc9b839aef9aa2a2764829d5497` (SHA1), `Confirmed`, `Approved` |
| **Inline strings in step descriptions** | Quoted literals — anything inside backticks, double quotes, or single quotes that names a value rather than a column | `"the value 'WI5' in the Type column"`, `'PRO1037'` |
| **Example tables in the Appendix** | Rows where each cell is a concrete value rather than a placeholder | `Vendor: ACME`, `Amount: 1250.00`, `Currency: EUR` |
| **Validation rule examples** | Concrete inputs paired with expected pass/fail outcomes | `Hash must be 40 lowercase hex chars; e.g., bde2c5964a3...` |
| **"For example" callouts in prose** | Sentences like "for example, ID PRO1037 produces hash X" | `e.g.`, `for example`, `such as` |
| **Error message screenshots** | Verbatim error strings the automation must match | `"Hash mismatch — expected ..., got ..."` |

Record each value as:

| Field | Content |
|---|---|
| Source location | PDD page or section, such as a screenshot and screen. |
| Data role | Input / Expected output / Validation rule / Error message. |
| Field name | Corresponding field in §5 Data Definitions. |
| Value | Literal value, quoted exactly. |

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

Before Phase 1 extraction is complete, verify every screenshot was visually inspected for values (not only labels/buttons), every inline-quoted string was captured, every example table was read row by row, §17 Canonical Test Case has at least one canonical input set and expected output or the genuine no-example `[SME REVIEW]` fallback, and hash/regex/format-shaped values are paired with the BR they validate (for example, a SHA1 output with its SHA1 format rule).

## Reading Strategy

PDD section names and numbers vary. Use the Table of Contents, then read: (1) Table of Contents; (2) Process Overview; (3) Detailed Process Steps; (4) Exception and Error sections; (5) Application Details and Credentials. The overview supplies high-level process, systems, frequency, volume, and scope; detailed steps are the core robot instructions.

## Extraction Rules by PDD Topic

### Introduction

Extract official process name; objective; department/function; explicitly named SME / Process Owner, Solution Architect, Business Analyst, Developer(s), and Project Manager (only named roles) into the §1 Delivery Team table; and the explicitly named Master project / process full name verbatim. A `Process Full Name` such as `PurchaseOrders_DataExtraction` becomes the Level 2.5 sub-project-name prefix and overrides a PascalCase title-derived short name. Capture initiative context without expanding SDD scope.

### Process Overview

Extract a structured table containing process full name; function/department; short description (operation, activity, outcome); required roles; schedule (frequency, business hours); volume and peaks; manual and automated average handling time; FTE count; exception-rate estimate; input; and output. Treat in-scope/out-of-scope as the SDD boundary and exclude out-of-scope items from the workflow inventory. For ranges such as "7-15 items," capture the range and use its upper bound for capacity planning.

### As-Is and To-Be Process

Capture both separately: **AS-IS** current steps, systems, manual handoffs, and pain points (do not skip); **TO-BE (high-level)** author/BA target and intended changes, not technical design. The SDD authors detailed TO-BE against the [need profile](sdd-generation-guide.md#step-35-synthesize-the-need)'s target KPI (cycle time, manual effort, quality, cost, throughput, compliance); do not copy AS-IS verbatim. Reconcile with high-level TO-BE; if they differ or one is absent, flag `[SME REVIEW]` and confirm with the user. If only one view exists, capture it and elicit the missing view.

### Detailed Process Map

Extract the PDD numbering scheme (for example, `1.1`, `1.5.A`, `1.5.B`), major flow, per-item loop boundaries, decisions, and application swimlanes. Record concrete Maestro Flow / Case / BPMN signals: parallel branches that fork/rejoin, event-based waits (message, signal, or timer), per-activity timeouts/deadlines, cancel/compensate-on-error steps, reusable subprocesses, and separate long-running-process invocations. Do not infer absent structure. If none exists, use a linear/branching pipeline (Flow); if structure exists without case stages/SLA, use BPMN structure (see [Product Selection Guide → Maestro disambiguation](product-selection-guide.md#level-1--primary-scope-selection)). Read flowchart images and verify them against detailed steps.

### Detailed Process Steps

For every step extract:

| Field | Content |
|---|---|
| Step number | PDD numbering (`1.1`, `1.5.A`, etc.). |
| Action description | What the robot does. |
| Application | Application used. |
| Expected result | State after completion. |
| Remarks | Errors, edge cases, and business rules. |

Extract embedded rules from remarks/descriptions and number them `BR-01`, `BR-02`, etc. Preserve typed rules and their `inputs → output` (`Deterministic`, `Reasoning: agent`, `Reasoning: person`, or document-language equivalents) for the SDD; they determine decision tables versus reasoning-list rows ([Business Rules Guide](business-rules-guide.md)). Collect field/variable/value references, complete value mappings, and implicit ordering constraints.

### Business Exceptions

Create a table with Exception ID (`B1`, `B2`, etc.; assign IDs if absent), name, trigger step, trigger condition (parameters, UI state, or data condition), and action (skip, retry, escalate, notify). Preserve catch-all default handlers and cross-reference exceptions that are also business rules.

### System Errors

Use the same table plus severity (if specified, such as `Sev-1`, `Sev-2`) and retry policy (count and backoff). If only generic errors are supplied, add `[DEFAULT]` entries for selector not found, browser crash, network timeout, and credential expiry.

### Application Details

Extract application name/version, language, login method, interface type (Web, desktop, terminal, API), access method (browser, URL, or application path), and special comments (routing, SPA behavior, etc.), including environment-specific URLs where available. For email, identify IMAP, Exchange/EWS, O365 Graph API, POP3, SMTP, or dedicated mailbox; if unspecified, `[SME REVIEW]`, never an O365 default. For FTP/SFTP, identify FTP, SFTP, or cloud storage (S3, Azure Blob), plus host/path when stated.

### Environment & Constraint Signals

**Mandatory scan on every PDD.** These signals gate product selection (see [Product Selection Guide → Constraint Gate](product-selection-guide.md#constraint-gate)):

| Signal | Extract; keyword signals |
|---|---|
| **Delivery model** | Automation Cloud, Automation Suite (self-hosted), or standalone Orchestrator; Automation Suite version if stated. Signals: "Automation Suite", "self-hosted", "on-prem", "on-premises", "air-gapped", "sovereign", "data residency", "Automation Cloud", `cloud.uipath.com`, internal base URLs. |
| **Product exclusions** | Ruled-out products and reasons: "we don't want <product>", "can't use", "not licensed for", "no cloud services", "Maestro is excluded". |
| **Orchestration constraints** | Preferred coordination for long-running orchestration: "Maestro", "Action Center", "state machine", "queues only", "Orchestrator queues". |
| **Signing modality** | Embedded e-signature versus local token-based qualified signing (download → sign locally → upload); signals include "e-signature", "DocuSign", "Adobe Sign", "qualified signature", "hardware token", "smart card", "signature verification". |
| **Document storage** | SharePoint, network share, Orchestrator storage bucket, ECM/DMS; never assume SharePoint. Signals include "SharePoint", "shared drive", "network drive", "file server", "DMS", "document archive". |
| **Robot attendance** | Attended/unattended and stated reason, such as physical 2FA. Signals include "attended", "unattended", "2FA", "hardware token", "OTP", "human present", "user's machine". |

Destinations: delivery model and exclusions → Phase 1 Step 0 skip rules and [Constraint Gate](product-selection-guide.md#constraint-gate); signing, storage, and attendance → §9 Application Inventory / §16 Deployment Environment (or product equivalents), with `[SME REVIEW]` when documents/signatures are involved but modality is ambiguous.

For human-only login (physical hardware 2FA token, smart card, biometric, or non-scriptable interactive sign-in), do not stop at `[SME REVIEW]`: emit the §9 *Interactive Authentication / Re-auth Handoff* subsection (RPA template), include the handoff contract, set §16 Robot type = Attended, and route the build to `uipath-rpa` per the [attended re-authentication pattern](attended-reauth-pattern-guide.md). A soft factor the robot can read (Google/MS/Okta TOTP, SMS/email code) is scripted by `uipath-rpa`; no handoff subsection.

### Development Details

Extract prerequisites (UiPath Studio version, packages, screen resolution, test setup), credentials (asset names, types, training values, notes), and password rotation/complexity/storage policies. Never hardcode training credentials; record them as Orchestrator assets.

### Appendix

Extract canonical test data using [Extract Canonical Examples](#extract-canonical-examples), selector references when provided, and value-mapping tables not covered in detailed steps.

### Reporting Requirements

Extract report type (Excel, email summary, dashboard data, PDF), frequency (real-time, daily, weekly, per-run), content (success counts, errors, processing times, item outcomes), recipients, and monitoring tool (Excel, Power BI, Orchestrator Insights, custom dashboard). Reporting signals a dedicated Reporting project in the decomposition decision (see [RPA Product Guide](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals) Level 2.5 Part A). If no reporting section exists but logging/monitoring is mentioned, mark reporting `[DEFAULT]` — Orchestrator logs only.

### Project Decomposition Signals

Capture this structured internal list for Level 2.5 Part A of the [RPA Product Guide](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals):

1. Distinct processing stages and boundaries (for example, collect emails → extract data → generate output).
2. Per-item transactional processing and start/end boundaries where one failure must not block others.
3. Document Understanding followed by Action Centre / human validation.
4. Multiple unrelated output channels (for example, XML to MQ, files to FTP, and email report).
5. Reporting requirements.
6. Queues, batches, or "items to process" mentions suggesting queue architecture.

## Gap Detection Checklist

After extraction, apply these results:

| Missing item | Required result |
|---|---|
| Business exceptions | `[DEFAULT]` rows for invalid credentials, malformed input data, missing required fields, and data validation failure; mark each `[DEFAULT]`. |
| System errors | `[DEFAULT]` rows for application unresponsive, element not found, timeout, and unhandled exception; mark each `[DEFAULT]`. |
| Process schedule/frequency | `[DEFAULT]` — assume on-demand trigger. |
| Volume/throughput | `[SME REVIEW]` — needed for capacity planning. |
| Retry counts on errors | `[DEFAULT]` — 3 retries with exponential backoff. |
| Element/activity timeouts | `[DEFAULT]` — 30s page loads, 10s element waits. |
| Max items per run | `[DEFAULT]` — 50 items safety cap. |
| Notification recipients for errors | `[SME REVIEW]` — needed for error escalation. |
| Amount/value thresholds | `[SME REVIEW]` — business decision. |
| Data retention requirements | `[SME REVIEW]` — compliance decision. |
| Credential rotation policy | `[DEFAULT]` — assume Orchestrator asset management. |
| Test data / canonical case | Run [Extract Canonical Examples](#extract-canonical-examples) first; use `[SME REVIEW]` only after every screenshot, inline-quoted string, and example table returns zero concrete values. |
| Reporting requirements | `[DEFAULT]` — Orchestrator logs only (no dedicated report). |
| Email protocol (when email is used) | `[SME REVIEW]` — needed for package selection (IMAP vs O365 vs Exchange). |
| Delivery model | Ask at Phase 1 Step 0 when unstated; never silently default. It gates product availability. |
| Document storage location (when the process handles documents) | `[SME REVIEW]` — never default to SharePoint. |
| Signing modality (when signatures are mentioned) | `[SME REVIEW]` — embedded e-signature versus local token-based signing changes architecture. |