> when: installing or bootstrapping the uip CLI, Node, .NET, Python, or agent skills on a machine where `uip --version` fails

## CLI Bootstrap for Fresh Machines

When `uip --version` fails, Node/npm is missing, or a coding agent needs a workstation prepared for UiPath work, use the official onboarding installers instead of reconstructing package-manager logic. They are idempotent and safe to rerun.

macOS/Linux:

```bash
curl -fsSL https://download.uipath.com/uipath-cli/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://download.uipath.com/uipath-cli/install.ps1 | iex
```

The installers:

- Ensure Node.js >= 20 and npm.
- Install `@uipath/cli` from public npm.
- Run `uip skills install --no-interactive` so installed AI coding agents (Claude Code, Codex, Gemini CLI, Cursor, etc.) can use the UiPath skills.
- Best-effort install .NET SDK 8.0 and Python 3.11-3.14 for RPA, coded-agent, and tool workflows.

For CI or a CLI-only machine where agent skills and runtimes are not needed, skip them explicitly:

```bash
curl -fsSL https://download.uipath.com/uipath-cli/install.sh | bash -s -- --skip-skills --skip-runtimes
```

```powershell
iwr https://download.uipath.com/uipath-cli/install.ps1 -OutFile install.ps1
./install.ps1 -SkipSkills -SkipRuntimes
```

Useful flags: `--skip-node`, `--skip-skills`, `--skip-dotnet`, `--skip-python`, `--skip-runtimes`, `--dry-run` on macOS/Linux; `-SkipNode`, `-SkipSkills`, `-SkipDotnet`, `-SkipPython`, `-SkipRuntimes`, `-DryRun` on Windows. The matching environment variables are `UIP_SKIP_NODE`, `UIP_SKIP_SKILLS`, `UIP_SKIP_DOTNET`, `UIP_SKIP_PYTHON`, `UIP_SKIP_RUNTIMES`, and `UIP_DRY_RUN`.
