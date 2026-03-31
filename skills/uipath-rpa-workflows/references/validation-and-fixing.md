# Validation and fixing

Read this file when: you are in the validate/fix loop and need detailed procedures for package resolution, JIT types, or debugging.

@../shared/validation-loop.md

RPA-specific validation procedures. Shared iteration loop, fix-one-thing rule, and smoke test are in the file above.

## Package error resolution

```bash
# Check current dependencies:
Read: file_path="{projectRoot}/project.json"

# Install or update (omit version for latest):
uip rpa install-or-update-packages --packages '[{"id": "UiPath.Excel.Activities"}]' --format json
```

If `install-or-update-packages` fails:
- Package not found: verify the exact package ID with `uip rpa find-activities`.
- Network/feed error: user may need to check NuGet feed configuration in Studio settings.

## Resolving dynamic activity custom types

After adding a dynamic activity (connector) via `get-default-activity-xaml`, read the JIT custom types schema to discover property names and CLR types:

```
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

See [jit-custom-types-schema.md](jit-custom-types-schema.md) for the full schema structure and type mapping.

## Focus activity for debugging

When `get-errors` returns an error referencing a specific activity, use `focus-activity` to highlight it in Studio:

```bash
uip rpa focus-activity --activity-id "Assign_1" --format json
```

## Fix order

1. **Package errors**: missing namespace, unknown activity type. Install/update the package.
2. **Structural errors**: invalid XML, missing closing tags. Read and edit the XAML.
3. **Type errors**: wrong property type, invalid cast. Check activity docs for correct types.
4. **Property errors**: unknown properties, misconfigured groups. Check activity docs or `get-default-activity-xaml`.
5. **Logic errors**: wrong behavior, incorrect expressions. Read XAML and correct. Use `run-file` for runtime validation.

## When stuck

- Defer minor configuration details to the user (connections, placeholder values).
- If an activity has unresolvable issues, consider `InvokeCode` as a last resort.
- Do not retry the same fix more than 3 times. Explain the error to the user.
