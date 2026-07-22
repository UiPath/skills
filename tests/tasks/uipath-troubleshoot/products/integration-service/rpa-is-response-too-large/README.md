# rpa-is-response-too-large

Faithful-replay scenario for the **Integration Service — Response Content Too Large** playbook
([`response-content-too-large.md`](../../../../../skills/uipath-troubleshoot/references/products/integration-service/playbooks/response-content-too-large.md)).

## What the scenario exercises

A scheduled unattended job (`Data Export`) faults at a ServiceNow **List Incidents** `ConnectorActivity`. The
runtime throws `UiPath.IntegrationService.Activities.Runtime.Exceptions.RuntimeException: Response content too large.`
because an **unbounded list query** returned more than the Integration Service **8 MB JSON limit** will marshal.

The agent must reach: the provider call *succeeded* and the failure is a **response-size** breach (8 MB JSON limit),
**not** an auth/connection/provider error — then recommend bounding the query (**Max records** + filter / paging), and
passing file bytes outside JSON (1 GB limit) if applicable.

## Why the two criteria stay aligned (no bypass)

- The decisive string `Response content too large` lives only in the **job Info / logs**, not the prompt — the agent
  must investigate to find it.
- The connection **pings Enabled** and there is **no `ProviderErrorCode`** — a plausible wrong-turn (chase an
  auth/connection cause) that a shallow read invites but the evidence rejects.
- The correct diagnosis requires the specific **8 MB limit** + **Max records/filter** fix (and the outside-JSON 1 GB
  nuance) from the playbook, so a skill-less shallow answer ("response too large, make it smaller") lands below the
  `llm_judge` pass threshold.

## Mock

CLI-driven (no `process/` snapshot). `data/m/r/manifest.json` dispatches `uip or …` job/folder/process queries and
`uip is …` connection/resource queries to canned fixtures; `docsai ask` is passthrough. Evidence surfaces in
`job-get.json` (Info) and `job-logs.json`.

Ground truth for the judge: [`RESOLUTION.md`](./RESOLUTION.md).
