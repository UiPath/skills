# Platform Availability Guide

> **Cloud is not uniform.** The ✅ Cloud column assumes standard Automation Cloud. Variants — Public Sector / GovCloud, Dedicated, Test Cloud, region-specific instances — plus per-tenant service enablement and license entitlements can block products inside that column. For any cloud variant or unverified entitlement, confirm the product is actually enabled on the tenant; unverifiable → `[SME REVIEW]` per product.

Product × delivery-model availability matrix. Consulted by the [Constraint Gate](product-selection-guide.md#constraint-gate) before any product is recommended. The most expensive SDD defect is an architecture the customer's platform cannot run.

> **As of:** 2026-06 · latest Automation Suite = **2.2510** (the 2025.10 LTS line; versioning is `[Major].[YYMM].[Patch]`), current patch **2.2510.2** (2026-04).
> **Authoritative live source:** [Product and feature availability across delivery options](https://docs.uipath.com/overview/other/latest/overview/product-and-feature-availability-across-delivery-options) — when this file and that page disagree, the page wins.

## Resolving the Delivery Model

Shared by every verb that chooses a product: `design` asks it as Question 2 of its entry prompt, `decompose` in its Step 3 batch, `author` (without an SDD) in its follow-ups.

**Delivery-model CLI preflight — run first, best-effort.** Before composing the questions, resolve the delivery model from the active CLI session:

```bash
uip login status --output json
```

**The login is the session's tenant, not necessarily the customer's.** It resolves the delivery model only when the automation runs on that tenant: the request says so, or nothing in the request or the source names another customer, environment or platform. A customer's PDD that states no platform is not resolved by the developer's login — ask Question 2, or, when autonomous, record `unspecified — assumed cloud` with an `[SME REVIEW]` item.

`uip login status` returns the authenticated `Data.BaseUrl` (host) and tenant. That separates **Automation Cloud** from **self-hosted**, but it does NOT reveal whether a self-hosted host is Automation Suite or standalone Orchestrator, nor the Automation Suite version/capabilities — validate those explicitly.

| `Data.BaseUrl` host | Resolves to | Question 2 |
|---|---|---|
| `cloud.uipath.com` | **Automation Cloud** — full catalog, entitlement-gated per tenant | skip (confidently resolved) |
| `staging.uipath.com`, `alpha.uipath.com` | **Automation Cloud** (a UiPath pre-production environment) | skip, as for `cloud.uipath.com` |
| any other `*.uipath.com` host | **Automation Cloud variant** (Public Sector / Dedicated / Test Cloud / region-specific) — catalog is variant-, region-, and entitlement-gated | skip the platform question, but verify each gated product (Maestro, Agents, Coded Apps, API Workflows, Solutions) against the tenant's actual entitlements; unverifiable → `[SME REVIEW]` per product |
| any other (customer / on-prem) host | **self-hosted — Automation Suite OR standalone Orchestrator (ambiguous)** | **do not skip** — ask the custom-host follow-up below |
| `Status` ≠ `Logged in`, call errors, or no `BaseUrl` | unknown | ask Question 2 in full; tell the user that running `uip login` first lets the next run auto-detect |

**Custom-host follow-up** — when the preflight hits the ambiguous row, replace Question 2 with these **two questions** in the same batched Step 0 structured prompt (the prompt then carries three questions). Show the detected host:

*Question 2a — Platform:*

> I detected a self-hosted URL (`<HOST>`). Which platform is it?
>
> 1. **Automation Suite** — product + capability availability is gated by version (and the EKS/AKS install profile for the Maestro/Agents stack)
> 2. **Standalone Orchestrator (MSI)** — Orchestrator + Studio/Robot only; most modern products unavailable

*Question 2b — Automation Suite version (applies only when 2a = Automation Suite):*

> Which Automation Suite version?
>
> 1. **2.2510 or later**
> 2. **2024.10**
> 3. **Older**
> 4. **Not sure / not Automation Suite**

Record the delivery model, and for Automation Suite the **version** — it determines which capabilities/products are available (gate via § Gating Rules and § Availability Matrix). Never silently treat a custom host as Automation Suite; standalone blocks far more. If the user picks Automation Suite but cannot give the version ("Not sure"), gate against the latest matrix column and add an `[SME REVIEW]` version row in §16 Deployment Environment.

Precedence: an explicit user-stated delivery model or a PDD signal **wins over** the preflight — never override an explicit statement with the detected value. The preflight is **best-effort and never blocks**: on any CLI failure, fall back to asking Question 2.

*Question 2 — Delivery model:*

> Where will this automation run?
>
> 1. **UiPath Automation Cloud** — full product catalog available
> 2. **Automation Suite (self-hosted)** — product availability depends on the Suite version; I will gate recommendations accordingly
> 3. **Standalone Orchestrator (MSI)** — most restrictive; modern platform products unavailable
> 4. **Not sure** — I will proceed assuming Automation Cloud and flag the assumption as `[SME REVIEW]`

**Skip Question 2** only when the delivery model is **fully** resolved — the user's request states it, the PDD carries a delivery-model signal (see [PDD Analysis Guide → Environment & Constraint Signals](pdd-analysis-guide.md#environment--constraint-signals)), or the preflight landed on a **known cloud host**. A custom / self-hosted host does NOT fully resolve it (Automation Suite vs standalone is ambiguous, and the AS version is unknown) — ask the custom-host follow-up above, batched into the Step 0 call. Record the resolved value. Only if the user picks Automation Suite and cannot give the version do you skip the version follow-up — then gate against the latest matrix column and add an `[SME REVIEW]` version row in §16 Deployment Environment.

## Gating Rules

1. **Gate against the customer's column.** `cloud` → everything below marked Cloud-available. `automation-suite` → the AS column **at the customer's version**: customer AS older than a product's "AS since" version → treat as **Not available**. `standalone` → see the Standalone note below. Version ordering across the renamed scheme: `2021.10 < 2022.4 < 2023.4 < 2024.10 < 2.2510 < 2.2510.2` — the `[Major].[YYMM]` scheme (2.2510 = 2025.10) sorts AFTER every `YYYY.MM` version.
2. **AS version unknown →** gate against the latest AS column, add an `[SME REVIEW]` row for the version in the SDD's deployment section (RPA §16 Deployment Environment, Agent §6 Orchestrator Bindings, the Deployment Target section of the others), and attach a warning to every product whose "AS since" is 2.2510 or newer (the customer may be on an older Suite).
3. **Install profile matters for the agentic stack.** Maestro and Agents on AS require the **EKS/AKS or OpenShift** profile (not the classic Linux/k3s profile) plus Temporal-as-a-Service and an AI Trust Layer LLM connection. When the SDD includes them on AS, add a profile-prerequisite warning + `[SME REVIEW]` row.
4. **Verification rule.** Web-search the authoritative page above before finalizing the SDD when ANY of: a needed cell is marked ⚠ Verify; the customer's AS version is unknown; this file's "As of" stamp is more than ~6 months old. A cell is *needed* only when its product remains a candidate after blocking — blocked products require no verification. Record what was verified (or why verification was skipped) in the `Decisions Made` row 1 reason.
5. **Even an ✅ AS cell can differ from cloud** in feature depth (per UiPath's own matrix page). Limitations called out in the Notes column go into the SDD as constraints, not footnotes.
6. **"No cloud connectivity" is ambiguous — classify before gating.** (a) The *install* is offline/air-gapped → treat every "unsupported on offline installs" note (DU modern, Integration Service) as **BLOCK**, and exclude SaaS dependencies (e.g., Microsoft 365 mailboxes) from the architecture. (b) Only the UiPath-cloud link is absent but the network has internet egress → **WARN** + `[SME REVIEW]`. When the statement cannot be classified from context, apply (b) and add an `[SME REVIEW]` row naming the stricter reading's consequences.

## Availability Matrix

> **Scope.** Lists products the planner can route to a skill. Document Understanding / IXP route through `uipath-ixp`. Pure platform/analytics features with no planner build path (Insights, AI Center, Task Mining, Autopilot for Everyone, Studio Web) are intentionally omitted — gate those manually if a PDD names them.

| Product | Cloud | Automation Suite | AS notes | Alternative when blocked |
|---|---|---|---|---|
| RPA (Studio, Robot, Orchestrator) | ✅ | ✅ since first AS (2021.10) | No serverless/cloud robots on AS — capacity via Automation Suite Robots or provisioned unattended robots | — |
| Solutions (`.uipx` deploy) | ✅ | ✅ since **2.2510** | Older AS cannot ingest `.uipx` — the planner's terminal artifact degrades to per-package Orchestrator deploys | Per-package publish via Orchestrator (route deploy tasks to `uipath-platform` instead of `uipath-solution`) |
| Maestro Flow (.flow orchestration) | ✅ | ✅ since **2.2510.2** — EKS/AKS + OpenShift profiles only | Requires Temporal-as-a-Service (auto-enabled); Optimize dashboard cloud-only | Orchestrator queues + dispatcher/performer state machine; Action Center approvals for human gates |
| Maestro BPMN (.bpmn orchestration) | ✅ | ✅ since **2.2510.2** — EKS/AKS + OpenShift profiles only | Requires Temporal-as-a-Service (auto-enabled); Optimize dashboard cloud-only | Orchestrator queues + dispatcher/performer state machine; Action Center approvals for human gates |
| Agents / Agent Builder | ✅ | ✅ since **2.2510.2** | Requires AI Trust Layer toggle + ≥1 LLM connection (cloud-hosted or self-hosted model); coded agents via Orchestrator 2.2510 | Deterministic RPA + rule-based decisioning; HITL escalation for judgment steps |
| Coded Apps (TypeScript web apps) | ✅ (some geo limits) | ❌ **Not available** — cloud only | "Automation Suite and Dedicated deployments are not supported at this time" | **None** — no on-prem app equivalent in this toolchain. Flag the app touchpoint as `[SME REVIEW]`; do not substitute a product the planner cannot build. |
| API Workflows | ✅ | ✅ since **2.2510** | Maestro integration needs 2.2510.2+ | RPA Process invoked via Orchestrator API / queue |
| Data Service (Data Fabric entities) | ✅ | ✅ since 2022.4 | No retention/TTL policy on file fields on any delivery model — design storage lifecycle (cleanup process) explicitly when storing files | — |
| Integration Service | ✅ (full catalog) | ✅ full since **2.2510** (2024.10 EKS/AKS-only, patched) | Not supported with FIPS 140-2 or air-gapped installs; connectors are admin-curated per tenant, not the full cloud catalog — confirm the needed connector is installed | Direct HTTP/REST calls from RPA or API Workflows |
| Action Center | ✅ | ✅ | Agent escalation integration needs 2.2510.2 | — |
| Document Understanding (classic) | ✅ | ✅ | — | — |
| Document Understanding (modern projects) | ✅ | ✅ since 2024.10 | Needs GPU allocation; unsupported on OpenShift / offline installs (per 2024.10 docs — ⚠ Verify for newer) | Classic DU; rule-based extraction for fixed-format generated documents |
| IXP | ✅ | ❌ Not available (⚠ Verify — on-prem delivery announced for late 2026) | — | DU modern/classic on AS; rule-based extraction for generated PDFs |
| Test Manager | ✅ | ✅ since 2021.10 (full Test Cloud since 2.2510) | — | — |

## Standalone (MSI Orchestrator) Note

Standalone delivery is Orchestrator + Studio/Robot (+ standalone Test Manager) only. **No** Apps, Integration Service, Studio Web, Data Service, API Workflows, Maestro (Flow and BPMN), Agents, Solutions. ⚠ Verify before relying on any product beyond core RPA + Orchestrator. Default architecture: RPA projects + Orchestrator queues/assets/triggers, deployed as individual packages via `uipath-platform`.

## Maintenance

When a cell changes (UiPath ships or removes a product on a delivery model), update the row AND the "As of" stamp. Keep "AS since" versions — they let the gate handle customers on older Suites without a separate historical table.
