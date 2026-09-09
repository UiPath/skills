# PDD Analysis Guide

Extract structured information from a PDD or any process-knowledge source for an SDD.

## Accepted Process-Knowledge Sources

Any artifact describing a business process is valid. Extract steps, applications, exceptions, business rules, data, AS-IS/TO-BE, and the need profile.

| Source | Ingest and notes |
|---|---|
| PDD (`.pdf` / `.docx` / `.md` / `.txt`) | Follow [Supported Input Formats](#supported-input-formats); usually richest. |
| Confluence / wiki / SharePoint | Ask the user to export or paste it, or run `WebFetch` on a reachable page. Session-connected Atlassian / Glean / Microsoft-365 connectors are best-effort. |
| BPMN (`.bpmn` XML, Signavio/Camunda export, or diagram image) | Run `Read` on XML/text or the diagram image; mine tasks, gateways, events, and lanes. It often represents TO-BE. |
| Meeting / Zoom transcript | Run `Read` on the file or pasted text, or use a session-connected transcript connector when available. Expect gaps. |
| SOP / work instructions / requirements / email thread | Use the applicable file-format procedure (`Read` / `docx-extract`). Scope varies. |

For less-structured sources, run heavier Phase 1 gap detection and use `AskUserQuestion` to fill missing steps, applications, exceptions, rules, and TO-BE information. Never invent business rules; flag gaps `[SME REVIEW]`.

## Supported Input Formats

| Format | Required action | Notes |
|---|---|---|
| Markdown (`.md`) | Run `Read` directly. | Structure is usually parseable. |
| Plain text (`.txt`) | Run `Read` directly. | For very large files, use `Read` offset/limit or the size strategy in [sdd-generation-guide.md Step 1](sdd-generation-guide.md#step-1-read-the-pdd). |
| PDF (`.pdf`) | Run `Read` with `pages` in chunks of up to 20 pages. | Read extracted text and visually inspect rendered screenshots/scanned pages. |
| Word (`.docx`) | Run `Bash` with `scripts/docx-extract.sh` (pandoc), then run `Read` on the markdown and extracted media. | Do not run `Read` directly on `.docx`. Parse complex raw HTML `<table>` output. Legacy `.doc` is unsupported; ask for `.docx`/PDF or pasted content. |
| Pasted text | Process conversation context. | For a large PDD, ask for section-by-section input. |

File ingestion requires `Read` and `Bash`; run `WebFetch` for remote pages. Connectors are best-effort; when unavailable, ask the user to export or paste content. These tools are in the skill's `allowed-tools`.

## Screenshots and Media

For every screenshot, record the application and screen; extract visible field names, buttons, navigation elements, and concrete values such as sample IDs, names, dates, expected outputs, and error messages. Do not extract selectors, XPath, CSS, coordinates, colors, or visual-layout details. Reference useful content in the process step's `Remarks`; use concrete values as test oracles per [Extract Canonical Examples](#extract-canonical-examples).

For unreadable `.emf` or `.wmf`, do not guess. Ask for a PNG export or mark every dependent extraction `[SME REVIEW]` with the filename.

## Extract Canonical Examples

Run this on every PDD before using `[SME REVIEW]` for test data. Scan screenshots, inline strings, example tables, validation examples, prose callouts, and error-message screenshots for concrete values.

For each value capture:

- **Source location:** page or section, including screenshot context.
- **Data role:** Input, Expected output, Validation rule, or Error message.
- **Field name:** corresponding §5 Data Definitions field.
- **Value:** literal value, quoted exactly.

Write values to §17 Testing Strategy → Canonical Test Case. Put inputs in the field/value table and outputs in a separate Expected Output subsection. Use them for business-rule assertions such as `BR-04: SHA1(input) == '<canonical hash>'`, the first happy-path test row, and output-format regex or other validation oracles.

A canonical example is fact, not `[SME REVIEW]`. Apply `[SME REVIEW]` only after scanning every screenshot, table, step description, appendix, and other surface and finding no concrete value. Before completing Phase 1, verify that every screenshot was visually inspected for values; every inline-quoted string and example-table row was captured; §17 contains a canonical input set and expected output or the genuine no-example fallback; and hash-, regex-, and format-shaped values are paired with the rule they validate, such as `SHA1 output: bde2c596...` → BR-04.

## Reading Strategy

Use the Table of Contents, then read: (1) Table of Contents, (2) Process Overview, including purpose, frequency, volume, and applications, (3) Detailed Process Steps, (4) Exceptions and Errors, and (5) Application Details and Credentials. Section names and numbers vary.

## Extraction Rules

### Introduction

Extract the official process name, objective, department/function, and explicitly named contacts. Put named roles only—SME / Process Owner, Solution Architect, Business Analyst, Developer(s), Project Manager—in the RPA SDD §1 Delivery Team table. Omit unnamed roles and do not invent them.

Capture an explicitly named Master project / process full name verbatim. A value such as `PurchaseOrders_DataExtraction` becomes the Level 2.5 sub-project naming prefix and overrides a PascalCase name derived from the title. Capture initiative context without expanding SDD scope.

### Process Overview

Extract a structured table containing process full name; function/department; short description; roles; schedule and business hours; volume and peak periods; manual and target automated handling time; FTE count; exception-rate estimate; input; and output. Keep in-scope and out-of-scope boundaries; excluded work must not enter the workflow inventory. Record vague ranges such as `7-15 items`; use the upper bound for capacity planning.

### As-Is and To-Be Process

Keep both views separate. AS-IS contains current steps, systems, manual handoffs, and pain points. TO-BE contains the source author's high-level target and proposed changes. The SDD authors the detailed technical TO-BE and re-engineers it for the [need profile](sdd-generation-guide.md#step-35-synthesize-the-need)'s KPI: cycle time, manual effort, quality, cost, throughput, or compliance. Reconcile with the source TO-BE; flag `[SME REVIEW]` and confirm differences or an absent view. If only one view exists, capture it and elicit the other.

### Detailed Process Map

Extract source numbering, major-flow sequence, per-item loop boundaries, decisions, and application swimlanes. Record control-flow signals for Maestro Flow / Case / BPMN selection: parallel branches that fork/rejoin, event-based waits for messages/signals/timers, activity timeouts/deadlines, cancellation or compensation on error, reusable subprocesses, and separate long-running process invocations. Do not infer absent structure.

For a flowchart image, read it and verify it against detailed steps. Use swimlanes for application mapping. No listed control-flow structure means a linear/branching pipeline (Flow); structure without case stages/SLA means BPMN (see [Product Selection Guide → Maestro disambiguation](product-selection-guide.md#level-1--primary-scope-selection)).

### Detailed Process Steps

For every step capture:

| Field | Content |
|---|---|
| Step number | Source numbering such as 1.1 or 1.5.A. |
| Action description | What the robot does. |
| Application | System used. |
| Expected result | State that must hold afterward. |
| Remarks | Errors, edge cases, rules, and screenshot references. |

Extract embedded business rules and number them `BR-01`, `BR-02`, etc.; collect field/variable names and data values; capture complete value mappings; and record implicit ordering constraints.

### Business Exceptions

Extract Exception ID (source ID such as B1; assign one if absent), name, trigger step, trigger condition (parameters, UI state, or data condition), and action (skip, retry, escalate, notify, or other required response). Preserve catch-all handlers. Cross-reference exceptions that are also business rules, such as amount thresholds.

### System Errors

Use the same table as business exceptions and add severity and retry policy, including retry count and backoff when specified. If only generic errors are given, add `[DEFAULT]` rows for selector not found, browser crash, network timeout, credential expiry, and unhandled exception as applicable.

### Application Details

Extract application name/version, language, login method, interface type, access method, URL/path, and special behaviors such as SPA routing. Record environment-specific URLs when available.

For email, extract IMAP, Exchange/EWS, O365 Graph API, POP3, SMTP, or dedicated-mailbox signals. If unspecified, mark `[SME REVIEW]`; never default to O365. For file transfer, distinguish FTP, SFTP, and cloud storage such as S3 or Azure Blob; capture host/path when stated.

### Environment & Constraint Signals

Run this mandatory scan on every PDD; these signals gate product selection via [Constraint Gate](product-selection-guide.md#constraint-gate).

| Signal | Extract |
|---|---|
| Delivery model | Automation Cloud, Automation Suite/self-hosted/standalone Orchestrator, version, air-gapped/sovereign/data-residency constraints, or relevant base URLs. |
| Product exclusions | Excluded products and reasons, including licensing or cloud restrictions. |
| Orchestration constraints | Preferred coordination such as Maestro, Action Center, state machine, queues only, or Orchestrator queues. |
| Signing modality | Embedded e-signature service versus local token-based qualified signing: download → sign locally → upload. |
| Document storage | SharePoint, shared/network drive, file server, storage bucket, ECM/DMS, or archive. Never assume SharePoint. |
| Robot attendance | Attended/unattended and reason, including 2FA, hardware token, OTP, human presence, or user's machine. |

Delivery model and exclusions feed Phase 1 Step 0 skip rules and the [Constraint Gate](product-selection-guide.md#constraint-gate). Signing, storage, and attendance feed §9 Application Inventory / §16 Deployment Environment (or product equivalents); use `[SME REVIEW]` when ambiguous.

For human-only login—physical hardware 2FA, smart card, biometric, or non-scriptable interactive sign-in—emit §9 *Interactive Authentication / Re-auth Handoff* with its handoff contract, set §16 Robot type = Attended, and route the build to `uipath-rpa` per the [attended re-authentication pattern](attended-reauth-pattern-guide.md). Script a soft factor the robot can read, such as Google/MS/Okta TOTP or an SMS/email code; no handoff subsection is required.

### Development Details

Extract UiPath Studio version, packages, screen resolution, test-environment setup, credential asset names/types/values/notes for training, and password rotation, complexity, and storage policies. Never hardcode training credentials; record them as Orchestrator assets.

### Appendix

Apply [Extract Canonical Examples](#extract-canonical-examples). Also extract selector references when present and value mappings not captured in detailed steps.

### Reporting Requirements

Extract report type—Excel, email summary, dashboard data, or PDF—frequency, content, recipients, and monitoring tool such as Excel, Power BI, Orchestrator Insights, or a custom dashboard. Search beyond a dedicated reporting section. Reporting signals a dedicated Reporting project in the decomposition decision (see [RPA Product Guide](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals) Level 2.5 Part A). If only logging or monitoring is mentioned and no report exists, mark reporting `[DEFAULT]` — Orchestrator logs only.

### Project Decomposition Signals

Capture a structured internal list for Level 2.5 Part A of the [RPA Product Guide](rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals):

1. Distinct stages, such as collect emails → extract data → generate output; record boundaries.
2. Per-item transactional processing where one failure should not block others; record loop boundaries.
3. Document Understanding extraction followed by Action Centre / human validation.
4. Multiple unrelated output channels, such as XML to MQ, files to FTP, and email reporting.
5. Reporting requirements.
6. Queues, batches, or items to process.

## Gap Detection Checklist

After extraction, apply these fallbacks:

| Item | If missing |
|---|---|
| Business exceptions | Add `[DEFAULT]` rows for invalid credentials, malformed input, missing required fields, and data validation failure, based on application types. |
| System errors | Add `[DEFAULT]` rows for unresponsive applications, element not found, timeout, and unhandled exception. |
| Process schedule/frequency | `[DEFAULT]` — assume on-demand trigger. |
| Volume/throughput | `[SME REVIEW]` — required for capacity planning. |
| Retry counts | `[DEFAULT]` — 3 retries with exponential backoff. |
| Element/activity timeouts | `[DEFAULT]` — 30s page loads, 10s element waits. |
| Max items per run | `[DEFAULT]` — 50 items safety cap. |
| Error notification recipients | `[SME REVIEW]` — required for escalation. |
| Amount/value thresholds | `[SME REVIEW]` — business decision. |
| Data retention | `[SME REVIEW]` — compliance decision. |
| Credential rotation | `[DEFAULT]` — assume Orchestrator asset management. |
| Test data / canonical case | Run [Extract Canonical Examples](#extract-canonical-examples) first; use `[SME REVIEW]` only when all screenshots, inline strings, and example tables contain zero concrete values. |
| Reporting requirements | `[DEFAULT]` — Orchestrator logs only; no dedicated report. |
| Email protocol when email is used | `[SME REVIEW]` — required for IMAP vs O365 vs Exchange package selection. |
| Delivery model | Ask at Phase 1 Step 0 when unstated; never silently default because it gates product availability. |
| Document storage when documents are handled | `[SME REVIEW]` — never default to SharePoint. |
| Signing modality when signatures are mentioned | `[SME REVIEW]` — embedded e-signature versus local token-based signing changes architecture. |