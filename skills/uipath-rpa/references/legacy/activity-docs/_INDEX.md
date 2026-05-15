# UiPath Legacy Activities Reference - Index

Reference documents for writing **legacy** UiPath RPA workflows (XAML). Each file documents activities, arguments, gotchas, and patterns.

**SCOPE: Windows-Legacy (.NET Framework 4.6.1) activities only.** Not Windows-compatibility or cross-platform variants. When a package has both legacy and "X" suffix activities, only the legacy versions are documented (e.g., `ExcelReadRange` not `ReadRangeX`, `SendMail` not `SendMailX`).

---

## Core Activity Packages

| File | Package | Key Activities |
|------|---------|----------------|
| [System.md](System.md) | UiPath.System.Activities | Collections, Text, Dates, Dialogs, Files, PowerShell, Triggers |
| [UIAutomation.md](UIAutomation.md) | UiPath.UIAutomation.Activities | Click, Type, Find Element, Selectors, Browser/Window scope |
| [Excel.md](Excel.md) | UiPath.Excel.Activities | Read/Write Range/Cell, Workbook/Application Scope, CSV, Macros |
| [Mail.md](Mail.md) | UiPath.Mail.Activities | SMTP, IMAP, POP3, Exchange, Outlook |
| [Web.md](Web.md) | UiPath.WebAPI.Activities | HTTP Request, SOAP, JSON, XML |
| [MicrosoftOffice365.md](MicrosoftOffice365.md) | UiPath.MicrosoftOffice365.Activities | Graph API: Mail, Calendar, Excel Online, OneDrive, SharePoint |
| [Testing.md](Testing.md) | UiPath.Testing.Activities | Assertions, PDF/Text comparison, test data queues |
| [PDF.md](PDF.md) | UiPath.PDF.Activities | Read PDF Text, OCR, Extract Pages, Join, Password |
| [Word.md](Word.md) | UiPath.Word.Activities | Word COM + Portable, text/image/table operations |
| [Presentations.md](Presentations.md) | UiPath.Presentations.Activities | PowerPoint COM + OpenXml |
| [Database.md](Database.md) | UiPath.Database.Activities | ExecuteQuery, ExecuteNonQuery, InsertDataTable, BulkInsert |
| [Credentials.md](Credentials.md) | UiPath.Credentials.Activities | Windows Credential Manager get/add/delete |
| [FTP.md](FTP.md) | UiPath.FTP.Activities | FTP/FTPS/SFTP file transfer |
| [Cryptography.md](Cryptography.md) | UiPath.Cryptography.Activities | AES encryption, HMAC hashing, PGP sign/verify |
| [Python.md](Python.md) | UiPath.Python.Activities | Python script execution and object interaction |
| [Java.md](Java.md) | UiPath.Java.Activities | Java method invocation and object interaction |

## Specialized Packages

| File | Package | Key Activities |
|------|---------|----------------|
| [Terminal.md](Terminal.md) | UiPath.Terminal.Activities | 3270/5250/VT terminal emulation |
| [GSuite.md](GSuite.md) | UiPath.GSuite.Activities | Gmail, Drive, Sheets, Docs, Calendar, Tasks |
| [Cognitive.md](Cognitive.md) | UiPath.Cognitive.Activities | Google/Azure/Watson NLP, sentiment, translation |
| [IntelligentOCR.md](IntelligentOCR.md) | UiPath.IntelligentOCR.Activities | Document Understanding: classify, extract, validate, train |
| [Forms.md](Forms.md) | UiPath.Form.Activities | FormIo/HTML forms, async display, field binding |
| [OmniPage.md](OmniPage.md) | UiPath.OmniPage.Activities | OmniPage OCR engine |
| [ImageProcessing.md](ImageProcessing.md) | UiPath.ImageProcessing | Template matching, image comparison |
| [MobileAutomation.md](MobileAutomation.md) | UiPath.MobileAutomation.Activities | iOS/Android via Appium |
| [SAP-BAPI.md](SAP-BAPI.md) | UiPath.SAP.BAPI.Activities | SAP BAPI function calls |
| [CommunicationsMining.md](CommunicationsMining.md) | UiPath.CommunicationsMining.Activities | CM validation with Action Center |
| [Vision-OCR.md](Vision-OCR.md) | UiPath.Vision.Activities | Multi-engine OCR (Azure, Google, ABBYY, Tesseract) |
| [WorkflowEvents.md](WorkflowEvents.md) | UiPath.WorkflowEvents.Activities | App-triggered workflows via SignalR |
| [Google-Speech.md](Google-Speech.md) | UiPath.Google.Activities | Google Cloud Speech-to-Text, Text-to-Speech |
| [ComplexScenarios.md](ComplexScenarios.md) | UiPath.ComplexScenarios.Activities | Pre-built StudioX scenario templates |
| [ActiveDirectory.md](ActiveDirectory.md) | (Deprecated) | Moved to github.com/UiPath/it-automation |

## Third-Party Packages

| File | Package |
|------|---------|
| [ThirdParty-Microsoft-WF4.md](ThirdParty-Microsoft-WF4.md) | Microsoft.Activities + Extensions |
| [ThirdParty-SharePoint.md](ThirdParty-SharePoint.md) | UiPathTeam.SharePoint.Activities |
| [ThirdParty-BalaReva-Excel.md](ThirdParty-BalaReva-Excel.md) | BalaReva.Excel + EasyExcel |
| [ThirdParty-Persistence.md](ThirdParty-Persistence.md) | UiPath.Persistence.Activities |

## Cross-Cutting References

| File | Purpose |
|------|---------|
| [_BUILT-IN-ACTIVITIES.md](_BUILT-IN-ACTIVITIES.md) | Top 20 built-in activities with complete XAML — no find-activities needed |
| [AllActivities.md](AllActivities.md) | Master catalog: every legacy activity organized by package |
| [_COMMON-PITFALLS.md](_COMMON-PITFALLS.md) | Real-world issues: zombie processes, selector failures, encoding traps |
| [_PATTERNS.md](_PATTERNS.md) | VB.NET expressions, DataTable cheat sheet, error handling, required scopes |
| [_XAML-GUIDE.md](_XAML-GUIDE.md) | XAML structure, VB vs C#, Sequence/Flowchart/StateMachine, ViewState layout |
| [_INVOKE-CODE.md](_INVOKE-CODE.md) | InvokeCode: compilation pipeline, arguments, namespaces, examples |
| [_REFRAMEWORK.md](_REFRAMEWORK.md) | REFramework: state machine, Config.xlsx, retry logic, Dispatcher/Performer |
| [_DU-PROCESS.md](_DU-PROCESS.md) | Document Understanding Process: digitize/classify/extract/validate pipeline |
