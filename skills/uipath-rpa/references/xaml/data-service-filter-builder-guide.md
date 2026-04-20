# Data Service Filter Builder — XAML Generation Guide

Use this guide when generating or editing a `QueryEntityRecords` activity that needs filtering. This guide covers the exact XAML serialization format for filter definitions.

## Filter Architecture

A filter on `QueryEntityRecords` consists of two sibling properties:

1. **`FilterArguments`** — a `FilterArgument` wrapping a tree of `GroupFilter` and `SimpleFilter` elements that define the filter structure (fields, operators, grouping logic)
2. **`FilterValues`** — a flat `List<InArgument>` holding the runtime values, indexed by each `SimpleFilter.ValueIndex`

```
QueryEntityRecords
├─ FilterArguments
│   └─ FilterArgument (FilterActivityType="{x:Null}")
│       └─ GroupFilter (root, Operator="AND" or "OR")
│           ├─ Filters: List<SimpleFilter>    ← conditions at this level
│           └─ Groups: List<GroupFilter>       ← nested child groups (recursive)
└─ FilterValues
    └─ List<InArgument>                        ← flat list, indexed by ValueIndex
```

### SimpleFilter Properties

| Property | Value | Description |
|----------|-------|-------------|
| `ExpressionValue` | `{x:Null}` | Always null. Legacy property — do not use. |
| `FieldName` | Entity field name | Use dot notation for relationship fields (e.g., `CreatedBy.Name`) |
| `FieldType` | `UiPath.DataService.Core.Models.EntityField` | Always this constant. Not a CLR type. |
| `Operator` | Operator string | See [Operator Reference](#operator-reference-by-field-type) below |
| `ValueIndex` | Integer | Zero-based index into the `FilterValues` list |

### GroupFilter Properties

| Property | Value | Description |
|----------|-------|-------------|
| `Index` | Integer | Position index. Use `0` for each group. |
| `Operator` | `AND` or `OR` | Uppercase. Logical operator combining child conditions. |
| `Filters` | `List<SimpleFilter>` | Conditions at this group level |
| `Groups` | `List<GroupFilter>` | Nested child groups (for AND-of-ORs, OR-of-ANDs, etc.) |

## XAML Namespace Requirements

The filter elements use namespaces already required by `QueryEntityRecords`. Ensure the root `<Activity>` declares:

```xml
xmlns:uda="clr-namespace:UiPath.DataService.Activities;assembly=UiPath.DataService.Activities.Core"
xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
xmlns:local="clr-namespace:<ProjectName>;assembly=DataService.<ProjectName>"
```

The `local:` namespace is required for entity type arguments (e.g., `x:TypeArguments="local:NumericEntity"`). It **must** include `assembly=DataService.<ProjectName>` — without the assembly qualifier, the XAML parser cannot locate entity types. See [overview.md § XAML Namespace Declarations](../../../../references/activity-docs/UiPath.DataService.Activities/25.9/activities/overview.md#xaml-namespace-declarations) for the full set of required declarations.

If any `FilterValues` entry uses `DateTimeOffset`, `Guid`, or `String[]`, also declare:

```xml
xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"
```

The `x:` prefix covers: `x:String`, `x:Int32`, `x:Int64`, `x:Double`, `x:Boolean`, `x:Decimal`.
The `s:` prefix is required for: `s:DateTimeOffset`, `s:Guid`, `s:String[]`, `s:DateTime`.

See [xaml-basics-and-rules.md § x: and s: namespace aliases](xaml-basics-and-rules.md) for the full type mapping.

## Operator Reference by Field Type

Look up the field's `SqlType.Name` and `FieldDisplayType` in `EntitiesStore.json` to determine which operators are valid.

### Basic Fields (FieldDisplayType = "Basic")

| SqlType.Name | Valid Operators |
|---|---|
| `NVARCHAR`, `MULTILINE` | `contains`, `not contains`, `=`, `!=`, `startswith`, `endswith`, `is empty`, `not empty`, `is null`, `is not null`, `in`, `not in` |
| `INT`, `BIGINT`, `FLOAT`, `DECIMAL` | `=`, `!=`, `>`, `<`, `>=`, `<=`, `is empty`, `not empty`, `is null`, `is not null`, `in`, `not in` |
| `DATETIMEOFFSET`, `DATE` | `=`, `!=`, `>`, `<`, `>=`, `<=`, `is empty`, `not empty`, `is null`, `is not null`, `in`, `not in` |
| `BIT` | `Equals true`, `Equals false`, `=`, `!=`, `is empty`, `not empty`, `is null`, `is not null` |
| `UNIQUEIDENTIFIER` | `contains`, `not contains`, `=`, `!=`, `startswith`, `endswith`, `is empty`, `not empty`, `is null`, `is not null`, `in`, `not in` |

### Non-Basic Fields

| FieldDisplayType | Valid Operators |
|---|---|
| `ChoiceSetSingle` | `=`, `!=`, `is empty`, `not empty`, `is null`, `is not null`, `in`, `not in` |
| `ChoiceSetMultiple` | `contains`, `not contains`, `=`, `!=`, `is empty`, `not empty`, `is null`, `is not null` |
| `AutoNumber` | `=`, `!=`, `>`, `<`, `>=`, `<=`, `is empty`, `not empty`, `is null`, `is not null`, `in`, `not in` |
| `Relationship` | `is empty`, `not empty`, `is null`, `is not null` |
| `File` | `is empty`, `not empty`, `is null`, `is not null` |

### XML Escaping

Comparison operators must be XML-escaped in the `Operator` attribute:

| Operator | XAML Attribute Value |
|----------|---------------------|
| `>` | `Operator="&gt;"` |
| `>=` | `Operator="&gt;="` |
| `<` | `Operator="&lt;"` |
| `<=` | `Operator="&lt;="` |

All other operators are written as-is (e.g., `Operator="contains"`, `Operator="!="`, `Operator="="`).

## FilterValues — InArgument Type Mapping

Each `SimpleFilter` points to a slot in `FilterValues` via `ValueIndex`. The `InArgument` in that slot must use the correct `x:TypeArguments` for the field's SqlType:

| SqlType.Name | x:TypeArguments | Example |
|---|---|---|
| `NVARCHAR`, `MULTILINE` | `x:String` | `<InArgument x:TypeArguments="x:String">hello</InArgument>` |
| `INT` | `x:Int32` | `<InArgument x:TypeArguments="x:Int32">42</InArgument>` |
| `BIGINT` | `x:Int64` | `<InArgument x:TypeArguments="x:Int64">100000</InArgument>` |
| `FLOAT` | `x:Double` | `<InArgument x:TypeArguments="x:Double">3.14</InArgument>` |
| `DECIMAL` | `x:Decimal` | `<InArgument x:TypeArguments="x:Decimal">23</InArgument>` |
| `BIT` | `x:Boolean` | `<InArgument x:TypeArguments="x:Boolean">True</InArgument>` |
| `DATETIMEOFFSET` | `s:DateTimeOffset` | `<InArgument x:TypeArguments="s:DateTimeOffset">2026-04-07 +05:30</InArgument>` |
| `DATE` | `s:DateTime` | `<InArgument x:TypeArguments="s:DateTime">2026-04-07</InArgument>` |
| `UNIQUEIDENTIFIER` | `s:Guid` | `<InArgument x:TypeArguments="s:Guid">[New Guid()]</InArgument>` |

### in / not in — Array Values

The `in` and `not in` operators use `s:String[]` regardless of the field's SqlType:

```xml
<InArgument x:TypeArguments="s:String[]">[{ "value1", "value2", "value3" }]</InArgument>
```

- VB projects: `[{ "val1", "val2" }]` — square brackets wrap a VB array initializer
- C# projects: use `<CSharpValue>` with `new string[] { "val1", "val2" }` syntax

### Value-less Operators

Operators `is empty`, `not empty`, `is null`, `is not null` take no value. They still require a `ValueIndex` and a corresponding `FilterValues` slot, but the slot contains `<x:Null />`:

```xml
<!-- SimpleFilter -->
<uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="NumField"
    FieldType="UiPath.DataService.Core.Models.EntityField"
    Operator="is empty" ValueIndex="0" />

<!-- Corresponding FilterValues slot -->
<x:Null />
```

### Boolean Operators (Equals true / Equals false)

`Equals true` and `Equals false` are NOT value-less — they require an `x:Boolean` value in the FilterValues slot:

```xml
<!-- SimpleFilter -->
<uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="CreatedBy.IsActive"
    FieldType="UiPath.DataService.Core.Models.EntityField"
    Operator="Equals true" ValueIndex="0" />

<!-- Corresponding FilterValues slot -->
<InArgument x:TypeArguments="x:Boolean">True</InArgument>
```

```xml
<!-- Equals false -->
<uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="UpdatedBy.IsActive"
    FieldType="UiPath.DataService.Core.Models.EntityField"
    Operator="Equals false" ValueIndex="1" />

<!-- Corresponding FilterValues slot -->
<InArgument x:TypeArguments="x:Boolean">False</InArgument>
```

### Expression Values (Variables and Expressions)

Filter values support variable references and expressions, not just literals.

**VB projects** — wrap the expression in square brackets:
```xml
<InArgument x:TypeArguments="x:String">[myVariable]</InArgument>
<InArgument x:TypeArguments="x:Decimal">[price * 1.1]</InArgument>
```

**C# projects** — use a nested `<CSharpValue>` element (never use brackets in C# projects):
```xml
<InArgument x:TypeArguments="x:String">
  <CSharpValue x:TypeArguments="x:String">myVariable</CSharpValue>
</InArgument>
<InArgument x:TypeArguments="x:Decimal">
  <CSharpValue x:TypeArguments="x:Decimal">price * 1.1m</CSharpValue>
</InArgument>
```

## XAML Templates

### Template 1 — Single Condition (AND group, one filter)

```xml
<uda:QueryEntityRecords.FilterArguments>
  <uda:FilterArgument FilterActivityType="{x:Null}">
    <uda:FilterArgument.Filter>
      <uda:GroupFilter Index="0" Operator="AND">
        <uda:GroupFilter.Filters>
          <scg:List x:TypeArguments="uda:SimpleFilter" Capacity="4">
            <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="FIELD_NAME"
                FieldType="UiPath.DataService.Core.Models.EntityField"
                Operator="OPERATOR" ValueIndex="0" />
          </scg:List>
        </uda:GroupFilter.Filters>
        <uda:GroupFilter.Groups>
          <scg:List x:TypeArguments="uda:GroupFilter" Capacity="0" />
        </uda:GroupFilter.Groups>
      </uda:GroupFilter>
    </uda:FilterArgument.Filter>
  </uda:FilterArgument>
</uda:QueryEntityRecords.FilterArguments>
<uda:QueryEntityRecords.FilterValues>
  <scg:List x:TypeArguments="InArgument" Capacity="4">
    <InArgument x:TypeArguments="TYPE_ARGUMENT">VALUE</InArgument>
  </scg:List>
</uda:QueryEntityRecords.FilterValues>
```

### Template 2 — Multiple AND Conditions

```xml
<uda:QueryEntityRecords.FilterArguments>
  <uda:FilterArgument FilterActivityType="{x:Null}">
    <uda:FilterArgument.Filter>
      <uda:GroupFilter Index="0" Operator="AND">
        <uda:GroupFilter.Filters>
          <scg:List x:TypeArguments="uda:SimpleFilter" Capacity="4">
            <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="FIELD_1"
                FieldType="UiPath.DataService.Core.Models.EntityField"
                Operator="OPERATOR_1" ValueIndex="0" />
            <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="FIELD_2"
                FieldType="UiPath.DataService.Core.Models.EntityField"
                Operator="OPERATOR_2" ValueIndex="1" />
            <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="FIELD_3"
                FieldType="UiPath.DataService.Core.Models.EntityField"
                Operator="OPERATOR_3" ValueIndex="2" />
          </scg:List>
        </uda:GroupFilter.Filters>
        <uda:GroupFilter.Groups>
          <scg:List x:TypeArguments="uda:GroupFilter" Capacity="0" />
        </uda:GroupFilter.Groups>
      </uda:GroupFilter>
    </uda:FilterArgument.Filter>
  </uda:FilterArgument>
</uda:QueryEntityRecords.FilterArguments>
<uda:QueryEntityRecords.FilterValues>
  <scg:List x:TypeArguments="InArgument" Capacity="4">
    <InArgument x:TypeArguments="TYPE_1">VALUE_1</InArgument>
    <InArgument x:TypeArguments="TYPE_2">VALUE_2</InArgument>
    <InArgument x:TypeArguments="TYPE_3">VALUE_3</InArgument>
  </scg:List>
</uda:QueryEntityRecords.FilterValues>
```

### Template 3 — Nested Groups (AND root with OR child group)

Logical meaning: `(FIELD_1 OP VALUE_1) AND ((FIELD_2 OP VALUE_2) OR (FIELD_3 OP VALUE_3))`

```xml
<uda:QueryEntityRecords.FilterArguments>
  <uda:FilterArgument FilterActivityType="{x:Null}">
    <uda:FilterArgument.Filter>
      <uda:GroupFilter Index="0" Operator="AND">
        <uda:GroupFilter.Filters>
          <scg:List x:TypeArguments="uda:SimpleFilter" Capacity="4">
            <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="FIELD_1"
                FieldType="UiPath.DataService.Core.Models.EntityField"
                Operator="OPERATOR_1" ValueIndex="0" />
          </scg:List>
        </uda:GroupFilter.Filters>
        <uda:GroupFilter.Groups>
          <scg:List x:TypeArguments="uda:GroupFilter" Capacity="4">
            <uda:GroupFilter Index="0" Operator="OR">
              <uda:GroupFilter.Filters>
                <scg:List x:TypeArguments="uda:SimpleFilter" Capacity="4">
                  <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="FIELD_2"
                      FieldType="UiPath.DataService.Core.Models.EntityField"
                      Operator="OPERATOR_2" ValueIndex="1" />
                  <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="FIELD_3"
                      FieldType="UiPath.DataService.Core.Models.EntityField"
                      Operator="OPERATOR_3" ValueIndex="2" />
                </scg:List>
              </uda:GroupFilter.Filters>
              <uda:GroupFilter.Groups>
                <scg:List x:TypeArguments="uda:GroupFilter" Capacity="0" />
              </uda:GroupFilter.Groups>
            </uda:GroupFilter>
          </scg:List>
        </uda:GroupFilter.Groups>
      </uda:GroupFilter>
    </uda:FilterArgument.Filter>
  </uda:FilterArgument>
</uda:QueryEntityRecords.FilterArguments>
<uda:QueryEntityRecords.FilterValues>
  <scg:List x:TypeArguments="InArgument" Capacity="4">
    <InArgument x:TypeArguments="TYPE_1">VALUE_1</InArgument>
    <InArgument x:TypeArguments="TYPE_2">VALUE_2</InArgument>
    <InArgument x:TypeArguments="TYPE_3">VALUE_3</InArgument>
  </scg:List>
</uda:QueryEntityRecords.FilterValues>
```

### Template 4 — Value-less Operators (is empty, not empty, is null, is not null)

```xml
<uda:QueryEntityRecords.FilterArguments>
  <uda:FilterArgument FilterActivityType="{x:Null}">
    <uda:FilterArgument.Filter>
      <uda:GroupFilter Index="0" Operator="AND">
        <uda:GroupFilter.Filters>
          <scg:List x:TypeArguments="uda:SimpleFilter" Capacity="4">
            <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="FIELD_1"
                FieldType="UiPath.DataService.Core.Models.EntityField"
                Operator="is empty" ValueIndex="0" />
            <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="FIELD_2"
                FieldType="UiPath.DataService.Core.Models.EntityField"
                Operator="not empty" ValueIndex="1" />
          </scg:List>
        </uda:GroupFilter.Filters>
        <uda:GroupFilter.Groups>
          <scg:List x:TypeArguments="uda:GroupFilter" Capacity="0" />
        </uda:GroupFilter.Groups>
      </uda:GroupFilter>
    </uda:FilterArgument.Filter>
  </uda:FilterArgument>
</uda:QueryEntityRecords.FilterArguments>
<uda:QueryEntityRecords.FilterValues>
  <scg:List x:TypeArguments="InArgument" Capacity="4">
    <x:Null />
    <x:Null />
  </scg:List>
</uda:QueryEntityRecords.FilterValues>
```

### Template 5 — in / not in Operators

```xml
<uda:QueryEntityRecords.FilterArguments>
  <uda:FilterArgument FilterActivityType="{x:Null}">
    <uda:FilterArgument.Filter>
      <uda:GroupFilter Index="0" Operator="AND">
        <uda:GroupFilter.Filters>
          <scg:List x:TypeArguments="uda:SimpleFilter" Capacity="4">
            <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="FIELD_1"
                FieldType="UiPath.DataService.Core.Models.EntityField"
                Operator="in" ValueIndex="0" />
            <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="FIELD_2"
                FieldType="UiPath.DataService.Core.Models.EntityField"
                Operator="not in" ValueIndex="1" />
          </scg:List>
        </uda:GroupFilter.Filters>
        <uda:GroupFilter.Groups>
          <scg:List x:TypeArguments="uda:GroupFilter" Capacity="0" />
        </uda:GroupFilter.Groups>
      </uda:GroupFilter>
    </uda:FilterArgument.Filter>
  </uda:FilterArgument>
</uda:QueryEntityRecords.FilterArguments>
<uda:QueryEntityRecords.FilterValues>
  <scg:List x:TypeArguments="InArgument" Capacity="4">
    <InArgument x:TypeArguments="s:String[]">[{ "value1", "value2" }]</InArgument>
    <InArgument x:TypeArguments="s:String[]">[{ "value3", "value4" }]</InArgument>
  </scg:List>
</uda:QueryEntityRecords.FilterValues>
```

> The `in`/`not in` values are always `s:String[]` regardless of the field's SqlType. Requires `xmlns:s`.

## Step-by-Step: Generate Filter XAML

1. **Read `EntitiesStore.json`** — find the target entity by name under `Entities[]`. Note the entity `Id`.
2. **Identify filter fields** — for each condition, find the field in `Entities[].Fields[]`. Note:
   - `Field.Name` — used as `SimpleFilter.FieldName`
   - `Field.SqlType.Name` — determines valid operators and `InArgument` type
   - `Field.FieldDisplayType` — determines operator set for non-Basic fields
3. **For relationship fields** — use dot notation: `RelationshipFieldName.ChildFieldName` (e.g., `CreatedBy.Name`). Look up the referenced entity's fields via `Field.ReferenceEntity` to find the child field's SqlType.
4. **Choose operators** — for each condition, pick an operator from the [Operator Reference](#operator-reference-by-field-type) table matching the field's SqlType and FieldDisplayType. Verify the operator is in the valid set.
5. **Determine grouping logic** — decide AND vs OR. For mixed logic (e.g., `A AND (B OR C)`), use nested `GroupFilter.Groups`.
6. **Assign ValueIndex** — assign sequential integers starting from 0 across ALL groups. Root group filters use 0, 1, 2...; nested group filters continue the sequence.
7. **Build FilterValues** — create `InArgument` entries in order matching ValueIndex. Use the correct `x:TypeArguments` from the [type mapping table](#filtervalues--inargument-type-mapping). For value-less operators, insert `<x:Null />`.
8. **Check namespace declarations** — if any FilterValues entry uses `s:DateTimeOffset`, `s:Guid`, or `s:String[]`, ensure `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"` is on the root `<Activity>` element.
9. **XML-escape comparison operators** — replace `>` with `&gt;`, `>=` with `&gt;=`, `<` with `&lt;`, and `<=` with `&lt;=` in the `Operator` attribute.

## Complete Worked Example

Query `NumericEntity` where: NumField equals 23, AND CreatedBy.IsActive equals True, AND CreatedBy.Name contains "suphal", AND (UpdateTime > 2026-04-07 OR Id != New Guid()).

Entity is VB project. EntityId from EntitiesStore.json: `cd543a02-3621-f111-9a48-000d3a354532`.

```xml
<uda:QueryEntityRecords x:TypeArguments="local:NumericEntity"
    OutputRecords="{x:Null}"
    SortAscending="True" SortByField="{x:Null}" TotalRecords="{x:Null}"
    ContinueOnError="False" DisplayName="Query Entity Records"
    EntityId="cd543a02-3621-f111-9a48-000d3a354532"
    ExpansionDepth="2"
    QueriedEntityId="cd543a02-3621-f111-9a48-000d3a354532"
    Skip="0" TimeoutInMs="30000" Top="100">
  <uda:QueryEntityRecords.FilterArguments>
    <uda:FilterArgument FilterActivityType="{x:Null}">
      <uda:FilterArgument.Filter>
        <uda:GroupFilter Index="0" Operator="AND">
          <uda:GroupFilter.Filters>
            <scg:List x:TypeArguments="uda:SimpleFilter" Capacity="4">
              <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="NumField"
                  FieldType="UiPath.DataService.Core.Models.EntityField"
                  Operator="=" ValueIndex="0" />
              <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="CreatedBy.IsActive"
                  FieldType="UiPath.DataService.Core.Models.EntityField"
                  Operator="=" ValueIndex="1" />
              <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="CreatedBy.Name"
                  FieldType="UiPath.DataService.Core.Models.EntityField"
                  Operator="contains" ValueIndex="2" />
            </scg:List>
          </uda:GroupFilter.Filters>
          <uda:GroupFilter.Groups>
            <scg:List x:TypeArguments="uda:GroupFilter" Capacity="4">
              <uda:GroupFilter Index="0" Operator="OR">
                <uda:GroupFilter.Filters>
                  <scg:List x:TypeArguments="uda:SimpleFilter" Capacity="4">
                    <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="UpdateTime"
                        FieldType="UiPath.DataService.Core.Models.EntityField"
                        Operator="&gt;" ValueIndex="3" />
                    <uda:SimpleFilter ExpressionValue="{x:Null}" FieldName="Id"
                        FieldType="UiPath.DataService.Core.Models.EntityField"
                        Operator="!=" ValueIndex="4" />
                  </scg:List>
                </uda:GroupFilter.Filters>
                <uda:GroupFilter.Groups>
                  <scg:List x:TypeArguments="uda:GroupFilter" Capacity="0" />
                </uda:GroupFilter.Groups>
              </uda:GroupFilter>
            </scg:List>
          </uda:GroupFilter.Groups>
        </uda:GroupFilter>
      </uda:FilterArgument.Filter>
    </uda:FilterArgument>
  </uda:QueryEntityRecords.FilterArguments>
  <uda:QueryEntityRecords.FilterValues>
    <scg:List x:TypeArguments="InArgument" Capacity="8">
      <InArgument x:TypeArguments="x:Decimal">23</InArgument>
      <InArgument x:TypeArguments="x:Boolean">True</InArgument>
      <InArgument x:TypeArguments="x:String">suphal</InArgument>
      <InArgument x:TypeArguments="s:DateTimeOffset">2026-04-07 +05:30</InArgument>
      <InArgument x:TypeArguments="s:Guid">[New Guid()]</InArgument>
    </scg:List>
  </uda:QueryEntityRecords.FilterValues>
</uda:QueryEntityRecords>
```

## Anti-Patterns — What NOT to Do

1. **Do NOT use CLR type strings for FieldType.** `FieldType` is always `"UiPath.DataService.Core.Models.EntityField"` — never `"System.String"`, `"System.Int32"`, etc.
2. **Do NOT use `x:DateTimeOffset` or `x:Guid`.** These are not in the `x:` schema. Use `s:DateTimeOffset` and `s:Guid` with the `s:` namespace.
3. **Do NOT skip FilterValues slots for value-less operators.** Even `is empty` / `not empty` / `is null` / `is not null` require a `ValueIndex` pointing to an `<x:Null />` slot. Note: `Equals true` / `Equals false` are NOT value-less — they require `<InArgument x:TypeArguments="x:Boolean">True</InArgument>` or `False`.
4. **Do NOT use lowercase `and` / `or`.** GroupFilter.Operator must be uppercase `AND` or `OR`.
5. **Do NOT forget to XML-escape comparison operators.** Write `&gt;` for `>`, `&gt;=` for `>=`, `&lt;` for `<`, `&lt;=` for `<=` in the Operator attribute.
6. **Do NOT use brackets `[...]` for expressions in C# projects.** Brackets create `VisualBasicValue` nodes. Use `<CSharpValue>` instead.
7. **Do NOT omit `GroupFilter.Groups`.** Every GroupFilter must have both `Filters` and `Groups` child elements, even if empty (use `Capacity="0"` for empty lists).
8. **Do NOT use separate FilterValues lists per group.** There is one flat `FilterValues` list shared across all groups. ValueIndex is globally sequential.
9. **Do NOT set FilterActivityType.** Leave it as `{x:Null}`.
