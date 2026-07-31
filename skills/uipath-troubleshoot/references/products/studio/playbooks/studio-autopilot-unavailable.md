---
confidence: medium
---

# Studio Autopilot Unavailable / "Disabled by Your Organization"

## Context

What this looks like:
- Studio (Desktop or Web): Autopilot panel greyed out — "Autopilot not available — This feature has been disabled by your organization."
- Output log: "Could not establish a connection with the Autopilot service."
- May co-occur with Studio running unlicensed ("No license exist for this installation") or license-acquisition errors ("Could not connect to Orchestrator"). A related but SEPARATE symptom on the same tenant: the **Autopilot for Everyone** install (the UiPath Assistant feature, installed from Admin > AI Trust Layer — not a Studio feature) returns HTTP 404.

What can cause it (originating cause first):
- Required tenant services are **Disabled** (Admin > Tenant > Services). Usual root cause:
  - **Orchestrator disabled** → Studio (License Provider = Orchestrator) cannot acquire a license → unlicensed → Autopilot's cloud feature-status check fails.
  - **autopilotstudio** disabled → Autopilot-for-developers service unavailable → "disabled by your organization".
  - **autopilotforeveryone / agenthub / agentsruntime / semanticproxy** disabled (or **Document Understanding** `du` not enabled — requires AI units) → the **Autopilot for Everyone** install returns 404. Autopilot for Everyone is the UiPath Assistant feature — a different product from Studio's developer Autopilot — so this is a separate symptom that happens to share the same disabled-tenant-service root cause. Document Understanding gates this *Everyone* (Assistant) install, NOT developer-Autopilot availability.
- Look-alike causes to rule out (not the usual root cause):
  - AI Trust Layer setting "Enable Studio and Studio Web features" = No, or an Automation Ops Studio policy "Allow Autopilot" toggle off.
  - License seat does not license the launched profile — a Citizen Developer seat licenses StudioX only; the full Studio profile needs an Automation Developer seat (otherwise "No license exist").
  - A stale local system proxy breaking the Orchestrator license-acquisition call.

What to look for:
- Tell-tale differential: Autopilot works on one tenant/org but not another — a freshly created tenant works while an existing one fails. The failing tenant has services disabled.

## Investigation

1. **Confirm the environment.** Run `uip login status --output json`; verify BaseUrl + org + tenant match the org/tenant the failing Studio is connected to (Studio > Backstage > Help shows License Provider + Company Policy). The same org slug can exist in multiple environments — readings from the wrong tenant are misleading.
2. **Check tenant service enablement FIRST** (highest yield). Run `uip admin tenants get <TENANT_ID> --output json` and inspect `TenantServiceInstances[].Status` for `orchestrator`, `autopilotstudio`, `autopilotforeveryone`, `agenthub`, `agentsruntime`, `semanticproxy`, `du`, `mls`, `ocr`. Any required one showing `Disabled` is the cause.
   > `uip admin tenants services list` reports *provisioned* services but NOT enabled/disabled state — a service can be listed yet switched off. Always use `tenants get` for `Status`.
3. **If a new tenant works but the existing one fails**, diff `tenants get` `Status` between them — the failing tenant has services disabled.
4. **Only if all required services are Enabled and it still fails**, rule out the look-alikes:
   - Studio > Backstage > Help "Company Policy": if a policy name shows, check Automation Ops "Allow Autopilot"; if "None", check Admin > AI Trust Layer "Enable Studio and Studio Web features" (UI-only — NOT exposed by `uip gov aops-policy deployed-policy`, which reads only deployed governance policies).
   - License seat: `uip platform users licenses get <USER_EMAIL> --output json` — confirm the seat licenses the launched profile (Studio vs StudioX).
   - Local transport: check the host's system/HTTP proxy configuration (the OS proxy settings and the `HTTP_PROXY` / `HTTPS_PROXY` environment variables) — a stale proxy (e.g. a debug proxy left registered) breaks the Orchestrator license call.

## Resolution

- **If a required service is Disabled:** enable it on the affected tenant (Admin > Tenant > Services, or CLI). For each disabled service:
  ```
  uip admin tenants services enable --tenant-id <TENANT_ID> --service <SERVICE_NAME> --output json
  ```
  Enable the services the symptom needs: for **Studio's developer Autopilot**, `orchestrator` (licensing) and `autopilotstudio`; for the separate **Autopilot for Everyone** (UiPath Assistant) install, also `autopilotforeveryone`, `agenthub`, `agentsruntime`, `semanticproxy`, plus `du` Document Understanding (requires AI units), `mls`, `ocr`. Then **verify** with `uip admin tenants get <TENANT_ID> --output json` that each `TenantServiceInstances[].Status` = `Enabled` — the enable command returns Success regardless, so verification is mandatory. Allow a few minutes for newly-enabled services to warm up, then restart Studio. Confirm the license acquires, the Autopilot panel connects, and the install no longer 404s.
- **If services are Enabled but Autopilot AI features are off:** enable Admin > AI Trust Layer "Enable Studio and Studio Web features" (and the Automation Ops "Allow Autopilot" toggle if a Studio policy applies); wait ~5 min for the policy cache, restart Studio.
- **If the license seat is wrong for the profile:** assign an Automation Developer seat for the full Studio profile, or open the StudioX profile if a Citizen Developer seat is intended; restart Studio.
- **If a stale local proxy is breaking license acquisition:** clear the host's system/HTTP proxy (the OS proxy settings and any `HTTP_PROXY` / `HTTPS_PROXY` environment variables) and exit any debug proxy cleanly, then restart Studio.
