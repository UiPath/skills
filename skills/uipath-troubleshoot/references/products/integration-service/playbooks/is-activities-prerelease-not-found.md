---
confidence: medium
---

# IS Activities Package — Prerelease/Beta Version Not Found (design-time feed resolution)

> **Design-time (Studio) failure — not a runtime fault.** The `UiPath.IntegrationService.Activities` package fails to restore/resolve in Studio because the project pins a **prerelease/beta** version that is not present in the configured feed. Integration Service connector activities disappear or error on the canvas; the project will not compile. NOT a job/execution failure → for runtime connector faults (`DAP-…`, `Response content too large`, connection errors) see the runtime playbooks in this folder.

## Context

What this looks like:
- Studio dependency restore / package manager fails on **`UiPath.IntegrationService.Activities`** with a version that has a prerelease suffix, e.g. `1.16.0-beta.20250603.1`, `1.15.0-beta.20250425.1`
- Verbatim message forms: **`Unable to find package 'UiPath.IntegrationService.Activities' with version '<X.Y.Z-beta...>'`**, `Failed to resolve dependencies`, `Could not find package ... in the configured feed`
- Every Integration Service activity in the project shows as missing/unavailable; the workflow will not validate or compile
- Often appears right after **opening** a project or after a Studio/connector upgrade

What can cause it:
- The `UiPath.IntegrationService.Activities` package is the **unified dynamic IS activities package** (Studio Desktop 2023.10+). It **auto-upgrades to the latest connector version when a workflow is opened** — which can pull a **prerelease/beta** reference into `project.json`.
- The configured feed does not serve that prerelease build. The **UiPath-Official** feed exposes stable versions (e.g. `1.14.0`, `1.15.0`); the beta build is not there.
- **Primary root cause in practice:** Studio is connected to the **wrong / non-official cloud environment**, so it resolves against a feed that does not front the official package versions. Connecting to the official `https://cloud.uipath.com/` restores resolution of the correct stable versions.
- Prerelease packages are only visible when **"Include prerelease"** is enabled and the feed actually hosts them; a stable-only feed cannot satisfy a `-beta` pin.

What to look for:
- The `-beta`/prerelease suffix on the `UiPath.IntegrationService.Activities` version in `project.json` `dependencies`
- Which cloud environment Studio is signed in to (official vs a staging/custom org)
- Whether UiPath-Official is in the enabled package sources, and whether the nearest **stable** version exists there

## Investigation

1. **Read `project.json` `dependencies`** — confirm the pinned `UiPath.IntegrationService.Activities` version and whether it carries a prerelease (`-beta…`) suffix.
2. **Check the signed-in cloud environment** — is Studio connected to the official `https://cloud.uipath.com/` org, or a staging/custom environment whose feed does not front official packages?
3. **Check package sources** — is **UiPath-Official** enabled? In Manage Packages, does a **stable** `UiPath.IntegrationService.Activities` version exist while the pinned `-beta` one does not?

## Resolution

- **Connect Studio to the official UiPath cloud environment** (`https://cloud.uipath.com/`). This is the primary fix — the official environment fronts the feed that serves the correct package versions, and resolution succeeds without touching the pin.
- **Pin a stable version:** in Manage Packages, switch to the **UiPath-Official** feed, disable "Include prerelease", and select the latest **stable** `UiPath.IntegrationService.Activities` (e.g. `1.15.0`) instead of the `-beta` build. Update `project.json` and restore.
- **Prevent the auto-upgrade re-pinning a beta** — after downgrading, verify the project does not re-pull the prerelease on next open; keep "Include prerelease" off unless a beta is explicitly required.
- Do not add the beta build to a custom feed to force resolution unless a prerelease is genuinely required — align to a stable version on the official feed instead.
