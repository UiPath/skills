# UiAutomation Prerequisites

**Required package:** `UiPath.UIAutomation.Activities`

The `uip rpa uia` subcommands (snapshot, selector-intelligence, object-repository) used by `uia-configure-target` require **`UiPath.UIAutomation.Activities` >= 26.3.1-beta.11555873**. Before configuring any target, check the installed version in `project.json` under `dependencies`.

If the installed version is below the minimum, ask the user whether to upgrade:

```bash
uip rpa get-versions --package-id UiPath.UIAutomation.Activities --project-dir "$PROJECT_DIR" --output json --use-studio

# If user approves the upgrade:
uip rpa install-or-update-packages --packages '[{"id": "UiPath.UIAutomation.Activities", "version": "26.3.1-beta.11555873"}]' --project-dir "$PROJECT_DIR" --output json --use-studio
```

If the user declines, warn that `uip rpa uia` commands will fail and fall back to the indication tools (see [uia-configure-target-workflows.md](uia-configure-target-workflows.md) for fallback commands).
