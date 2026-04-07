# JIT Custom Types Schema Lookup

Use this skill to discover properties and CLR types of custom JIT-compiled types in the current project.

## When to Use

- Populating an `Assign` activity that targets a custom type property
- Creating a variable typed to a custom entity
- Setting properties on an Integration Service entity (e.g., Salesforce, ServiceNow)
- Any time you need to know what properties a custom type exposes and their .NET types

## Steps

### 1. Read the Schema File

Use the `Read` tool to read the JIT custom types schema:

```
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

### 2. Navigate the JSON Structure

The file has the following structure:

```json
{
  "jitAssemblyCompilerCommands": [
    {
      "bundleOptions": {
        "entitiesBundle": {
          "Types": {
            "<TypeName>": {
              "properties": [
                {
                  "name": "<PropertyName>",
                  "type": {
                    "ClrType": "<FullClrTypeString>"
                  }
                }
              ]
            }
          }
        }
      }
    }
  ]
}
```

Key path: `jitAssemblyCompilerCommands[*].bundleOptions.entitiesBundle.Types`

Each entry under `Types` is keyed by the fully-qualified type name. Each type contains a `properties` array where each property has:
- `name` - the property name (e.g., `AccountId`, `Name`, `Amount`)
- `type.ClrType` - the full .NET CLR type string

### 3. Map CLR Types to Short Forms

Convert the verbose CLR type strings to usable short forms:

| Full CLR Type | Short Form |
|---------------|------------|
| `System.String, System.Private.CoreLib` | `String` |
| `System.Int32, System.Private.CoreLib` | `Int32` |
| `System.Int64, System.Private.CoreLib` | `Int64` |
| `System.Double, System.Private.CoreLib` | `Double` |
| `System.Boolean, System.Private.CoreLib` | `Boolean` |
| `System.DateTime, System.Private.CoreLib` | `DateTime` |
| `System.DateTimeOffset, System.Private.CoreLib` | `DateTimeOffset` |
| `System.Decimal, System.Private.CoreLib` | `Decimal` |
| `System.Guid, System.Private.CoreLib` | `Guid` |
| ``System.Nullable`1[[System.Double, ...]]`` | `Double?` |
| ``System.Nullable`1[[System.Int32, ...]]`` | `Int32?` |
| ``System.Nullable`1[[System.Boolean, ...]]`` | `Boolean?` |
| ``System.Nullable`1[[System.DateTime, ...]]`` | `DateTime?` |
| ``System.Nullable`1[[System.DateTimeOffset, ...]]`` | `DateTimeOffset?` |

**General rules:**
- For simple types: extract the type name before the first comma (e.g., `System.String` becomes `String`)
- For `Nullable` types: extract the inner type name and append `?`
- For collection types (e.g., `System.Collections.Generic.List`1[...]`): use **arrays** in XAML — short form `InnerType[]` (e.g., `Int32[]`). In XAML use `x:TypeArguments="s:Int32[]"`; in expressions use array literals (e.g., VB `New Integer() {1, 2, 3}`, C# `new int[] { 1, 2, 3 }`).

### 4. Apply to Workflow

Use the discovered property names and their simplified types when:
- Writing XAML `Assign` activities: set the correct property path and value type
- Declaring variables: use the correct CLR type annotation
- Building `InvokeCode` or coded workflow expressions that reference custom type properties
- Declaring arguments in the workflow: use the correct CLR type for In/Out/InOut arguments that hold custom types
- Configuring an `InvokeWorkflow` activity: map arguments whose types are custom entities so types match the callee workflow
