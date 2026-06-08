---
confidence: high
---

# Healing Agent — No License / Heals Available

## Context

Healing Agent is enabled on the run but cannot perform recovery because the tenant has no Healing Agent license consumables (Heals, Test Heals, Platform Units, or Agent Units) available — or has the wrong **type** for the runtime. The activity faults with a standard selector exception, HA emits an explicit "no license" error in the robot log, and no diagnostic data is produced.

### Licensing model — the discriminator

HA license consumption depends on two axes, not just one:

| Axis | Values | Effect |
|------|--------|--------|
| **License type** | `Flex` / `Unified` | Flex can only assign Heals; Unified can assign both Heals **and** Test Heals |
| **RuntimeType of the job** | **Test set** (→ **Test Heals** required): `AppTest`, `TestAutomation`, `ServerlessTestAutomation`, `AutomationCloudTestAutomation`, `PerformanceTest`. **Non-Test set** (→ regular **Heals** required) — commonly observed values include `Production`, `NonProduction`, `Development`, `Attended`, `Unattended`, `StudioPro`, `Studio`. Any value not in the Test set routes to regular Heals — match by Test-set membership, not by enumerating Non-Test names. | Orchestrator returns RuntimeType on the job; HA picks the pool from it |

Consumption rates after the bundled 5K heals are exhausted: **3 Platform Units per heal (Unified)** or **15 Agent Units per heal (Flex)**. One heal covers one unique recovered element per job — re-running the same element inside a loop is still one charge. A new job re-charges.

### What this looks like (primary, deterministic)

- A robot log entry at level `Error` containing the substring **`No available license / Agentic units to perform healing analysis and recovery`**. Full template (display name varies): `"'<activity-display-name>' activity recovery failed. No available license / Agentic units to perform healing analysis and recovery."` Canonical English message; localized robots emit the equivalent translation at the same log level. Match the English substring first via `uip or jobs logs`.
- The operation code in the log line distinguishes the pool: **`HealingAgent.Test`** = Test Heals requested, **`HealingAgent`** = regular Heals requested. App Insights / backend logs surface this as `CanConsume=False for orgId=..., tenantId=... and licenseCode:HealingAgent.Test` (or `HealingAgent`).

### Corroborating signals (when the log line is ambiguous, missing, or localized)

- `AutopilotForRobots.Enabled = true` AND `AutopilotForRobots.HealingEnabled = true` on the job
- Job log contains `"Healing agent analysis and recovery are enabled for current job."` near start of execution, but no subsequent HA recovery activity
- HA diagnostic archive is empty — `uip or jobs healing-data <job-key> -o <out>.zip` produces a 22-byte ZIP containing zero entries (`PK\x05\x06` end-of-central-directory record only)
- `uip or licenses info` shows `Data.Allowed.AgentService == 0` and `Data.LicensedFeatures: []` (or HA features absent)
- App Insights / backend: `Could not find any enabled consumption pools for [org-id]`
- Job-level `Info` contains the underlying selector exception (`NodeNotFoundException`, `SelectorNotFoundException`, etc.) — **not** the license message. License diagnosis lives in the robot log, not in `jobs get`.

### What can cause it

1. **No Healing Agent entitlement on the tenant.** Subscription does not include HA on this tenant. Applies across all plans. Discriminator is `Allowed.AgentService == 0`, not the plan name. Flex Advanced and Unified Enterprise bundle 5K heals; other tiers require the HA Add-On.
2. **Heals/Test Heals pool mismatch.** Run executes on a Test RuntimeType (e.g., the job uses an Unattended-Test robot or runs from Test Manager / Test Cloud) but the tenant only has regular Heals allocated. Even with thousands of regular Heals and bundled trial Heals, a Test runtime with 0 Test Heals will fail. **Flex tenants cannot assign Test Heals at all** — only Unified can.
3. **UIA package version behavior.** **UIA 25.10.22 and lower always consumes Heals regardless of RuntimeType** — it does not differentiate. **UIA 25.10.23 and above** correctly routes Test runtimes to Test Heals. This means a Flex tenant running tests on UIA 25.10.22 succeeds (consumes Heals); upgrade to 25.10.23+ and the same job fails with this error.
4. **Preview-vs-GA version mismatch.** UIA 24.10.x was the Public Preview of HA and lacked proper license validation. UIA 25.10.x is GA and enforces it. A job that "worked before" on 24.10.x and breaks after upgrade to 25.10.x is hitting GA enforcement, not a regression — the preview was unlicensed and is no longer supported.
5. **Heals purchased but not assigned to this tenant.** Heals exist at the organization level but are not allocated to the specific tenant. Manifests as `Could not find any enabled consumption pools` in App Insights and `CanConsume=False` in backend logs.
6. **Consumption pool not enabled.** Tenant has the entitlement and allocation but the pool itself is disabled.
7. **Pool exhausted.** Allocation is non-zero but fully consumed for the billing period.

### Distinguish from related playbooks

- **`no-recovery-data.md`** — HA is licensed but produced no data for other reasons (connectivity, image-only target, classic activities). Inspect `licenses info`. If `Allowed.AgentService == 0` OR the robot log carries the "No available license / Agentic units" line, this playbook applies. If both checks come back negative, fall back to `no-recovery-data.md`.
- **`selector-failure-healing-disabled.md`** — that playbook requires `AutopilotForRobots.HealingEnabled = false`. Here HealingEnabled is `true` but the run still produced no data because HA refused to run.
- HA-no-license fires regardless of job type. Attended, Unattended, Unattended-Test, and TestAutomation runs all surface the same log line when entitlement is missing or the wrong pool is targeted. The `Type` and RuntimeType only determine which consumable pool (Heals vs. Test Heals) is the relevant fix.

## Investigation

1. **Fetch error-level robot logs.** `uip or jobs logs <job-key> --level Error --output json`. Search case-insensitively for the substring `No available license` (or `Agentic units to perform healing`). A match at level `Error` is **the** deterministic signal — record the full log line verbatim (it includes the activity display name in single quotes) and check the operation code:
   - `HealingAgent.Test` → Test Heals were requested. Job ran on a Test RuntimeType. Fix targets the Test Heals pool.
   - `HealingAgent` → regular Heals were requested. Fix targets the Heals pool.

   Then proceed to Resolution. If no match, continue to step 2. `jobs logs` is cross-folder; no `--folder-path` flag needed.

2. **Get the faulted job.** `uip or jobs get <job-key> --output json`. Confirm `State = Faulted` and read:
   - `AutopilotForRobots.Enabled` and `AutopilotForRobots.HealingEnabled` — both must be `true` for this playbook to apply.
   - `Type` and the underlying RuntimeType. Test RuntimeTypes (`AppTest`, `TestAutomation`, `ServerlessTestAutomation`, `AutomationCloudTestAutomation`, `PerformanceTest`) consume Test Heals; everything else consumes Heals.
   - `errorCode = "Robot"` is the typical job-level field; `jobError` is often empty `{}` — actionable detail lives in logs, not in `jobError`.

   `jobs get` is cross-folder; no `--folder-path` flag needed.

3. **Fetch the HA diagnostic archive.** `uip or jobs healing-data <job-key> -o <out>.zip`. A **22-byte file is an empty ZIP** (zero entries) — HA produced no data. Combined with HA being enabled on the job, this confirms HA refused to run. `healing-data` takes the job key as a positional argument and `-o` for the output path; no `--folder-path` flag exists.

4. **Check the UIA package version of the failing process.** Determine which UIAutomation package version the process is pinned to. If the project is local, read `project.json`. Two thresholds matter:
   - **< 25.10.x** → likely on UIA 24.10.x preview. Preview HA is unsupported on GA tenants; upgrade is the fix regardless of license state.
   - **25.10.22 and below** → does not differentiate Heals vs Test Heals (always consumes Heals). Symptom: a Test-runtime job fails on a Flex tenant after upgrading from 25.10.22 to 25.10.23+. This is expected GA behavior, not a regression.
   - **25.10.23+** → correctly routes by RuntimeType.

5. **Check tenant license allocation.** `uip or licenses info --output json`. Read these fields:
   - `Data.SubscriptionPlan` — informational only. Commonly observed string values: `COMMUNITY`, `TRIAL`, `PRO_TRIAL`, `STANDARD`, `ADVANCED`, `ENTERPRISE` (and trial variants). **The field reports the tier label only — it does NOT encode the license type (Flex vs Unified).** HA bundling depends on BOTH axes: Flex bundles HA on the Advanced tier (5K Heals); Unified bundles HA on the Enterprise tier (5K Heals). A bare `ENTERPRISE` plan could be Flex Enterprise (no bundle) or Unified Enterprise (bundles HA) — `licenses info` cannot tell you which. Therefore, even an `ENTERPRISE` tenant can have `Allowed.AgentService = 0` if the HA Add-On is not provisioned. **Never branch on `SubscriptionPlan` alone** — always read `Allowed.AgentService` and `LicensedFeatures` for the deterministic signal.
   - `Data.Allowed.AgentService` — must be `> 0` for HA to run on this tenant. `== 0` confirms the missing-entitlement case.
   - `Data.Used.AgentService` — if `Used >= Allowed` and `Allowed > 0`, the pool is exhausted.
   - `Data.LicensedFeatures` — should list HA-related features; an empty array `[]` means no HA entitlement on this tenant.

   Note: `licenses info` reports aggregate `AgentService` units. It does **not** distinguish Heals from Test Heals separately — the operation code in step 1 is the only CLI-accessible signal for which pool was requested. Per-pool inspection requires the Automation Cloud UI.

6. **If steps 1–5 are inconclusive** (no log line, `licenses info` looks normal, healing-data is still empty), the likely cause is pool-not-assigned-to-tenant or pool-not-enabled, and **there is no `uip` command to inspect this**. Verify in the Automation Cloud UI: Admin → Licenses → Consumables. Confirm the Heals (or Test Heals) pool is allocated to this tenant and the pool is enabled.

## Resolution

Pick the branch that matches the operation code from step 1 and the `licenses info` reading from step 5.

- **Operation code `HealingAgent` and `Allowed.AgentService == 0` with `LicensedFeatures: []` (missing entitlement):** the tenant subscription does not include Healing Agent. Acquire the HA Add-On for this tenant via the Automation Cloud admin portal, or move the tenant to a plan that bundles Heals (Flex Advanced, Unified Enterprise). Plan name alone does not predict the fix — every plan can be entitled or not based on the add-on.

- **Operation code `HealingAgent` and `Allowed.AgentService > 0` and `Used.AgentService >= Allowed.AgentService` (pool exhausted):** allocate additional Heals consumables to the tenant in the admin portal (Admin → Licenses → Consumables) or wait for the billing period to reset. After the bundled 5K is consumed, Unified tenants spend 3 Platform Units per heal and Flex tenants spend 15 Agent Units per heal — verify the unit pool covering overflow has capacity.

- **Operation code `HealingAgent.Test` (Test runtime):** the consumable is **Test Heals**, not regular Heals. Required entitlements:
  - **Unified tenant:** Test Heals via the Test Healing Agent Add-On.
  - **Flex tenant:** Flex **cannot** assign Test Heals. Options: (a) migrate to Unified to access Test Heals, (b) switch the failing job to an Unattended (non-test) robot if the workflow does not require Test Manager features, or (c) **temporarily pin UIA to 25.10.22 or lower** so the activity consumes Heals regardless of RuntimeType (workaround only — 25.10.23+ will enforce Test Heals on Test runtimes). Verify Tester License + Test Healing Add-On + Test Heals allocation in the admin portal. There is no CLI surface for Test Heals — UI inspection is required.

- **Heals exist at the org level but not allocated to this tenant (step 6, or App Insights shows `Could not find any enabled consumption pools`):** allocate Heals to the specific tenant in the admin portal (Admin → Licenses → Consumables). Confirm the pool is in the **Enabled** state, not just present.

- **License configuration looks correct but HA still produces empty data and the log line is absent:** the consumption pool may not be enabled on the tenant. Verify in the admin portal (Admin → Licenses → Consumables). There is no `uip` command for this — UI verification is required.

- **Job "worked before" and started failing after upgrade:** likely UIA 24.10.x preview → 25.10.x GA, or 25.10.22 → 25.10.23+ where Test-runtime jobs now correctly demand Test Heals. Identify which threshold was crossed (step 4) and resolve via the matching branch above — do not roll back package versions as a permanent fix; preview HA is no longer supported.

- **In all branches:** after the licensing issue is resolved, restart the same job (or trigger a new run). If HA produces data on the retry, the investigation continues with the recovery-data playbooks (`selector-failure-healing-fix.md` or `selector-failure-manual.md`). If HA still produces no data after the license fix, escalate to `no-recovery-data.md` (other causes: connectivity to Semantic Proxy / LLM Gateway, classic activity, image-only target).

## References

- Healing Agent prerequisites: https://docs.uipath.com/agents/automation-suite/2.2510/user-guide-ha/healing-agent-prerequisites
- Healing Agent licensing (Flex): https://docs.uipath.com/agents/automation-cloud/latest/user-guide-ha/licensing#flex
- Enabling Healing Agent for Test: https://docs.uipath.com/test-manager/automation-cloud/latest/user-guide/enabling-healing-agent
- Test Cloud licensing: https://docs.uipath.com/test-cloud/automation-cloud/latest/admin-guide/licensing-test-cloud
