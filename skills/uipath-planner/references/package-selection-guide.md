# Package Selection Guide

Load this guide when an SDD lists dependencies: usually §14 Packages in the RPA template, package/tool tables in Agent templates, or downstream specialist package notes. Case Management uses the Case Definition Blueprint shared with `uipath-maestro-case`; it has no planner-only Packages subsection, and dependencies surface in §4 Integrations.

Distinguish NuGet packages, Integration Service connectors, and product-specific dependency managers. See [Integration Service Connectors vs NuGet Packages](#integration-service-connectors-vs-nuget-packages) and [Per-Product Dependency Manager](#per-product-dependency-manager).

## Core Packages (always include for RPA)

| Package | Use | Required |
|---|---|---|
| `UiPath.System.Activities` | Data tables, files, Orchestrator, workflow operators | Every RPA project |
| `UiPath.UIAutomation.Activities` | Web/desktop UI automation | Any UI application in §9 |
| `UiPath.Testing.Activities` | Assertions, VerifyExpression, VerifyControlAttribute | RPA Test Automation sub-type |

## Application Type → Package Matrix

Infer packages from §9 Application Inventory by Interface and Access Method. If an application matches multiple rows, install all listed packages.

### Email

| Access Method | Package | Assets/guidance |
|---|---|---|
| IMAP | `UiPath.Mail.Activities` | Credential (username + app password), host and port text assets; do not default to O365; check PDD; IMAP needs app password, not user password, on 2FA accounts. |
| POP3 | `UiPath.Mail.Activities` | Credential, host and port; rare—prefer IMAP or Graph API when available. |
| Exchange / EWS | `UiPath.Mail.Activities` | Credential and EWS URL; confirm tenant allows EWS because Microsoft is deprecating it. |
| O365 Graph API | `UiPath.MicrosoftOffice365.Activities` | App registration client ID and tenant ID text assets; certificate or secret credential; different activity set from `UiPath.Mail.Activities`; admin consent for mail scopes. |
| Gmail API | `UiPath.GSuite.Activities` | OAuth client JSON credential; prefer Integration Service unless the PDD requires specific activity packages. |

### Microsoft Office files

| File type/access | Package | Guidance |
|---|---|---|
| Excel (`.xlsx`, `.xlsm`, `.xlsb`) | `UiPath.Excel.Activities` | Prefer modern “Use Excel File” over classic activities. |
| Excel via Office 365 / OneDrive | `UiPath.MicrosoftOffice365.Activities` | O365 package. |
| Word | `UiPath.Word.Activities` | |
| PowerPoint | `UiPath.Presentations.Activities` | |

### Document Understanding

| Scenario | Packages | Guidance |
|---|---|---|
| Digital PDF text extraction | `UiPath.PDF.Activities` | No OCR required. |
| PDF OCR/scanned documents | `UiPath.PDF.Activities` + `UiPath.IntelligentOCR.Activities` | OCR is separate. |
| DU framework (classify → extract → validate) | `UiPath.IntelligentOCR.Activities` + `UiPath.DocumentUnderstanding.ML.Activities` | Required for Taxonomy Manager + Data Extraction Scope. |
| Action Centre validation for DU | `UiPath.Persistence.Activities` + `UiPath.FormActivityLibrary` | Required for `WaitForFormTaskAndResume` on DU validation tasks. |

### SaaS platforms (non–Integration Service path)

| Platform | Package | Use |
|---|---|---|
| SAP GUI | `UiPath.SAP.BAPI.Activities` | BAPI function calls (RFC). |
| SAP Fiori (web) | `UiPath.UIAutomation.Activities` | UI automation; no SAP package. |
| Salesforce (native activities) | `UiPath.Salesforce.Activities` | Only when Integration Service is unavailable; prefer the connector. |
| ServiceNow | `UiPath.ServiceNow.Activities` | Only when Integration Service is unavailable. |
| Workday | `UiPath.Workday.Activities` | Only when Integration Service is unavailable. |

If the PDD mentions “Integration Service” or a preconfigured connector slug, skip the NuGet package and use [the decision below](#integration-service-connectors-vs-nuget-packages).

### Web, API, and integration primitives

| Scenario | Package | Guidance |
|---|---|---|
| Generic REST calls (HTTP verbs, headers, auth) | `UiPath.WebAPI.Activities` | `HTTPRequest` / `NetHTTPRequest` activity. |
| Web UI automation | `UiPath.UIAutomation.Activities` | Same package as desktop UI. |
| Modern browsers (Edge, Chrome, Firefox) via Selenium | `UiPath.UIAutomationModern.Activities` | If using the modern experience. Studio installs alongside UIAutomation. |
| Terminal/mainframe (3270, 5250, VT) | `UiPath.Terminal.Activities` | |
| FTP/SFTP | `UiPath.FTP.Activities` | |

### Database

| Scenario | Package | Guidance |
|---|---|---|
| SQL Server, Oracle, MySQL, PostgreSQL | `UiPath.Database.Activities` | Uses ODBC/OLEDB; a connection string asset is recommended. |
| NoSQL (Mongo, Cosmos) | `UiPath.WebAPI.Activities` via REST | No first-party NoSQL package; call the REST API. |

### Orchestrator and persistence

| Scenario | Package | Guidance |
|---|---|---|
| Queue items, assets, storage buckets, processes | `UiPath.System.Activities` | Core; no extra install. |
| Long-running workflows, Form Tasks, External Tasks | `UiPath.Persistence.Activities` | Required for `CreateFormTask`, `WaitForFormTaskAndResume`, `CreateExternalTask`. |
| Form Tasks with form.io forms | `UiPath.Persistence.Activities` + `UiPath.FormActivityLibrary` | Both required. |

### Credentials and security

| Scenario | Package | Guidance |
|---|---|---|
| Robot-scoped credential retrieval (`GetRobotCredential`, `GetRobotAsset`) | `UiPath.System.Activities` | Core; already installed. |
| Credential Provider integrations (CyberArk, HashiCorp, Azure Key Vault) | Configured in Orchestrator — no package | Robot fetches credentials through Orchestrator’s credential store. |

## Integration Service Connectors vs NuGet Packages

Connectors and packages both access third-party systems but are not interchangeable. Declare the selected mechanism in the proper SDD location.

### Decision

1. If Orchestrator has a configured **Integration Service** connection for the target system and the PDD does not require specific native-package activities, use the **Integration Service connector**.
2. Otherwise, use the matching **NuGet package**.
3. If both paths appear in §9 for one application, use Integration Service as primary and note the NuGet package as fallback in §14.

### Side-by-side

| Aspect | Integration Service Connector | NuGet Package |
|---|---|---|
| Where configured | Orchestrator → Integration Service → Connections | Project’s `project.json` dependencies |
| Reference | Slug (e.g., `salesforce`, `service-now`, `gmail`) in the Integration Service activity | `Using` namespace + activity from installed package |
| Authentication | Stored in Connection (OAuth, API key) | Credential asset + in-workflow auth logic |
| Deployment | No per-robot install; lives in Orchestrator | Packaged into the .nupkg and pulled on the robot |
| Runtime dependency | Robot must have `UiPath.IntegrationService.Activities`, one dependency regardless of connector count | One package per third-party system |
| SDD location | §9 Access Method as `Integration Service — <CONNECTOR_SLUG>` | §14 Packages table |

### Do not

- **Do not** list the connector slug in §14 Packages; slugs are not NuGet packages.
- **Do not** install `UiPath.Salesforce.Activities` when using the Salesforce Integration Service connector; the paths are parallel, not complementary.
- **Do not** assume every Orchestrator instance has Integration Service enabled. Confirm during Phase 1 scoping; if uncertain, default to NuGet.

### Salesforce examples

For Integration Service, §9 Application Inventory row:

| # | Application | Interface | Access Method | Role | Interaction Pattern |
|---|---|---|---|---|---|
| 3 | Salesforce | API | `Integration Service — salesforce` | Target | Write |

§14 adds only the Integration Service host package, not `UiPath.Salesforce.Activities`:

| Package | Version | Purpose |
|---|---|---|
| `UiPath.IntegrationService.Activities` | pin at build | Runtime host for Integration Service connector activities |

`pin at build` is the template’s literal sentinel: version is unknowable at design time; the build skill resolves and writes the exact version. See [rpa-sdd-template.md §14 Packages](../assets/templates/rpa-sdd-template.md).

For the native package, §9 Application Inventory row:

| # | Application | Interface | Access Method | Role | Interaction Pattern |
|---|---|---|---|---|---|
| 3 | Salesforce | API | OAuth 2.0 direct (native package) | Target | Write |

§14 adds:

| Package | Version | Purpose |
|---|---|---|
| `UiPath.Salesforce.Activities` | pin at build | Native Salesforce activities — used because Integration Service connector not available in this tenant |

## Per-Product Dependency Manager

Use each product’s mechanism and location; do not cross them.

| Product | Dependency manager | SDD location | Notes |
|---|---|---|---|
| RPA (Process, Library, Test Automation) | NuGet | §14 Packages table | Covered by this guide. |
| Case Management | Downstream Case project dependencies | Not a planner-only Packages subsection; resolution belongs to `uipath-maestro-case` from the Case Blueprint | Keep package hints in the `uipath-maestro-case` task prompt only when Section 2/4 resource choices require them. |
| Maestro Flow | Connector references + RPA step packages | Integrated Components section | Flow itself has no packages; each called RPA step uses the RPA template’s §14. |
| Agents | C# tool packages (subset of NuGet) | Tool Packages table in Agent template | Declare only packages whose activities are wrapped as Agent tools. |
| Coded Apps | **npm** (not NuGet) | Dependencies subsection in Coded App template | Use `package.json` semantics; do not list NuGet packages. |
| API Workflows | Integration Service connector references | Connectors section in API Workflow template | Hosted in Orchestrator; no package file. |

## Selection Checklist

Before finalising a Packages table:

1. Every §9 application has a matching package or Integration Service connector row.
2. Include `UiPath.System.Activities` always, plus `UiPath.UIAutomation.Activities` when any UI exists.
3. A PDD step containing “download”, “attach”, or “send email” has an email package.
4. A PDD step containing “extract from PDF” or “read invoice” has the DU / PDF packages.
5. A PDD step containing “approval”, “action centre”, or “long-running” has `UiPath.Persistence.Activities`.
6. Do not list Integration Service connector slugs in §14.
7. For Master Project, use a separate §14 table per sub-project; a Dispatcher that only downloads email does not need Excel packages.
8. For Coded App, use npm package names (e.g., `@uipath/apps-sdk`), not NuGet.

## Pitfalls

1. **Guessing package versions.** Default to `Latest` in SDDs. Resolve versions at build time (`uip` / Studio); do not pin unless the PDD explicitly requires a feature gate.
2. **Listing `UiPath.Mail.Activities` and `UiPath.MicrosoftOffice365.Activities` together “just in case”.** They overlap; choose one per email access method.
3. **Mixing IntegrationService slugs with NuGet names.** `salesforce` is a slug; `UiPath.Salesforce.Activities` is the package.
4. **Forgetting `UiPath.Persistence.Activities` for HITL.** Any workflow using `WaitForFormTaskAndResume`, `CreateFormTask`, or `CreateExternalTask` needs it. It also requires `supportsPersistence: true` in `project.json`; call this out in §14.
5. **Listing NuGet for Coded App dependencies.** Coded Apps are TypeScript/React and use npm; the template has a separate section.
6. **Omitting Testing packages in RPA Test Automation sub-type.** Test Automation requires `UiPath.Testing.Activities` for assertions; omission breaks Test Manager integration.