# Acquisition Guide

How the skill finds and verifies the Activity Migrator: Helm's, through `uip`, else the standalone `UiPath.Upgrade.exe` from the public archive. The script `scripts/ensure-migrator.mjs` implements this, run with `node`; read here when it fails or the user asks where the tool lives. Nothing is downloaded without the user's choice (SKILL.md Rule 15): a migrator from `uip` needs no download, and for the archive a plain run only locates and verifies, `--install` downloads.

## What ships

| Item | Value |
|---|---|
| Helm | The migrator ships inside every Windows Helm and runs from Helm's folder with Helm's DLLs: `UiPath.Upgrade.exe analyze\|upgrade\|bulk\|version <args>`, next to `UiPath.Studio.Helm.exe`, is Helm's own apphost under another name, and `uip` runs it (a Helm without it runs the migrator as `UiPath.Studio.Helm.exe migrate <verb> <args>`). `uip` installs Helm with its RPA tool, from the npm packages `@uipath/studio-helm-win32-x64` and `@uipath/studio-helm-win32-arm64`, which are optional dependencies of `@uipath/rpa-tool`. The Studio MSI carries the same Helm |
| `uip` commands | `uip rpa project migrate analyze\|upgrade\|bulk\|version <args>` hands its arguments to Helm's migrator unchanged. stdout, stderr and the exit code are the migrator's; stdout is SARIF with `--output-format sarif`. The commands take no `uip` options of their own (no `--format`, `--output`, `--verbose`): everything goes to the migrator. There is no install step |
| Public download | `https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip`, the standalone `UiPath.Upgrade.exe`. The fallback when `uip` cannot supply the migrator |
| Also available from | Automation Cloud → Help → Resources → Downloads → Activity Migrator Tool; Customer Portal (`https://customerportal.uipath.com/`) |
| Archive | Zip with `UiPath.Upgrade.exe` at the archive root and extensions under `Extensions/<Name>/` |
| Runtime | Through `uip`: Helm runs on the dotnet of the Robot or Studio install, else on the `dotnet` on `PATH` with `DOTNET_ROLL_FORWARD=LatestMajor`. `uip` resolves it; the script checks nothing. The archive: Windows and the .NET Desktop Runtime of the major version the build targets, recorded in `UiPath.Upgrade.runtimeconfig.json` next to the exe |
| Version | `uip rpa project migrate version` prints Helm's version as its last stdout line, e.g. `27.0.207-dev` or `26.10.x`; the SARIF `tool.driver.version` carries the same. `UiPath.Upgrade.exe version` prints the archive's own |
| Freshness signal | Through `uip`: the CLI version. The archive URL is unversioned; `latest.json`, published next to the archive (`https://download.uipath.com/upgrade/latest.json`), names the `version` the archive holds. The script compares it with the cached tool's, reports `update: true` when the server's is newer, and re-downloads on an install run |

Both forms take the same arguments and write the same SARIF and reports: exit code 0 whatever the outcome, extension options bind only as `--name=value`, reports go to `<PROJECT_DIR>/.upgrade` ([tool-behavior-guide.md](tool-behavior-guide.md)).

Studio does not need to be installed. Opening the migrated project afterwards needs Studio 2024.10 or later.

## Helm through uip

The script runs `uip rpa project migrate version` without `UIPATH_STUDIO_PID` in its environment, with or without a flag. A version on the last stdout line means the migrator is there: the script reports `source: uip` and the skill runs `uip rpa project migrate <verb>` from then on. No environment variable is needed and nothing is downloaded.

| Setup | What to do | Helm comes from |
|---|---|---|
| Online | Nothing | The Helm npm package installed with `uip` |
| Internal npm registry (Artifactory, Nexus, …) | `.npmrc` routes the `@uipath` scope to the registry, as for the CLI itself | The same registry, at `uip` install time; nothing reaches `download.uipath.com` |
| Air-gapped, CLI installed from its air-gapped archive (Windows) | Nothing: the archive carries Helm | The archive |
| Studio installed (MSI) | Set `HELM_LOCAL_DIR` to the Studio folder that holds `UiPath.Studio.Helm.exe` | The Studio install, run in place |

The first call after a CLI update copies Helm into its run slot under `%LOCALAPPDATA%\UiPath\Helm`, which can take a minute or two; later calls start at once.

`uip`'s own failures print one JSON object, on stdout or stderr, and exit 1:

```json
{"Result":"Failure","Message":"…","Instructions":"…","Code":"helm-missing"}
```

| `uip` result | Cause | Script |
|---|---|---|
| `Code: not-windows` | Not a Windows machine | Fails with `not-windows` |
| `Code: helm-missing` | `uip` was installed without its optional Helm dependency (`--omit=optional`, `--no-optional`), or `HELM_LOCAL_DIR` names a folder without Helm. The fix: reinstall `uip` with its optional dependencies, or correct `HELM_LOCAL_DIR` | Falls back to the archive |
| An unknown-command error | A `uip` released before `project migrate`. The fix: update the CLI (`uip update`) | Falls back to the archive |
| `version` exits non-zero with Helm's own error | A Helm released before the `migrate` verb, typically through `HELM_LOCAL_DIR`. The fix: a newer Helm | Falls back to the archive |
| `uip` is not found | No CLI on `PATH` | Falls back to the archive |

After a fallback every result carries `uipMessage`, the reason above, so the user can fix the `uip` side instead of downloading the archive.

## Archive fallback

The script uses the archive when `uip` cannot supply the migrator, and right away when `UIPATH_ACTIVITY_MIGRATOR_DIR` or `UIPATH_ACTIVITY_MIGRATOR_URL` is set.

### Cache layout

Default root: `%LOCALAPPDATA%\UiPath\ActivityMigrator` (`$LOCALAPPDATA/UiPath/ActivityMigrator` in Git Bash).

```text
ActivityMigrator/
  current/                 extracted tool; UiPath.Upgrade.exe lives here
  current.old/             previous build during a replacement; removed once the new one is in place
  UiPath.Upgrade.Cli.download.zip   transient during download; kept only when it cannot be extracted or moved into an empty folder, so it can be extracted by hand
```

Resolution order inside the archive fallback:

1. `UIPATH_ACTIVITY_MIGRATOR_DIR` when set: use `<dir>/UiPath.Upgrade.exe` if present, else `<dir>/current/UiPath.Upgrade.exe`. Nothing is downloaded into an override dir unless the exe is missing there and the run is an install run.
2. Default root, `current/UiPath.Upgrade.exe`.
3. Nothing found: a plain run reports `missing` with `dir`, `url` and any `uipMessage`, and the skill asks the user ([Install question](#install-question)). An install run (`--install` or `--force`) downloads and extracts into the default root (or the override dir).

### Environment variables and flags

| Variable / flag | Effect |
|---|---|
| `UIPATH_ACTIVITY_MIGRATOR_DIR` | A folder holding `UiPath.Upgrade.exe`, used as is; also the archive's install root. Skips `uip`. Use for shared tool drives or manual placement |
| `UIPATH_ACTIVITY_MIGRATOR_URL` | Alternate archive URL, for internal mirrors. Skips `uip` |
| `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1` | The archive never touches the network: a cached tool is used as is, a missing one is `offline-missing`. Wins over `--install` and `--force`. `uip` is still asked; `migrate version` downloads nothing |
| `HELM_LOCAL_DIR` | Read by `uip`, not by the script: a Helm folder to use instead of the npm package, such as the Studio install's |
| `--install` | Archive only: download and extract when nothing is cached; replace the cache when the server holds a newer version. The skill passes it only after the user chose the download. When `uip` supplies the migrator it changes nothing |
| `--force` | Archive only: re-download and re-extract even when cached. Implies `--install` |

Download: the script tries `curl` first, which honors `HTTPS_PROXY` / `HTTP_PROXY`, then PowerShell's WebClient, which uses the system proxy and the signed-in user's credentials. Both run as commands, never as script files. The update check's read of `latest.json` falls back the same way, so a machine that reaches the internet only through the system proxy still sees updates. A curl connection that stalls below 1 KB/s for a minute fails instead of hanging. Corporate TLS inspection that breaks both surfaces as `download-failed`, with each downloader's error in the message.

Extraction: `Expand-Archive`, then Windows `tar.exe`, then `unzip`. An install root whose extracted paths would pass the 260-character Windows limit makes `Expand-Archive` fail; `tar.exe` still extracts it.

## Managed environments

The skill never downloads without the user's choice. A `uip` installed with its optional Helm dependency, from the company's npm registry or the CLI's air-gapped archive, needs no setting and no download: see [Helm through uip](#helm-through-uip). For the archive, these settings, set machine- or user-wide by an administrator, decide the outcome before the install question would be asked, so it never appears.

| Situation | Set | Effect |
|---|---|---|
| Binary distributed by desktop engineering or placed on a tool share | `UIPATH_ACTIVITY_MIGRATOR_DIR=<FOLDER>` and `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1` | The preinstalled tool is used (`source: env`) and the network is never touched. A missing tool is `offline-missing`: the skill gives the manual steps instead of offering a download |
| Archive mirrored on an internal server | `UIPATH_ACTIVITY_MIGRATOR_URL=<MIRROR_URL>` | Download and update check go to the mirror; the update check needs `latest.json` next to the mirrored archive. The user's choice is still required; the install question names the mirror |
| No downloads, nothing preinstalled yet | `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1` | Without a `uip` that supplies the migrator, every run is `offline-missing` until the tool is placed by hand |

The tool is a zip: placing it needs no installer and no elevation. The `Extensions/` folder must stay next to the exe.

## Activity packages offline

Whatever the source of the migrator, `upgrade` restores the project's packages and the newer activity packages it migrates to, from the project's `nuget.config` when there is one, else from the machine's NuGet configuration. Offline, add a `nuget.config` next to `project.json` whose only source is a local folder (`<clear />`, then `<add key="offline" value="D:\nuget-offline" />`), holding `.nupkg` files or merged NuGet global packages folders with two sets:

- every package at the exact version `project.json` lists (the Legacy versions, e.g. `UiPath.System.Activities 20.10.4`). The migrator looks each one up before moving it to a Windows-compatible version; an online migration only reads their metadata and never downloads them, so take them from the package cache of a machine where the project builds in Studio, or from the feed;
- the versions the migration moves to: migrate the same projects once online with `NUGET_PACKAGES` set to an empty folder, which then holds them all.

A missing package is `RESTORE-MISSING-PACKAGE` in the SARIF, naming the package and version.

## Script output contract

The last stdout line is one JSON object.

```json
{"status":"ok","source":"uip","command":"uip rpa project migrate","version":"27.0.207-dev"}
{"status":"ok","source":"cached","command":"C:\\Users\\me\\AppData\\Local\\UiPath\\ActivityMigrator\\current\\UiPath.Upgrade.exe","exe":"C:\\Users\\me\\AppData\\Local\\UiPath\\ActivityMigrator\\current\\UiPath.Upgrade.exe","version":"26.10.0","uipMessage":"uip rpa project migrate version: helm-missing: …"}
{"status":"missing","dir":"C:\\Users\\me\\AppData\\Local\\UiPath\\ActivityMigrator","url":"https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip","uipMessage":"uip rpa project migrate version: helm-missing: …"}
```

| Field | Values |
|---|---|
| `status` | `ok`, `missing` (archive only), `error` |
| `source` | `uip` (Helm, through `uip`); for the archive `env` (override dir), `cached`, `downloaded` (first install), `updated` (newer archive replaced the cache) |
| `command` (`ok`) | What runs the migrator: `uip rpa project migrate` for `uip`, the exe path for the archive. The skill's `<MIGRATOR>` is built from it |
| `exe` (`ok`, archive only) | The exe path |
| `update` (`ok`, archive only) | `true` when a plain run found the server's version newer than the cached tool's: a newer build exists and the cached tool was kept. Absent otherwise |
| `dir`, `url` (`missing` only) | The folder an install run would fill and the archive it would fetch: the facts the skill puts in its install question |
| `uipMessage` (archive only) | Why `uip` could not supply the migrator, when it was asked: `helm-missing`, an unknown command, Helm's error, or `uip` not found |
| `code` (errors) | `not-windows` (from `uip` or the script); for the archive `download-failed`, `extract-failed`, `verify-failed`, `offline-missing`, `runtime-missing`, `telemetry-flag` |
| `env` (`telemetry-flag` only) | The assignment the tool starts with, `UIPATH_TELEMETRY_DISABLED=true` or `=false` |
| `message` | Human-readable detail, including the manual steps for the failing stage |

Exit codes: `0` ok, `1` error, `3` missing.

## Install question

SKILL.md Step 0 sends the agent here when the script reports `missing`: `uip` could not supply the migrator and no archive copy is installed. `<URL>` and `<DIR>` are the `url` and `dir` values of that object; `<UIP_REASON>` is its `uipMessage`, put in plain words (for example "`uip` is installed without its Helm component", "this `uip` is too old to have `project migrate`", "`uip` is not installed"). Use the host's structured question tool when it has one, otherwise ask in text. Offer exactly these two options, the first as the recommended one, and no other:

> The Activity Migrator is not available: <UIP_REASON>. Updating `uip` (`uip update`), or reinstalling it with its optional Helm dependency, makes `uip rpa project migrate` provide it with no separate download. Otherwise UiPath distributes the standalone `UiPath.Upgrade.exe` as a zip for Windows.
>
> 1. **Download it now** (recommended). I fetch `<URL>`, extract it into `<DIR>` and run the tool from there.
> 2. **You provide it.** Fix `uip` as above, or download `UiPath.Upgrade.Cli.zip` yourself from `<URL>`, from Automation Cloud → Help → Resources → Downloads → Activity Migrator Tool, or from the Customer Portal. Extract it so `UiPath.Upgrade.exe` and the `Extensions/` folder sit directly in one folder, then tell me that folder or set `UIPATH_ACTIVITY_MIGRATOR_DIR` to it.
>
> On a machine an administrator manages, these settings can be preset so this question never comes up.

Leave out the `<UIP_REASON>` clause and the `uip` sentence when the object carries no `uipMessage` (`UIPATH_ACTIVITY_MIGRATOR_DIR` or `_URL` is set, so `uip` was not asked).

Option 1: rerun the script with `--install`. Download, extraction and the version check can outlast the host's default timeout: give the command at least 10 minutes. Apply Step 0's table to its output.

Option 2: wait for the user. When they fixed `uip`, rerun the script without a flag and apply Step 0's table: `source: uip` is the expected result. When they named a folder, rerun the script without a flag, with the variable set to that folder in the syntax of the shell that runs it: bash `UIPATH_ACTIVITY_MIGRATOR_DIR="<FOLDER>" node ...`, PowerShell `$env:UIPATH_ACTIVITY_MIGRATOR_DIR = '<FOLDER>'; node ...`. Apply Step 0's table. `missing` again means the folder holds no `UiPath.Upgrade.exe`, neither at its root nor under `current/`: say so, name those two places, and wait for the user; do not download and do not ask the question a second time. A variable set in the command lasts for that command only: tell the user to set it in their user environment so later sessions find the tool; a folder placed at the default `%LOCALAPPDATA%\UiPath\ActivityMigrator\current` needs no variable. The preset settings for managed machines are in [Managed environments](#managed-environments); point an administrator there when asked.

## Manual placement

For air-gapped machines without a usable `uip`, or when both downloaders are blocked ([Helm through uip](#helm-through-uip) lists the shorter routes):

1. Download `UiPath.Upgrade.Cli.zip` on a machine with access (URL above, or the Automation Cloud download page).
2. Extract it so that `UiPath.Upgrade.exe` and the `Extensions/` folder sit directly inside one folder.
3. Either place that folder at `%LOCALAPPDATA%\UiPath\ActivityMigrator\current`, or set `UIPATH_ACTIVITY_MIGRATOR_DIR` to it.
4. Set `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1` so the script never tries the network.
5. Rerun the acquisition script. Expected: `status: ok`, `source: env` or `cached`.

Runtime missing (`runtime-missing`, archive only): the tool did not start because the .NET Desktop Runtime its build targets is not installed where .NET's launcher looks. The message names the version and the fix; apply it, then verify by rerunning the script:

```bash
node "<SKILL_DIR>/scripts/ensure-migrator.mjs"
```

## Telemetry flag crash

Archive only. The `25.10.x` builds read `UIPATH_TELEMETRY_DISABLED` with a strict boolean parse; the current builds no longer read it. Any value other than `true` or `false`, the documented `1` included, makes every command of a 25.10 build die at startup with `The type initializer for 'UiPath.Service.Api.Communication' threw an exception.` A re-download of the same build does not help. When `version` fails while the variable holds such a value, the script retries with the strict spelling of the same choice (`0`, `no`, `off` → `false`; anything else → `true`) and, when that starts, reports `telemetry-flag` with the assignment in `env`. Prefix it to the script and to every `<MIGRATOR>` command:

```bash
UIPATH_TELEMETRY_DISABLED=true node "<SKILL_DIR>/scripts/ensure-migrator.mjs"
UIPATH_TELEMETRY_DISABLED=true <MIGRATOR> analyze --help
```

Never unset the variable instead: that turns telemetry on for a user who disabled it. A build that accepts `1` and `0` starts on the first try, and the script then never reports this code. Older `uip` CLIs crash the same way in `uip rpa build`; [build-verification-guide.md](build-verification-guide.md) covers that.

## Updating

Through `uip`: update the CLI (`uip update`). It brings the matching Helm, and with it the migrator; the script sends no request of its own.

Archive fallback: every plain run reads `latest.json` and compares its `version` with the cached tool's. When the server's is newer it keeps the cached tool and reports `update: true`; nothing is replaced without an install run. To update, rerun with `--install`: `current/` is replaced only when the server's version is newer (`source: updated`). `--force` refreshes even an unchanged cache. An override dir is never updated unless its exe is missing, and neither is a build placed by hand at the top of the default root: only the build under `current/` is checked and updated; replace the others by hand. No update is reported under `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1`, when `latest.json` cannot be read, or when a mirror serves none next to its archive; a server that never answers delays a plain run by about 15 seconds.

A replacement runs in this order: download, extract, start the new build, swap it into `current/`, remove the previous build. A new build that does not start is not installed, and neither is one that cannot be swapped in because a program still runs from `current/`: the script reports the cause as an error and the cached tool stays, so a rerun without a flag continues with it. A removal Windows refuses never fails the run: the leftover stays until a later run removes it.

## Verifying by hand

```bash
<MIGRATOR> version
<MIGRATOR> analyze --help
```

With `source: uip`, `<MIGRATOR>` carries Rule 8's `UIPATH_STUDIO_PID` prefix. The help output lists the active extensions through their flags: `--uia-*` for UI Automation, `--mail-*` / `--config` for Mail, `--gsuite-*` only in preview builds. An extension whose flags are absent is not active in this build.
