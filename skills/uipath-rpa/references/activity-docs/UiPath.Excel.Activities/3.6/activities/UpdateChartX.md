# Update Chart

`UiPath.Excel.Activities.Business.UpdateChartX`

Applies one or more modifications to an existing Excel chart. This is a container activity that holds child modification activities, each representing a specific chart change.

**Package:** `UiPath.Excel.Activities`
**Platform:** Windows only
**Required Scope:** `ExcelApplicationCard`

## Properties

### Input
| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Chart` | Chart | InArgument | `IChartRef` | Yes | | Chart to update. |

### Designer Controls (Not Mapped to XAML)
| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `ModificationToAdd` | Modification type | `UpdateChartModification` | Selects the type of modification to add as a child activity. |
| `AddModification` | Add Modification | Action Button | Inserts a new child modification activity of the selected type. |

## Available Modification Types

Child modification activities are added inside the `UpdateChartX` body. Each modification is a separate activity:

### `UpdateChartModification` Enum
| Value | Description |
|-------|-------------|
| `ChangeDataRange` | Changes the data range of the chart. |
| `ModifyChartTitle` | Modifies the chart title. |
| `UpdateAxisTitle` | Updates an axis title. |
| `UpdateAxisBounds` | Updates axis bounds (min/max). |
| `ShowHideLegend` | Shows or hides the chart legend. |
| `ShowHideDataLabels` | Shows or hides data labels. |

## XAML Example
```xml
<excel:ExcelApplicationCard DisplayName="Use Excel File">
  <excel:UpdateChartX
    Chart="[chartRef]"
    DisplayName="Update Chart">
    <excel:UpdateChartX.Body>
      <ActivityAction x:TypeArguments="excel:UpdateChartXDescriptor">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="excel:UpdateChartXDescriptor" Name="UpdateChartXDescriptor" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Do">
          <!-- Add modification activities here, e.g.: -->
          <!-- <excel:ModifyChartTitleModification ... /> -->
        </Sequence>
      </ActivityAction>
    </excel:UpdateChartX.Body>
  </excel:UpdateChartX>
</excel:ExcelApplicationCard>
```

## Notes
- This activity inherits from `BaseParentActivityWithDescriptor` and executes its child modification activities sequentially.
- At least one child modification activity is required; otherwise a runtime error occurs.
- The chart reference is typically obtained from the output of `InsertExcelChartX` or by referencing an existing chart.
- The "Add Modification" button in the designer inserts a new child activity of the selected type into the body.
