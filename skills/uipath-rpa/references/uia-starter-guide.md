# UIA Starter Guide

Read this file in full before any UI-automation work (Rule 7). Then:

1. **Verify prerequisites** — minimum package version: [§ UIA Prerequisites](#uia-prerequisites) below. If the package cannot be installed, use [uia-policies-catalog.md § Placeholder-Selector Stub Pattern](uia-policies-catalog.md#placeholder-selector-stub-pattern).
2. **Read the UIA package's core guide IN FULL** — `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md`. It owns the shared UIA law — window baseline, the mandatory target-generation gate, terminology, common pitfalls, control-specific interaction, reading values — and its § Documentation routes to everything else, including the per-mode authoring guides. **Before authoring UIA activities, additionally read your mode's authoring guide IN FULL** (XAML or coded, routed from § Documentation) — during capture-only phases neither mode guide is needed yet. The core guide ships with the package: if the package is installed but the file is absent, the installed version predates it — treat as below the minimum version (§ UIA Prerequisites).

Prerequisites are below. The skill's other UIA policies — running and debugging UIA workflows, the deliverable when live capture is unavailable, publishing Object Repository descriptors as a shared UI Library — are entries of [uia-policies-catalog.md](uia-policies-catalog.md), each read when its condition holds.

---

## UIA Prerequisites

**Required package:** `UiPath.UIAutomation.Activities` — minimum version (`<MIN_VERSION>`): **`26.10.2`**, a stable release on the official UiPath NuGet feed. The `uip rpa uia` CLI, the package docs, and the UIA skills require `<MIN_VERSION>` or newer — before any UIA work, check the installed version in `project.json` under `dependencies`. Do not hardcode the version from memory; this section is the only source of truth.

Install or upgrade the package through the version question in SKILL.md § Resolving Packages & Activity Docs, Step 1, which offers only versions at or above `<MIN_VERSION>`.
