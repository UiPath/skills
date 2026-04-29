# UiAutomation Prerequisites

**Required package:** `UiPath.UIAutomation.Activities`
**Minimum version (`<MIN_VERSION>`):** `26.4.1-preview`
**Source feed:** the official UiPath NuGet feed — the same feed Studio resolves by default. Prerelease / preview builds of `UiPath.UIAutomation.Activities` are published there alongside stable releases. Installing them is a normal supported path, not a third-party workaround.

> **Prerelease required.** `<MIN_VERSION>` is a preview — stable releases of `UiPath.UIAutomation.Activities` do NOT yet ship the `uia-configure-target` skill content. Install the prerelease build explicitly. `uip rpa get-versions` MUST be invoked with `--include-prerelease` (the flag defaults to `false`), otherwise the required preview is filtered out of the listing and the agent will report "no upgrade available" against a feed that actually has it.

The `uip rpa uia` CLI used by `uia-configure-target` requires `UiPath.UIAutomation.Activities` at `<MIN_VERSION>` or newer. Before configuring any target, check the installed version in `project.json` under `dependencies`.

## Upgrades require explicit user consent

Never upgrade UIA silently. Every upgrade requires explicit user consent before any package mutation. Consent comes from one of:

- **Plan-mode:** approval of a plan whose Task 0 names the upgrade explicitly — both package ID and version. Plan approval IS the consent — do NOT re-ask at execution time.
- **Interactive mode (no plan):** a direct prompt before `install-or-update-packages` runs.

| Scenario | Behavior |
|---|---|
| No UIA installed, request needs UIA | Ask before installing `<MIN_VERSION>`. Disclose that it is a prerelease build from the official UiPath feed. |
| Major-version upgrade (e.g. `25.x` → `26.x`) | Ask. Note that breaking changes are possible across major versions. |
| Minor-version upgrade (e.g. `26.3.x` → `26.4.x`) | Ask. Note that the minimum required for `uia-configure-target` is a preview. |
| Patch / build upgrade within the preview band | Ask before installing the newer preview build. |
| Already at or above `<MIN_VERSION>` | Proceed without prompting. |

If the user declines, do NOT install. Warn that `uip rpa uia` commands will fail without UIA at `<MIN_VERSION>` and fall back to indication authoring (see [uia-configure-target-workflows.md](uia-configure-target-workflows.md) § Indication Fallback). Record `UI capture: indication-only` in the plan header so downstream tasks do not route to `uia-configure-target`.

## Commands

Discovery (non-mutating, no consent required):

```bash
uip rpa get-versions --package-id UiPath.UIAutomation.Activities --include-prerelease --project-dir "$PROJECT_DIR" --output json
```

Install / upgrade (mutating — only after consent per the table above; substitute `<MIN_VERSION>` with the value declared at the top of this file):

```bash
uip rpa install-or-update-packages --packages '[{"id": "UiPath.UIAutomation.Activities", "version": "<MIN_VERSION>"}]' --project-dir "$PROJECT_DIR" --output json
```

`install-or-update-packages` accepts the beta version directly via the `version` field — no separate prerelease flag is needed once the version string is specified explicitly.
