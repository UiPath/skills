# UiAutomation Prerequisites

**Required package:** `UiPath.UIAutomation.Activities`
**Minimum version (`<MIN_VERSION>`):** `26.4.1-beta.11749457`

The `uip rpa uia` subcommands (snapshot, selector-intelligence, object-repository) used by `uia-configure-target` require `UiPath.UIAutomation.Activities` at `<MIN_VERSION>` or newer. Before configuring any target, check the installed version in `project.json` under `dependencies`.

If the installed version is below the minimum, ask the user whether to upgrade:

```bash
uip rpa get-versions --package-id UiPath.UIAutomation.Activities --project-dir "$PROJECT_DIR" --output json
# If user approves the upgrade (substitute <MIN_VERSION> with the value declared above):
uip rpa install-or-update-packages --packages '[{"id": "UiPath.UIAutomation.Activities", "version": "<MIN_VERSION>"}]' --project-dir "$PROJECT_DIR" --output json```

If the user declines, warn that `uip rpa uia` commands will fail and fall back to the indication tools (see [uia-configure-target-workflows.md](uia-configure-target-workflows.md) for fallback commands).
