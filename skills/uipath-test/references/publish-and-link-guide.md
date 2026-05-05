# Publish and Link Automation to Test Manager

End-to-end pipeline: take a UiPath project's coded `[TestCase]` (or any test entry point), get it on Orchestrator, and bind it to a Test Manager test case so it can be executed from Test Manager. Each step lives in a different `uip` subdomain — this guide stitches them together.

## Pipeline

```
uip rpa pack            → .nupkg
uip or packages upload  → package on Orchestrator feed
uip or folders list-current-user  → folder UUID (the --folder-key value)
uip tm testcase list-automations  → test entry point name (the --test-name value)
uip tm testcase link-automation   → test case is bound
uip tm testcase execute  / testset execute   → run
uip tm wait              → block until terminal
```

## Prerequisites

- Logged in: `uip login status --output json`. If not, `uip login`.
- Project builds clean: `uip rpa build "<PROJECT_DIR>" --output json` returns `Result: "Success"`.
- Test case exists in Test Manager: `uip tm testcase list --project-key <PROJECT_KEY> --output json`. Capture the `ObjKey` (e.g. `DEMO:1`) — it is the `--test-case-key` value.

## Step 1 — Pack

```bash
uip rpa pack "<PROJECT_DIR>" "<OUTPUT_DIR>" --output json
```

Both arguments are positional — there is no `--project-dir` / `--project-path` flag here. See [/uipath:uipath-rpa § publishing-guide.md](../../uipath-rpa/references/publishing-guide.md) for full pack flags. Capture `OutputPath` from the JSON output — that's the `.nupkg` to upload.

## Step 2 — Upload to Orchestrator

```bash
uip or packages upload "<NUPKG_PATH>" --output json
```

Capture the returned `Id` (the package name) and `Version` from the JSON output. Both are needed downstream.

## Step 3 — Find the Orchestrator folder

`link-automation` requires `--folder-key <UUID>` (NOT `--folder-path`). Discover it:

```bash
uip or folders list-current-user --output json
```

Filter for the folder that owns the package. The `Key` field is the UUID.

> **Use `list-current-user`, not `list`.** `list` may omit personal workspaces and solution folders. `list-current-user` returns every folder the authenticated user can target.

## Step 4 — Find the test entry point name

A single package can expose multiple test entry points (one per `[TestCase]` method or test workflow). `link-automation` needs the exact `--test-name`. Discover it:

```bash
uip tm testcase list-automations --project-key <PROJECT_KEY> --folder-key <FOLDER_UUID> --output json
```

Optional filter: `--package-name <PACKAGE_ID>` (case-insensitive substring) when many packages live in the same folder. Pick the row whose `PackageName` matches the `Id` from Step 2 and note its `TestName`.

## Step 5 — Link the automation

```bash
uip tm testcase link-automation \
  --project-key <PROJECT_KEY> \
  --test-case-key <TEST_CASE_KEY> \
  --folder-key <FOLDER_UUID> \
  --package-name <PACKAGE_ID> \
  --test-name <TEST_NAME> \
  --output json
```

The output should show `Result: "Linked"`. `link-automation` is idempotent on the `(test-case-key, package-name, test-name)` triple — re-running with the same triple replaces the previous link.

## Step 6 — Execute

Two execution modes — pick one:

**Single test case** — uses `--test-case-id <UUID>`, NOT `--test-case-key`. Get the UUID from `uip tm testcase list --output json` (`Id` field):

```bash
uip tm testcase execute --project-key <PROJECT_KEY> --test-case-id <TEST_CASE_UUID> --execution-type automated --output json
```

**Whole test set** — uses `--test-set-key`:

```bash
uip tm testset execute --test-set-key <TEST_SET_KEY> --execution-type automated --output json
```

Capture the returned `ExecutionId`.

## Step 7 — Wait for terminal status

```bash
uip tm wait --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --timeout 900 --output json
```

`--timeout 0` means no timeout. The output `Status` is `Passed` / `Failed` / `Cancelled` when the call returns.

For result download, attachment download, and report generation: see [/uipath:uipath-test SKILL.md § Result, Attachment, Report Commands](../SKILL.md).

## Common pitfalls

- **`--test-case-id` (UUID) vs `--test-case-key` (`PROJECT_KEY:NUMBER`).** `link-automation`, `unlink-automation`, `update`, `delete`, `list-testsets` use `--test-case-key`. `execute`, `list-steps`, `list-result-history` use `--test-case-id`. They are NOT interchangeable.
- **Wrong folder identifier.** `link-automation` requires the UUID. A folder name or path passed in `--folder-key` fails silently with "folder not found" or links to the wrong folder.
- **Re-uploading the same package version.** Orchestrator rejects duplicates. Bump `--package-version` (or `project.json` `projectVersion`) on every change.
- **Linking before upload.** `link-automation` does not validate the package exists on Orchestrator at link time — it only validates at execute time. A stale `--package-name` value silently links to nothing and the next execute fails with `package not found`. Always discover via `list-automations` (Step 4) before linking.
- **Trying `uip tm testcase link` (no suffix).** The command is `link-automation`. Same for `unlink-automation`. See [/uipath:uipath-test § Anti-patterns](../SKILL.md#anti-patterns).
