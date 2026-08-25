# is-activities-prerelease-not-found

Hand-authored **design-time** scenario for the **IS Activities Prerelease/Beta Not Found** playbook
([`is-activities-prerelease-not-found.md`](../../../../../skills/uipath-troubleshoot/references/products/integration-service/playbooks/is-activities-prerelease-not-found.md)).

## What the scenario exercises

A Studio project (`AccountSync`) whose `project.json` pins `UiPath.IntegrationService.Activities` to a
prerelease build (`1.16.0-beta.20250603.1`) the configured feed does not serve. Dependency restore fails and
every Integration Service activity shows invalid. The agent must diagnose the **prerelease-not-in-feed** cause
(pulled by the unified package's auto-upgrade-on-open) and recommend connecting to the official cloud
env / UiPath-Official feed and pinning a **stable** version.

No Orchestrator job exists — this is a design-time restore failure, so the agent investigates by reading the
project source (`project.json`), not by querying `uip or jobs …`.

## Why the two criteria stay aligned (no bypass, correct routing)

- The exact `-beta` version lives in `project.json`, not the prompt — the agent must Read the source to find it.
- The prompt uses **regression + diagnostic** framing ("worked last week … figure out why it broke") to route to
  `uipath-troubleshoot` rather than a build/fix skill.
- The correct fix (official feed / stable pin / disable prerelease, and *why* the auto-upgrade re-pinned a beta)
  requires the playbook, so a shallow "just pick another version" answer lands below the `llm_judge` threshold.

## Mock

Source-driven. `data/m/r/manifest.json` proxies only `docsai ask`; every other `uip` call returns an empty array
(there is no job to query). Ground truth for the judge: [`RESOLUTION.md`](./RESOLUTION.md).
