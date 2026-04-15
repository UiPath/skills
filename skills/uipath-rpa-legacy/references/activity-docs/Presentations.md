# UiPath Presentations (PowerPoint) Activities - Legacy Reference

## Overview
PowerPoint automation with COM Interop and OpenXml (portable). Package: `UiPath.Presentations.Activities`.

---

## Activities

### COM-based (require PowerPointApplicationScope)
| Activity | Key Arguments | Output |
|----------|---------------|--------|
| `PowerPointApplicationScope` | PresentationPath, Password, EditPassword, CreateIfNotExists, AutoSave, TemplatePath | Container scope |
| `InsertSlide` | SlideMasterName, LayoutName, InsertType (SpecifiedIndex/Beginning/End), InsertPosition | InsertedAtPosition (1-based) |
| `DeleteSlide` | DeletePosition (1-based) | |
| `CopyPasteSlide` | SourcePresentation, SlideToCopy, DestinationPresentation, WhereToInsert, Move | |
| `InsertTextInPresentation` | SlideIndex (1-based), ShapeName, Text, ClearExistingText | |
| `FindAndReplaceTextInPresentation` | SearchFor, ReplaceWith, MatchCase, WholeWordsOnly, ReplaceAll | NumberOfReplacements |
| `ReplaceShapeWithDataTable` | SlideIndex, ShapeName, TableToInsert, AppendMode, ExcludeHeaders | |
| `ReplaceShapeWithMedia` | SlideIndex, ShapeName, Media (path), Left/Top/Width/Height (EMUs) | |
| `PasteIntoSlide` | SlideIndex, ShapeName, position/size | |
| `InsertFile` | SlideIndex, ShapeName, FilePath, IconLabel | |
| `FormatSlideContent` | SlideIndex, ShapeName + child modifications (ZIndex, FontSize, ShapeName change) | |
| `RunMacro` | MacroName + child RunMacroArgument activities | Result (object) |
| `SavePresentationAsPdf` | PdfPath, ReplaceExisting | Auto-adds .pdf |
| `SavePresentationFileAs` | FilePath, SaveAsFileType (.pptx/.pptm/.ppt), ReplaceExisting | |
| `AddSensitivityLabel` | SensitivityLabel, Justification | |
| `GetSensitivityLabel` | | SensitivityLabel |

### Portable/OpenXml (no PowerPoint required)
PptDocumentCreateNew, PptDocumentAddTextToSlide, PptDocumentInsertSlide, PptDocumentDeleteSlide, PptDocumentFindAndReplaceTextInPresentation, PptDocumentReplaceShapeWithDataTable, PptDocumentReplaceShapeWithMedia, PptDocumentFormatSlideContent

---

## Critical Gotchas

### Slide Indexing
1. **Both COM and OpenXml UiPath APIs expose 1-based indexing** to users (SlideIndex=1 is first slide)
2. **OpenXml internally converts to 0-based** for SDK array access, but this is transparent to users
3. **InsertPosition outputs are 1-based** in both modes

### COM Interop
4. **All COM activities MUST be inside PowerPointApplicationScope** - constraint enforced at design time
5. **MarshalHelpers.ReleaseComObject()** used for cleanup with retry on known COM errors
6. **PowerPointRefCountInstanceManager** prevents premature COM cleanup

### Position/Size in EMUs
7. **Left/Top must be >= 0**, Width/Height must be >= 50 (English Metric Units)
8. **EMUs are NOT pixels** - 1 inch = 914400 EMUs

### Find & Replace
9. **WholeWordsOnly=true requires ONLY alphanumeric SearchFor** - fails otherwise
10. **COM version allows empty ReplaceWith; OpenXml REQUIRES it** (not optional)

### DataTable Operations
11. **TableAppendMode**: CreateNewTable (replace shape), AppendToTable, OverwriteExistingData
12. **StartRow/StartColumn are 0-based for append mode**

### Template Handling
13. **Supported template extensions**: .potx, .potm, .pptx, .pptm
14. **Default embedded template** included in assembly resources for PptDocumentCreateNew

### CopyPasteSlide
15. **Moving within same presentation** - if destination < source, deletion index adjusted automatically

### AutoSave
16. **AutoSave=true (default)** saves on scope exit
17. **OpenXml activities call SaveChanges()** after each modification internally

### File Formats
18. **SaveAsFileType**: XmlPresentation (.pptx), MacroEnabledPresentation (.pptm), OldPresentation (.ppt)
19. **Extension auto-added** if missing
