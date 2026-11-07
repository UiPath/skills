# Acquisition Guide

How the skill obtains, caches, verifies, and updates `UiPath.Upgrade.exe`. The script `scripts/ensure-migrator.mjs` implements this, run with `node`; read here when it fails or the user asks where the tool lives. Nothing is downloaded without the user's choice (SKILL.md Rule 15): a plain run only locates and verifies, `--install` downloads.

## What ships

| Item | Value |
|---|---|
| Public download | `https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip` |
| Also available from | Automation Cloud → Help → Resources → Downloads → Activity Migrator Tool; Customer Portal (`https://customerportal.uipath.com/`) |
| Archive | Zip with `UiPath.Upgrade.exe` at the archive root and extensions under `Extensions/<Name>/` |
| Runtime | Windows, .NET 8: `Microsoft.NETCore.App 8.x` and `Microsoft.WindowsDesktop.App 8.x` (the .NET Desktop Runtime 8 installer provides both) |
| Version | `UiPath.Upgrade.exe version` prints it (GA line `25.10.x`) |
| Freshness signal | The URL is unversioned. The server's `Last-Modified` header is the only change signal; the script stores it, reports `update: true` when it changes, and re-downloads on an install run |

Studio does not need to be installed. Opening the migrated project afterwards needs Studio 2024.10 or later.

## Cache layout

Default root: `%LOCALAPPDATA%\UiPath\ActivityMigrator` (`$LOCALAPPDATA/UiPath/ActivityMigrator` in Git Bash).

```text
ActivityMigrator/
  current/                 extracted tool; UiPath.Upgrade.exe lives here
  .last-modified           Last-Modified header of the archive that produced current/
  UiPath.Upgrade.Cli.download.zip   transient during download; removed on success, kept on an extraction failure so it can be extracted by hand
```

Resolution order used by the script:

1. `UIPATH_ACTIVITY_MIGRATOR_DIR` when set: use `<dir>/UiPath.Upgrade.exe` if present, else `<dir>/current/UiPath.Upgrade.exe`. Nothing is downloaded into an override dir unless the exe is missing there and the run is an install run.
2. Default root, `current/UiPath.Upgrade.exe`.
3. Nothing found: a plain run reports `missing` with `dir` and `url`, and the skill asks the user. An install run (`--install` or `--force`) downloads and extracts into the default root (or the override dir).

## Environment variables and flags

| Variable / flag | Effect |
|---|---|
| `UIPATH_ACTIVITY_MIGRATOR_DIR` | Install or cache root. Use for shared tool drives or manual placement |
| `UIPATH_ACTIVITY_MIGRATOR_URL` | Alternate archive URL, for internal mirrors |
| `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1` | Never touch the network. A cached tool is used as is; a missing tool is an error. Wins over `--install` and `--force` |
| `--install` | Download and extract when nothing is cached; replace the cache when the archive changed. The skill passes it only after the user chose the download |
| `--force` | Re-download and re-extract even when cached. Implies `--install` |

Download: the script tries `curl` first, which honors `HTTPS_PROXY` / `HTTP_PROXY`, then PowerShell's WebClient, which uses the system proxy and the signed-in user's credentials. Both run as commands, never as script files. The update check's `HEAD` request falls back the same way, so a machine that reaches the internet only through the system proxy still sees updates. A curl connection that stalls below 1 KB/s for a minute fails instead of hanging. Corporate TLS inspection that breaks both surfaces as `download-failed`, with each downloader's error in the message.

Extraction: `Expand-Archive`, then Windows `tar.exe`, then `unzip`. An install root whose extracted paths would pass the 260-character Windows limit makes `Expand-Archive` fail; `tar.exe` still extracts it.

## Managed environments

The skill never downloads without the user's choice. These settings, set machine- or user-wide by an administrator, decide the outcome before the question would be asked, so it never appears.

| Situation | Set | Effect |
|---|---|---|
| Binary distributed by desktop engineering or placed on a tool share | `UIPATH_ACTIVITY_MIGRATOR_DIR=<FOLDER>` and `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1` | The preinstalled tool is used (`source: env`) and the network is never touched. A missing tool is `offline-missing`: the skill gives the manual steps instead of offering a download |
| Archive mirrored on an internal server | `UIPATH_ACTIVITY_MIGRATOR_URL=<MIRROR_URL>` | Download and update check go to the mirror. The user's choice is still required; the install question names the mirror |
| No downloads, nothing preinstalled yet | `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1` | Every run is `offline-missing` until the tool is placed by hand |

The tool is a zip: placing it needs no installer and no elevation. The `Extensions/` folder must stay next to the exe.

## Script output contract

The last stdout line is one JSON object.

```json
{"status":"ok","exe":"C:\\Users\\me\\AppData\\Local\\UiPath\\ActivityMigrator\\current\\UiPath.Upgrade.exe","version":"25.10.0","source":"cached","runtime":"8.0.11"}
```

| Field | Values |
|---|---|
| `status` | `ok`, `missing`, `error` |
| `dir`, `url` (`missing` only) | The folder an install run would fill and the archive it would fetch: the facts the skill puts in its install question |
| `update` (`ok` only) | `true` when the server's `Last-Modified` differs from the stamp on a plain run: a newer build exists and the cached tool was kept. Absent otherwise |
| `source` | `env` (override dir), `cached`, `downloaded` (first install), `updated` (newer archive replaced the cache) |
| `code` (errors) | `not-windows`, `runtime-missing`, `download-failed`, `extract-failed`, `verify-failed`, `offline-missing`, `telemetry-flag` |
| `env` (`telemetry-flag` only) | The assignment the tool starts with, `UIPATH_TELEMETRY_DISABLED=true` or `=false` |
| `message` | Human-readable detail, including the manual steps for the failing stage |

Exit codes: `0` ok, `1` error, `3` missing.

## Install question

SKILL.md Step 0 sends the agent here when the script reports `missing`. `<URL>` and `<DIR>` are the `url` and `dir` values of that object. Use the host's structured question tool when it has one, otherwise ask in text. Offer exactly these two options, the first as the recommended one, and no other:

> The Activity Migrator (`UiPath.Upgrade.exe`) is not installed. UiPath distributes it as a zip of a few hundred MB for Windows.
>
> 1. **Download it now** (recommended). I fetch `<URL>`, extract it into `<DIR>` and run the tool from there.
> 2. **You provide it.** Download `UiPath.Upgrade.Cli.zip` yourself from `<URL>`, from Automation Cloud → Help → Resources → Downloads → Activity Migrator Tool, or from the Customer Portal. Extract it so `UiPath.Upgrade.exe` and the `Extensions/` folder sit directly in one folder, then tell me that folder or set `UIPATH_ACTIVITY_MIGRATOR_DIR` to it.
>
> On a machine an administrator manages, these settings can be preset so this question never comes up.

Option 1: rerun the script with `--install`. The download is a few hundred MB: give the command at least 10 minutes, not the host's default timeout. Apply Step 0's table to its output.

Option 2: wait for the user, then rerun the script without a flag, with the variable set to the folder they named in the syntax of the shell that runs it: bash `UIPATH_ACTIVITY_MIGRATOR_DIR="<FOLDER>" node ...`, PowerShell `$env:UIPATH_ACTIVITY_MIGRATOR_DIR = '<FOLDER>'; node ...`. Apply Step 0's table. `missing` again means the folder holds no `UiPath.Upgrade.exe`, neither at its root nor under `current/`: say so, name those two places, and wait for the user; do not download and do not ask the question a second time. A variable set in the command lasts for that command only: tell the user to set it in their user environment so later sessions find the tool; a folder placed at the default `%LOCALAPPDATA%\UiPath\ActivityMigrator\current` needs no variable. The preset settings for managed machines are in [Managed environments](#managed-environments); point an administrator there when asked.

## Manual placement

For air-gapped machines or when both downloaders are blocked:

1. Download `UiPath.Upgrade.Cli.zip` on a machine with access (URL above, or the Automation Cloud download page).
2. Extract it so that `UiPath.Upgrade.exe` and the `Extensions/` folder sit directly inside one folder.
3. Either place that folder at `%LOCALAPPDATA%\UiPath\ActivityMigrator\current`, or set `UIPATH_ACTIVITY_MIGRATOR_DIR` to it.
4. Set `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1` so the script never tries the network.
5. Rerun the acquisition script. Expected: `status: ok`, `source: env` or `cached`.

Runtime missing: install the .NET Desktop Runtime 8 (x64) from `https://dotnet.microsoft.com/download/dotnet/8.0`, then rerun. The script checks the one place the migrator loads its runtime from: `DOTNET_ROOT_X64` or `DOTNET_ROOT` while one is set; otherwise the install location the .NET installer registers, else `%ProgramFiles%\dotnet`. It never uses the `dotnet` on `PATH`, which the migrator ignores. Verify by rerunning the script, which checks those same places:

```bash
node "<SKILL_DIR>/scripts/ensure-migrator.mjs"
```

## Telemetry flag crash

The `25.10.x` builds read `UIPATH_TELEMETRY_DISABLED` with a strict boolean parse. Any value other than `true` or `false`, the documented `1` included, makes every command die at startup with `The type initializer for 'UiPath.Service.Api.Communication' threw an exception.` A re-download does not help. When `version` fails while the variable holds such a value, the script retries with the strict spelling of the same choice (`0`, `no`, `off` → `false`; anything else → `true`) and, when that starts, reports `telemetry-flag` with the assignment in `env`. Prefix it to the script and to every `UiPath.Upgrade.exe` command:

```bash
UIPATH_TELEMETRY_DISABLED=true node "<SKILL_DIR>/scripts/ensure-migrator.mjs"
UIPATH_TELEMETRY_DISABLED=true "<MIGRATOR_EXE>" analyze --help
```

Never unset the variable instead: that turns telemetry on for a user who disabled it. A build that accepts `1` and `0` starts on the first try, and the script then never reports this code. Older `uip` CLIs crash the same way in `uip rpa build`; [build-verification-guide.md](build-verification-guide.md) covers that.

## Updating

Every plain run sends a `HEAD` request and compares `Last-Modified` with `.last-modified`. When they differ it keeps the cached tool and reports `update: true`; nothing is replaced without an install run. To update, rerun with `--install`: `current/` is replaced only when the archive changed (`source: updated`). `--force` refreshes even an unchanged cache. An override dir is never updated unless its exe is missing; replace its contents by hand. Under `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1` no `HEAD` is sent and no update is reported.

## Verifying an install by hand

```bash
"<MIGRATOR_EXE>" version
"<MIGRATOR_EXE>" analyze --help
```

The help output lists the active extensions through their flags: `--uia-*` for UI Automation, `--mail-*` / `--config` for Mail, `--gsuite-*` only in preview builds. An extension whose flags are absent is not active in this build.
