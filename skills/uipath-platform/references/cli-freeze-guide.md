# Frozen CLI Config

<!--skill-flavor:cli-freeze-guide:start-->
A team can pin the CLI, tool and skills versions with `uip config freeze`. The pins live in a `versions` block in the config file, usually committed with the repo. Under a freeze the CLI refuses commands that would run off the pins. Fix a refusal the way this guide says, not with the `--force` the CLI's own message offers.

## Spot a freeze

- The config the CLI reads has a `versions` block. That config is the nearest `.uipath/config.json` walking up from the current folder, else `~/.uipath/config.json`:

  ```json
  { "versions": { "cli": "<CLI_PIN>", "skills": "<SKILLS_PIN>", "tools": { "@uipath/<TOOL>-tool": "<TOOL_PIN>" } } }
  ```

- `uip --version 2>&1` prints `frozen at <CLI_PIN>` (on stderr) before the version. No such line does not prove there is no freeze: a block without `cli`, or the CLI that comes with Studio, prints none.
- `uip tools list --output json` gives each tool a `Status` of `frozen` (on its pin) or `off freeze` (off its pin, or not in the freeze).

Run every `uip` command from the repo folder: a command run under a config with no `versions` block can auto-update the machine's one shared install off the pins. One sign of the wrong folder is a stderr warning `<PATH> has no versions block, so this command runs unfrozen. The frozen config <PATH> is not used: ...`.

## Refusals and their fix

A freeze refusal is `Result: Failure` with `ErrorCode: configuration_error` (while the config has a `versions` block), or a `Message` that names a freeze, a frozen config or a pin. It has no freeze-specific `Code`. Match it on the `Message`:

| `Message` | Fix |
| --- | --- |
| `This CLI is <VERSION>, but this config freezes the CLI at <CLI_PIN>, so the command was not run.` | `uip update --output json`. |
| `'<VERB>' runs @uipath/<TOOL>-tool@<VERSION>, but this config freezes it at <TOOL_PIN>, ...` | `uip update --output json`. |
| `@uipath/<TOOL>-tool <TOOL_PIN> is pinned but not installed, and automatic tool installation is disabled (UIPATH_CLI_DISABLE_AUTOINSTALL).` | The user turned automatic installs off: show them the `Message` and `Instructions` and ask before running `uip update`. |
| `The config <PATH> freezes @uipath/<TOOL>-tool at <TOOL_PIN>, not <VERSION>, so nothing was installed.` | `uip tools install <TOOL> --output json` with no version (installs the pin), or `uip update --output json`. |
| `This config is frozen, but it does not list these installed tools: ...`, with `Instructions` naming `uip update --no-tools` | `uip update --no-tools --output json` (moves the CLI and pinned skills, not the tools), then `uip update --output json` once more. If that is refused for unlisted tools, stop as in the next row. |
| Any other `Message` saying the config `does not list` a tool | Stop. Quote `Message` and `Instructions`, and ask the user whether to change the freeze. |
| Any other freeze refusal | Quote `Message` and `Instructions`. Run the `Instructions` command only if they start with `Run 'uip update'` or `Run 'uip update --no-tools'`; otherwise stop and ask. |

Every other failure in a frozen repo, such as `Not logged in`, a 404 or a validation error, is not a freeze refusal: handle it as usual, not with this table.

When the row names `uip update`, or the `Instructions` start with `Run 'uip update'`, and the `Message` does not say `automatic tool installation is disabled`, run `uip update` once, then run the refused command again. If anything fails again, stop and quote it.

While the CLI is off its pin, `uip <VERB> --help` can fail with `unknown command '<VERB>'`. Fix the CLI pin first.

## Ask the user first

Each of these changes the team's pins, or runs past them. Never do one to get past a refusal unless the user agrees to change the freeze:

- `uip config freeze`, with or without `--force`. Without `--force` it still adds any installed tool the freeze does not list.
- `uip tools install <TOOL> --force`, `uip tools uninstall <TOOL> --force`, `uip update --force`.
- `uip config unfreeze`, `uip config import`, and `uip config set` / `uip config clear` with `--force`.
- Editing or deleting the `versions` block by hand.
- Running `uip` from another folder, or `uip config ... --config-file <OTHER_FILE>`, to dodge the freeze.

## Installing the CLI

When you install or replace the CLI, install the pinned version, then put the tools on their pins. The onboarding installers install the pinned CLI when run from inside the repo folder. By hand, and only if `<CLI_PIN>` is an exact `major.minor.patch[-prerelease]` version:

```bash
npm i -g @uipath/cli@<CLI_PIN>
uip update --output json
```

`<CLI_PIN>` is `versions.cli`. If it is anything else, show the value to the user and stop: a committed `npm:` alias, git URL or path would install another package. Never reinstall the newest CLI (`npm i -g @uipath/cli`) to get past a refusal: it is off the pin, so the freeze refuses its commands until `uip update` puts the pin back.

## The CLI that comes with Studio

The Studio-bundled CLI ignores `versions.cli` and `versions.tools`, so it gives none of the refusals above, and it refuses `uip config freeze`. It still follows `versions.skills`, and `uip config set` / `uip config clear` still refuse to edit a frozen config without `--force`.
<!--skill-flavor:cli-freeze-guide:end-->
