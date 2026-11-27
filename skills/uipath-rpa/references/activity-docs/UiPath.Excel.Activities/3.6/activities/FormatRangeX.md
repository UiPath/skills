# Format Range

`UiPath.Excel.Activities.Business.FormatRangeX`

Sets the format for all the cells in a specified range.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Range` | Source range | InArgument | `IReadRangeRef` | Yes | | The range to format. |

### Format Settings

The Format section is organized into three tabs: **Data Type**, **Alignment**, and **Font**. A tab selector (`FormatType`) controls which tab is displayed.

#### Format Tab Selector
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `FormatType` | Format | `CellFormatType` | `DataType` | Selects the active format settings tab. |

#### Data Type Tab
| Name | Display Name | Type | Default | Visible When | Description |
|------|-------------|------|---------|------------|-------------|
| `CategoryType` | Category | `CellFormat` | `General` | Always (within Data Type tab) | The cell format category. |
| `NumberDecimalPlaces` | Decimals | `int` | `2` | CategoryType = Number | Number of decimal places. |
| `NumberUseThousandSeparator` | Use 1000 Separator | `bool` | `False` | CategoryType = Number | Use a thousand separator. |
| `CurrencyDecimalPlaces` | Decimals | `int` | `2` | CategoryType = Currency | Number of decimal places for currency. |
| `CurrencyUseThousandSeparator` | Use 1000 Separator | `bool` | `False` | CategoryType = Currency | Use a thousand separator for currency. |
| `CurrencySymbol` | Symbol | `string` | `$` | CategoryType = Currency | The currency symbol. |
| `CurrencySetAtTheEnd` | Set at the end | `bool` | `False` | CategoryType = Currency | Place the currency symbol after the value. |
| `PercentageDecimalPlaces` | Decimals | `int` | `2` | CategoryType = Percentage | Number of decimal places for percentage. |
| `DateType` | Date format | `DateType` | `Short` | CategoryType = Date | The date format to use. |
| `TimeType` | Time format | `TimeType` | `HoursMinutes` | CategoryType = Time | The time format to use. |
| `TimeIsAMPM` | AM/PM | `bool` | `False` | CategoryType = Time | Use 12-hour AM/PM format. |
| `CustomFormatAsString` | Custom format | `string` | `#,##0_);[Red](#,##0)` | CategoryType = Custom | A custom Excel format string. |

#### Alignment Tab
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `HorizontalAlignment` | Horizontal | `ExcelRangeHorizontalAlignment` | `xlHAlignGeneral` | Horizontal alignment for cell content. |
| `VerticalAlignment` | Vertical | `ExcelRangeVerticalAlignment` | `xlVAlignBottom` | Vertical alignment for cell content. |
| `WrapText` | Wrap text | `bool` | `False` | Wrap text within the cell. |

#### Font Tab
| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `FontFamily` | Font | `string` | `Calibri` | The font family name. |
| `FontStyle` | Font style | `ExcelRangeFontStyle` | `Regular` | The font style. |
| `FontSize` | Font size | `double` | `11` | The font size in points. |
| `FontColor` | Font color | `string` | `Black` | The font color (system color name). |
| `FontFillColor` | Fill color | `string` | `Transparent` | The cell background fill color (system color name). |
| `FontUnderlineStyle` | Underline style | `ExcelRangeUnderlineStyle` | `None` | The underline style for the font. |

### Enum Reference

#### `CellFormatType`
| Value | Display Name |
|-------|-------------|
| `DataType` | Data Type |
| `Alignment` | Alignment |
| `Font` | Font |

#### `CellFormat`
| Value | Display Name |
|-------|-------------|
| `General` | General |
| `Number` | Number |
| `Date` | Date |
| `Time` | Time |
| `Percentage` | Percentage |
| `Currency` | Currency |
| `Text` | Text |
| `Custom` | Custom |

#### `DateType`
| Value | Display Name |
|-------|-------------|
| `Long` | Long |
| `Short` | Short |

#### `TimeType`
| Value | Display Name |
|-------|-------------|
| `HoursMinutes` | Hours:Minutes |
| `HoursMinutesSeconds` | Hours:Minutes:Seconds |

#### `ExcelRangeHorizontalAlignment`
| Value | Display Name |
|-------|-------------|
| `xlHAlignGeneral` | General |
| `xlHAlignLeft` | Left |
| `xlHAlignCenter` | Center |
| `xlHAlignRight` | Right |
| `xlHAlignFill` | Fill |
| `xlHAlignJustify` | Justify |
| `xlHAlignCenterAcrossSelection` | Center Across Selection |
| `xlHAlignDistributed` | Distributed |

#### `ExcelRangeVerticalAlignment`
| Value | Display Name |
|-------|-------------|
| `xlVAlignTop` | Top |
| `xlVAlignCenter` | Center |
| `xlVAlignBottom` | Bottom |
| `xlVAlignJustify` | Justify |
| `xlVAlignDistributed` | Distributed |

#### `ExcelRangeFontStyle`
| Value | Display Name |
|-------|-------------|
| `Regular` | Regular |
| `Italic` | Italic |
| `Bold` | Bold |
| `BoldItalic` | Bold Italic |

#### `ExcelRangeUnderlineStyle`
| Value | Display Name |
|-------|-------------|
| `None` | None |
| `Single` | Single |
| `Double` | Double |
| `SingleAccounting` | Single Accounting |
| `DoubleAccounting` | Double Accounting |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Excel Application Scope">
  <excel:FormatRangeX
    Range="[MyRange]"
    DisplayName="Format Range">
    <excel:FormatRangeX.Format>
      <excel:NumberFormat DecimalPlaces="2" UseThousandSeparator="True" />
    </excel:FormatRangeX.Format>
    <excel:FormatRangeX.Alignment>
      <excel:AlignmentOptions HorizontalAlignment="xlHAlignCenter" VerticalAlignment="xlVAlignCenter" WrapText="False" />
    </excel:FormatRangeX.Alignment>
    <excel:FormatRangeX.Font>
      <excel:FontOptions FontFamilyName="Calibri" Style="Bold" Size="12" Color="Black" FillColor="Transparent" UnderlineStyle="None" />
    </excel:FormatRangeX.Font>
  </excel:FormatRangeX>
</excel:ExcelApplicationCard>
```

## Notes
- The `Format`, `Alignment`, and `Font` properties are not directly visible in the designer; instead, the designer presents them as tabbed sections within the **Format** category.
- Only one format settings tab is visible at a time, controlled by the `FormatType` selector.
- The `CategoryType` selection (General, Number, Date, etc.) determines which sub-properties are shown within the Data Type tab.
- A format must be selected; leaving the `Format` property null causes a validation error.
- The `Format` property defaults to `GeneralFormat`.
