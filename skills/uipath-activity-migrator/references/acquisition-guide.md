# Acquisition Guide

How the skill obtains, caches, verifies, and updates `UiPath.Upgrade.exe`. The script `scripts/ensure-migrator.mjs` implements this, run with `node`; read here when it fails or the user asks where the tool lives.

## What ships

| Item | Value |
|---|---|
| Public download | `https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip` |
| Also available from | Automation Cloud → Help → Resources → Downloads → Activity Migrator Tool; Customer Portal (`https://customerportal.uipath.com/`) |
| Archive | Zip with `UiPath.Upgrade.exe` at the archive root and extensions under `Extensions/<Name>/` |
| Runtime | Windows, .NET 8: `Microsoft.NETCore.App 8.x` and `Microsoft.WindowsDesktop.App 8.x` (the .NET Desktop Runtime 8 installer provides both) |
| Version | `UiPath.Upgrade.exe version` prints it (GA line `25.10.x`) |
| Freshness signal | The URL is unversioned. The server's `Last-Modified` header is the only change signal; the script stores it and re-downloads when it changes |

Studio does not need to be installed. Opening the migrated project afterwards needs Studio 2024.10 or later.

## Cache layout

Default root: `%LOCALAPPDATA%\UiPath\ActivityMigrator` (`$LOCALAPPDATA/UiPath/ActivityMigrator` in Git Bash).

```text
ActivityMigrator/
  current/                 extracted tool; UiPath.Upgrade.exe lives here
  .last-modified           Last-Modified header of the archive that produced current/
  UiPath.Upgrade.Cli.download.zip   transient during download; removed on success, kept on an extraction failure so it can be extracted by hand
  .chunks/                 transient during a download: the 16 MiB parts fetched so far and .etag naming the archive they belong to; kept across runs so a rerun resumes, removed on success or when the archive changed
  .lock, .lock.pid         held as an exclusive file handle by the run that owns the download, the archive, the extraction folder and current/; the OS releases it when that run ends, however it ends. .lock.pid names the holder for the busy message
```

Resolution order used by the script:

1. `UIPATH_ACTIVITY_MIGRATOR_DIR` when set: use `<dir>/UiPath.Upgrade.exe` if present, else `<dir>/current/UiPath.Upgrade.exe`. Nothing is downloaded into an override dir unless the exe is missing there.
2. Default root, `current/UiPath.Upgrade.exe`.
3. Download and extract into the default root (or the override dir).

## Environment variables and flags

| Variable / flag | Effect |
|---|---|
| `UIPATH_ACTIVITY_MIGRATOR_DIR` | Install or cache root. Use for shared tool drives or manual placement |
| `UIPATH_ACTIVITY_MIGRATOR_URL` | Alternate archive URL, for internal mirrors |
| `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1` | Never touch the network. A cached tool is used as is; a missing tool is an error, and `--force` is refused |
| `UIPATH_ACTIVITY_MIGRATOR_WINDOW_SECONDS` | Download budget of one run (default `480`). When it runs out the script stops, reports the bytes kept, and a rerun resumes from them. Lower it on a host whose command budget is under 10 minutes |
| `--check-only` | Report what is cached without downloading. Exit 3 with `status: missing` when nothing is cached |
| `--force` | Re-download and re-extract even when cached |

Download, in order:

1. One `HEAD` request, `curl` first, then PowerShell's `WebRequest` behind a system proxy. It doubles as the update check, so a machine that reaches the internet only through the system proxy still sees updates, and it reads `Content-Length`, `Accept-Ranges`, `ETag` and `Content-MD5` for step 2.
2. When the server accepts byte ranges and `curl` reached it: `curl` fetches sequential 16 MiB ranges into `.chunks/`, each request capped at 30 s. The bytes a request delivered are kept and the next one continues from that offset, so nothing is fetched twice and a rerun resumes. Requests use the plain URL until one runs out of time before finishing its range; from then on, reruns of that download included, each request carries its own query string, which gets its own origin fetch from a CDN edge that serves every request for the plain URL at the pace of a stuck cache fill. A URL that already has a query string is never altered. A response from the wrong offset is discarded, a changed `ETag` discards the parts, and the assembled file must match `Content-Length` and `Content-MD5`.
3. Otherwise, or when the server answers a range request with the whole archive: one `curl` stream, which honors `HTTPS_PROXY` / `HTTP_PROXY` and fails instead of hanging when it stalls below 1 KB/s for a minute, then PowerShell's WebClient, which uses the system proxy and the signed-in user's credentials. `curl` is skipped when its `HEAD` already failed where PowerShell's succeeded.

Every downloader ends at the run's download budget (`UIPATH_ACTIVITY_MIGRATOR_WINDOW_SECONDS`, the wait for the lock included). A chunked download that stopped reports the bytes kept in `completedBytes`, unless the run moved too little to finish in a few more: then the message says so and gives the manual steps. One run at a time works on the install root: `.lock` is an exclusive file handle that the OS releases when its run ends, however it ends. A second run waits up to a minute for the holder and then uses what it installed (`source: cached`), and otherwise reports the holder's pid in `holder`. Everything runs as commands, never as script files. A leftover download file that a process from an earlier run still holds open, a downloader or extractor that outlived a killed run, surfaces as `download-failed` with `holder: true`, like a live run: it ends on its own. Corporate TLS inspection that breaks every downloader surfaces as `download-failed` with each downloader's error in the message.

Extraction: `Expand-Archive`, then Windows `tar.exe`, then `unzip`. An install root whose extracted paths would pass the 260-character Windows limit makes `Expand-Archive` fail; `tar.exe` still extracts it.

## Script output contract

The last stdout line is one JSON object.

```json
{"status":"ok","exe":"C:\\Users\\me\\AppData\\Local\\UiPath\\ActivityMigrator\\current\\UiPath.Upgrade.exe","version":"25.10.0","source":"cached","runtime":"8.0.11"}
```

| Field | Values |
|---|---|
| `status` | `ok`, `missing` (check-only), `error` |
| `source` | `env` (override dir), `cached`, `downloaded` (first install), `updated` (newer archive replaced the cache) |
| `code` (errors) | `not-windows`, `runtime-missing`, `download-failed`, `extract-failed`, `verify-failed`, `offline-missing`, `telemetry-flag` |
| `env` (`telemetry-flag` only) | The assignment the tool starts with, `UIPATH_TELEMETRY_DISABLED=true` or `=false` |
| `message` | Human-readable detail, including the manual steps for the failing stage or, when a rerun resumes a download, how much of it is kept |
| `completedBytes`, `totalBytes` | On `download-failed` when a rerun is worth it: bytes already under `.chunks/` and the archive size. The rerun resumes from them |
| `holder` | On `download-failed` when another run of the script owns the install root: its pid, or `true` before that run has written `.lock.pid` or when a process of an earlier run still holds the archive. It is working and ends on its own; rerun after a minute |

Exit codes: `0` ok, `1` error, `3` missing (check-only).

## Manual placement

For air-gapped machines or when both downloaders are blocked:

1. Download `UiPath.Upgrade.Cli.zip` on a machine with access (URL above, or the Automation Cloud download page).
2. Extract it so that `UiPath.Upgrade.exe` and the `Extensions/` folder sit directly inside one folder.
3. Either place that folder at `%LOCALAPPDATA%\UiPath\ActivityMigrator\current`, or set `UIPATH_ACTIVITY_MIGRATOR_DIR` to it.
4. Set `UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1` so the script never tries the network.
5. Rerun the acquisition script. Expected: `status: ok`, `source: env` or `cached`.

Runtime missing: install the .NET Desktop Runtime 8 (x64) from `https://dotnet.microsoft.com/download/dotnet/8.0`, then rerun. The script checks the one place the migrator loads its runtime from: `DOTNET_ROOT_X64` or `DOTNET_ROOT` while one is set; otherwise the install location the .NET installer registers, else `%ProgramFiles%\dotnet`. It never uses the `dotnet` on `PATH`, which the migrator ignores. Verify by rerunning the script, which checks those same places:

```bash
node "<SKILL_DIR>/scripts/ensure-migrator.mjs" --check-only
```

## Telemetry flag crash

The `25.10.x` builds read `UIPATH_TELEMETRY_DISABLED` with a strict boolean parse. Any value other than `true` or `false`, the documented `1` included, makes every command die at startup with `The type initializer for 'UiPath.Service.Api.Communication' threw an exception.` A re-download does not help. When `version` fails while the variable holds such a value, the script retries with the strict spelling of the same choice (`0`, `no`, `off` → `false`; anything else → `true`) and, when that starts, reports `telemetry-flag` with the assignment in `env`. Prefix it to the script and to every `UiPath.Upgrade.exe` command:

```bash
UIPATH_TELEMETRY_DISABLED=true node "<SKILL_DIR>/scripts/ensure-migrator.mjs"
UIPATH_TELEMETRY_DISABLED=true "<MIGRATOR_EXE>" analyze --help
```

Never unset the variable instead: that turns telemetry on for a user who disabled it. A build that accepts `1` and `0` starts on the first try, and the script then never reports this code. Older `uip` CLIs crash the same way in `uip rpa build`; [build-verification-guide.md](build-verification-guide.md) covers that.

## Updating

Rerun the script without flags. It sends a `HEAD` request, compares `Last-Modified` with `.last-modified`, and replaces `current/` only when the archive changed (`source: updated`). Force a refresh with `--force`. An override dir is never auto-updated unless its exe is missing. A download that stopped partway, an update included, resumes on the next run from the parts already under `.chunks/`.

## Verifying an install by hand

```bash
"<MIGRATOR_EXE>" version
"<MIGRATOR_EXE>" analyze --help
```

The help output lists the active extensions through their flags: `--uia-*` for UI Automation, `--mail-*` / `--config` for Mail, `--gsuite-*` only in preview builds. An extension whose flags are absent is not active in this build.
