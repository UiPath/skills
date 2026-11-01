# UIA Starter Guide

Read this file in full before any UI-automation work (Rule 7). Then:

1. **Verify prerequisites** — minimum package version and upgrade-consent rules: [§ UIA Prerequisites](#uia-prerequisites) below. If the package cannot be installed, use [uia-policies-catalog.md § Placeholder-Selector Stub Pattern](uia-policies-catalog.md#placeholder-selector-stub-pattern).
2. **Read the UIA package's core guide IN FULL** — `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md`. It owns the shared UIA law — window baseline, the mandatory target-generation gate, terminology, common pitfalls, control-specific interaction, reading values — and its § Documentation routes to everything else, including the per-mode authoring guides. **Before authoring UIA activities, additionally read your mode's authoring guide IN FULL** (XAML or coded, routed from § Documentation) — during capture-only phases neither mode guide is needed yet. The core guide ships with the package: if the package is installed but the file is absent, the installed version predates it — treat as below the minimum version (§ UIA Prerequisites).

Prerequisites and upgrade consent are below. The skill's other UIA policies — running and debugging UIA workflows, the deliverable when live capture is unavailable, publishing Object Repository descriptors as a shared UI Library — are entries of [uia-policies-catalog.md](uia-policies-catalog.md), each read when its condition holds.

---

## UIA Prerequisites

**Required package:** `UiPath.UIAutomation.Activities` — minimum version (`<MIN_VERSION>`): **`26.10.2`**, from the official UiPath NuGet feed (no prerelease flag needed). The `uip rpa uia` CLI, the package docs, and the UIA skills require `<MIN_VERSION>` or newer — before any UIA work, check the installed version in `project.json` under `dependencies`. Do not hardcode the version from memory; this section is the only source of truth.

**Upgrades require explicit user consent.** Never install or upgrade UIA silently. Consent comes from one of:

- **Plan-mode:** approval of a plan whose Task 0 names the upgrade explicitly — both package ID and version. Plan approval IS the consent — do NOT re-ask at execution time.
- **Interactive mode (no plan):** a direct prompt before `packages install` runs.

| Scenario | Behavior |
|---|---|
| No UIA installed, request needs UIA | Ask before installing `<MIN_VERSION>` from the official UiPath feed. |
| Major-version upgrade (e.g. `25.x` → `26.x`) | Ask. Breaking changes are possible across major versions. |
| Minor / patch / build upgrade | Ask before installing the newer build. |
| Already at or above `<MIN_VERSION>` | Proceed without prompting. |

Discovery (non-mutating, no consent required):

```bash
uip rpa packages versions --package-id UiPath.UIAutomation.Activities --include-prerelease --project-dir "$PROJECT_DIR" --output json
```

Install / upgrade (mutating — only after consent per the table above):

```bash
uip rpa packages install --packages 'id=UiPath.UIAutomation.Activities,version=<MIN_VERSION>' --project-dir "$PROJECT_DIR" --output json
```

Omit `,version=<MIN_VERSION>` to resolve the latest compatible build (at or above `<MIN_VERSION>`).
