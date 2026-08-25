---
confidence: high
---

# Healing Agent — Orchestrator Status, Logs & Notifications (Is This Expected?)

## Context

Customer sees a Healing Agent (HA) signal on an Orchestrator-side surface — a Jobs-grid status, a robot log line, an email/in-app notification, or an informational "no license" notice — and asks whether it is **expected** and whether HA is silently running or consuming units. Four distinct surfaces produce these reports. They look alike but mean different things. Route by **WHERE the customer saw it**.

### Routing table — pick the surface first

| # | Surface (where seen) | Tell-tale string | Default verdict |
|---|----------------------|------------------|-----------------|
| 1 | Jobs grid → **"Healing Agent" column**, or job detail → **"Healing Agent" tab** | `Issues Detected`; tab banner `Unlicensed version` (preview) | Expected. Detection-only; on preview UIA (`24.10.x`) detects unlicensed. No unit spend. |
| 2 | Job detail → **Logs** tab, robot Info log | `Healing agent configuration.` / `Healing Agent settings` | Benign config read. Appears every run. Non-blocking, zero consumption. |
| 3 | **Email / in-app "Notification Summary"**, Component = Healing Agent | `a problem has been identified… recommendations… available for review` | Real HA event → org is licensed OR on preview `24.10.x` (alerts unlicensed). |
| 4 | Robot log, informational notice | `'<activity>' activity recovery failed. No available license / Agentic units to perform healing analysis and recovery.` | Benign if customer does NOT want HA (job continues). If they DO → real error. |

If the surface does not match any row, this playbook does not apply.

### Does this consume units? (shared rule — applies to all four surfaces)

- **Prereqs not met** (wrong UIA version, or no UI activity in process) → HA never engages, the Healing Agent panel does not show, **zero consumption**.
- **Prereqs met but no license/units** → HA logs "No license available", does nothing, **job runs normally, zero consumption**.
- **Units charged only on a successful heal/recommendation.** Recommendation-only consumes the same as self-heal. HA can heal via **local heuristics with no LLM call** (e.g. org AI Trust Layer policy blocks AI), so detection shown ≠ LLM/unit spend.

HA is **available by default — recommendations on, self-healing off** (docs: "Healing Agent is available by default, offering only fix recommendations, not self-healing"). A signal appearing on a process the customer never explicitly enabled is expected for that reason. Self-healing must be activated explicitly per process/job.

---

### Surface 1 — Jobs-grid `Issues Detected` / Healing Agent tab

**What it means.** HA ran during the job and **flagged one or more UI automation issues** (analyzed the failure, may have generated recommendations). Detection/indicative status — does NOT by itself mean HA self-healed or that recommendations are actionable under the current license. On **preview UIA `24.10.x`** HA detects and analyzes **without any license check**, so the column populates even on a tenant with zero entitlement. The job's Healing Agent tab confirms with:

> ⚠ **Unlicensed version** — A preview version of the Healing Agent is currently in use. To upgrade to the GA version, update to the GA release of the UIAutomation.Activities packages. **Remaining days: 0**

That banner is the tell. GA UIA (`25.10.2`+) enforces licensing — without entitlement HA does not run, so the status reflects GA enforcement instead of preview detection. A single tenant can show both: robots pinned to preview `24.10.x` populate `Issues Detected` unlicensed; `25.10.2`+ robots do not. Identify the package version **per job**, not per tenant.

> The Jobs-grid Healing Agent column **filter is over-inclusive** — it surfaces jobs where HA was flagged but did not actually engage. For true engagement, use **Insights** (Healing Agent templates), not the grid filter.

**Investigation cue.** Identify the UIAutomation.Activities version for that specific job (read `project.json` if local). `24.10.x` → preview, detects unlicensed (primary branch). `25.10.2`+ → GA, requires entitlement → check `licenses info`.

**Resolution.**
- Preview `24.10.x` + no entitlement: **expected and informational**. No self-heal, no unit spend. To make HA actionable → upgrade to GA `25.10.2`+, acquire the Healing Agent add-on, allocate Heals/units. If they do NOT want HA → preview HA is deprecated: Enterprise tenants must upgrade to GA by **1 Nov 2025**, after which the preview **Healing Agent Orchestrator Jobs panel ceases to function and is disabled**. Upgrading to GA without the add-on means HA will not run and the status stops appearing. No setting fully suppresses preview detection on `24.10.x` short of upgrading.
- GA `25.10.2`+ + entitlement present (`Allowed.AgentService > 0`): tenant **is** licensed (check for promo, bundled Heals, or active trial). `Issues Detected` is normal — to act on findings, see [selector-failure-healing-fix.md](./selector-failure-healing-fix.md) or [no-recovery-data.md](./no-recovery-data.md).

### Surface 2 — Robot Info log `"Healing agent configuration."` / `"Healing Agent settings"`

**What it means.** Benign config read. Appears on **every** run regardless of license or whether HA is enabled — the robot reads HA settings at startup. **Non-blocking, consumes nothing.** The visible timestamp gap before/after this line is an **async-logging artifact** — the workflow does NOT wait on this log; it is NOT HA gating execution. Newer UIA reworded the line to state the actual HA state, because the old wording caused exactly this confusion. There is no setting that suppresses this line short of upgrading UIA; disabling HA in libraries/Automation Ops does not remove it.

**Investigation cue.** Confirm the line is `Level: Info` in the Logs tab and that the customer's concern is latency or "is HA running secretly". Pull logs: `uip or jobs logs <job-key> --output json`.

**Resolution.** Tell the customer the line is informational config-read only — no execution wait, no consumption. Latency they observe between timestamps is a logging artifact, not an HA network round-trip blocking the run. If they want the clearer wording, upgrade UIA to a version that reports HA state.

### Surface 3 — Orchestrator email / in-app "Notification Summary", Component = Healing Agent

**What it means.** A **real HA event** — HA does not send a notification unless it actually did something, and to do something the org must have the correct license. So either the org **has an HA license/active trial**, OR it is on **preview UIA `24.10.x`**, which alerts unlicensed (same preview root cause as Surface 1). HA notifications fire on a Heals-usage / recommendation event, not on license status — a notification means HA produced something, not that licensing changed. The notification text reads: "a problem has been identified within the job. Recommendations for resolution or self-healing procedures have been quickly generated and are now available for review."

**Investigation cue.** Identify the UIA version of the process that triggered the alert (`24.10.x` preview vs `25.10.2`+ GA). Check entitlement with `uip or licenses info --output json`. Recall HA is available by default (recommendations on) — the triggering process may have been auto-enabled without the customer realizing.

**Resolution.**
- Preview `24.10.x`: alerts fire unlicensed. Same fix as Surface 1 — upgrade to GA / provision add-on, or accept the alerts until the preview Jobs panel is disabled on 1 Nov 2025. No way to stop the alerts on `24.10.x` short of upgrading.
- GA `25.10.2`+ with entitlement: the org **is** licensed (promo, bundled Heals, or trial) — the alert is a genuine HA recommendation event. Open the job's Healing Agent tab to review.
- Customer worried about silent unit spend: see the shared consume block — a notification means HA produced a recommendation, which is a charged event only if a license was available; preview detection charges nothing.

### Surface 4 — `'<activity>' activity recovery failed. No available license / Agentic units…` (informational)

**What it means.** HA was enabled and prereqs were met, but the tenant lacks an available consumable pool, so HA logged this notice and did nothing. **The job continues normally.**

**Investigation cue.** Determine intent: does the customer **want** HA working?

**Resolution.**
- Customer does **NOT** want HA: the notice is **benign/non-blocking** — the job ran fine, nothing consumed. Optionally disable HA on the process/Automation Ops to stop the notice.
- Customer **DOES** want HA: this is the real licensing error → [healing-agent-no-license.md](./healing-agent-no-license.md).

---

## Investigation

1. **Confirm the surface** against the routing table. Route by where the customer saw it. A status, a log line, a notification, and the no-license notice are four different things — do not conflate.
2. **Identify the UIAutomation.Activities version per job.** Read `project.json` if local. `24.10.x` = preview (detects/alerts unlicensed). `25.10.2`+ = GA (enforces license).
3. **Read the job's HA state.** `uip or jobs get <job-key> --output json` — check `AutopilotForRobots.Enabled` and `AutopilotForRobots.HealingEnabled`. Cross-folder; no `--folder-path` flag.
4. **Pull logs when the surface is a log line or notification.** `uip or jobs logs <job-key> --output json` (add `--level Error` for Surface 4's notice). Cross-folder.
5. **Fetch the recovery archive to confirm engagement.** `uip or jobs healing-data <job-key> -o <out>.zip` — a populated archive corroborates HA produced detection/recommendation data; a 22-byte ZIP is empty (HA produced nothing).
6. **Check entitlement.** `uip or licenses info --output json`: `Data.Allowed.AgentService > 0` with HA features in `Data.LicensedFeatures` → tenant is entitled. `== 0` with `LicensedFeatures: []` → no entitlement. `SubscriptionPlan` is the tier label only and does NOT encode Flex vs Unified — never branch on it alone.

## Resolution

Apply the per-surface Resolution above for the matched row. Cross-cutting rules:

- **Preview `24.10.x` is the common unlicensed cause for Surfaces 1 and 3.** Detection/alerts without entitlement are expected; nothing is consumed. Preview is deprecated: Enterprise tenants must upgrade to GA by 1 Nov 2025, after which the preview Orchestrator Jobs panel is disabled. Upgrade to GA `25.10.2`+ + provision the add-on to make HA actionable, or accept the signals until then.
- **Surface 2** is always benign — config read, no consumption, no execution wait.
- **Surface 4** routes on intent: benign if HA unwanted; otherwise → [healing-agent-no-license.md](./healing-agent-no-license.md).
- Use **Insights** (Healing Agent templates) for the true engagement/consumption picture — the Jobs-grid filter over-reports.

## Distinguish from related playbooks

- **[healing-agent-no-license.md](./healing-agent-no-license.md)** — the **real** blocking-intent path for Surface 4: HA is wanted but the tenant lacks the right consumable pool (Heals vs Test Heals, pool not assigned/enabled, exhausted). Go there when the customer wants HA working and the robot log carries `No available license / Agentic units`.
- **[no-recovery-data.md](./no-recovery-data.md)** — HA is licensed and engaged but produced **no data** for other reasons (connectivity to Semantic Proxy / LLM Gateway, classic activity, image-only target). Go there when entitlement checks pass, the healing-data archive is genuinely empty, and none of the four surfaces above explains it.

## References

- Healing Agent setup (available by default — recommendations on, self-healing off; GA needs UIA `25.10.2`+): https://docs.uipath.com/agents/automation-cloud/latest/user-guide-ha/setup
- Healing Agent prerequisites (UIA `25.10.2`+): https://docs.uipath.com/agents/automation-suite/2.2510/user-guide-ha/healing-agent-prerequisites
- Healing Agent licensing (Flex): https://docs.uipath.com/agents/automation-cloud/latest/user-guide-ha/licensing#flex
- Healing Agent release notes (preview deprecation — upgrade by 1 Nov 2025; Orchestrator Jobs panel disabled after): https://docs.uipath.com/agents/automation-cloud/latest/release-notes-ha/september-2025
- Insights — Healing Agent: https://docs.uipath.com/insights/automation-cloud/latest/user-guide/healing-agent
