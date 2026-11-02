# Platform Availability Guide

> **Cloud is not uniform.** The ✅ Cloud column assumes standard Automation Cloud. Public Sector / GovCloud, Dedicated, Test Cloud, region-specific instances, per-tenant service enablement, and license entitlements can block products inside that column; for any variant or unverified entitlement, confirm the product is enabled on the tenant, or mark it `[SME REVIEW]` per product.

Product × delivery-model availability matrix consulted by the [Constraint Gate](product-selection-guide.md#constraint-gate) before recommendation. The authoritative live source is [Product and feature availability across delivery options](https://docs.uipath.com/overview/other/latest/overview/product-and-feature-availability-across-delivery-options); it wins over this file.

> **As of:** 2026-06 · latest Automation Suite = **2.2510** (2025.10 LTS; versioning `[Major].[YYMM].[Patch]`), current patch **2.2510.2** (2026-04).

## Gating Rules

1. Gate against the customer's column: `cloud` → Cloud-available products; `automation-suite` → the AS column at the customer's version; `standalone` → the Standalone note. An AS version older than a product's "AS since" is **Not available**. Ordering: `2021.10 < 2022.4 < 2023.4 < 2024.10 < 2.2510 < 2.2510.2`; `[Major].[YYMM]` (`2.2510 = 2025.10`) sorts after every `YYYY.MM` version.
2. If the AS version is unknown, gate against the latest AS column, add an `[SME REVIEW]` row for the version in §16 Deployment Environment, and warn on every product whose "AS since" is 2.2510 or newer.
3. Maestro and Agents on AS require the EKS/AKS or OpenShift profile (not classic Linux/k3s), Temporal-as-a-Service, and an AI Trust Layer LLM connection. If the SDD includes them on AS, add a profile-prerequisite warning and `[SME REVIEW]` row.
4. **Verification rule.** Web-search the authoritative page before finalizing the SDD when a needed cell is ⚠ Verify, the customer's AS version is unknown, or this file's "As of" is more than ~6 months old. A cell is needed only while its product remains a candidate after blocking; do not verify blocked products. Record what was verified, or why verification was skipped, in `Decisions Made` row 1 reason.
5. An ✅ AS cell may differ from cloud in feature depth (per UiPath's own matrix page). Put Notes-column limitations into the SDD as constraints, not footnotes.
6. Classify "No cloud connectivity" before gating: (a) offline/air-gapped install → every "unsupported on offline installs" note (DU modern, Integration Service) is **BLOCK**, and exclude SaaS dependencies such as Microsoft 365 mailboxes; (b) only the UiPath-cloud link is absent while internet egress exists → **WARN** + `[SME REVIEW]`. If unclassifiable, apply (b) and add an `[SME REVIEW]` row naming the stricter reading's consequences.

## Availability Matrix

> **Scope.** Lists products the planner can route to a skill. Document Understanding / IXP route through `uipath-ixp`. Pure platform/analytics features without a planner build path (Insights, AI Center, Task Mining, Autopilot for Everyone, Studio Web) are omitted and must be gated manually if a PDD names them.

| Product | Cloud | Automation Suite | AS notes | Alternative when blocked |
|---|---|---|---|---|
| RPA (Studio, Robot, Orchestrator) | ✅ | ✅ since first AS (2021.10) | No serverless/cloud robots on AS; use Automation Suite Robots or provisioned unattended robots | — |
| Solutions (`.uipx` deploy) | ✅ | ✅ since **2.2510** | Older AS cannot ingest `.uipx`; terminal artifact degrades to per-package Orchestrator deploys | Per-package publish via Orchestrator (route deploy tasks to `uipath-platform` instead of `uipath-solution`) |
| Maestro Flow (.flow orchestration) | ✅ | ✅ since **2.2510.2** — EKS/AKS + OpenShift profiles only | Requires Temporal-as-a-Service (auto-enabled); Optimize dashboard cloud-only | Orchestrator queues + dispatcher/performer state machine; Action Center approvals for human gates |
| Maestro BPMN (.bpmn orchestration) | ✅ | ✅ since **2.2510.2** — EKS/AKS + OpenShift profiles only | Requires Temporal-as-a-Service (auto-enabled); Optimize dashboard cloud-only | Orchestrator queues + dispatcher/performer state machine; Action Center approvals for human gates |
| Agents / Agent Builder | ✅ | ✅ since **2.2510.2** | Requires AI Trust Layer toggle + ≥1 LLM connection (cloud-hosted or self-hosted model); coded agents via Orchestrator 2.2510 | Deterministic RPA + rule-based decisioning; HITL escalation for judgment steps |
| Coded Apps (TypeScript web apps) | ✅ (some geo limits) | ❌ **Not available** — cloud only | "Automation Suite and Dedicated deployments are not supported at this time" | **None** — no on-prem app equivalent in this toolchain. Flag the app touchpoint as `[SME REVIEW]`; do not substitute a product the planner cannot build. |
| API Workflows | ✅ | ✅ since **2.2510** | Maestro integration needs 2.2510.2+ | RPA Process invoked via Orchestrator API / queue |
| Data Service (Data Fabric entities) | ✅ | ✅ since 2022.4 | No retention/TTL policy on file fields on any delivery model; explicitly design storage lifecycle (cleanup process) when storing files | — |
| Integration Service | ✅ (full catalog) | ✅ full since **2.2510** (2024.10 EKS/AKS-only, patched) | Not supported with FIPS 140-2 or air-gapped installs; connectors are admin-curated per tenant, not the full cloud catalog; confirm the needed connector is installed | Direct HTTP/REST calls from RPA or API Workflows |
| Action Center | ✅ | ✅ | Agent escalation integration needs 2.2510.2 | — |
| Document Understanding (classic) | ✅ | ✅ | — | — |
| Document Understanding (modern projects) | ✅ | ✅ since 2024.10 | Needs GPU allocation; unsupported on OpenShift / offline installs (per 2024.10 docs — ⚠ Verify for newer) | Classic DU; rule-based extraction for fixed-format generated documents |
| IXP | ✅ | ❌ Not available (⚠ Verify — on-prem delivery announced for late 2026) | — | DU modern/classic on AS; rule-based extraction for generated PDFs |
| Test Manager | ✅ | ✅ since 2021.10 (full Test Cloud since 2.2510) | — | — |

## Standalone (MSI Orchestrator) Note

Standalone is Orchestrator + Studio/Robot (+ standalone Test Manager) only: **No** Apps, Integration Service, Studio Web, Data Service, API Workflows, Maestro (Flow and BPMN), Agents, or Solutions. ⚠ Verify before relying on any product beyond core RPA + Orchestrator. Default architecture: RPA projects + Orchestrator queues/assets/triggers, deployed as individual packages via `uipath-platform`.

## Maintenance

When a cell changes (UiPath ships or removes a product on a delivery model), update that row and the "As of" stamp. Keep "AS since" versions so the gate handles older Suites without a separate historical table.