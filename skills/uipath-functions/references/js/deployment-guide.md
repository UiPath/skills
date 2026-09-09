# Deployment Guide

Pack → publish → release update → live HTTP endpoint. Covers package anatomy, the production cold-start model (the top source of deployed-only failures), publish credentials, invoke URL discovery, Studio Web push, and solution registration.

## Pack

```bash
uip function pack            # -> .uipath/<PACKAGE>.<VERSION>.nupkg
uip function pack --nolock   # exclude package-lock.json from the package
```

`<PACKAGE>`/`<VERSION>` come from `package.json` `name`/`version`. The package ships **raw sources — no bundling, no compilation**:

- Entire project tree copied verbatim into `content/`, excluding `node_modules`, `.git`, `.env`, `.deno`, `dist`, `.uipath`, `*.nupkg` (extra excludes via `uipath.json` `packOptions.directoriesExcluded`/`filesExcluded`).
- `package-lock.json` included by default; `--nolock` or `packOptions.includeLockFile: false` drops it.
- `.npmrc` ships **sanitized**: `@uipath:*` scope lines and credential lines (`_authToken`, `_auth`, `_password`) are stripped; the file is omitted entirely if only comments remain. Custom scope routes (e.g. `@acme:registry=...`) survive.
- Generated manifests: `entry-points.json`, `bindings_v2.json`, `operate.json`, `package-descriptor.json` — see [bindings-guide.md](bindings-guide.md).

Re-packing the same version **overwrites** the existing `.nupkg`; older version files stay in `.uipath/`, and `publish` picks the most recently modified `.nupkg` by mtime. Bump `version` in `package.json` before packing a release, or you may publish a stale file.

## Cold Start — How Production Runs the Package

The production worker does at cold start what pack deliberately did not do: it extracts `content/`, runs `npm install --omit=dev` from the shipped `package-lock.json`, then loads the `.ts` sources directly. **The install runs with no credentials** — pack stripped tokens from `.npmrc`, and no GitHub or private-registry token is available at install time. Everything below follows from that:

1. **Every runtime dependency must be public npm and listed in `dependencies`.** `--omit=dev` skips `devDependencies` entirely. The SDK (`@uipath/coded-functions-js-sdk`) stays in `devDependencies` — the platform provides the runtime.
2. **A runtime dep the lockfile resolves to a private registry breaks the install** — the function crashes or hangs with no logs. Routing `@uipath` to GitHub Packages in the project `.npmrc` is safe for pack-time tooling (that line is stripped from the shipped copy), but every `dependencies` entry in `package-lock.json` must show a `resolved` URL on `registry.npmjs.org`. Gate before packing — after adding a dependency, or whenever `.npmrc` carries custom registry routes: `grep '"resolved"' package-lock.json | grep -v registry.npmjs.org` must print nothing.
3. **Regenerate the lockfile after any `package.json` change** — run `npm install`, then pack. A stale lockfile fails the production install: `errorCode 4801` on every route.
4. **Extensionless intra-project imports hang cold start silently** — local dev resolves them, production does not ([SKILL.md](../../SKILL.md) JS Rule 4).
5. **Genuinely private code cannot be installed — vendor it as source.** Copy it into the project (`functions/_helpers.ts`, or any non-excluded directory such as `lib/`) and import it with explicit `.ts` extensions.

Failure mode when any of these is violated (known sharp edge — install failures have no error surface yet): all functions in the package hang for up to 15 minutes with no logs — exception: a stale lockfile (item 3) surfaces as `errorCode 4801` instead. A healthy deploy may also 500 once on the first call while cold start runs — retry before diagnosing.

## Publish

```bash
uip function publish --feed-id <FEED_ID>   # omit --feed-id for the interactive feed picker
```

Uploads the newest `.nupkg` (by mtime) from `.uipath/` to an Orchestrator process feed. Credentials via flags or env vars:

| Flag | Env var | Value |
|---|---|---|
| `--url` | `UIPATH_URL` | platform base URL |
| `--org` | `UIPATH_ORGANIZATION_NAME` | organization **name** |
| `--tenant` | `UIPATH_TENANT_NAME` | tenant **name** |
| `--token` | `UIPATH_ACCESS_TOKEN` | access token |

> Names, not GUIDs — distinct from the handler-local `UIPATH_ORG_ID`/`UIPATH_TENANT_ID` fallbacks ([local-dev-guide.md](local-dev-guide.md)).

Publish failures: `401`/`403` → re-check the credential env vars above; feed errors → rerun without `--feed-id` for the interactive picker.

### Manual step: update the Function Release

Publishing uploads the version, but the Function Release stays pinned to the previous one until you update it in Orchestrator → **Automations → Processes** (REST: `/odata/Releases` — the UI says "Processes", the API says "Releases"). Only then does Orchestrator re-read the manifests and sync triggers — full lifecycle table (rename = trigger delete+create) → [bindings-guide.md](bindings-guide.md).

## Invoke

```text
https://api.<HOST>/<ORG_ID>/<TENANT_ID>/orchestrator_/t/<FOLDER_KEY>/<PACKAGE_ID>/<SLUG>
```

| Segment | Value |
|---|---|
| `api.<HOST>` | the `api.*` subdomain (e.g. `api.uipath.com`) — browsers must call `api.*` ([http-semantics-guide.md](http-semantics-guide.md#cors)) |
| `<ORG_ID>` / `<TENANT_ID>` | org/tenant **GUIDs** for browser callers (slugs also work from curl) |
| `<FOLDER_KEY>` | the **folder's Key GUID** — same for every function in the folder, not per-trigger |
| `<PACKAGE_ID>` | `package.json` `name` (sanitized) |
| `<SLUG>` | `defineFunction` `path` without the leading `/` — its own segment after `<PACKAGE_ID>` |

```bash
curl -s -X POST "https://api.<HOST>/<ORG_ID>/<TENANT_ID>/orchestrator_/t/<FOLDER_KEY>/<PACKAGE_ID>/<SLUG>" \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{}'
```

Always send `Content-Type: application/json` and a JSON body — `'{}'` when the function takes no input ([SKILL.md](../../SKILL.md) JS Rule 7). GET functions take input as query-string parameters instead.

### Discovering `<FOLDER_KEY>` and slugs

```bash
curl -s "https://api.<HOST>/<ORG_ID>/<TENANT_ID>/orchestrator_/odata/HttpTriggers" \
  -H "Authorization: Bearer <TOKEN>" -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>"
```

Each row carries `Method`, `Slug`, `Release.Name` (= `<PACKAGE_ID>`), and `ExternalReference` of the form `<METHOD> <PACKAGE_ID>/<SLUG> <FOLDER_KEY>` — the trailing GUID is the `<FOLDER_KEY>` for the URL.

| Wrong move | Result |
|---|---|
| Trigger's own `Id` as `<FOLDER_KEY>` | `404 errorCode 1623` ("HTTP trigger not found") |
| Wrong folder key or unmatched slug | `404 errorCode 1623` |
| `odata/ApiTriggers` with `$filter=ProcessKey ...&$select=Key,Name,Url` | `400 errorCode 1000` — the DTO lacks those fields; use `HttpTriggers` |

Deployed status codes and the 25 s timeout / 303 behavior → [http-semantics-guide.md](http-semantics-guide.md); calling from a Coded App frontend → [coded-app-wiring-guide.md](coded-app-wiring-guide.md).

## Studio Web push

```bash
uip function push --project-id <PROJECT_ID>
```

Diff-by-hash source sync into a Studio Web project (same credential env vars as publish). Updates `.uipath/studio_metadata.json` (project version auto-increments; open editors prompt Reload); never touches `project.uiproj`, `.project`, or `.settings`.

## Solution registration

JS/TS projects have no `uip function init` (Python-only) and need none — the `uipath.json` marker already identifies the project:

```bash
uip solution projects add <FUNCTION_PROJECT_PATH>
uip solution pack   # packs the function project in-process; no separate uip function pack needed
```
