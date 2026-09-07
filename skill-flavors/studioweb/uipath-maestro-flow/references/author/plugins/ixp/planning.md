<!--skill-flavor:ixp-intro:start-->
IxP Extraction nodes invoke a **trained, published** UiPath Intelligent eXtraction Platform (IxP) model to pull structured fields out of unstructured or semi-structured documents (PDFs, photos, scanned forms). They are tenant-specific resources that appear in the registry after `uip maestro flow registry pull` (auth is host-provided).
<!--skill-flavor:ixp-intro:end-->

<!--skill-flavor:ixp-prerequisites:start-->
- Auth is host-provided — a 401/403 from the registry means the signed-in user lacks rights on the tenant; never run `uip login`.
- `uip maestro flow registry pull --force` must be run to cache IxP model node types locally.
- A trained IxP model must be **deployed to an Orchestrator folder** — the flow registry lists folder deployments only. Create one via the `uipath-ixp` skill. If none exists, see [No published model](#no-published-model-branch-on-documents).
<!--skill-flavor:ixp-prerequisites:end-->

<!--skill-flavor:ixp-discovery-note:start-->
Auth is host-provided. Only models with a folder deployment on your tenant appear — publishing alone does not surface a model here. The returned node type uses a **two-segment tail** (`{modelName}.{fullyQualifiedName}`), unlike `uipath.core.*` siblings which use a single-segment tail. Both tail segments are sanitized: lowercase, then runs of any character outside `[a-z0-9]` → single `-`. So an FQN of `Shared/invoice-model` lands as `shared-invoice-model`. See [impl.md](impl.md) for the full rule and worked examples.
<!--skill-flavor:ixp-discovery-note:end-->

<!--skill-flavor:ixp-listing-steps:start-->
1. Refresh the cache and search (auth is host-provided — there is no login status to check):
   ```bash
   uip maestro flow registry pull --force
   uip maestro flow registry search "uipath.ixp" --output json
   ```
2. Format `Data[]` as a table — `DisplayName`, `NodeType`, `Version`. Each entry is one published model / runtime project. See [impl.md — Listing Published Models](impl.md#listing-published-models) for parsing details.
<!--skill-flavor:ixp-listing-steps:end-->
