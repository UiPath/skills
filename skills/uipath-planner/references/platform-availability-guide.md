# Platform Availability Guide

Product × delivery-model availability matrix. Consulted by the [Constraint Gate](product-selection-guide.md#constraint-gate) before any product is recommended. The most expensive SDD defect is an architecture the customer's platform cannot run.

> **As of:** 2026-06 · latest Automation Suite = **2.2510** (the 2025.10 LTS line; versioning is `[Major].[YYMM].[Patch]`), current patch **2.2510.2** (2026-04).
> **Authoritative live source:** [Product and feature availability across delivery options](https://docs.uipath.com/overview/other/latest/overview/product-and-feature-availability-across-delivery-options) — when this file and that page disagree, the page wins.

## Gating Rules

1. **Gate against the customer's column.** `cloud` → everything below marked Cloud-available. `automation-suite` → the AS column **at the customer's version**: customer AS older than a product's "AS since" version → treat as **Not available**. `standalone` → see the Standalone note below.
2. **AS version unknown →** gate against the latest AS column, add an `[SME REVIEW]` row for the version in §16 Deployment Environment, and attach a warning to every product whose "AS since" is 2.2510 or newer (the customer may be on an older Suite).
3. **Install profile matters for the agentic stack.** Maestro and Agents on AS require the **EKS/AKS or OpenShift** profile (not the classic Linux/k3s profile) plus Temporal-as-a-Service and an AI Trust Layer LLM connection. When the SDD includes them on AS, add a profile-prerequisite warning + `[SME REVIEW]` row.
4. **Verification rule.** Web-search the authoritative page above before finalizing the SDD when ANY of: a needed cell is marked ⚠ Verify; the customer's AS version is unknown; this file's "As of" stamp is more than ~6 months old. Record what was verified in the `Decisions Made` row 1 reason.
5. **Even an ✅ AS cell can differ from cloud** in feature depth (per UiPath's own matrix page). Limitations called out in the Notes column go into the SDD as constraints, not footnotes.

## Availability Matrix

| Product | Cloud | Automation Suite | AS notes | Alternative when blocked |
|---|---|---|---|---|
| RPA (Studio, Robot, Orchestrator) | ✅ | ✅ since first AS (2021.10) | No serverless/cloud robots on AS — capacity via Automation Suite Robots or provisioned unattended robots | — |
| Solutions (`.uipx` deploy) | ✅ | ✅ since **2.2510** | Older AS cannot ingest `.uipx` — the planner's terminal artifact degrades to per-package Orchestrator deploys | Per-package publish via Orchestrator (route deploy tasks to `uipath-platform` instead of `uipath-solution`) |
| Maestro (.flow / BPMN orchestration) | ✅ | ✅ since **2.2510.2** — EKS/AKS + OpenShift profiles only | Requires Temporal-as-a-Service (auto-enabled); Optimize dashboard cloud-only | Orchestrator queues + dispatcher/performer state machine; Action Center approvals for human gates |
| Agents / Agent Builder | ✅ | ✅ since **2.2510.2** | Requires AI Trust Layer toggle + ≥1 LLM connection (cloud-hosted or self-hosted model); coded agents via Orchestrator 2.2510 | Deterministic RPA + rule-based decisioning; HITL escalation for judgment steps |
| UiPath Apps (low-code) | ✅ | ✅ since 2021.10 | The on-prem app product. **No CLI/skill in this toolchain builds it** — design the app in the SDD, mark the build as a manual deliverable (Apps designer) with `[SME REVIEW]` | — |
| Coded Apps (TypeScript web apps) | ✅ (some geo limits) | ❌ **Not available** — cloud only | Official: "Automation Suite and Dedicated deployments are not supported at this time" | UiPath Apps (low-code, manual build — see row above) or Action Center HITL forms for approval/validation touchpoints |
| API Workflows | ✅ | ✅ since **2.2510** | Maestro integration needs 2.2510.2+ | RPA Process invoked via Orchestrator API / queue |
| Data Service (Data Fabric entities) | ✅ | ✅ since 2022.4 | No retention/TTL policy on file fields on any delivery model — design storage lifecycle (cleanup process) explicitly when storing files | — |
| Integration Service | ✅ (full catalog) | ✅ full since **2.2510** (2024.10 EKS/AKS-only, patched) | Not supported with FIPS 140-2 or air-gapped installs; connectors are admin-curated per tenant, not the full cloud catalog — confirm the needed connector is installed | Direct HTTP/REST calls from RPA or API Workflows |
| Action Center | ✅ | ✅ | Agent escalation integration needs 2.2510.2 | — |
| Document Understanding (classic) | ✅ | ✅ | — | — |
| Document Understanding (modern projects) | ✅ | ✅ since 2024.10 | Needs GPU allocation; unsupported on OpenShift / offline installs (per 2024.10 docs — ⚠ Verify for newer) | Classic DU; rule-based extraction for fixed-format generated documents |
| IXP | ✅ | ❌ Not available (⚠ Verify — on-prem delivery announced for late 2026) | — | DU modern/classic on AS; rule-based extraction for generated PDFs |
| Studio Web | ✅ | ✅ since 2024.10 | Web app projects + Agent Builder hosting since 2.2510 | Studio Desktop |
| Test Manager | ✅ | ✅ since 2021.10 (full Test Cloud since 2.2510) | — | — |
| Insights | ✅ | ✅ since 2021.10 | — | — |
| AI Center | ✅ (OOTB ML packages being phased out) | ✅ | Sunset trajectory — do not base new designs on AI Center OOTB models | IXP (cloud) / DU modern (AS) / GenAI activities |
| Task Mining | ✅ | ❌ Removed in 2.2510 (last AS version: 2024.10) | — | Manual process discovery |
| Autopilot for Everyone | ✅ | ✅ since 2024.10 | AS feature set lags cloud baseline | — |

## Standalone (MSI Orchestrator) Note

Standalone delivery is Orchestrator + Studio/Robot (+ standalone Test Manager, Insights, AI Center) only. **No** Apps, Integration Service, Studio Web, Data Service, API Workflows, Maestro, Agents, Solutions. ⚠ Verify before relying on any product beyond core RPA + Orchestrator. Default architecture: RPA projects + Orchestrator queues/assets/triggers, deployed as individual packages via `uipath-platform`.

## Maintenance

When a cell changes (UiPath ships or removes a product on a delivery model), update the row AND the "As of" stamp. Keep "AS since" versions — they let the gate handle customers on older Suites without a separate historical table.
