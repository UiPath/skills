# PDD Analysis Guide

How to extract structured information from a PDD — or any other process-knowledge source — in any format.

## Accepted process-knowledge sources

The input need not be a formal PDD. **Any artifact that describes a business process** is a valid basis for an SDD — extract the *same structured model* from it (steps, applications, exceptions, business rules, data, as-is/to-be, and the need profile):

| Source | How to ingest | Notes |
|---|---|---|
| **PDD** (`.pdf` / `.md` / `.txt`) | per Supported Input Formats below | richest, most structured source |
| **Confluence / wiki / SharePoint page** | user exports (→ md/pdf) or pastes it; or web-fetch a reachable page; a session-connected Atlassian / Glean / Microsoft-365 connector also works (best-effort) | often an SOP or process write-up |
| **BPMN model** (`.bpmn` XML, Signavio/Camunda export, or a diagram image) | read the XML/text directly, or read the diagram image | already a process map — mine its tasks, gateways, events, lanes; it often encodes the *to-be* |
| **Meeting / Zoom transcript** | read the text file or pasted content; or a session-connected transcript connector (best-effort) | least structured — expect heavy gaps |
| **SOP / work instructions / requirements doc / email thread** | per its file format (file-read tool) | scope varies |

**Less-structured sources need more elicitation.** A formal PDD is near-complete; a transcript or a thin wiki page is not — run heavier Phase 1 gap-detection and structured questions to fill missing steps, applications, exceptions, rules, and the to-be. Never invent business rules; flag gaps `[SME REVIEW]`.

## Supported Input Formats

| Format | Tool | How to Read | Notes |
|---|---|---|---|
| Markdown (`.md`) | file-read tool | Read the file directly. | Easiest — structure already parseable. |
| Plain text (`.txt`) | file-read tool | Read the file directly (same as Markdown). | No conversion. For a very large file, read it by line range or use the size strategy in [design-guide.md Step 1](../design/design-guide.md#step-1-read-the-pdd). |
| PDF (`.pdf`) | file-read tool | Read it by page range, in chunks of up to 20 pages. | Text is extracted; screenshots and scanned/image-only pages render as images — Read them visually (see "Handling Screenshots"). When pages do not render, or a render is too small to read a value, extract the embedded images and text with any tool the machine has, in a scratch folder — a PDD is unreadable only when nothing can extract it. |
| Pasted text | (conversation) | Process from the conversation context. | Ask the user to paste section by section if the PDD is large. |

File-based ingestion needs only a **file-read tool** (Markdown, `.txt`, PDF, images/media); remote pages need **web fetch**. Session-connected MCP connectors (Atlassian / Glean / Microsoft 365 / transcript) are best-effort extras — when absent, ask the user to export or paste the content.

## Handling Screenshots

When you encounter screenshots in the PDD:

1. **Note** the application name and screen shown.
2. **Extract** visible field names, button labels, and navigation elements — these become data field references and process step descriptions.
3. **Do NOT extract** selectors, XPath, CSS, coordinates, colors, or visual layout details — these are determined at development time, not from static images.
4. **Reference** the screenshot content in the relevant process step's "Remarks" field if useful.
5. **DO extract concrete data values** shown in the screenshot — sample IDs, names, dates, expected outputs, error messages. These are oracles for the test strategy, not selectors. See "Extract Canonical Examples" below.
6. **Unreadable media formats (.emf, .wmf):** file-read tools cannot render these. Do not guess their content — ask the user for a PNG export of the figure, or mark every extraction that depended on it as `[SME REVIEW]` naming the file.

## Extract Canonical Examples

**Mandatory step. Run this on every PDD before falling back to `[SME REVIEW]` for test data.** PDDs almost always carry concrete example values somewhere — most agents miss them because the values live in screenshots, inline strings, or example tables rather than in a dedicated "Test Data" section.

### Where to look

Scan every surface for concrete values — sample IDs, names, codes, dates, amounts, computed outputs, statuses, verbatim error texts:

| Surface | What to look for |
|---|---|
| **Screenshots** | Values filled into forms and lists (inputs); results, statuses and computed values (expected outputs); error dialogs. Read data-bearing screenshots first; pure navigation screens (logins, menus) carry no values |
| **Embedded files** | Sample documents, mails or spreadsheets attached inside the PDD — often the real canonical data |
| **Step descriptions** | Quoted literals that name a value rather than a column; "for example" / "e.g." callouts |
| **Example and appendix tables** | Rows whose cells are concrete values, not placeholders |

### What to extract and where it goes

For every value: its source location (page or section, which screenshot), its data role (input, expected output, validation example, error text), the §5 field it maps to, and the value exactly as the PDD shows it. Write them into §17 Testing Strategy → Canonical Test Case (inputs as field/value rows, an Expected Output subsection for outputs). They are the oracles of §4 business rules (`BR-04: SHA1(<input>) == <expected hash>`), the first happy-path row and the output-format checks.

**A canonical example in the PDD is fact, not an `[SME REVIEW]` item.** The fallback applies only when the whole PDD — screenshots, embedded files, tables, steps, appendices — has been scanned and no value exists for the field. A pair the agent cannot reproduce (the stated output does not follow from the stated input by the stated rule) is recorded as the PDD gives it, with an `[SME REVIEW]` item naming the mismatch. An unreadable figure (EMF, an illegible render) that carries values is an `[SME REVIEW]` item naming the figure; an icon or decoration is not.

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

### As-Is and To-Be Process

A PDD (and most process-knowledge sources) carries two views — extract **both**, kept separate:

- **AS-IS** — the current process as performed today (steps, systems, manual handoffs, pain points). Essential for understanding the process holistically; skipping it pushes cost to UAT scope-creep.
- **TO-BE (high-level)** — the target the author/BA proposed (what changes, what gets automated). A high-level *intent*, not the technical design.

The SDD authors the **detailed TO-BE** — the technical solution design. **Do not copy the as-is verbatim into the to-be:** re-engineer the process for automation against the [need profile](../design/design-guide.md#step-35-synthesize-the-need)'s target KPI (cycle time, manual effort, quality, cost, throughput, compliance). Reconcile with the PDD's high-level to-be; where they differ, or the to-be is absent, flag `[SME REVIEW]` and confirm with the user. When a source carries only one view (a transcript describing today's process = as-is only; a BPMN model of the target = to-be only), capture what's present and elicit the missing side.

### Detailed Process Map

Extract:
- **Step numbering scheme** — usually 1.1, 1.2, ..., 1.5.A, 1.5.B, etc.
- **High-level flow** — the sequence of major steps
- **Loop boundaries** — where the per-item processing starts and ends
- **Decision points** — any branching logic in the flow
- **Control-flow structure** — the orchestration shape, for the Maestro Flow / Case / BPMN choice: parallel branches that fork and rejoin, event-based waits (wait for a message, signal, or timer), per-activity timeouts / deadlines, steps that cancel or compensate on error, reusable sub-process groupings, and steps that invoke a separate long-running process. None present → linear/branching pipeline (Flow). Present without case stages/SLA → BPMN structure (see [Product Selection Guide → Maestro disambiguation](product-selection-guide.md#level-1--primary-scope-selection)). Note each concretely; never infer structure the PDD does not describe.

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
- **Typed business rules** — a PDD Business Rules table may give each rule a type (`Deterministic`, `Reasoning: agent`, `Reasoning: person`, possibly in the document's language) and its `inputs → output`. Carry both into the SDD: they decide whether the rule becomes a decision table or a reasoning-list row ([Business Rules Guide](../design/business-rules-guide.md)).
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
- **Email protocol** — when email is an application, extract the protocol signal: IMAP, Exchange/EWS, O365 Graph API, POP3, SMTP. Look for keywords like "IMAP", "Exchange", "O365", "Graph API", "dedicated mailbox". If not specified: an unattended run on Microsoft 365 mailboxes defaults to the Outlook 365 connector (Graph) — never the desktop Outlook client, which needs a signed-in profile on every robot — and an unknown mail platform defaults to IMAP/SMTP; either default is `[DEFAULT]` with an `[SME REVIEW]` item to confirm.
- **FTP/SFTP** — note whether the PDD specifies FTP, SFTP, or cloud storage (S3, Azure Blob). Capture host/path if mentioned.

### Environment & Constraint Signals

**Mandatory scan on every PDD.** These constraints gate product selection (see [Product Selection Guide → Constraint Gate](product-selection-guide.md#constraint-gate)). Missing them produces architectures the customer cannot run — the most expensive SDD defect.

| Signal | What to extract | Keyword signals |
|---|---|---|
| **Delivery model** | Automation Cloud vs Automation Suite (self-hosted) vs standalone Orchestrator. Capture the Automation Suite version if stated. | "Automation Suite", "self-hosted", "on-prem", "on-premises", "air-gapped", "sovereign", "data residency", "Automation Cloud", `cloud.uipath.com`, internal base URLs |
| **Product exclusions** | Products the client rules out, with the stated reason. | "we don't want <product>", "can't use", "not licensed for", "no cloud services", "Maestro is excluded" |
| **Orchestration constraints** | Preferred coordination style when the process needs long-running orchestration. | "Maestro", "Action Center", "state machine", "queues only", "Orchestrator queues" |
| **Signing modality** | How documents get signed: embedded e-signature service vs token-based qualified signing in a local reader (download → sign locally → upload). | "e-signature", "DocuSign", "Adobe Sign", "qualified signature", "hardware token", "smart card", "signature verification" |
| **Document storage** | Where documents live: SharePoint, network share, Orchestrator storage bucket, ECM/DMS. **Never assume SharePoint.** | "SharePoint", "shared drive", "network drive", "file server", "DMS", "document archive" |
| **Robot attendance** | Attended vs unattended, and the reason when stated (e.g., physical 2FA token requires a human at the machine). | "attended", "unattended", "2FA", "hardware token", "OTP", "human present", "user's machine" |

Destinations:

- Delivery model + product exclusions → the skip rule of [platform-availability-guide.md § Resolving the Delivery Model](platform-availability-guide.md#resolving-the-delivery-model) and the [Constraint Gate](product-selection-guide.md#constraint-gate).
- Signing modality, document storage, robot attendance → §9 Application Inventory / §16 Deployment Environment (or product equivalents); `[SME REVIEW]` when the PDD handles documents or signatures but leaves the modality ambiguous.

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
- If the PDD mentions reporting, this is a signal for a dedicated Reporting project in the project decomposition decision (see [RPA Product Guide](../design/rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals) Level 2.5 Part A).
- If the PDD has no reporting section but mentions logging or monitoring, mark reporting as `[DEFAULT]` — Orchestrator logs only.

### Project Decomposition Signals

While extracting, record in the internal model every signal of [RPA Product Guide → Level 2.5 Part A](../design/rpa-product-guide.md#level-25-part-a--rpa-decomposition-signals) — stage boundaries, where per-item processing starts and ends, DU with human validation, multiple output channels, reporting — plus any mention of queues, batches or "items to process". Product selection decides from them.

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
| Email protocol (when email is used) | `[DEFAULT]` per § Application Details (Outlook 365 connector for Microsoft 365 mailboxes, IMAP/SMTP otherwise) + an `[SME REVIEW]` item |
| Delivery model | Asked at Phase 1 Step 0 when the PDD doesn't state it — never silently default. Gates product availability. |
| Document storage location (when the process handles documents) | `[SME REVIEW]` — never default to SharePoint |
| Signing modality (when signatures are mentioned) | `[SME REVIEW]` — embedded e-signature service vs local token-based signing changes the architecture |
