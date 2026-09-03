# Acquisition Guide

How the skill obtains, caches, verifies, and updates `UiPath.Upgrade.exe`. The scripts `scripts/ensure-migrator.sh` and `scripts/ensure-migrator.ps1` implement this; read here when a script fails or the user asks where the tool lives.

## What ships

| Item | Value |
|---|---|
| Public download | `https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip` |
| Also available from | Automation Cloud → Help → Resources → Downloads → Activity Migrator Tool; Customer Portal (`https://customerportal.uipath.com/`) |
| Archive | ~178 MB zip, ~520 MB extracted, `UiPath.Upgrade.exe` at the archive root, extensions under `Extensions/<Name>/` |
| Runtime | Windows, .NET 8: `Microsoft.NETCore.App 8.x` and `Microsoft.WindowsDesktop.App 8.x` (the .NET Desktop Runtime 8 installer provides both) |
| Version | `UiPath.Upgrade.exe version` prints it (GA line `25.10.x`) |
| Freshness signal | The URL is unversioned. The server's `Last-Modified` header is the only change signal; the scripts store it and re-download when it changes |

Studio does not need to be installed. Opening the migrated project afterwards needs Studio 2024.10 or later.

## Cache layout

Default root: `%LOCALAPPDATA%\UiPath\ActivityMigrator` (`$LOCALAPPDATA/UiPath/ActivityMigrator` in Git Bash).

```text
ActivityMigrator/
  current/                 extracted tool; UiPath.Upgrade.exe lives here
  .last-modified           Last-Modified header of the archive that produced current/
  UiPath.Upgrade.Cli.zip.tmp   transient during download; removed on success
```

Resolution order used by the scripts:

1. `UIPATH_ACTIVITY_MIGRATOR_DIR` when set: use `<dir>/UiPath.Upgrade.exe` if present, else `<dir>/current/UiPath.Upgrade.exe`. Nothing is downloaded into an override dir unless the exe is missing there.
2. Default root, `current/UiPath.Upgrade.exe`.
3. Download and extract into the default root (or the override dir).

## Environment variables and flags

| Variable / flag | Effect |
|---|---|
| `UIPATH_ACTIVITY_MIGRATOR_DIR` | Install or cache root. Use for shared tool drives or manual placement |
| `UIPATH_ACTIVITY_MIGRATOR_URL` | Alternate archive URL, for internal mirrors |
| `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1` | Never touch the network. A cached tool is used as is; a missing tool is an error |
| `--check-only` (bash) / `-CheckOnly` (PowerShell) | Report what is cached without downloading. Exit 3 with `status: missing` when nothing is cached |
| `--force` (bash) / `-Force` (PowerShell) | Re-download and re-extract even when cached |

Proxies: `curl` honors `HTTPS_PROXY` / `HTTP_PROXY`; PowerShell uses the system proxy. Corporate TLS inspection that breaks either download surfaces as `download-failed`.

## Script output contract

The last stdout line is one JSON object. Both twins emit the same shape.

```json
{"status":"ok","exe":"C:\\Users\\me\\AppData\\Local\\UiPath\\ActivityMigrator\\current\\UiPath.Upgrade.exe","version":"25.10.0","source":"cached","runtime":"8.0.11"}
```

| Field | Values |
|---|---|
| `status` | `ok`, `missing` (check-only), `error` |
| `source` | `env` (override dir), `cached`, `downloaded` (first install), `updated` (newer archive replaced the cache) |
| `code` (errors) | `not-windows`, `runtime-missing`, `download-failed`, `extract-failed`, `verify-failed`, `offline-missing` |
| `message` | Human-readable detail, including the manual steps for the failing stage |

Exit codes: `0` ok, `1` error, `3` missing (check-only).

## Manual placement

For air-gapped machines or when both downloaders are blocked:

1. Download `UiPath.Upgrade.Cli.zip` on a machine with access (URL above, or the Automation Cloud download page).
2. Extract it so that `UiPath.Upgrade.exe` and the `Extensions/` folder sit directly inside one folder.
3. Either place that folder at `%LOCALAPPDATA%\UiPath\ActivityMigrator\current`, or set `UIPATH_ACTIVITY_MIGRATOR_DIR` to it.
4. Set `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1` so the scripts never try the network.
5. Rerun the acquisition script. Expected: `status: ok`, `source: env` or `cached`.

Runtime missing: install the .NET Desktop Runtime 8 (x64) from `https://dotnet.microsoft.com/download/dotnet/8.0`, then rerun. Verify with:

```bash
dotnet --list-runtimes | grep "Microsoft.WindowsDesktop.App 8."
```

## Updating

Rerun the script without flags. It sends a `HEAD` request, compares `Last-Modified` with `.last-modified`, and replaces `current/` only when the archive changed (`source: updated`). Force a refresh with `--force`. An override dir is never auto-updated unless its exe is missing.

## Verifying an install by hand

```bash
"<MIGRATOR_EXE>" version
"<MIGRATOR_EXE>" analyze --help
```

The help output lists the active extensions through their flags: `--uia-*` for UI Automation, `--mail-*` / `--config` for Mail, `--gsuite-*` only in preview builds. An extension whose flags are absent is not active in this build.
