# PowerPoint Activities API Reference

Reference for the `powerpoint` service from `UiPath.Presentations.Activities` package.

**Required package:** `"UiPath.Presentations.Activities": "[2.3.1]"`

**Auto-imported namespaces:** `System`, `System.Collections.Generic`, `System.Data`, `UiPath.Presentations`, `UiPath.Presentations.Activities`, `UiPath.Presentations.Activities.API`, `UiPath.Presentations.Activities.API.Models`

**Service accessor:** `powerpoint` (type `IPresentationsService`)

---

## Two API Layers

The PowerPoint API has two layers:

1. **Windows (Interop) API** — uses `powerpoint.UsePowerPointPresentation(...)` returning `IPresentation`. This is the full-featured API that opens PowerPoint via COM interop. Supports slides, shapes, text, tables, images, media, macros, copy/paste, formatting, save/export, and sensitivity labels. See [windows-api.md](windows-api.md).

2. **Portable API** — uses `powerpoint.UsePresentationDocument(...)` returning `IPresentationDocumentHandle`. This is a lightweight cross-platform API using OpenXml. Supports basic slide operations: add/delete slides, add text, add tables, add images, replace text, and format content. See [portable-api.md](portable-api.md).

**Always prefer the Windows API (`UsePowerPointPresentation`) unless cross-platform compatibility is required.**

For full coded workflow examples, see [examples.md](examples.md).

---

## Key Enum Reference Summary

| Enum | Values | Description |
|---|---|---|
| `PresentationSaveAsType` | `XmlPresentation`, `MacroEnabledPresentation`, `OldPresentation` | Format when saving presentations |
| `TableAppendMode` | `CreateNewTable`, `AppendToTable`, `OverwriteExistingData` | How DataTable data is added to a slide table |
| `InsertPositionType` | `SpecifiedIndex`, `Beginning`, `End` | Where to insert a new slide |
| `PptLabelOperation` | `None`, `Add`, `Clear` | Sensitivity label operation on open/create |
