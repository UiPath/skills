# Governance Recipes Guide

Common governance intents mapped to the product policy and fields that implement them. Use these as **priors** for Mode A auto-fill in [configure-aops-policy-data-guide.md](./configure-aops-policy-data-guide.md) — always grep the live `form-template-locale-resource.json` for the listed keywords to confirm the field keys still exist in the current template version before writing values.

> **How to use this file.** When the user's intent matches a recipe, apply its field mapping first, then fall back to general locale grep for anything unmapped. Do NOT hard-code these keys without verifying them in the current template — product fields drift between template versions (22.4, 23.10, 24.10.1, ...).

---

## Prerequisites that shape every recipe

These platform-level conditions affect whether a deployed policy actually takes effect. Verify them before creating policies, and surface them to the user if unmet:

1. **Interactive Sign-In is required on the client.** Studio / StudioX / Assistant must be connected to Orchestrator via Interactive Sign-In for a cloud-deployed policy to apply. A machine running under an unattended/service account without interactive login will not pick up the policy. If the user asks "why isn't my policy taking effect?", check this first.
2. **Runtime governance is off until the tenant's first Robot policy is deployed.** All RT-* runtime rules (R1–R3 below) require runtime governance to be enabled at the tenant level. The Automation Ops UI shows a banner "Runtime governance is disabled" until the first Robot policy is deployed — enabling it is tenant-wide from that moment (see R4).
3. **Enforcing a Studio governance policy disables every built-in Analyzer rule by default.** Once a Studio policy is enforced, the default rule set does not ship with it — each rule must be listed explicitly in `Analyzer.EmbeddedRulesConfig.Rules` with `IsEnabled: true`. Silently enforcing governance without enumerating rules is a common reason CoEs report "our analyzer got quieter after we rolled out governance" (see S3).
4. **Legacy file-based governance is overridden on deployment.** An Automation Ops policy supersedes any local or JSON governance file on the developer's machine. If the org already has a legacy JSON governance file, import it via the Automation Ops UI before rolling out a new policy so existing rules are not lost.

---

## How recipes are structured

Each recipe lists:

- **Intent keywords** — user phrases that trigger it (use these for keyword search against the locale resource).
- **Product** — the `product.name` to pass to `--product-name` on `create`.
- **Fields** — candidate component `key`s and the values that implement the rule.
- **Notes** — empty-parameter warnings, license-type compatibility, template-version hints.

Field names below reflect the doc's example JSON; the live `form-template.json` for your tenant may use slightly different keys. Always verify against the bootstrapped schema.

---

## Assistant recipes

### A1 — Minimize Assistant while a process is running

- **Intent keywords:** "stop Assistant popping up", "Assistant keeps appearing", "Assistant pops up during runs", "minimize Assistant while running", "don't interrupt users when a bot runs"
- **Product:** Assistant policy
- **Fields:** `MinimizeAssistantWhileRunning: true` (under Feature Toggles).
- **Notes:** Requires users to sign into Assistant with interactive sign-in for the policy to apply. No parameters — simple toggle.

### A2 — Auto-launch Assistant at Windows startup

- **Intent keywords:** "Assistant should start with Windows", "launch Assistant automatically", "make sure users never miss a scheduled job"
- **Product:** Assistant policy
- **Fields:** `AutoLaunchAssistant: true`.
- **Notes:** Opposite intent (do NOT auto-launch) → `false`.

### A3 — Disable the UiPath Marketplace widget

- **Intent keywords:** "disable Marketplace widget", "stop users installing from Marketplace", "block community automations in Assistant", "only allow vetted automations"
- **Product:** Assistant policy
- **Fields:** `Widgets.UiPath.Marketplace.Widget: false`.
- **Notes:** All-or-nothing — there is no per-item allow-list for Marketplace. To offer specific Marketplace automations, download, vet, and republish through Orchestrator or Automation Hub instead.

### A4 — Block custom widgets and external widget feeds

- **Intent keywords:** "only allow official widgets", "block custom widgets", "don't let users add widget feeds"
- **Product:** Assistant policy
- **Fields:**
  - `Widgets.AllowCustomWidgets: false`
  - `Widgets.UseOfficialWidgetFeed: false` (only Orchestrator feed allowed).
- **Notes:** Useful as a pair when the goal is "no widget installs outside corporate-hosted feed."

### A5 — Curate individual widget availability

- **Intent keywords:** "enable Apps widget", "disable Automation Store widget", "show only the Apps widget in Assistant"
- **Product:** Assistant policy
- **Fields:** individual toggles under `Widgets`, e.g. `UiPath.Apps.Widget`, `UiPath.AutomationStore.Widget`.
- **Notes:** After deploying, users may need to sign out/in of Assistant for new widgets to appear. Apps widget also requires at least one published App to be visible.

---

## Robot (Runtime Analyzer) recipes

### R1 — RT-UIA-001 application/URL allow-list

- **Intent keywords:** "only allow automating Outlook and Excel", "block automation of cmd.exe / regedit / Start Menu", "restrict which apps robots can automate", "whitelist these applications"
- **Product:** Robot policy
- **Fields:** `RT-UIA-001` rule under `RuntimeAnalyzer`:
  - `AllowedApplications: ["outlook.exe", "excel.exe", ...]` (allow-list mode)
  - `BlockedApplications: ["cmd.exe", "regedit.exe", ...]` (block-list mode)
  - `Action: "Error"` (default — stops the robot at runtime on violation)
- **Notes:** **Do NOT deploy RT-UIA-001 with empty lists — it enforces nothing.** If the user names apps, populate the list; if they don't, surface that the rule will be a no-op and ask what to include. Test in a non-production tenant first; an overly tight allow-list can halt production jobs.

### R2 — RT-UIA-001 web URL allow/block-list

- **Intent keywords:** "only allow internal domains", "block automation of gmail.com / facebook.com", "restrict web automation to *.internalcompany.com"
- **Product:** Robot policy
- **Fields:** `RT-UIA-001`:
  - `AllowedURLs: ["*.internalcompany.com"]` (allow-list)
  - `BlockedURLs: ["*facebook.com*", "*gmail.com*"]` (block-list)
  - `Action: "Error"`
- **Notes:** Same empty-list warning as R1. Use broad patterns carefully — `*gmail.com*` is safer than a bare `gmail.com` to avoid matching unrelated substrings.

### R3 — RT-OUT-001 email recipient blocklist

- **Intent keywords:** "block robots from emailing gmail/yahoo", "stop bots emailing external domains", "no robot emails outside @mycompany.com", "prevent data leak via email"
- **Product:** Robot policy
- **Fields:** `RT-OUT-001` rule under `RuntimeAnalyzer`:
  - `BlockedEmails: ["*@gmail.com", "*@yahoo.com"]` (pattern list)
  - `Action: "Error"`
- **Notes:** Same empty-list warning — `BlockedEmails: []` enforces nothing. Blocks the specific Mail / GSuite / Office365 activity packages the rule covers; other email channels (API-based integrations) are not caught by this rule.

### R4 — Enable runtime governance (prerequisite)

- **Intent keywords:** (any runtime-rule intent above) — and the tenant has never deployed a Robot policy.
- **Product:** Robot policy
- **Notes:** Runtime governance is off until the first Robot policy is deployed to the tenant. The Automation Ops UI surfaces a "Runtime governance is disabled" banner; the agent should warn the user before the first deployment so they know the effect is tenant-wide from that moment on.

---

## Studio (design-time) recipes

### S1 — Gate Publish/Run on Workflow Analyzer

- **Intent keywords:** "enforce analyzer before publish", "block publish if analyzer errors", "require clean analyzer before running"
- **Product:** Studio policy (`Development` or equivalent)
- **Fields:** `Design.EnforceAnalyzerBeforePublish: true`, `Design.EnforceAnalyzerBeforeRun: true`.
- **Notes:** With these on, any Analyzer rule at `ErrorLevel: "Error"` stops publish/run. Pair with specific rule configs (S3).

### S2 — Require release notes and source-control check-in

- **Intent keywords:** "require release notes on publish", "must check in before publish", "enforce versioning discipline"
- **Product:** Studio policy
- **Fields:** `Design.EnforceReleaseNotes: true`, `Design.EnforceCheckInBeforePublish: true`.

### S3 — Enable and configure Workflow Analyzer rules

- **Intent keywords:** "enforce naming conventions", "require camelCase variables", "block hardcoded credentials", "enforce our coding standards"
- **Product:** Studio policy
- **Fields:** `Analyzer.EmbeddedRulesConfig.Rules` — array of `{Id, IsEnabled, Parameters, ErrorLevel}`. Well-known rule IDs:
  - `ST-NMG-001` — variable / argument / activity naming regex. Parameter: `Regex` (e.g. `^[a-z][A-Za-z0-9]*$`).
  - `ST-SEC-*` — security rules (hardcoded credentials, untrusted sources).
  - `ST-USG-027` — Required Packages. Parameter: `Packages` — semicolon- or version-suffixed list (e.g. `MyCompany.CustomRulesPackage>=1.0.0`). Used to force developers to include a custom NuGet-packaged analyzer rule.
- **Notes:**
  - **Built-in rules are DISABLED by default once governance is enforced.** Every rule you want active must appear in the array with `IsEnabled: true` and a valid `ErrorLevel`. If the user asks you to "enforce Workflow Analyzer" without naming rules, do NOT deploy — ask which rules matter, or apply a CoE baseline (e.g. `ST-NMG-001`, `ST-SEC-*`, `ST-USG-027`) and confirm with the user before saving.
  - `Analyzer.AllowEdit: false` (default) prevents local overrides. Set to `true` only if the user explicitly wants developers to toggle rules locally.
  - Set `ErrorLevel: "Error"` for blocking issues, `"Warning"` for stylistic ones. Pair `Error` rules with S1 (`EnforceAnalyzerBeforePublish`) so violations actually block publish.
  - Runtime rules (R1–R3) are a safety net — always pair with design-time Studio rules so violations are caught at design time first, not only at runtime.

### S4 — Source-control repository whitelist

- **Intent keywords:** "only allow our corporate GitHub", "whitelist these repositories", "block pushing to unauthorized repos"
- **Product:** Studio policy
- **Fields:** `SourceControl.AllowedRepositories: ["https://github.com/MyOrg/Repo1.git", ...]`, `SourceControl.AllowEditRepositories: false`.
- **Notes:** `AllowEditRepositories: false` prevents developers from adding repos; the `AllowedRepositories` list is exhaustive.

### S5 — Restrict package sources (feeds)

- **Intent keywords:** "block public Marketplace feed", "only allow internal NuGet", "no external packages", "use only our vetted feed"
- **Product:** Studio policy
- **Fields:**
  - `Feeds.OfficialFeed: false` (disable UiPath public feed)
  - `Feeds.MarketplaceFeed: false`
  - `Feeds.AllowUserDefinedFeeds: false`
  - `Feeds.CustomFeeds: ["OrchestratorTenantFeed"]` (or an internal URL)
- **Notes:** Pair with S3 `ST-USG-027` to force a custom NuGet-packaged analyzer rule to be included in every project.

### S6 — Export analyzer results for CI/CD

- **Intent keywords:** "capture analyzer output", "save analysis results for audits", "feed analyzer results into pipelines"
- **Product:** Studio policy
- **Fields:** `Design.ExportAnalyzerResults: true`.
- **Notes:** Each analyzer run writes a JSON report into the project folder; a CI job can aggregate these.

---

## StudioX (Citizen Developer) recipes

### X1 — Hide the developer panel from citizen devs

- **Intent keywords:** "lock down StudioX", "citizen devs shouldn't see developer activities", "hide advanced activities"
- **Product:** StudioX policy (`Business` or equivalent)
- **Fields:** `ShowDeveloperPanel: false`.

### X2 — Hide specific activities from StudioX

- **Intent keywords:** "hide Execute Macro", "block WriteRange for business users", "remove these activities from StudioX"
- **Product:** StudioX policy
- **Fields:** `ActivitiesToHide: "UiPath.Excel.Activities.Business.WriteRangeX, UiPath.Core.Activities.ExecuteMacro"` (comma-separated activity namespaces).

### X3 — Prevent StudioX as an ad-hoc runtime

- **Intent keywords:** "stop users running the same automation repeatedly in StudioX", "force promotion to Orchestrator", "limit consecutive runs"
- **Product:** StudioX policy
- **Fields:** `PermittedConsecutiveRunsWithNoChange: 2` (or similar low integer). After the cap, further runs from StudioX are blocked.

### X4 — Force projects off the local PC

- **Intent keywords:** "don't let citizen devs save to C:", "all projects must go to Orchestrator personal workspace", "no local project storage"
- **Product:** StudioX policy
- **Fields:** `AllowSavingProjectLocally: false`.
- **Notes:** Ensure a valid Orchestrator personal workspace or shared location is configured via the Locations tab in the same policy — otherwise users can't save anywhere.

---

## Deployment recipe — precedence and narrowest scope

When the user asks for a scope-limited rule:

- "Apply to one user only" → deploy at **user** level. Overrides group and tenant for that user.
- "Apply to the X team / group" → deploy at **group** level. Overrides tenant for group members.
- "Apply to everyone in this tenant" → deploy at **tenant** level (with a `(product, licenseType)` key). Base-layer default.
- "Exception for team X that ignores the tenant rule" → deploy a different policy at group level; tenant-level rule still applies to non-members.

Order of effective resolution: **User > Group > Tenant > (no policy)**. See [aops-policy-deploy-guide.md — Deployment precedence](./aops-policy-deploy-guide.md#deployment-precedence) for the decision flow.

---

## Anti-patterns

- Do NOT write runtime-rule policies (RT-UIA-001, RT-OUT-001) with empty parameter arrays — the rule is enabled by default but enforces nothing until populated. Surface this to the user if their intent didn't list any apps / URLs / emails.
- Do NOT assume a recipe's field `key`s match the live template without grepping. Template versions (22.4 → 23.10 → 24.10.1) occasionally rename or add fields. Verify against `form-template-locale-resource.json` before writing.
- Do NOT deploy an Assistant-product policy to a license type that doesn't include Assistant (e.g. `Unattended Robot` → Robot only). See [license-type list output](./aops-policy-commands.md#uip-gov-aops-policy-license-type-list) for the product coverage per license type.
- Do NOT pair "block Marketplace widget" with "allow these specific Marketplace items" — the toggle is all-or-nothing. Re-host vetted automations in a controlled feed instead.
- Do NOT assume enforcing a Studio policy activates the default Workflow Analyzer rule set. Governance turns EVERY built-in rule off by default — you must enumerate each rule in `Analyzer.EmbeddedRulesConfig.Rules` with `IsEnabled: true`. An empty `Rules` array = zero analyzer enforcement.
- Do NOT deploy a cloud policy expecting it to apply to clients that aren't Interactively Signed-In to Orchestrator. Unattended / service-account Studio or Assistant installs ignore cloud policies — the user must use Interactive Sign-In.

---

## Related references

- [configure-aops-policy-data-guide.md](./configure-aops-policy-data-guide.md) — Mode A auto-fill consumes these recipes as priors before general locale grep.
- [aops-policy-deploy-guide.md](./aops-policy-deploy-guide.md) — user / group / tenant precedence and license-type compatibility.
- [aops-policy-commands.md — license-type list](./aops-policy-commands.md#uip-gov-aops-policy-license-type-list) — authoritative mapping of license type `name` → products.
