# BalaReva Excel Activities - Legacy Reference

## Overview
Third-party Excel activities with advanced formatting, charts, and cell-level control. Two packages: `BalaReva.Excel.Activities` (COM, requires Excel - **38 activities**) and `BalaReva.EasyExcel.Activities` (library-based, no Excel). **#19 (3.4%) and #26 (1.2%) by adoption**.

Source: [UiPath Marketplace](https://marketplace.uipath.com/listings/balareva-xl-activities)

---

## BalaReva.Excel.Activities - All 38 Activities (from Marketplace)

### Charts (4)
| Activity | Purpose |
|----------|---------|
| `Pie Chart` | Generate pie chart from data |
| `Column Chart` | Generate column chart |
| `Line Chart` | Generate line chart |
| `Bar Chart` | Generate bar chart |

### Comments (4)
| Activity | Purpose |
|----------|---------|
| `Add Comment` | Insert comment into cell |
| `Get Comment` | Extract comment text |
| `Delete Comment` | Remove comment from cell |
| `Show/Hide Comment` | Toggle comment visibility |

### Cell Operations (7)
| Activity | Purpose |
|----------|---------|
| `Copy Data to Clipboard` | Transfer cell data to clipboard |
| `Clipboard To DataTable` | Convert clipboard to DataTable |
| `Delete Data` | Clear/remove cell contents from range |
| `Merge Cells` | Combine cell ranges with alignment |
| `UnMerge Cells` | Separate merged cells |
| `Change Cell Type` | Format numbers for currency/percentage/date/decimal |
| `Format Cells` | Comprehensive formatting (alignment, orientation, font) |

### Row/Column (4)
| Activity | Purpose |
|----------|---------|
| `Hide/Unhide Column` | Toggle column visibility |
| `Hide/Unhide Row` | Toggle row visibility |
| `AutoFit Columns` | Auto-adjust column widths |
| `AutoFit Rows` | Auto-adjust row heights |

### Sheet Management (8)
| Activity | Purpose |
|----------|---------|
| `Add Sheet` | Create new worksheet |
| `Delete Sheet` | Remove worksheet |
| `Rename Work Sheet` | Change sheet name |
| `Copy To File` | Copy worksheet between files |
| `Copy To WorkBook` | Copy worksheet within workbook |
| `HideUnhide` | Toggle sheet visibility |
| `Protect UnProtect` | Enable/disable sheet protection |
| `Get Sheets Name` | List all sheet names |

### Content Operations (5)
| Activity | Purpose |
|----------|---------|
| `Find Replace` | Find and replace text in range |
| `Remove Duplicates` | Eliminate duplicate rows (multi-column) |
| `Hyperlink Remove` | Strip hyperlinks from range |
| `Insert Table Format` | Create formatted table (28 styles) |
| `Set Table Format` | Modify existing table format |

### Images & Export (4)
| Activity | Purpose |
|----------|---------|
| `Insert Image` | Place image at position |
| `Insert Image At Cell` | Position image in specific cell |
| `Extract Graph Image` | Export chart as image (BMP/GIF/JPG/PNG) |
| `Export WorkBook` | Save as PDF or XPS |

### Workbook (2)
| Activity | Purpose |
|----------|---------|
| `Create WorkBook` | Generate new Excel file |
| `Set Password` | Add password protection |

---

## BalaReva.EasyExcel.Activities

Similar activities but uses **EPPlus/ClosedXML libraries** instead of COM Interop. Key difference: **does NOT require Excel installed**.

---

## BalaReva.Excel vs EasyExcel

| Aspect | BalaReva.Excel | BalaReva.EasyExcel |
|--------|---------------|-------------------|
| Excel Required | YES (COM) | NO (library) |
| Performance | Slower (COM) | Faster |
| Process Risk | Zombie EXCEL.EXE | None |
| .xls Support | Yes | No (.xlsx only) |
| Chart Support | Full (4 chart types) | Limited |
| Image Export | Yes (Extract Graph Image) | Limited |

---

## Critical Gotchas (Forum-Verified)

### Compatibility Issues
1. **v2019.10.1 incompatible with UiPath 2019.10.3** - [Forum](https://forum.uipath.com/t/balareva-excel-activities-v2019-10-1-problems/237430): "none of the activities actually work"
2. **EasyExcel only works for 'windows-legacy' projects** - [Forum](https://forum.uipath.com/t/unable-to-install-bala-reva-easy-excel-packages/517950): won't install in Windows or cross-platform projects
3. **Change Cell Type errors with .xlsx** - [Forum](https://forum.uipath.com/t/change-cell-type-error-while-using-balareva-easy-excel-activities/261970)

### Activity-Specific Issues
4. **AutoFit fails**: "AutoFit method of Range class failed" - [Forum](https://forum.uipath.com/t/balareva-excel-activities-autofit/282792)
5. **Format Cells vertical alignment**: "Unable to set the HorizontalAlignment property" error when setting vertical alignment
6. **Export WorkBook not working** - [Forum](https://forum.uipath.com/t/export-workbook-not-working-balareva-excel-activities/331344)
7. **Extract Hyperlinks locks Excel** - [Forum](https://forum.uipath.com/t/balareva-enterprise-easyexcel-activities-extract-hyperlinks-problem/409437): document stays locked

### General
8. **Don't mix with UiPath built-in Excel** in same workflow - assembly/version conflicts
9. **COM version leaves orphaned EXCEL.EXE** on crash - same issue as UiPath built-in
10. **Free for community** but enterprise version (BalaReva Enterprise) has separate licensing
11. **Also available**: [Graph Activities for Excel Charts](https://marketplace.uipath.com/listings/balareva-excel-graph-activities) - separate specialized chart package
