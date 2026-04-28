# Compliance · Business (StudioX) — product quirks

Product-specific conventions for `productIdentifier: "Business"`. Follow the shared CREATE recipe in [../../../policy-crud.md](../../../policy-crud.md). Shared Studio-family quirks live in [_studio-family.md](_studio-family.md) — read that first.

## Product identifiers

| Field | Value |
|---|---|
| `--product-name` | `Business` (exact case — UiPath's internal name) |
| Display label | `StudioX` (what admins see in the AOPS UI) |
| Default license | `StudioX` or `Business` depending on license mix |

## Shared quirks

See [_studio-family.md](_studio-family.md) — enum casing for `default-project-language`, `default-project-framework`, `default-action`; array identifier contracts; nested-object container casing.

## Business-specific notes

- **No `default-pip-type`** field — this is a Development/Automate-only setting.
- **Smaller rule set**: ~14 embedded Workflow Analyzer rules by default (Development has ~65). Counter array is empty by default.
- **Has `require-user-publish-dialog-message`** — a free-text string shown to users when they publish. Not an enum; pass any string.
- Uses the same Azure DevOps default package source as Development.
- **Nested objects present**: `allowed-project-frameworks`, `telemetry-redirection-options`, `allowed-publish-feeds`, `enforce-repositories-config`.

## Error triage

Shared patterns in [_studio-family.md](_studio-family.md#shared-error-triage). No Business-only errors observed yet — add here when found.
