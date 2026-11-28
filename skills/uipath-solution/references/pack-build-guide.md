# Pack Build Guide

What `uip solution pack` does inside the build, and the options that steer it: dependency feeds, package signing, the workflow analyzer and governance, coded-app builds, member package ids, and `solution cleanup`. The basic pack → publish → deploy flow is in [Pack and Deploy](pack-and-deploy.md).

## Read `Data.Projects` on a failed pack

A failed pack names the broken project and file in `Data.Projects`, not in `Message`. `Message` flattens every failed project into one sentence and names no file.

```bash
uip solution pack ./MySolution ./output --output json
```

Each `Data.Projects` entry is one member project:

| Field | Meaning |
|---|---|
| `Path` | Project directory relative to the solution (`.` at the root) |
| `Type` | Project type |
| `Result` | That project's result |
| `Message` | That project's own message |
| `Findings` | List of findings: `Source` (`Analyzer`, `Validator`, `Compiler`, `Other`), `ErrorCode`, `Description`, `FilePath`, `ActivityIdRef` (when the compiler reported one) |

A failure that belongs to no project (not logged in, no packager for a project `Type`) has no `Data.Projects`.

## Dependency feeds

Packing an RPA project restores its NuGet dependencies first. `pack`, `restore` and `cleanup` take the same three feed options:

```bash
uip solution pack ./MySolution ./output --feed-folder "Shared/Production" --output json
uip solution pack ./MySolution ./output --nuget-sources-config-path ./NuGet.config --output json
uip solution pack ./MySolution ./output --exclude-configured-sources --nuget-sources-config-path ./NuGet.config --output json
```

By default dependencies resolve against every tenant library feed the session can see, plus the built-in feeds: nuget.org, UiPath-Official, Connect (`gallery.uipath.com`) and the UiPath internal feed.

| Option | Effect |
|---|---|
| `--feed-folder <name>` | Add one Orchestrator folder's package feed to the tenant library feeds; it excludes no other feed. Folder name or full path. Fails closed: with no logged-in session it is an error, never a silent fall back to other feeds |
| `--nuget-sources-config-path <path>` | Add the sources in that `NuGet.config` to the ones above. It adds; it does not replace |
| `--exclude-configured-sources` | Drop the built-in feeds. Resolution uses only the tenant library feeds, the `--feed-folder` feed and `--nuget-sources-config-path` |

> **Bare `--exclude-configured-sources` restores only where the tenant includes the host libraries feed.** Official activity packages (`UiPath.System.Activities`, `UiPath.UIAutomation.Activities`, …) must then come from the feeds that are left. The tenant's library feeds are still used, the same ones Studio restores from: where the tenant includes the host libraries feed (UiPath-Official on Automation Cloud) they resolve from it. Where it does not, the restore fails; pair the flag with a `NuGet.config` that points at your own mirror.

## Package signing

Signing is opt-in. `--signing-certificate-path` signs each packed project `.nupkg` with that `.pfx` certificate. Needs the `dotnet` CLI on `PATH`.

```bash
uip solution pack ./MySolution ./output --version "<VERSION>" \
  --signing-certificate-path ./cert.pfx \
  --signing-certificate-password env.SIGNING_PASSWORD \
  --signing-timestamp-server "<TIMESTAMP_SERVER_URL>" --output json
```

`--signing-certificate-password` and `--signing-timestamp-server` are optional. Pass the password as `env.<VAR_NAME>` so it is read from an environment variable and stays out of shell history and CI logs.

## Workflow analyzer and governance

`pack` runs the workflow analyzer over every RPA project.

| Option | Effect |
|---|---|
| `--skip-analyze` | Skip the analyzer rules only. Restore, compile and validation still run, so a broken project still fails the pack |
| `--ignored-rules <rules>` | Run the analyzer but drop the findings of these rule IDs for every RPA project: not reported, cannot fail the pack. Comma-separated (`ST-USG-034,ST-MRD-002`); repeat the flag to add more; matched case-insensitively |
| `--governance-file-path <path>` | Analyze against this local AutomationOps policy file |
| `--governance-product <product>` | Analyze against the policy the signed-in tenant publishes in AutomationOps for that product (`StudioWeb`, `Development`, `Business`, …) |

With no governance flag the analyzer uses the rules shipped with the compiler. `--automation-ops-profile` is the old, hidden name of `--governance-product`; use the new one, and never pass both (refused).

### Which policy wins

Signed in as a user, the tenant is asked first, even when `--governance-file-path` is passed. When `--governance-file-path` or `--ignored-rules` is passed without `--governance-product`, the tenant is asked about `StudioWeb`. Those are the only cases with a product default.

| Tenant answer | Analyzer uses | `--ignored-rules` |
|---|---|---|
| Publishes a policy | The tenant policy. `--governance-file-path` is not used (warning) | Not applied (warning naming the rules); the pack does not fail because of it |
| Publishes nothing | `--governance-file-path`, otherwise shipped rules | Applied on top, even to rules the file raises to `Error` |
| Could not be asked (expired token, unreachable, timeout), or signed in as an external app | `--governance-file-path`, otherwise shipped rules | Applied on top |
| No signed-in tenant | `--governance-file-path`, otherwise shipped rules | Applied on top |

An external-app (client-credentials) login is never asked: AutomationOps does not accept external-app tokens yet. The warning names the reason `applicationLogin`.

### Governance does not gate a build

When AutomationOps cannot be asked, `pack` still returns `Result: Success` and exit `0` with the shipped rules (or your `--governance-file-path`). A CI stage using `--governance-product` as a gate goes green having enforced only the defaults. The only sign is a `warn`-level line on stderr naming the reason (`unauthorized`, `notFound`, `serverError`, `timedOut`, `applicationLogin`, …).

- `--log-level error` hides that warning. Keep the default `warn` level.
- A stage that must enforce governance reads stderr, or passes `--log-file <path>` and reads the file.
- Never combine `--log-file` with `--log-level error`: the level filter runs before the file, so the warning is dropped.

### The policy file

Pass the AutomationOps export **exactly as exported**, envelope included. The inner `data` object alone is refused, with a message to pass the export. A file that cannot be read or is not JSON fails the pack; it never falls back to the shipped rules.

## Coded apps: `pack` builds them

`uip solution pack` builds every coded app it packs, so a CI pipeline needs only Node.js on the runner, no separate build step. In the folder holding the app's `package.json` (nearest one above the bundle folder), pack installs dependencies when `node_modules/` is missing, then runs the `build` script, with the package manager the lockfile names:

| Lockfile | Install command |
|---|---|
| `package-lock.json` | `npm ci` |
| `pnpm-lock.yaml` | `pnpm install --frozen-lockfile` |
| `yarn.lock` | `yarn install --frozen-lockfile` |
| `bun.lock` | `bun install --frozen-lockfile` |
| none | `npm install` (writes a `package-lock.json`) |

Pack skips the build when the bundle folder exists and the app's files match the last build. It keeps a SHA-256 of the app's files (except `node_modules/`) in `.uipath-build.json` beside `package.json`. **Git-ignore `.uipath-build.json`.** An app with no `build` script, or no `package.json`, is packed from its existing folder as is. Coded-app init's default React starter has a `build` script and no bundle folder, so pack installs and builds it. Init's static pages (`--template form`, `dashboard`, `inline-automation`: a `dist/index.html` and a `package.json` with no scripts) are such apps, packed as that page. Where a React app was meant, scaffold it into `source/` first (uipath-coded-apps).

The packed folder is `config.bundlePath` in `webAppManifest.json`, relative to the project: `source/dist` for an app registered with `uip codedapp init` in a solution, `dist` for a standalone one. The build must write there.

- **`--skip-build`**: no install, no build, for every coded app. Ships whatever `config.bundlePath` holds — stale output ships as is, a missing folder fails the pack. Use it when an earlier step built the app or the pack step cannot reach the package registry.
- **`--dry-run` and a `.uis` input install from scratch.** The dry run's temporary copy has no `node_modules/`, nor does a `.uis`, so an app that needs a build needs the same registry access a real pack does. An app whose build is current is not rebuilt.
- **The build runs without the CLI's UiPath token.** `UIPATH_CLI_AUTH_TOKEN` and `UIPATH_ACCESS_TOKEN` are removed from its environment. `PATH`, proxy and registry settings (a private registry token included) pass through. A build that needs a UiPath credential gets it under its own variable name.
- **No HTML entry point fails the pack.** `config.bundlePath` must hold `index.html`, `main.html` or `app.html` (or the HTML file `config.mainFile` names). Build the app or repoint `config.bundlePath`; do not retry.

| Failure | `ErrorCode` / `Retry` | Do |
|---|---|---|
| Build fails, or the package manager is not on `PATH` | `invalid_argument` / `RetryWillNotFix` | `Message` names the folder, command, exit code and the end of the build output. Fix the build; retrying will not help |
| Install fails | `execution_failed` / `RetryLater` | Often the registry or network. Pack again once it is reachable, or build in an earlier step and pass `--skip-build`. Otherwise run the named install command in that folder and fix what it reports |
| No `build` script and no bundle folder | `invalid_argument` | Add a `build` script or repoint `config.bundlePath` |

## Member package ids

Each member project is published as `<solution>.<project-type>.<member-folder>`: the `.uipx` name, the short type (`Rpa`, `Case`, `Flow`, …) and the member's folder inside the solution. The name a project declares for itself is not used. A `packageName` saved on the project's process resource (Studio Web writes one) takes precedence, and renaming does not change it; `uip solution resources edit <PROCESS_RESOURCE_KEY> --patch '{"packageName":"<PACKAGE_ID>"}'` does.

- `pack --name` renames the **solution archive only**. Member ids stay anchored on the `.uipx` name, so an upgrade lands on the same feed entries. Renaming the solution directory does not move them either.
- **Ids must be unique.** Two members whose folders compose the same id fail the pack, naming the id and every folder. Spaces and dots collapse to one dot and ids are case-insensitive, so `collide me`, `collide.me` and `Collide.Me` are one id.
- **Ids are at most 100 characters.** A longer id fails the pack, naming the member folder.

Both are checked before anything is packed and fail with `ErrorCode: invalid_argument` / `Retry: RetryWillNotFix`. Fix by renaming the member folder or the `.uipx`. A whole-solution pack takes no `--package-id`; only a single-project pack (`--project <id-or-path> --package-id <id>`) overrides the id.

`--author` and `--description` set every member's author and description. Without them, a member keeps the values its project file declares, else `UiPath` / `Created by UiPath`.

## Solution cleanup

`uip solution cleanup` removes unused items from every project. On a solution directory it **edits project sources in place**.

```bash
uip solution cleanup ./MySolution --dry-run --output json   # detect only, change nothing
uip solution cleanup ./MySolution --output json             # apply
uip solution cleanup ./MySolution --skip-imports --output json  # apply, leave now-unused references in project files
```

1. **No confirmation prompt and no `--yes`.** The bare command changes the working tree. Commit the tree first, then run `--dry-run` and read the result.
2. **The feeds decide what is deleted.** "Unused" comes from resolving dependencies, so cleanup takes the same `--feed-folder`, `--nuget-sources-config-path` and `--exclude-configured-sources` as `pack` ([Dependency feeds](#dependency-feeds)). Run it against the feeds you pack against.

## Related

- [pack-and-deploy.md](pack-and-deploy.md) — pack, publish, deploy
- [develop-solution.md](develop-solution.md) — resources and bindings that pack reads
