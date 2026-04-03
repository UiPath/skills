# Validation & Fixing — RPA

@../shared/validation-loop.md

RPA-specific validation procedures. Shared iteration loop, fix-one-thing rule, and smoke test are in the file above.

## Package Error Resolution

```
Read: file_path="{projectRoot}/project.json"     -> check current dependencies

Bash: uip rpa install-or-update-packages --packages '[{"id": "UiPath.Excel.Activities"}]' --use-studio
```

Omit `version` to automatically resolve the latest compatible version (preferred — gets newest docs and features). Only pin a specific version when you have a reason to (e.g., known compatibility constraint).

**If `install-or-update-packages` fails:**
- **Package not found**: Verify the exact package ID — check spelling, use `uip rpa find-activities --use-studio` to discover the correct package name from an activity's assembly
- **Network/feed error**: The user may need to check their NuGet feed configuration in Studio settings

## Resolving Dynamic Activity Custom Types

Dynamic activities (e.g., Integration Service connectors) retrieved via `uip rpa get-default-activity-xaml --use-studio` (with `--activity-type-id`) may use **JIT-compiled custom types** for their input/output properties. After the activity is added to the workflow, when you need to discover the property names and CLR types of these custom entities (e.g., to populate an `Assign` activity targeting a custom type property, or to create a variable of a custom type), read the JIT custom types schema:

```
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

## Focus Activity for Debugging

When `get-errors` returns an error referencing a specific activity (by IdRef or DisplayName), use `focus-activity` to highlight it in the Studio designer. This helps the user see the problematic activity in context and verify fixes visually:

```bash
# Focus a specific activity by its IdRef (from the error output):
uip rpa focus-activity --activity-id "Assign_1" --use-studio

# Focus all activities sequentially (useful for walkthrough):
uip rpa focus-activity --use-studio
```

This is especially useful when:
- An error references an activity and you want the user to confirm the context
- You've made a fix and want to show the user which activity was modified
- The error is ambiguous and you need to verify which activity instance is affected

For full runtime debugging capabilities (breakpoints, stepping, `TestActivity`, `StartDebuggingFromHere`, exception handling), see **[debugging.md](debugging.md)**.
