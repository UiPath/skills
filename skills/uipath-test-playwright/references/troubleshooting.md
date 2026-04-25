# Troubleshooting

Failure modes the `uipath-test-playwright` skill encounters, with diagnosis and fix.

## Pre-flight failures

### `uip` not on PATH

**Symptom:** `command -v uip` returns non-zero in pre-flight.

**Cause:** CLI not installed in this environment.

**Fix:** Tell the user to install the published CLI: `npm i -g @uipath/cli`. `tm pack` requires a CLI build that ships the command.

### Auth check fails

**Symptom:** `uip login status --output json` returns `.Data.Status != "Logged in"`.

**Causes and fixes:**

| Hostname in `state.uipUrl` | Fix |
|---|---|
| `*.uipath.com` (cloud / staging) | `uip login --interactive` and let the user complete the browser flow |
| `localhost` or custom | Cannot use `uip login` (the CLI rejects non-`uipath.com` hostnames in `cli/packages/auth/src/config.ts:142-150`). Tell the user to manually populate `~/.uipath/.auth` (dotenv-format `KEY=VALUE` lines) with `UIPATH_URL`, `UIPATH_ACCESS_TOKEN`, `UIPATH_ORGANIZATION_ID`, `UIPATH_TENANT_ID`. CLI walks up from cwd first, falling back to `~/.uipath/.auth`. |
| Token expired | Same fix as above (cloud → `uip login --interactive`; local → refresh token) |

**Never auto-retry login** from the skill — it requires browser interaction.

### Project doesn't look like Playwright

**Symptom:** No `playwright.config.{ts,js,mjs}` at the supplied `projectPath`.

**Fix:** Stop. Ask the user to confirm the path. Playwright config is the only reliable Playwright-project marker.

## Pack phase

### `tm pack` refuses: `--tmh-project` required

**Symptom:** `tm pack` exits before emitting anything, complaining a TM project key is required.

**Cause:** Create-test-cases is ON by default; the CLI enforces `--tmh-project` at pack time (friendlier than failing post-upload).

**Fix:** Pass `--tmh-project <TM_PROJECT_KEY>`. If the user genuinely wants no TM Test Cases, pass `--no-create-test-cases` and drop `--tmh-project`.

### `playwright --list` exits non-zero

**Symptom:** `tm pack` errors with a Playwright list failure.

**Cause:** Customer's `playwright.config.ts` has a runtime error (broken import, type error in `defineConfig`, etc.). Discovery uses the customer's own resolver — there is no fallback.

**Fix:** Print the error verbatim and stop. Customer-side issue; do not edit their source.

### Duplicate `uniqueId` collision

**Symptom:** `tm pack` fails loudly reporting two tests collapse to the same id.

**Cause:** Two tests share file + full title chain but sit on different source lines. `uniqueId` = UUID v5 of `(packageName, filePath, titleChain)`, so they collide — packing fails rather than silently shipping fewer tests.

**Fix:** Tell the user to disambiguate the duplicated test title (or its `describe` chain). Do not edit their source yourself.

### Empty test discovery

**Symptom:** `tm pack` succeeds but reports 0 tests (`testCount: 0`).

**Causes:** `testMatch` in `playwright.config.ts` matches no files; or all projects are setup-only.

**Fix:** Surface the count and ask the user to confirm. Do not auto-bail — they may be testing the packager itself.

## Publish phase

### Upload rejected: V2 metadata / descriptor error

**Symptom:** `uip or packages upload` fails with a descriptor / `V1Metadata` rejection (not an auth error).

**Cause:** `tm pack` emits a **V2 new-format** test package. Orchestrator rejects V2 test packages at upload unless the feature flag `AllowTestAutomationPackagesWithV1Metadata` is ON.

**Fix:** Enable `AllowTestAutomationPackagesWithV1Metadata` on the Orchestrator tenant. This is an environment prerequisite, not something the skill can work around — surface it and stop.

### Upload 401 / 403

**Symptom:** `uip or packages upload` returns an auth error.

**Causes:** Token lacks Orchestrator scope; or wrong tenant selected (token for tenant A, package uploaded to tenant B's URL).

**Fix:** `uip login tenant set <name>` or re-login with `--tenant <name>`.

### Upload 413 / size limit

**Symptom:** Large nupkg rejected by Orch.

**Fix:** Trim `node_modules` from the customer's project before pack (the packager already excludes `node_modules`, `dist`, `.git`, `.uipath`, `test-results`, `playwright-report` — verify this happened for this project).

## Ingestion phase (TM auto-creates Test Cases)

### Test Cases don't appear after upload

**Symptom:** `tm testcases list --filter <packageName>` returns fewer rows than `content/testCases.json` (or none).

**Causes:**
- Ingestion runs asynchronously off the `package.uploaded` event — TM hasn't caught up yet.
- The package was packed with `--no-create-test-cases`, so nothing is created.
- `--tmh-project` at pack time pointed at a different TM project than you're listing.
- The upload's tenant differs from the TM project's tenant.

**Fix:**
1. Retry `tm testcases list` with backoff (5×, 2s/4s/8s/16s/32s).
2. Confirm the package was packed **without** `--no-create-test-cases` and with the correct `--tmh-project`.
3. If still short after the loop, surface which `displayName`s are missing and stop. Do **not** hand-create the missing Test Cases — that drifts from the package's `uniqueId`s and duplicates on the next upload.

### Debugging ingestion with `list-automations`

To check whether Orchestrator surfaced the package's automation entry points to TM at all:

```bash
uip tm testcases list-automations --project-key "$TM_PROJECT_KEY" --folder-key "$FOLDER_KEY" --output json
```

Empty here means Orchestrator hasn't propagated the package to the folder yet, or the folder doesn't use the tenant feed. This is diagnostic only — the normal flow never needs it.

## Execute phase

### `tm testsets run` fails: no default folder

**Symptom:** `testsets run` errors that the project has no default folder / execution target.

**Cause:** `tm testsets run` (like `tm testcases run`) requires a default Orchestrator folder on the TM project.

**Fix:** Set it once before running: `uip tm project set-default-folder --project-key "$TM_PROJECT_KEY" --folder-key "$FOLDER_KEY" --output json`. Get folder keys with `uip or folders list --all --output json` (`.Data[].Key`).

### `tm testsets run` 404

**Symptom:** Test set key not found.

**Cause:** Wrong tenant, or the test set was deleted between create and run.

**Fix:** `uip tm testsets list --project-key <KEY>` to verify the key exists.

### `tm testsets run` succeeds but reports 0 cases run

**Symptom:** Execution starts but `executions testcaselogs list` returns empty.

**Causes:** Test set has no test cases (forgot `tm testcases add`); or the selected keys weren't valid `ObjKey`s.

**Fix:** `uip tm testsets list-testcases --test-set-key <KEY>` to confirm membership; re-add via `uip tm testcases add --test-set-key <KEY> --test-case-keys <...>`.

## Wait phase

### `tm wait` times out

**Symptom:** Returns `Result: "Failure"` with a TimedOut message after 1800s.

**Cause:** Execution still running on Orch — large suite, pod startup delay, browser install at runtime.

**Fix:** Do **not** auto-fail. AskUserQuestion: extend timeout 30 min, skip to fetch in-progress, or print execution URL and stop. Most failures here are recoverable.

## Fetch phase

### `tm attachment download` returns no files

**Symptom:** Command succeeds but `find $ARTEFACTS_DIR -type f` is empty.

**Causes:** Handler pod hasn't written attachments yet (race between execution-complete and pod upload); or the executor failed before producing artefacts (e.g. `npm install` failure inside the pod).

**Fix:**
1. Re-run `attachment download` once after a 30s wait.
2. If still empty, fall back to `tm executions testcaselogs list --output json` and surface the log text — the per-testcase `Message`/`Status` indicates executor-side failure.

### Downloaded `trace.zip` rejected by `playwright show-trace`

**Symptom:** "newer Playwright version required" error.

**Cause:** The pod ran a Playwright version newer than the local user's installed `playwright-core`.

**Fix:** Tell the user to bump local Playwright (`npm i -g playwright@latest`) or use the project's pinned viewer (`npx playwright show-trace ...`).
