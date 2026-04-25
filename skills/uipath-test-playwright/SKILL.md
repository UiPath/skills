---
name: uipath-test-playwright
description: "UiPath external Playwright test runner: pack a `playwright.config.{ts,js}` project via `uip tm pack`, upload to Orchestrator so Test Manager auto-creates Test Cases, run, poll, fetch report.json + trace.zip. TM CRUD→uipath-test. Studio/XAML→uipath-rpa."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
user-invocable: true
---

# UiPath External Test Runner

Drive the full **pack → publish → auto-create → run → poll → fetch** pipeline for a customer Playwright project on UiPath. One prompt, branching dialog, recoverable mid-pipeline.

Packaging uses `uip tm pack` (single-source `content/testCases.json`, V2 package format). On upload, Test Manager ingests that blob and **auto-creates the Test Cases** — no manual create/link loop.

## When to Use This Skill

- User says "run my Playwright project on UiPath", "demo the Playwright integration", "execute these Playwright tests via Test Manager"
- User has a Playwright project (`playwright.config.{ts,js,mjs}`) and wants it to flow through Orchestrator + Test Manager
- User asks to fetch `report.json` / `trace.zip` artefacts from a Playwright run

**Do NOT use for:**
- Generic Test Manager CRUD (list/create/update test cases/sets/projects without a Playwright pack) → `uipath-test`
- Studio coded workflows or XAML test cases → `uipath-rpa`
- Pure Orchestrator package operations → `uipath-platform`

## Critical Rules

1. **Never run `uip login` against a non-`*.uipath.com` URL.** The CLI rejects it (`cli/packages/auth/src/config.ts`). For a non-cloud Orch the user must populate `~/.uipath/.auth` (dotenv-format file: `KEY=VALUE` per line) with `UIPATH_URL`, `UIPATH_ACCESS_TOKEN`, `UIPATH_ORGANIZATION_ID`, `UIPATH_TENANT_ID`. The CLI walks up from cwd looking for any `.uipath/.auth`, falling back to `~/.uipath/.auth`. Detect via `uip login status --output json`; do NOT auto-retry login.
2. **Always pass `--output json` to `uip` commands.** Free-form output is for humans; this skill must parse. See `references/cli-commands.md` for the exact JSON shape each command returns.
3. **Never modify the customer's Playwright source.** Pack verbatim. If discovery is wrong, fix the packager; don't edit customer code.
4. **Bump `--package-version` between source changes.** Orchestrator caches packages by `(name, version)` and silently returns the old payload otherwise. (Note the flag is `--package-version`, not `--version` — `-V/--version` prints the CLI version.)
5. **Pack with `uip tm pack`; let Test Manager auto-create the Test Cases on upload.** `tm pack --tmh-project <KEY>` embeds `content/testCases.json`. On `uip or packages upload`, Orchestrator fires `package.uploaded` and TM ingests that blob — creating Test Cases and hydrating the six `PW_` label facets (File / Path / Project / Suite / Tag / Annotation). Do **NOT** manually `tm testcases create` + `link-automation` per test — that path is superseded. Use `--no-create-test-cases` only for publish-only (no TM Test Cases).
6. **One Playwright test = one Test Case; project is NOT part of identity.** `tm pack` dedupes each test×project row into a single test carrying a `projects[]` array; TM records the browser as a `PW_Project` facet. Never split per browser or append `[<project>]` to names. `uniqueId` is a deterministic UUID v5 of `(packageName, filePath, titleChain)`, stable across re-packs — so a re-upload updates the same Test Cases instead of duplicating.
7. **V2 test packages require Orchestrator flag `AllowTestAutomationPackagesWithV1Metadata` ON**, or upload is rejected. The package's `operate.json` carries `targetRuntime: "playwright-javascript"` (the serverless-pod discriminator) and `contentType: "tests"`.
8. **Set a default Orchestrator folder on the TM project before any `run`.** `uip tm project set-default-folder --project-key <KEY> --folder-key <FOLDER_KEY> --output json`; `tm testsets run` fails without it. Resolve folders via `uip or folders list -n <name> --all --output json` (`.Data[].Key` is the folder UUID).
9. **Checkpoint state after every major step.** Write `<outputDir>/.demo-state.json`. A 4MB upload that completed must not redo because a later step hiccupped. See `references/state-resume.md` for the schema.
10. **Surface `tm wait` timeouts to the user, do not auto-fail.** A 30-min poll cap doesn't mean the run failed — it means it's still going on Orch. Offer to extend or skip-to-fetch.

## Inputs

Parse the user's prompt for these. Anything missing, ask in **one** consolidated text reply (not five separate prompts):

| Input | Required | Default |
|---|---|---|
| `projectPath` | yes | — |
| `tmProjectKey` | yes | — (e.g. `DEMO`) |
| `version` | no | `1.0.0` for first run, else patch-bump from `state.version` |
| `packageName` | no | basename of `projectPath` |
| `outputDir` | no | `<projectPath>/.uipath` |

Then ask via **AskUserQuestion** (multi-choice — these are decision branches, not free text):

- **Q1: Auto-create TM Test Cases?** Yes (recommended) / No (publish-only)
- **Q2: Run which?** All N / Subset (let me pick) / None (just create Test Cases) — only asked if Q1 = Yes

For subset selection, do NOT use AskUserQuestion (multi-choice doesn't scale beyond ~5 options). Print a numbered table and accept free-text reply: `1,3,5` or `DEMO:23,DEMO:25` or `all`.

## Workflow

### Phase 0 — Pre-flight (always)

Verify all three before any pack/upload. Fail fast; tell the user which to fix and stop.

```bash
# 1. uip on PATH
command -v uip >/dev/null 2>&1 || { echo "uip not on PATH"; exit 1; }

# 2. Authenticated
uip login status --output json | jq -e '.Data.Status == "Logged in"' >/dev/null \
  || { echo "Not authenticated. See SKILL.md Critical Rule #1."; exit 1; }

# 3. Project looks like Playwright
ls "$PROJECT_PATH"/playwright.config.{ts,js,mjs} 2>/dev/null | head -1 | grep -q . \
  || { echo "$PROJECT_PATH is not a Playwright project."; exit 1; }
```

**`uip` install.** If `command -v uip` fails, the skill cannot run. Install the published CLI: `npm i -g @uipath/cli`. Tell the user to install it (don't auto-install). `tm pack` requires a CLI build that ships the command.

Resolve / create the TM project:

```bash
uip tm project list --filter "$TM_PROJECT_KEY" --output json
# If no row matches ProjectKey == TM_PROJECT_KEY → create it:
uip tm project create --name "$TM_PROJECT_KEY" --project-key "$TM_PROJECT_KEY" --output json
```

Resolve a folder and set it as the project default (**required before any `run`** — Critical Rule #8):

```bash
uip or folders list --all --output json   # .Data[].Key = folder UUID, .Data[].Name
uip tm project set-default-folder --project-key "$TM_PROJECT_KEY" --folder-key "$FOLDER_KEY" --output json
```
- Single folder → auto-pick. Multiple → AskUserQuestion (≤4 options; else numbered table + free-text). Save to `state.folderKey`.

### Phase 1 — Pack

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

Verify `success == true`. Compute `nupkgPath = "$OUTPUT_DIR/$PACKAGE_NAME.$VERSION.nupkg"`; save to state. Skip this phase if `state.nupkgPath` exists on disk for the current version.

Preview the tests the package will register (source of truth = the embedded single-source file):

```bash
unzip -p "$NUPKG_PATH" content/testCases.json | jq '.testCases | length, .testCases[].displayName'
```

Each `testCases[]` entry is one logical test: `{ uniqueId, filePath, line, displayName, describePath[], projects[], tags[], annotations[] }`. `projects[]` lists the browsers; it is NOT part of identity (Critical Rule #6).

### Phase 2 — Publish

```bash
uip or packages upload "$NUPKG_PATH" --output json
```

Verify `.Result == "Success"`. Save `state.uploadedAt`. Skip if `state.uploadedAt` is set for the current `(packageName, version)`.

On success, Orchestrator's `package.uploaded` event drives Test Manager to ingest `content/testCases.json` and **auto-create the Test Cases** in `$TM_PROJECT_KEY` (unless the package was packed with `--no-create-test-cases`). Upload requires the Orchestrator flag `AllowTestAutomationPackagesWithV1Metadata` (Critical Rule #7) — a `V1Metadata`/`descriptor`-rejection error means it is OFF; see `references/troubleshooting.md`.

**Branch on Q1 = No (publish-only):** the user opted out of TM Test Cases. Re-pack in Phase 1 with `--no-create-test-cases` and omit `--tmh-project`, upload, print `{packageName, version}`, **stop**.

### Phase 3 — Confirm auto-created Test Cases (only if Q1 = Yes)

TM ingestion runs asynchronously off the upload event; **retry with backoff** until the count matches the package:

```bash
# Retry up to 5 times (2s, 4s, 8s, 16s, 32s) until count >= expected.
uip tm testcases list --project-key "$TM_PROJECT_KEY" --filter "$PACKAGE_NAME" --output json
```

Each row is one auto-created Test Case; capture `.Data[].ObjKey` (e.g. `DEMO:23`) — that is the `--test-case-key` value. Cross-check the count against `content/testCases.json` (Phase 1). If short after 5 retries, surface the diff (which `displayName`s are missing) and stop — do NOT hand-create the missing ones.

Save the `{ displayName → ObjKey }` mapping to `state.testCaseMap`.

> Do NOT run `tm testcases create` / `link-automation` here. TM created and linked the automation on ingestion (Critical Rule #5).

### Phase 4 — Subset selection (only if Q1 = Yes)

If Q2 = None → skip Phases 5–7. Print: "Package $PACKAGE_NAME:$VERSION uploaded; TM created N Test Cases in $TM_PROJECT_KEY. Stopped before execution as requested."

If Q2 = All → set `selectedKeys = all values from state.testCaseMap`, skip to Phase 5.

If Q2 = Subset → print numbered table:
```
  #   Key         Test Case
  1   DEMO:23     Google Search Bar > should have a visible search bar
  2   DEMO:24     auth > should reject expired token
  ...
```
Ask (free text, not AskUserQuestion): "Type indices or keys to run (`1,3,5` or `DEMO:23,DEMO:25`), or `all`." Parse into `selectedKeys`; reject unknown indices/keys with a clear error and re-ask.

### Phase 5 — Test set + run

Create the per-run test set (named for sortability and bulk-cleanup later), add the selected cases, run it:

```bash
TEST_SET_NAME="_pw_run_$(date -u +%Y%m%d-%H%M%S)"

TEST_SET_KEY=$(uip tm testsets create \
  --project-key "$TM_PROJECT_KEY" \
  --name "$TEST_SET_NAME" \
  --description "Auto-created by uipath-test-playwright for $PACKAGE_NAME:$VERSION" \
  --output json | jq -r '.Data.ObjKey')

uip tm testcases add \
  --test-set-key "$TEST_SET_KEY" \
  --test-case-keys "$(IFS=,; echo "${selectedKeys[*]}")" \
  --output json

EXECUTION_ID=$(uip tm testsets run \
  --test-set-key "$TEST_SET_KEY" \
  --execution-type automated \
  --output json | jq -r '.Data.ExecutionId')
```

Print the count: "Running N Test Cases via test set `$TEST_SET_KEY`." Save `state.testSetKey`, `state.testSetName`, `state.executionId`.

### Phase 6 — Wait, summarize, fetch artefacts

```bash
uip tm wait \
  --execution-id "$EXECUTION_ID" \
  --project-key "$TM_PROJECT_KEY" \
  --test-set-key "$TEST_SET_KEY" \
  --timeout 1800 \
  --output json
```

On timeout, do **not** fail. AskUserQuestion: A) extend timeout 30 min B) skip to fetch in-progress C) print execution URL and stop.

```bash
uip tm executions testcaselogs list \
  --execution-id "$EXECUTION_ID" \
  --project-key "$TM_PROJECT_KEY" \
  --output json
```

Print a compact table: `TestCase | Status | Duration`. Highlight failures.

```bash
ARTEFACTS_DIR="$OUTPUT_DIR/artefacts/$EXECUTION_ID"
mkdir -p "$ARTEFACTS_DIR"

uip tm result download --execution-id "$EXECUTION_ID" --test-set-key "$TEST_SET_KEY" --result-path "$ARTEFACTS_DIR" --output json
uip tm attachment download --execution-id "$EXECUTION_ID" --test-set-key "$TEST_SET_KEY" --result-path "$ARTEFACTS_DIR" --output json
```

After download, run `find "$ARTEFACTS_DIR" -type f` and list per-testcase artefacts. For failed cases, point at the trace:
> Open the trace: `npx playwright show-trace <path-to-trace.zip>`

### Phase 7 — Final summary

```
PIPELINE: DONE
  TM project   : DEMO
  Test set     : _pw_run_20260426-103015 (DEMO:142)
  Execution    : 550e8400-e29b-41d4-a716-446655440000
  Status       : Failed (1 of 12 cases)
  Artefacts    : /abs/path/.uipath/artefacts/550e8400-.../
  Failed case  : auth › login should reject expired token
                 Trace: /.../trace.zip
                 Run:   npx playwright show-trace /.../trace.zip
```

## Reference Navigation

- **Exact CLI commands and JSON shapes** → `references/cli-commands.md`
- **Failure modes and fixes** → `references/troubleshooting.md`
- **State checkpointing and resume recipes** → `references/state-resume.md`

## Anti-patterns — Don't Do This

- **Do not** manually `tm testcases create` + `link-automation` per test. `tm pack` + upload makes TM auto-create the Test Cases (Critical Rule #5). Manual creation duplicates and drifts from the package's `uniqueId`s.
- **Do not** create one Test Case per Playwright `(test, project)` pair, and do not append `[<project>]` to names. One test = one Test Case; browser is a `PW_Project` label facet (Critical Rule #6).
- **Do not** use `--version` for the package version — that flag prints the CLI version. Use `--package-version`.
- **Do not** call `uip tm testcases run` for the pipeline — that starts an ad-hoc single-case execution. Group the selection into a test set and use `tm testsets run` so results land under one execution.
- **Do not** run before setting the project's default Orchestrator folder — `tm testsets run` fails without it (Critical Rule #8).
- **Do not** assume the test set already exists. Always create a per-run `_pw_run_<ts>` set.
- **Do not** auto-delete the test set after the run. The user may want to drill in via TM UI. Document cleanup in the final summary instead.
- **Do not** retry `uip login` if `login status` fails. Login is browser-interactive; tell the user to run it themselves.
