# Compliance · Automate — product quirks

Product-specific conventions for `productIdentifier: "Automate"`. Follow the shared CREATE recipe in [../../../policy-crud.md](../../../policy-crud.md). Shared Studio-family quirks live in [_studio-family.md](_studio-family.md) — read that first.

## Product identifiers

| Field | Value |
|---|---|
| `--product-name` | `Automate` (exact case) |
| Default license | varies — Automate is a newer SKU bundle; check org's license mix |
| Restricted | Yes — `"isRestricted": true` in `uip gov aops-policy product list`. Some orgs don't have this product enabled. |

## Shared quirks

See [_studio-family.md](_studio-family.md) — enum casing for `default-project-language`, `default-project-framework`, `default-action`; array identifier contracts; nested-object container casing.

## Automate-specific notes

- **Has `default-pip-type`** (same as Development): `"ChildSession"` \| `"Host"`.
- **Same rule set as Development**: ~65 embedded Workflow Analyzer rules + counters.
- Same default package source as Development (Azure DevOps public feed).
- **Nested objects present**: `allowed-project-frameworks`, `telemetry-redirection-options`, `allowed-publish-feeds`, `enforce-repositories-config` — identical structure to Development.

## Error triage

| Error message fragment | Likely cause | Action |
|---|---|---|
| `403 Forbidden` on create or assign | Org may not have Automate enabled | Halt. Check `uip gov aops-policy product get Automate` — if `isRestricted: true` and not in the org's entitlement, skip the policy with a `reason: "product-not-entitled"` in the deploy record. |

Plus the shared patterns in [_studio-family.md](_studio-family.md#shared-error-triage).
