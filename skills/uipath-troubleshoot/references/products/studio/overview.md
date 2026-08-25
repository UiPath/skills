# Studio

UiPath Studio (Desktop and Web) — the authoring IDE for RPA workflows, coded workflows, and tests. This domain covers Studio-level platform failures that are NOT workflow-code or activity faults: license acquisition, profile entitlement (Studio vs StudioX), and in-IDE AI features (Autopilot for developers).

For `.xaml` / `.cs` workflow authoring and runtime activity faults → use **UI Automation**, **System Activities**, or **Runtime Exceptions**. For agent / product LLM routing → **LLM Gateway**. For Orchestrator-side jobs/queues/assets → **Orchestrator**.

## Key Concepts

- **Profiles** — Studio Desktop opens either the **Studio** profile (full developer experience) or the **StudioX** profile (business-user). The license seat gates which profile can be licensed: an **Automation Developer** seat licenses the Studio profile (and StudioX); a **Citizen Developer** seat licenses StudioX only.
- **License acquisition** — Studio acquires its license at sign-in/startup. With **License Provider = Orchestrator**, the license is fetched from the connected tenant's Orchestrator service. If that service is disabled or unreachable, Studio runs unlicensed ("No license exist for this installation").
- **Autopilot for developers** — the in-Studio AI coding assistant. Enabled by default, but gated by the `autopilotstudio` tenant service, a valid Studio-profile license, and AI Trust Layer / Automation Ops policy. Distinct from **Autopilot for Everyone** — the Autopilot built into the **UiPath Assistant** for attended/end users, a separate product from Studio — which is installed separately (Admin > AI Trust Layer) and depends on `autopilotforeveryone` / `agenthub` / `agentsruntime` / `semanticproxy` plus Document Understanding (`du`, which requires AI units). Document Understanding is an Autopilot-for-Everyone (Assistant) install prerequisite, NOT a developer-Autopilot availability requirement. Installing Autopilot for Everyone does NOT enable Studio's developer Autopilot.

## Dependencies

- **Tenant services** (Admin > Tenant > Services) — Studio features depend on services being **Enabled** on the connected tenant: `orchestrator` (licensing), `autopilotstudio` (developer Autopilot), and `autopilotforeveryone` / `agenthub` / `agentsruntime` / `semanticproxy` + `du` Document Understanding (Autopilot for Everyone). A service can be *provisioned* yet *disabled*.
- **AI Trust Layer / Automation Ops** — org/tenant policy can disable Studio AI features. See [`uipath-governance`](/uipath:uipath-governance).
- **Licensing** — per-user seat assignment determines the licensable profile. See `uip platform users licenses`.

## CLI (diagnosis)

```
uip login status --output json                          — confirm the connected org + tenant (envs can share an org slug)
uip admin tenants get <TENANT_ID> --output json         — TenantServiceInstances[].Status: per-service Enabled/Disabled
uip admin tenants services enable --tenant-id <TENANT_ID> --service <SERVICE_NAME> --output json
uip platform users licenses get <USER_EMAIL> --output json   — the user's assigned license seats
```

> `uip admin tenants services list` reports *provisioned* services only — it does NOT show enabled/disabled state. Use `uip admin tenants get` (`TenantServiceInstances[].Status`) to read enablement.

## What the CLI does NOT expose

The AI Trust Layer org setting "Enable Studio and Studio Web features" is UI-only (Admin > AI Trust Layer) — `uip gov aops-policy deployed-policy` reads only *deployed governance policies*, not this setting. Studio's local license/proxy state is read on the host (Studio > Backstage > Help; the OS proxy / `HTTP_PROXY` settings), not via `uip`.

- [summary.md](./summary.md) — All playbooks for Studio issues
