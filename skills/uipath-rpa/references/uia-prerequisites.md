# UiAutomation Prerequisites

**Required package:** `UiPath.UIAutomation.Activities`
**Minimum version (`<MIN_VERSION>`):** `26.4.1-beta.11835126`

The `uip rpa uia` CLI used by `uia-interact` and `uia-configure-target` requires `UiPath.UIAutomation.Activities` at `<MIN_VERSION>` or newer. Treat this as a hard gate for UI automation work.

## Required Sequence

Before any live-app inspection, target capture, selector work, or UIA workflow authoring:

1. Resolve `PROJECT_DIR` and read `project.json`.
2. Check `dependencies["UiPath.UIAutomation.Activities"]`.
3. If the package is absent or below `<MIN_VERSION>`, install or upgrade to `<MIN_VERSION>` unless the user explicitly forbids dependency changes.
4. Restore the project.
5. Verify the generated UIA docs and CLI surface exist before proceeding.

Do not choose an older stable-looking package when UI exploration or selector capture is needed. The minimum version here is the source of truth.

`--project-dir` is an option on `uip rpa`, not on the nested `uia` command. When a project directory is needed, put it before `uia`:

```bash
uip rpa get-versions --package-id UiPath.UIAutomation.Activities --include-prerelease --project-dir "$PROJECT_DIR" --output json
uip rpa install-or-update-packages --packages '[{"id":"UiPath.UIAutomation.Activities","version":"26.4.1-beta.11835126"}]' --project-dir "$PROJECT_DIR" --output json
uip rpa restore "$PROJECT_DIR" --output json
uip rpa --project-dir "$PROJECT_DIR" uia --help
```

With `@uipath/rpa-tool` 0.9.x, restore may try to resolve `UiPath.Studio.Helm.Windows` 0.9.0 even when only a newer `1.0.0-alpha.*` package exists on the feed. If the restore error reports a nearest available Helm version, set `HELM_NUGET_VERSION` to that exact version and rerun restore, for example:

```bash
HELM_NUGET_VERSION=1.0.0-alpha.20260422.11 uip rpa restore "$PROJECT_DIR" --output json
```

Expected docs after restore:

- `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-interact/SKILL.md`
- `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-configure-target/SKILL.md`
- `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md`

If the user declines the upgrade, or if the CLI surface is still unavailable after the upgrade and restore, do not use OS-level substitutes. If docs are missing but `uip rpa --project-dir "$PROJECT_DIR" uia --help` exposes `snapshot`, `interact`, `target-app`, `target-anchorable`, `object-repository`, and `selector-intelligence`, proceed from CLI help and package activity docs, then record the missing-docs issue. Report the blocker and use indication fallback only if the UIA command surface itself is unavailable. See [uia-configure-target-workflows.md](uia-configure-target-workflows.md) Indication Fallback.
