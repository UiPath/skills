# UiPath ComplexScenarios Activities - Legacy Reference

## Overview
Pre-built workflow scenario templates for common automation tasks (StudioX). Package: `UiPath.ComplexScenarios.Activities`. **#23 by adoption (3%)**.

---

## Scenario Categories

### File/Folder Scenarios (7)
| Scenario | Purpose | Requires |
|----------|---------|----------|
| `AddCurrentDateToFileAndMove` | Append date to filename, move to "Processed" | FileInfo + Excel workspace |
| `AddCurrentDateToFilesInFolder` | Batch: date-stamp multiple files | IEnumerable\<FileInfo\> + workspace |
| `CopyFileInfoToExcel` | Extract file metadata to Excel | FileInfo + workspace |
| `DeleteFolder` | Delete folder recursively | (always available) |
| `GroupByFileCreationDate` | Organize files by creation date | FileInfo + workspace |
| `GroupByFileSize` | Organize files by size | FileInfo + workspace |
| `GroupByFileType` | Organize files by extension | FileInfo + workspace |

### Email Scenarios (8)
| Scenario | Purpose | Requires |
|----------|---------|----------|
| `CopyEmailsToExcel` | Extract inbox to Excel (From, To, Subject, CC, Bcc, Body) | IMailQuickHandle + workspace |
| `CreateContactsDatabase` | Extract unique sender addresses | IMailQuickHandle + workspace |
| `DownloadEmailAttachments` | Save all attachments from inbox | IMailQuickHandle |
| `EmailFilesInFolder` | Send folder contents as attachments | IMailQuickHandle |
| `EmailFolderBackup` | Backup email folder | IMailQuickHandle |
| `ForwardEmail` | Forward messages | IMailQuickHandle |
| `MoveMail` | Move to another folder | IMailQuickHandle |
| `ReplyToEmail` | Reply to messages | IMailQuickHandle |

### Excel/Office Scenarios (3)
| Scenario | Purpose | Requires |
|----------|---------|----------|
| `FillFormFromExcel` | Read Excel data, fill forms | Workspace |
| `MergeRanges` | Merge Excel ranges | Workspace |
| `PasteExcelChartIntoPowerPoint` | Copy chart to PowerPoint slide | IPresentationQuickHandle + workspace |

---

## Architecture

Three base class variants determine when scenarios appear:
- **DefaultScenarioDefinition** - Always shown (e.g., DeleteFolder)
- **ExtendedScenarioDefinition\<T\>** - Shown when argument type T matched, workspace optional
- **WorkspaceScenarioDefinition\<T\>** - Shown when argument type T matched AND Excel workspace available

---

## Critical Gotchas

### Visibility/Matching
1. **Scenarios only appear when argument types match exactly** - `IMailQuickHandle` vs generic mail interfaces must match precisely
2. **WorkspaceScenario variants require open Excel workspace** - silently hidden if no Excel file open
3. **Type metadata matching** checks `TypesMetadata.WorkspaceWorkbookMetadata` - not just any IWorkbook

### Email Scenarios
4. **CopyEmailsToExcel uses scratchpad cells A1:F1** for temporary data before appending - cells must be managed between iterations
5. **CreateContactsDatabase deduplicates with DeleteRowsOption.Duplicates** - order may be affected
6. **EmailFilesInFolder has hardcoded Subject="Requested Files" and Body="See Attachments"** - cannot customize
7. **OutlookForEachMail vs ForEachEmailX** used inconsistently across scenarios - different property names

### File Scenarios
8. **Folder selection via UI dialog** (`IoSystemHelpers.TryGetSelectedFolderPathExpression()`) - returns false if user cancels, producing NO activities (silent failure)
9. **File metadata extraction**: Folder returns parent directory only, not full path; date format follows system locale

### Office Scenarios
10. **PasteExcelChartIntoPowerPoint uses clipboard** (Windows-specific) - requires active Excel and PowerPoint instances
11. **Scenario explicitly excluded from some builds** - check build .targets for availability

### General
12. **Expression language dependency** - scenario builders generate VB or C# expressions based on project language; manual edits must match
13. **These are StudioX design-time scenarios** - not runtime activities you add to XAML directly
