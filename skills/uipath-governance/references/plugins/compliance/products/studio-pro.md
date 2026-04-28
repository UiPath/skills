# Compliance · StudioPro — product quirks

Product-specific conventions for `productIdentifier: "StudioPro"`. Follow the shared CREATE recipe in [../../../policy-crud.md](../../../policy-crud.md). Shared Studio-family quirks live in [_studio-family.md](_studio-family.md) — read that first.

## Product identifiers

| Field | Value |
|---|---|
| `--product-name` | `StudioPro` (exact case) |
| Default license | `StudioPro` |

## Shared quirks

See [_studio-family.md](_studio-family.md) — enum casing for `default-project-language`, `default-project-framework`, `default-action`; array identifier contracts.

## StudioPro-specific notes

- **No `default-pip-type`** — this is Development / Automate only.
- **No top-level nested objects** (unlike Development / Business / Automate which have `allowed-project-frameworks`, `telemetry-redirection-options`, `allowed-publish-feeds`, `enforce-repositories-config`).
- **Default package source points to MyGet**, not Azure DevOps:
  `https://www.myget.org/F/workflow/` (Development/Business/Automate use `pkgs.dev.azure.com/uipath/Public.Feeds/...`)
  Packs shared across Studio-family products must account for this difference — StudioPro has a different `identifier` value for the default source.
- ~63 embedded Workflow Analyzer rules by default. Same identifier contract as other Studio-family products.

## Error triage

Shared patterns in [_studio-family.md](_studio-family.md#shared-error-triage). No StudioPro-only errors observed yet — add here when found.
