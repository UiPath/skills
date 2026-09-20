# Platform Availability Guide

> **Cloud is not uniform.** The ✅ Cloud column assumes standard Automation Cloud. Public Sector / GovCloud, Dedicated, Test Cloud, region-specific instances, tenant enablement, and license entitlements can block products. For any variant or unverified entitlement, confirm tenant enablement; if unverifiable, add `[SME REVIEW]` per product.

Product × delivery-model availability matrix for the [Constraint Gate](product-selection-guide.md#constraint-gate). Do not recommend an architecture the customer's platform cannot run.

> **As of:** 2026-06 · latest Automation Suite = **2.2510** (the 2025.10 LTS line; versioning is `[Major].[YYMM].[Patch]`), current patch **2.2510.2** (2026-04).
> **Authoritative live source:** [Product and feature availability across delivery options](https://docs.uipath.com/overview/other/latest/overview/product-and-feature-availability-across-delivery-options) — when this file and that page disagree, the page wins.

## Gating Rules

1. Gate against the customer's column: `cloud` uses Cloud; `automation-suite` uses AS at the customer's version; `standalone` uses the Standalone note. An AS version older than a product's “AS since” version means **Not available**. Version order is `2021.10 < 2022.4 < 2023.4 < 2024.10 < 2.2510 < 2.2510.2`; `[Major].[YYMM]` (`2.2510` = `2025.10`) sorts after every `YYYY.MM` version.
2. If the AS version is unknown, gate against the latest AS column, add an `[SME REVIEW]` row for the version in §16 Deployment Environment, and warn on every product whose “AS since” is `2.2510` or newer.
3. Maestro and Agents on AS require the EKS/AKS or OpenShift profile, not classic Linux/k3s, plus Temporal-as-a-Service and an AI Trust Layer LLM connection. If included on AS, add a profile-prerequisite warning and `[SME REVIEW]` row.
4. Web-search the authoritative page before finalizing the SDD when any needed cell is marked ⚠ Verify, the AS version is unknown, or this file's “As of” stamp is more than ~6 months old. A cell is needed only if its product remains a candidate after blocking. Record what was verified, or why verification was skipped, in the `Decisions Made` row 1 reason.
5. An ✅ AS cell can still differ from Cloud in feature depth. Put Notes-column limitations in the SDD as constraints.
6. Classify “no cloud connectivity” before gating:
   - Offline/air-gapped install: every “unsupported on offline installs” note (DU modern, Integration Service) is **BLOCK**; exclude SaaS dependencies such as Microsoft 365 mailboxes.
   - UiPath-cloud link absent but internet egress available: **WARN** + `[SME REVIEW]`.
   - Unclear classification: apply the second interpretation and add an `[SME REVIEW]` row naming the stricter interpretation's consequences.

## Availability Matrix

> **Scope.** DU/IXP route through `uipath-ixp`. Insights, AI Center, Task Mining, Autopilot for Everyone, and Studio Web are omitted because they have no planner build path; gate them manually if a PDD names them.

| Product | Cloud | Automation Suite | AS notes | Alternative when blocked |
|---|---|---|---|---|
| RPA (Studio, Robot, Orchestrator) | ✅ | ✅ since first AS (2021.10) | No serverless/cloud robots; use Automation Suite Robots or provisioned unattended robots | — |
| Solutions (`.uipx` deploy) | ✅ | ✅ since **2.2510** | Older AS cannot ingest `.uipx`; use per-package Orchestrator deploys | Per-package publish via Orchestrator; route deploy tasks to `uipath-platform`, not `uipath-solution` |
| Maestro Flow (.flow orchestration) | ✅ | ✅ since **2.2510.2** — EKS/AKS + OpenShift only | Temporal-as-a-Service auto-enabled; Optimize dashboard cloud-only | Orchestrator queues + dispatcher/performer state machine; Action Center approvals for human gates |
| Maestro BPMN (.bpmn orchestration) | ✅ | ✅ since **2.2510.2** — EKS/AKS + OpenShift only | Temporal-as-a-Service auto-enabled; Optimize dashboard cloud-only | Orchestrator queues + dispatcher/performer state machine; Action Center approvals for human gates |
| Agents / Agent Builder | ✅ | ✅ since **2.2510.2** | AI Trust Layer toggle + ≥1 cloud-hosted or self-hosted LLM; coded agents via Orchestrator 2.2510 | Deterministic RPA + rule-based decisioning; HITL escalation for judgment steps |
| Coded Apps (TypeScript web apps) | ✅ (some geo limits) | ❌ **Not available** — cloud only | Automation Suite and Dedicated deployments are not supported | **None** — flag the app touchpoint as `[SME REVIEW]`; do not substitute an unavailable planner product |
| API Workflows | ✅ | ✅ since **2.2510** | Maestro integration requires 2.2510.2+ | RPA Process invoked via Orchestrator API / queue |
| Data Service (Data Fabric entities) | ✅ | ✅ since 2022.4 | No file-field retention/TTL policy on any delivery model; explicitly design storage cleanup | — |
| Integration Service | ✅ (full catalog) | ✅ full since **2.2510** (2024.10 EKS/AKS-only, patched) | Unsupported with FIPS 140-2 or air-gapped installs; connectors are admin-curated, not the full cloud catalog—confirm the needed connector is installed | Direct HTTP/REST calls from RPA or API Workflows |
| Action Center | ✅ | ✅ | Agent escalation integration needs 2.2510.2 | — |
| Document Understanding (classic) | ✅ | ✅ | — | — |
| Document Understanding (modern projects) | ✅ | ✅ since 2024.10 | GPU required; unsupported on OpenShift / offline installs (per 2024.10 docs — ⚠ Verify for newer) | Classic DU; rule-based extraction for fixed-format generated documents |
| IXP | ✅ | ❌ Not available (⚠ Verify — on-prem delivery announced for late 2026) | — | DU modern/classic on AS; rule-based extraction for generated PDFs |
| Test Manager | ✅ | ✅ since 2021.10 (full Test Cloud since 2.2510) | — | — |

## Standalone (MSI Orchestrator) Note

Standalone is Orchestrator + Studio/Robot (+ standalone Test Manager) only. It does not support Apps, Integration Service, Studio Web, Data Service, API Workflows, Maestro (Flow and BPMN), Agents, or Solutions. ⚠ Verify before relying on any product beyond core RPA + Orchestrator. Default architecture: RPA projects + Orchestrator queues/assets/triggers, deployed as individual packages via `uipath-platform`.

## Maintenance

When a delivery-model cell changes, update its row and the “As of” stamp. Keep “AS since” versions so the gate handles older Suites without a separate historical table.