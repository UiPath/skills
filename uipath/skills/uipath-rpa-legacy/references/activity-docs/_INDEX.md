# UiPath Legacy Activities Reference - Index

## Purpose
Reference documents for Claude Code when writing **legacy** UiPath RPA workflows (XAML, classic design experience). Each file documents activities, arguments, gotchas, and things to remember.

**SCOPE: Legacy/Classic activities ONLY.** Not modern/Next/portable/coded workflows. When a package has both legacy and modern ("X" suffix) activities, only the legacy (classic) ones are covered. For example: `SendMail` (legacy SMTP) not `SendMailX` (modern), `ExcelApplicationScope` + `ExcelReadRange` (legacy) not `ExcelProcessScopeX` + `ReadRangeX` (modern).

---

## Core Activities (from UiPath/Activities repo) - by adoption rank

| # | File | Package | Adoption | Key Activities |
|---|------|---------|----------|----------------|
| 1 | [System.md](System.md) | UiPath.System.Activities | 93.6% | Collections, Text, Dates, Dialogs, Files, PowerShell, Triggers |
| 2 | [UIAutomation.md](UIAutomation.md) | UiPath.UIAutomation.Activities | 92.6% | Click, Type, Find Element, Selectors, Browser/Window scope |
| 3 | [Excel.md](Excel.md) | UiPath.Excel.Activities | 90.2% | Read/Write Range/Cell, Workbook/Application Scope, CSV, Macros |
| 4 | [Mail.md](Mail.md) | UiPath.Mail.Activities | 77.7% | SMTP, IMAP, POP3, Exchange, Outlook, Lotus Notes |
| 5 | [Web.md](Web.md) | UiPath.WebAPI.Activities | 33.9% | HTTP Request, SOAP, JSON, XML |
| 8 | [MicrosoftOffice365.md](MicrosoftOffice365.md) | UiPath.MicrosoftOffice365.Activities | 17.5% | Graph API: Mail, Calendar, Excel Online, OneDrive, SharePoint |
| 9 | [Testing.md](Testing.md) | UiPath.Testing.Activities | 16.1% | Assertions, PDF/Text comparison, test data queues |
| 10 | [PDF.md](PDF.md) | UiPath.PDF.Activities | 15.5% | Read PDF Text, OCR, Extract Pages, Join, Password |
| 13 | [Word.md](Word.md) | UiPath.Word.Activities | 10.1% | Word COM + Portable, text/image/table operations |
| 15 | [Terminal.md](Terminal.md) | UiPath.Terminal.Activities | 4.8% | 3270/5250/VT terminal emulation |
| 17 | [GSuite.md](GSuite.md) | UiPath.GSuite.Activities | 3.9% | Gmail, Drive, Sheets, Docs, Calendar, Tasks |
| 18 | [Cognitive.md](Cognitive.md) | UiPath.Cognitive.Activities | 3.8% | Google/Azure/Watson NLP, sentiment, translation |
| 20 | [Presentations.md](Presentations.md) | UiPath.Presentations.Activities | 3.3% | PowerPoint COM + OpenXml |
| 23 | [ComplexScenarios.md](ComplexScenarios.md) | UiPath.ComplexScenarios.Activities | 3.0% | Pre-built StudioX scenario templates |
| 24 | [IntelligentOCR.md](IntelligentOCR.md) | UiPath.IntelligentOCR.Activities | 3.0% | Document Understanding: classify, extract, validate, train |
| 25 | [Forms.md](Forms.md) | UiPath.Form.Activities | 2.5% | FormIo/HTML forms, async display, field binding |
| 29 | [OmniPage.md](OmniPage.md) | UiPath.OmniPage.Activities | 1.1% | OmniPage OCR engine |

## Other Packages (lower adoption / specialized)

| File | Package | Key Activities |
|------|---------|----------------|
| [ImageProcessing.md](ImageProcessing.md) | UiPath.ImageProcessing | Template matching, image comparison (native C++) |
| [MobileAutomation.md](MobileAutomation.md) | UiPath.MobileAutomation.Activities | iOS/Android via Appium |
| [SAP-BAPI.md](SAP-BAPI.md) | UiPath.SAP.BAPI.Activities | SAP BAPI function calls |
| [CommunicationsMining.md](CommunicationsMining.md) | UiPath.CommunicationsMining.Activities | CM validation with Action Center |
| [Vision-OCR.md](Vision-OCR.md) | UiPath.Vision.Activities | Multi-engine OCR (Azure, Google, ABBYY, Tesseract) |
| [WorkflowEvents.md](WorkflowEvents.md) | UiPath.WorkflowEvents.Activities | App-triggered workflows via SignalR |
| [ActiveDirectory.md](ActiveDirectory.md) | (Deprecated) | Moved to github.com/UiPath/it-automation |

## Community Activities (from UiPath/Community.Activities repo) - by adoption rank

| # | File | Package | Adoption | Key Activities |
|---|------|---------|----------|----------------|
| 6 | [Community-Database.md](Community-Database.md) | UiPath.Database.Activities | 22.7% | ExecuteQuery, ExecuteNonQuery, InsertDataTable, BulkInsert |
| 7 | [Community-Credentials.md](Community-Credentials.md) | UiPath.Credentials.Activities | 22.3% | Windows Credential Manager get/add/delete |
| 16 | [Community-FTP.md](Community-FTP.md) | UiPath.FTP.Activities | 4.5% | FTP/FTPS/SFTP file transfer |
| 21 | [Community-Cryptography.md](Community-Cryptography.md) | UiPath.Cryptography.Activities | 3.2% | AES encryption, HMAC hashing, PGP sign/verify |
| 22 | [Community-Python.md](Community-Python.md) | UiPath.Python.Activities | 3.0% | Python script execution and object interaction |
| - | [Community-Java.md](Community-Java.md) | UiPath.Java.Activities | <3% | Java method invocation and object interaction |
| - | [Community-Google-Speech.md](Community-Google-Speech.md) | UiPath.Google.Activities | <1% | Google Cloud Speech-to-Text, Text-to-Speech |

## Not In This Repo (Third-Party/External)

| # | Package | Adoption | Notes |
|---|---------|----------|-------|
| 11 | Microsoft.Activities | 15.1% | WF4 built-in activities (Delay, Parallel, etc.) - part of .NET Framework |
| 12 | Microsoft.Activities.Extensions | 12.5% | WF4 extensions - third party |
| 14 | UiPathTeam.SharePoint.Activities | 4.9% | SharePoint CSOM integration - separate NuGet |
| 19 | BalaReva.Excel.Activities | 3.4% | Third-party Excel (background processing, no Excel required) |
| 26 | BalaReva.EasyExcel.Activities | 1.2% | Third-party simplified Excel |
| 28 | UiPath.Persistence.Activities | 1.1% | Long-running workflow persistence (Orchestrator queues) |

---

## Third-Party Packages (documented but external to UiPath)

| # | File | Package | Adoption |
|---|------|---------|----------|
| 11+12 | [ThirdParty-Microsoft-WF4.md](ThirdParty-Microsoft-WF4.md) | Microsoft.Activities + Extensions | 15.1% + 12.5% |
| 14 | [ThirdParty-SharePoint.md](ThirdParty-SharePoint.md) | UiPathTeam.SharePoint.Activities | 4.9% |
| 19+26 | [ThirdParty-BalaReva-Excel.md](ThirdParty-BalaReva-Excel.md) | BalaReva.Excel + EasyExcel | 3.4% + 1.2% |
| 28 | [ThirdParty-Persistence.md](ThirdParty-Persistence.md) | UiPath.Persistence.Activities | 1.1% |

## Cross-Cutting References

| File | Purpose |
|------|---------|
| [AllActivities.md](AllActivities.md) | Master catalog: every UiPath legacy activity with description, organized by package |
| [_COMMON-PITFALLS.md](_COMMON-PITFALLS.md) | Real-world issues: zombie processes, selector failures, encoding traps, silent errors |
| [_PATTERNS.md](_PATTERNS.md) | Practical patterns: VB.NET expressions, DataTable cheat sheet, error handling, required scopes |
| [_XAML-GUIDE.md](_XAML-GUIDE.md) | XAML internals: file structure, VB vs C#, arguments, variables, Sequence/Flowchart/StateMachine templates, project.json, ViewState |
| [_INVOKE-CODE.md](_INVOKE-CODE.md) | Invoke Code deep-dive: compilation pipeline, VB/C# generated code, arguments mapping, available namespaces, examples, gotchas |
| [_REFRAMEWORK.md](_REFRAMEWORK.md) | REFramework complete guide: state machine, transitions, Config.xlsx, exception handling, retry logic, Dispatcher/Performer, gotchas |
| [_DU-PROCESS.md](_DU-PROCESS.md) | Document Understanding Process template: digitize/classify/extract/validate pipeline, Action Center, taxonomy, training, multi-robot sync |

## How to Use
When writing legacy UiPath RPA workflows, consult the relevant package file for:
- Available activities and their arguments
- Critical gotchas and edge cases
- Default values that may cause unexpected behavior
- Platform constraints and dependencies
- Deprecated activities and their replacements
