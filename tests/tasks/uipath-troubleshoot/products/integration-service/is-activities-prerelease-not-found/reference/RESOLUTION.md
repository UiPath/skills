# Final Resolution

Investigation complete. Here are the findings.

---

# Why `AccountSync` fails to restore in Studio — Resolution

## Root Cause
The project pins **`UiPath.IntegrationService.Activities`** to a **prerelease/beta** version — **`1.16.0-beta.20250603.1`** (see `project.json` → `dependencies`). That prerelease build is **not present in the configured package feed**, so Studio's dependency restore cannot resolve it and every Integration Service activity shows as invalid/missing. The project will not compile.

- Domain: Integration Service (activity package) — **design-time**, not a runtime job failure
- Confidence: High on the mechanism (prerelease pin unresolvable in feed); the corrective lever depends on the environment (see below)

## What went wrong
- `UiPath.IntegrationService.Activities` is the **unified dynamic IS activities package**. It **auto-upgrades to the latest connector version when a workflow is opened**, which pulled a **`-beta` prerelease** reference into `project.json`.
- The feed Studio is resolving against (typically **UiPath-Official**) serves **stable** versions (e.g. `1.14.0`, `1.15.0`) — it does **not** host that `-beta` build. Restore fails: *"Unable to find package 'UiPath.IntegrationService.Activities' with version '1.16.0-beta.20250603.1'"*.
- Because the whole IS activity set ships in this one package, when it fails to restore, **all** Integration Service activities go invalid at once — matching the reported symptom.

## Why it "worked last week"
Nothing changed in the user's logic. The auto-upgrade-on-open behavior re-pinned the dependency to a newer prerelease that the current feed/environment cannot resolve — commonly because Studio is signed in to a **non-official / staging cloud environment** whose feed does not front the official package versions.

## Immediate fix
1. **Connect Studio to the official UiPath cloud environment** (`https://cloud.uipath.com/`). The official environment fronts the feed that serves the correct package versions; restore then succeeds. This is the primary lever.
2. **Pin a stable version:** in **Manage Packages**, select the **UiPath-Official** feed, turn **off** "Include prerelease", and choose the latest **stable** `UiPath.IntegrationService.Activities` (e.g. `1.15.0`) in place of the `-beta` build. Update `project.json` and restore.
3. **Keep it from recurring:** leave "Include prerelease" **off** so the auto-upgrade-on-open does not re-pin a `-beta` build.

## What this is NOT
- **Not** a runtime/connector fault — there is no Orchestrator job and no `DAP-…` execution error. It is a Studio design-time **dependency-restore** failure.
- **Not** a broken connection, credential, or permission issue — no connection is even reachable until the package restores.
- **Not** fixed by adding the beta build to a custom feed — align to a stable version on the official feed instead.

---

## Investigation summary

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|---|---|---|---|---|---|
| H1 | `project.json` pins `UiPath.IntegrationService.Activities` to a prerelease `-beta` version the configured feed does not serve, so Studio restore fails and all IS activities go invalid. | High | Confirmed | **Yes** | `project.json` → `dependencies` → `UiPath.IntegrationService.Activities: [1.16.0-beta.20250603.1]`; unified IS package auto-upgrades on open; UiPath-Official feed serves only stable versions | Connect to the official cloud env / UiPath-Official feed, pin a **stable** IS activities version, disable "Include prerelease", restore. |
