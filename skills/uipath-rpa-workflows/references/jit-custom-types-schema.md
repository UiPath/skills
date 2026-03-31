# JIT custom types schema

Read this file when: you need to discover property names and CLR types for dynamic/connector activities.

## When to use

- Populating an `Assign` activity that targets a custom type property
- Creating a variable typed to a custom entity (Salesforce, ServiceNow, etc.)
- Setting properties on an Integration Service entity

## Steps

### 1. Read the schema file

```
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

### 2. Navigate the JSON

Key path: `jitAssemblyCompilerCommands[*].bundleOptions.entitiesBundle.Types`

Each type has a `properties` array with `name` and `type.ClrType`.

### 3. Map CLR types to short forms

| Full CLR type | Short form |
|---------------|------------|
| `System.String, System.Private.CoreLib` | `String` |
| `System.Int32, System.Private.CoreLib` | `Int32` |
| `System.Double, System.Private.CoreLib` | `Double` |
| `System.Boolean, System.Private.CoreLib` | `Boolean` |
| `System.DateTime, System.Private.CoreLib` | `DateTime` |
| `System.Guid, System.Private.CoreLib` | `Guid` |
| ``System.Nullable`1[[System.Double, ...]]`` | `Double?` |
| ``System.Nullable`1[[System.DateTime, ...]]`` | `DateTime?` |

Rules:
- Simple types: extract the type name before the first comma.
- Nullable types: extract the inner type and append `?`.
- Collection types: use arrays in XAML (`InnerType[]`).
