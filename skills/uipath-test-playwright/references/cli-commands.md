# CLI commands reference

Exact `uip` invocations used by `uipath-test-playwright`, with the JSON shape returned by `--output json` and the field(s) the skill must parse.

> **Always pass `--output json`.** All shapes below assume that flag.
>
> **Noun/verb naming:** Test Manager resources are **plural** (`testcases`, `testsets`, `executions`, `project`). Test-set membership verbs live under `testcases` (`testcases add` / `testcases remove`), not under `testsets`. Execution is `testsets run`, not `execute`.

## Auth

### `uip login status`

```bash
uip login status --output json
```

Returns:
```json
{ "Result": "Success", "Code": "LogIn", "Data": { "Status": "Logged in" | "Logged out", "Organization": "...", "Tenant": "..." } }
```

**Parse:** `.Data.Status` — must equal `"Logged in"`. If not, fail pre-flight.

## External-test packager

### `uip tm pack`

Packages an external (non-Studio) test project — Playwright today — into a UiPath **V2 test package** (`.nupkg`). All per-test richness rides in one CLI-owned file, `content/testCases.json`, which Orchestrator forwards opaquely to Test Manager on the `package.uploaded` event.

```bash
uip tm pack \
  --project-path "$PROJECT_PATH" \
  --type playwright \
  --tmh-project "$TM_PROJECT_KEY" \
  --name "$PACKAGE_NAME" \
  --package-version "$VERSION" \
  --output "$OUTPUT_DIR" \
  --output json
```

| Flag | Required | Notes |
|---|---|---|
| `--project-path <path>` | yes | Test project root. |
| `--type <type>` | yes | Framework; validated against the registry (today: `playwright`). |
| `--tmh-project <projectKey>` | yes* | TM project the auto-created Test Cases land in. **Required when create-test-cases is on (the default)** — the CLI refuses to pack otherwise. |
| `-n, --name <name>` | no | Default: project folder name. |
| `--package-version <v>` | no | Default `1.0.0`. Named `--package-version` to avoid colliding with the CLI's `-V/--version`. |
| `-o, --output <dir>` | no | Default `.uipath`. |
| `--author <author>` | no | Default `UiPath`. |
| `--description <desc>` | no | Default `<name> — <SubType> test package`. |
| `--no-create-test-cases` | no | Opt OUT of TM auto-creating Test Cases; per-test label metadata is still embedded. Drops the `--tmh-project` requirement. |
| `--dry-run` | no | Preview discovered tests, emit nothing. |

Returns:
```json
{ "success": true, "message": "...", "packageName": "e2e-playwright", "outputPath": ".uipath/e2e-playwright.1.0.0.nupkg", "testCount": 12 }
```

**Parse:** `.success == true`. The emitted nupkg is at `$OUTPUT_DIR/$PACKAGE_NAME.$VERSION.nupkg` (deterministic).

**Discovery** shells out to the customer's own resolver (`playwright test --list --reporter=json`) — no AST/glob fallback. `--list` emits one row per test×project, deduped into one test with a `projects[]` array (project is an execution parameter, not identity).

### Inspecting the package (single source of truth)

```bash
unzip -p "$NUPKG_PATH" content/testCases.json | jq '.testCases'
```

`content/testCases.json` (schemaVersion `2.0`):
```json
{
  "schemaVersion": "2.0",
  "testCases": [
    {
      "uniqueId": "c411e822-3417-5c5a-92b4-66ad0700beb2",
      "filePath": "content/tests/google-search-bar.spec.ts",
      "line": 4,
      "displayName": "Google Search Bar > should have a visible search bar",
      "describePath": ["Google Search Bar"],
      "projects": ["chromium", "firefox", "webkit"],
      "tags": [],
      "annotations": []
    }
  ],
  "packageName": "e2e-playwright",
  "packageVersion": "1.0.0",
  "subType": "Playwright",
  "subTypeOptions": { "package": "@playwright/test", "version": "1.x" },
  "testManagerOptions": { "createTestCases": true, "projectKey": "DEMO" },
  "allProjects": ["chromium", "firefox", "webkit"]
}
```

**Parse:** `.testCases[]`. `uniqueId` is a deterministic UUID v5 of `(packageName, filePath, titleChain)` — stable across re-packs, so a re-upload updates the same TM Test Cases. `content/entry-points.json` carries only `{ filePath, uniqueId, type }` (no richness) — do NOT use it as the test list.

## Orchestrator

### `uip or folders list`

```bash
uip or folders list --all --output json          # or: -n <folder-name> --all
```

Returns:
```json
{ "Result": "Success", "Data": [ { "Key": "f0...", "Name": "Shared", "Path": "Shared" } ] }
```

**Parse:** `.Data[].Key` (folder UUID). Save the chosen one to `state.folderKey` and set it as the TM project default (`tm project set-default-folder`).

### `uip or packages upload`

```bash
uip or packages upload "$NUPKG_PATH" --output json
```

Returns:
```json
{ "Result": "Success", "Code": "PackageUploaded", "Data": { "Status": "Package uploaded successfully" } }
```

**Parse:** `.Result == "Success"`. On success Orchestrator emits `package.uploaded`; Test Manager ingests `content/testCases.json` and auto-creates the Test Cases. Requires the Orchestrator flag `AllowTestAutomationPackagesWithV1Metadata` — a V2 test package is rejected at upload if it is OFF.

## Test Manager — Project

### `uip tm project list` / `create` / `set-default-folder`

```bash
uip tm project list --filter "$TM_PROJECT_KEY" --output json
uip tm project create --name "$NAME" --project-key "$KEY" --output json
uip tm project set-default-folder --project-key "$KEY" --folder-key "$FOLDER_KEY" --output json
```

`list` returns `.Data[]` with `ProjectKey`, `Name`. Match `ProjectKey == TM_PROJECT_KEY`; if empty, `create`. `set-default-folder` is mandatory before any `run` (else `tm testsets run` fails).

## Test Manager — Test cases

### `uip tm testcases list`

```bash
uip tm testcases list --project-key "$TM_PROJECT_KEY" --filter "$PACKAGE_NAME" --output json
```

Returns:
```json
{ "Result": "Success", "Data": [ { "ObjKey": "DEMO:23", "Id": "b1...uuid", "Name": "Google Search Bar > should have a visible search bar" } ] }
```

**Parse:** `.Data[].ObjKey` (format `PROJECT_KEY:NUMBER`) is the `--test-case-key` value. `.Data[].Id` (UUID) is the `--test-case-id` value used by `run`. `--filter` is a substring search; tighten with an exact `.Name` match in jq if needed.

Use this to **confirm the Test Cases TM auto-created after upload** — retry with backoff until the count matches `content/testCases.json`.

### `uip tm testcases list-automations` *(diagnostic only)*

```bash
uip tm testcases list-automations --project-key "$TM_PROJECT_KEY" --folder-key "$FOLDER_KEY" --output json
```

Lists automation entry points TM sees in an Orchestrator folder (optional `--package-name`). The skill does **not** need this for the normal flow — Test Cases are auto-created on upload. Useful only to debug ingestion (did TM see the package's entry points?).

### `uip tm testcases add` / `remove` (test-set membership)

```bash
uip tm testcases add    --test-set-key "$TEST_SET_KEY" --test-case-keys "DEMO:23,DEMO:24" --output json
uip tm testcases remove --test-set-key "$TEST_SET_KEY" --test-case-keys "DEMO:23"         --output json
```

`--test-case-keys` is **plural**, comma-separated (`PROJECT_KEY:NUMBER`). These verbs live under `testcases`, not `testsets`.

## Test Manager — Test sets

### `uip tm testsets create`

```bash
uip tm testsets create --project-key "$TM_PROJECT_KEY" --name "$TEST_SET_NAME" --description "..." --output json
```

Returns `.Data.ObjKey` (format `PROJECT_KEY:NUMBER`) — pass to `testcases add` and `testsets run`.

### `uip tm testsets run`

```bash
uip tm testsets run --test-set-key "$TEST_SET_KEY" --execution-type automated --output json
```

Optional `--execution-type <automated|manual|mixed|none>` (default `automated`), `--input-path <FILE>` for parameter overrides. **Requires a default Orchestrator folder on the project** (`tm project set-default-folder`).

Returns:
```json
{ "Result": "Success", "Data": { "ExecutionId": "550e8400-e29b-41d4-a716-446655440000", "Status": "Running" } }
```

**Parse:** `.Data.ExecutionId` — save to state; used by `tm wait`, `tm executions testcaselogs list`, `tm result download`, `tm attachment download`.

### `uip tm testsets list` (cleanup)

```bash
uip tm testsets list --project-key "$TM_PROJECT_KEY" --filter "_pw_run_" --output json
uip tm testsets delete --test-set-key "$TEST_SET_KEY" --output json
```

## Test Manager — Wait + results

### `uip tm wait`

```bash
uip tm wait --execution-id "$EXECUTION_ID" --project-key "$TM_PROJECT_KEY" --test-set-key "$TEST_SET_KEY" --timeout 1800 --output json
```

Polls until terminal. On timeout returns `Result: "Failure"` with a TimedOut message. **Do not auto-fail** — see SKILL.md Phase 6.

### `uip tm executions testcaselogs list`

```bash
uip tm executions testcaselogs list --execution-id "$EXECUTION_ID" --project-key "$TM_PROJECT_KEY" --output json
```

Nested subcommand path (NOT `tm execution list-testcaselogs`). Returns per-test-case rows; display `TestCase`, `Status` (`Passed`/`Failed`), `Duration`. Optional `--only-failed`, `--filter`, `--limit`, `--offset`.

### `uip tm result download`

```bash
uip tm result download --execution-id "$EXECUTION_ID" --test-set-key "$TEST_SET_KEY" --result-path "$ARTEFACTS_DIR" --output json
```

Writes JUnit XML to `$ARTEFACTS_DIR`. Optional `--project-key`.

### `uip tm attachment download`

```bash
uip tm attachment download --execution-id "$EXECUTION_ID" --test-set-key "$TEST_SET_KEY" --result-path "$ARTEFACTS_DIR" --output json
```

Writes per-testcase attachments to `$ARTEFACTS_DIR/<testcase-name>/`. Common Playwright attachments: `report.json`, `trace.zip`, `error-context.md`, screenshots. Optional flags: `--only-failed`, `--test-case-name <name>` (repeatable, substring).
