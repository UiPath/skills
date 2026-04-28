# Compliance · Development (Studio) — product quirks

Product-specific conventions for `productIdentifier: "Development"`. Follow the shared CREATE recipe in [../../../policy-crud.md](../../../policy-crud.md). Shared Studio-family quirks live in [_studio-family.md](_studio-family.md) — read that first.

## Product identifiers

| Field | Value |
|---|---|
| `--product-name` | `Development` (exact case — this is UiPath's internal name for Studio) |
| Display label | `Studio` (what admins see in the AOPS UI) |
| Default license | `Development` or `StudioPro` depending on the org's license mix |

## Shared quirks

See [_studio-family.md](_studio-family.md) — enum casing for `default-project-language`, `default-project-framework`, `default-action`; array identifier contracts; nested-object container casing.

## Development-specific notes

- **Has `default-pip-type`** enum: `"ChildSession"` \| `"Host"` (Business / StudioPro do not).
- **Default package source** points to UiPath's Azure DevOps public feed:
  `https://pkgs.dev.azure.com/uipath/Public.Feeds/_packaging/UiPath-Official/nuget/v3/index.json`
  (StudioPro uses MyGet — see its file.)
- **Largest rule set of the family**: ~65 embedded Workflow Analyzer rules by default. Packs that touch `embedded-rules-config-rules[]` should prefer setting `is-enabled-*` on existing items over inserting new ones.
- **Nested objects present**: `allowed-project-frameworks`, `telemetry-redirection-options`, `allowed-publish-feeds`, `enforce-repositories-config`.

## Error triage

Shared patterns in [_studio-family.md](_studio-family.md#shared-error-triage). No Development-only errors observed yet — add here when found.
