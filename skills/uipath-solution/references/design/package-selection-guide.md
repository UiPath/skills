# Package Selection Guide

Load this guide whenever an SDD section needs to list dependencies — typically §14 Packages in the RPA template, the Packages subsection of the Case template, or the Tool Packages table in the Agent template. Use it to infer packages from the Application Inventory (§9 in the RPA template) and from the process steps.

Two things this guide disambiguates:

1. **NuGet packages vs Integration Service connectors.** They solve overlapping problems but live in different places. See [Integration Service Connectors vs NuGet Packages](#integration-service-connectors-vs-nuget-packages).
2. **Per-product dependency managers.** RPA/Case use NuGet. Coded Apps use **npm** (not NuGet). Agents declare C# tool packages (subset of NuGet). API Workflows use Integration Service connector references, not packages. See [Per-Product Dependency Manager](#per-product-dependency-manager).

## Core Packages (always include for RPA)

| Package | Purpose | Required |
|---|---|---|
| `UiPath.System.Activities` | Core activities: data tables, files, Orchestrator, workflow operators | Yes — every RPA project |
| `UiPath.UIAutomation.Activities` | UI automation (web, desktop) | Yes if §9 contains any UI application |
| `UiPath.Testing.Activities` | Assertions, VerifyExpression, VerifyControlAttribute | Yes for RPA Test Automation sub-type |

## Application Type → Package Matrix

Use this matrix to infer packages from §9 Application Inventory. Match on the **Interface** and **Access Method** columns. If an application matches multiple rows, install all listed packages.

### Email

| Access Method in §9 | Package(s) | Required Assets | Common Pitfalls |
|---|---|---|---|
| IMAP | `UiPath.Mail.Activities` | Credential asset (username + app password); server host + port as text assets | Do not default to O365 — check PDD for protocol. IMAP needs app password, not user password, on 2FA accounts. |
| POP3 | `UiPath.Mail.Activities` | Credential asset; host + port | Rarely used — prefer IMAP or Graph API if available. |
| Exchange / EWS | `UiPath.Mail.Activities` | Credential asset; EWS URL | Being deprecated by Microsoft — confirm the tenant still allows EWS. |
| O365 Graph API | `UiPath.MicrosoftOffice365.Activities` | App registration client ID + tenant ID (text assets); certificate or secret (credential asset) | Different activity set from `UiPath.Mail.Activities`. Requires admin consent for mail scopes. |
| Gmail API | `UiPath.GSuite.Activities` | OAuth client JSON (credential asset) | Integration Service alternative exists — prefer the connector unless the PDD requires specific activity packages. |

### Microsoft Office files

| File Type | Package | Notes |
|---|---|---|
| Excel (.xlsx, .xlsm, .xlsb) | `UiPath.Excel.Activities` | Modern "Use Excel File" activities preferred over classic. |
| Excel via Office 365 / OneDrive | `UiPath.MicrosoftOffice365.Activities` | Same package as O365 mail. |
| Word | `UiPath.Word.Activities` | |
| PowerPoint | `UiPath.Presentations.Activities` | |

### Document Understanding

| Scenario | Packages | Notes |
|---|---|---|
| PDF text extraction (digital PDFs) | `UiPath.PDF.Activities` | No OCR required. |
| PDF OCR / scanned documents | `UiPath.PDF.Activities` + `UiPath.IntelligentOCR.Activities` | OCR engine is a separate dependency. |
| Document Understanding framework (classify → extract → validate) | `UiPath.IntelligentOCR.Activities` + `UiPath.DocumentUnderstanding.ML.Activities` | Required for Taxonomy Manager + Data Extraction Scope. |
| Action Centre validation for DU | `UiPath.Persistence.Activities` + `UiPath.FormActivityLibrary` | Needed for `WaitForFormTaskAndResume` on DU validation tasks. |

### SaaS platforms (non–Integration Service path)

| Platform | Package | Use When |
|---|---|---|
| SAP GUI | `UiPath.SAP.BAPI.Activities` | BAPI function calls (RFC). |
| SAP Fiori (web) | `UiPath.UIAutomation.Activities` | UI automation — no SAP package. |
| Salesforce (native activities) | `UiPath.Salesforce.Activities` | Only when Integration Service is not available. Prefer the connector. |
| ServiceNow | `UiPath.ServiceNow.Activities` | Only when Integration Service is not available. |
| Workday | `UiPath.Workday.Activities` | Only when Integration Service is not available. |

> For any of the above, if the PDD mentions "Integration Service" or a preconfigured connector slug, skip the NuGet package — see the next section.

### Web, API, and integration primitives

| Scenario | Package | Notes |
|---|---|---|
| Generic REST calls (HTTP verbs, headers, auth) | `UiPath.WebAPI.Activities` | `HTTPRequest` / `NetHTTPRequest` activity. |
| Web UI automation | `UiPath.UIAutomation.Activities` | Same package as desktop UI. |
| Modern browsers (Edge, Chrome, Firefox) via Selenium | `UiPath.UIAutomationModern.Activities` | If using the modern experience. Studio installs alongside UIAutomation. |
| Terminal / mainframe (3270, 5250, VT) | `UiPath.Terminal.Activities` | |
| FTP / SFTP | `UiPath.FTP.Activities` | |

### Database

| Scenario | Package | Notes |
|---|---|---|
| SQL Server, Oracle, MySQL, PostgreSQL | `UiPath.Database.Activities` | Uses ODBC/OLEDB under the hood. Connection string asset recommended. |
| NoSQL (Mongo, Cosmos) | `UiPath.WebAPI.Activities` via REST | No first-party NoSQL package — call the REST API. |

### Orchestrator and persistence

| Scenario | Package | Notes |
|---|---|---|
| Queue items, assets, storage buckets, processes | `UiPath.System.Activities` | Core package — no extra install. |
| Long-running workflows, Form Tasks, External Tasks | `UiPath.Persistence.Activities` | Required for `CreateFormTask`, `WaitForFormTaskAndResume`, `CreateExternalTask`. |
| Form Tasks with form.io forms | `UiPath.Persistence.Activities` + `UiPath.FormActivityLibrary` | Both required. |

### Credentials and security

| Scenario | Package | Notes |
|---|---|---|
| Robot-scoped credential retrieval (`GetRobotCredential`, `GetRobotAsset`) | `UiPath.System.Activities` | Core — already installed. |
| Credential Provider integrations (CyberArk, HashiCorp, Azure Key Vault) | Configured in Orchestrator — no package | Robot fetches credentials via Orchestrator's credential store. |

## Integration Service Connectors vs NuGet Packages

These two mechanisms both provide access to third-party systems, but they are **not interchangeable**. Pick the right one for each application, and declare it in the right place.

### Decision

1. If Orchestrator has a configured **Integration Service** connection for the target system AND the PDD does not require specific native-package activities → use the **Integration Service connector**.
2. Otherwise → use the matching **NuGet package**.
3. If both paths are listed in §9 for the same application, pick Integration Service for the primary path and note the NuGet package as a fallback in §14.

### Side-by-side

| Aspect | Integration Service Connector | NuGet Package |
|---|---|---|
| Where it's configured | Orchestrator → Integration Service → Connections | Project's `project.json` dependencies |
| How it's referenced | Slug (e.g., `salesforce`, `service-now`, `gmail`) in the Integration Service activity | `Using` namespace + activity from the installed package |
| Authentication | Stored in the Connection (OAuth, API key) | Credential asset + in-workflow auth logic |
| Deployment | No per-robot install — lives in Orchestrator | Packaged into the .nupkg and pulled on the robot |
| Runtime dependency | Robot must have the Integration Service activity package installed (`UiPath.IntegrationService.Activities`), which is a single dependency regardless of how many connectors are used | One package per third-party system |
| Listed in SDD where | §9 Access Method as `Integration Service — <CONNECTOR_SLUG>` | §14 Packages table |

### Do not

- **Do not** list the connector slug in §14 Packages. Slugs are not NuGet packages.
- **Do not** install `UiPath.Salesforce.Activities` when the design uses the Salesforce Integration Service connector — they are parallel paths, not complementary.
- **Do not** assume every Orchestrator instance has Integration Service enabled. Confirm during Phase 1 scoping; default to the NuGet package path if in doubt.

### Example — Salesforce via Integration Service

§9 Application Inventory row:

| # | Application | Interface | Access Method | Role | Interaction Pattern |
|---|---|---|---|---|---|
| 3 | Salesforce | API | `Integration Service — salesforce` | Target | Write |

§14 Packages — add only the Integration Service host package, not `UiPath.Salesforce.Activities`:

| Package | Version | Purpose |
|---|---|---|
| `UiPath.IntegrationService.Activities` | Latest | Runtime host for Integration Service connector activities |

### Example — Salesforce via NuGet native package

§9 Application Inventory row:

| # | Application | Interface | Access Method | Role | Interaction Pattern |
|---|---|---|---|---|---|
| 3 | Salesforce | API | OAuth 2.0 direct (native package) | Target | Write |

§14 Packages:

| Package | Version | Purpose |
|---|---|---|
| `UiPath.Salesforce.Activities` | Latest | Native Salesforce activities — used because Integration Service connector not available in this tenant |

## Per-Product Dependency Manager

SDD templates across the 6 products use different dependency mechanisms. List dependencies under the correct mechanism; do not cross them.

| Product | Dependency Manager | Where Declared in SDD | Notes |
|---|---|---|---|
| RPA (Process, Library, Test Automation) | NuGet | §14 Packages table | Covered by this guide. |
| Case Management | NuGet | Packages subsection in the Case template | Case-specific packages: `UiPath.Persistence.Activities`, `UiPath.FormActivityLibrary` for HITL tasks. |
| Maestro Flow | Connector references + RPA step packages | Integrated Components section | Flow itself has no packages. Each RPA step called from the flow uses the RPA template's §14. |
| Agents | C# tool packages (subset of NuGet) | Tool Packages table in the Agent template | Declare only packages whose activities are wrapped as Agent tools. |
| Coded Apps | **npm** (not NuGet) | Dependencies subsection in the Coded App template | Use `package.json` semantics. Do not list NuGet packages. |
| API Workflows | Integration Service connector references | Connectors section in the API Workflow template | API Workflows are hosted in Orchestrator — no package file. |

## Selection Checklist

Before finalising a Packages table:

1. Every application in §9 has at least one matching package OR an Integration Service connector row.
2. Core packages (`UiPath.System.Activities`; `UiPath.UIAutomation.Activities` if any UI) are present.
3. Every PDD step with "download", "attach", "send email" has an email package.
4. Every PDD step with "extract from PDF", "read invoice" has the DU / PDF packages.
5. Every PDD step with "approval", "action centre", "long-running" has `UiPath.Persistence.Activities`.
6. No Integration Service connector slug is listed in §14 by mistake.
7. For Master Project: a separate §14 table per sub-project. A Dispatcher that only downloads email does not need Excel packages.
8. For Coded App: the dependency list uses npm package names (e.g., `@uipath/apps-sdk`), not NuGet.

## Pitfalls

1. **Guessing package versions.** Default to `Latest` in SDDs. Version resolution happens at build time (`uip` / Studio) — the SDD should not pin versions unless the PDD explicitly requires a specific feature gate.
2. **Listing `UiPath.Mail.Activities` and `UiPath.MicrosoftOffice365.Activities` together "just in case".** They provide overlapping activities and will confuse implementers. Pick one per email access method.
3. **Mixing IntegrationService slug names with NuGet package names.** The slug `salesforce` is not a package; the package is `UiPath.Salesforce.Activities`.
4. **Forgetting `UiPath.Persistence.Activities` for HITL.** Any workflow using `WaitForFormTaskAndResume`, `CreateFormTask`, or `CreateExternalTask` needs it. The Persistence package also requires `supportsPersistence: true` in `project.json` — call out in §14.
5. **Listing NuGet packages for Coded App dependencies.** Coded Apps are TypeScript/React — the dependency manager is npm, and the template has a separate section.
6. **Omitting Testing packages in RPA Test Automation sub-type.** Test Automation projects require `UiPath.Testing.Activities` for assertions; omitting it breaks Test Manager integration.
