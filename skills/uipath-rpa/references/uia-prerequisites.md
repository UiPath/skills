# UiAutomation Prerequisites

**Required package:** `UiPath.UIAutomation.Activities`
**Minimum version (`<MIN_VERSION>`):** `26.10.0`
**Source feed:** the official UiPath NuGet feed — the same feed Studio resolves by default.

> **Stable release.** `<MIN_VERSION>` is a stable GA build — it ships the `uia-configure-target` skill content and resolves from the official feed without any prerelease flag. Querying with `--include-prerelease` is still fine (it surfaces newer preview builds), but it is not needed to reach `<MIN_VERSION>`.

The `uip rpa uia` CLI used by `uia-configure-target` requires `UiPath.UIAutomation.Activities` at `<MIN_VERSION>` or newer. Before configuring any target, check the installed version in `project.json` under `dependencies`.

## Upgrades require explicit user consent

Never upgrade UIA silently. Every upgrade requires explicit user consent before any package mutation. Consent comes from one of:

- **Plan-mode:** approval of a plan whose Task 0 names the upgrade explicitly — both package ID and version. Plan approval IS the consent — do NOT re-ask at execution time.
- **Interactive mode (no plan):** a direct prompt before `packages install` runs.

| Scenario | Behavior |
|---|---|
| No UIA installed, request needs UIA | Ask before installing `<MIN_VERSION>` from the official UiPath feed. |
| Major-version upgrade (e.g. `25.x` → `26.x`) | Ask. Note that breaking changes are possible across major versions. |
| Minor-version upgrade (e.g. `26.4.x` → `26.10.x`) | Ask before installing the newer build. |
| Patch / build upgrade within the `26.10.x` band | Ask before installing the newer build. |
| Already at or above `<MIN_VERSION>` | Proceed without prompting. |

If the user declines, do NOT install. Warn that `uip rpa uia` commands will fail without UIA at `<MIN_VERSION>` and fall back to indication authoring — [uia-configure-target-workflows.md](uia-configure-target-workflows.md) MUST be read IN FULL first (see § Indication Fallback). Record `UI capture: indication-only` in the plan header so downstream tasks do not route to `uia-configure-target`.

## Commands

Discovery (non-mutating, no consent required):

```bash
uip rpa packages versions --package-id UiPath.UIAutomation.Activities --include-prerelease --project-dir "$PROJECT_DIR" --output json
```

Install / upgrade (mutating — only after consent per the table above; substitute `<MIN_VERSION>` with the value declared at the top of this file):

```bash
uip rpa packages install --packages 'id=UiPath.UIAutomation.Activities,version=<MIN_VERSION>' --project-dir "$PROJECT_DIR" --output json
```

`packages install` resolves `<MIN_VERSION>` directly via the `version` field — no prerelease flag is needed, since it is a stable release. Omit `,version=<MIN_VERSION>` to resolve the latest compatible build (which will be at or above `<MIN_VERSION>`).
