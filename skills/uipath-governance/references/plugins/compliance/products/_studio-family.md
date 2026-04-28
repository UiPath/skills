# Compliance · Studio Family — shared quirks

Shared quirks for the four Studio-family AOPS products: **Development** (Studio), **Business** (StudioX), **Automate**, and **StudioPro**. Each product's own `*.md` file picks up from here and layers product-specific bits.

All four share the same form-template structure: ~40–90 boolean toggles, a handful of enum strings, and four complex arrays. The quirks below apply to every Studio-family product unless the product file overrides.

## CLI value quirks — will cause 400 if wrong

### Enum string values — case-sensitive

These enums use specific casing the API enforces. A string with the wrong case is a 400.

| Property | Accepted values |
|---|---|
| `default-project-language` | `"visualBasic"` \| `"csharp"` · camelCase, NOT `"VisualBasic"` / `"VB"` / `"CSharp"` |
| `default-project-framework` | `"Modern"` \| `"Legacy"` \| `"CrossPlatform"` · PascalCase / compound |
| `default-pip-type` *(Development + Automate only)* | `"ChildSession"` \| `"Host"` · PascalCase |

Every embedded-rules item carries a `default-action` enum:
| `default-action` | `"Error"` \| `"Warning"` \| `"Info"` · PascalCase |

### Array item contracts

Four array fields show up (in varying subsets per product). All share the same contract: **every item must have an `identifier` field**, and `is-enabled-*` flags must match the array's key.

| Array | Item shape (minimum) |
|---|---|
| `default-package-source[]` | `{ is-enabled-default-package-source, default-package-source-name, default-package-source-source, identifier }` where `identifier = name + source` concatenated |
| `template-feeds[]` | `{ template-feed-is-enabled, template-feed-name, identifier }` |
| `embedded-rules-config-rules[]` | `{ is-enabled-embedded-rules-config-rules, code-embedded-rules-config-rules, default-action, parameters-embedded-rules-config-rules, identifier }` where `identifier = code` |
| `embedded-rules-config-counter[]` | `{ is-enabled-embedded-rules-config-counter, code-embedded-rules-config-counter, parameters-embedded-rules-config-counter, identifier }` |

**Rule:** when building these arrays from a pack, either pass the full default item shape from `template get --output-form-data` (don't shortcut), or ensure your items include every field listed above — including the `identifier` concatenation. Missing `identifier` causes silent de-duplication or 400 depending on path.

### Nested-object fields

These products wrap some settings inside object fields whose keys are enum-like. The container keys themselves are not freely nameable — they must match the template.

| Container | Expected keys |
|---|---|
| `allowed-project-frameworks` *(Development)* | `Classic`, `Modern`, `CrossPlatform` — PascalCase boolean values |
| `telemetry-redirection-options` *(Development + Automate)* | `instrumentation-keys` — object with string values |
| `allowed-publish-feeds` *(Development + Automate)* | `Custom`, `PersonalWorkspace`, `TenantPackages`, `FolderPackages`, `HostLibraries` — PascalCase boolean values |
| `enforce-repositories-config` | `enforce-repositories-config-allow-edit-repositories` (bool), `enforce-repositories-config-repositories` (array of repo configs) |

A pack that sets `allowed-publish-feeds.custom` (lowercase `custom`) instead of `Custom` will silently omit the value.

## Shared error triage

| Error message fragment | Likely cause | Action |
|---|---|---|
| `default-project-language` invalid enum | Wrong case (`"VisualBasic"` / `"VB"`) | Coerce to `"visualBasic"`. |
| `default-project-framework` invalid enum | Wrong value (`"Windows"` instead of `"Legacy"`) | Map to `"Modern"` \| `"Legacy"` \| `"CrossPlatform"`. |
| `default-action` invalid in an embedded rule | Passed lowercase | Coerce to `"Error"` \| `"Warning"` \| `"Info"`. |
| Array item missing `identifier` | Item built without concat | Rebuild per the generate-data shape, or pass the whole array from generate-data untouched. |
| `allowed-publish-feeds.custom` has no effect | Wrong case on the container key | Use PascalCase: `Custom`, not `custom`. |
