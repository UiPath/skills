# State checkpointing and resume

The `uipath-test-playwright` skill writes progress to `<outputDir>/.demo-state.json` after each major step. A re-run resumes mid-pipeline by reading this file and skipping completed phases.

> **Why:** A 4MB `or packages upload` that completed must not redo because a later phase hiccupped. Pipelines die on retried-from-zero runs.

## Schema

```json
{
  "version": 1,
  "projectPath": "/abs/path/to/project",
  "tmProjectKey": "DEMO",
  "packageName": "e2e-playwright",
  "packageVersion": "1.0.5",
  "outputDir": "/abs/path/to/project/.uipath",
  "folderKey": "f0f0f0f0-0000-0000-0000-000000000001",

  "nupkgPath": "/abs/path/to/project/.uipath/e2e-playwright.1.0.5.nupkg",
  "packedAt": "2026-04-26T10:30:00Z",

  "uploadedAt": "2026-04-26T10:30:30Z",

  "confirmedAt": "2026-04-26T10:31:00Z",
  "testCaseMap": {
    "auth > should login": "DEMO:23",
    "auth > should reject expired": "DEMO:24"
  },

  "selectedKeys": ["DEMO:23", "DEMO:24"],

  "testSetKey": "DEMO:142",
  "testSetName": "_pw_run_20260426-103200",

  "executionId": "550e8400-e29b-41d4-a716-446655440000",
  "executionStartedAt": "2026-04-26T10:32:15Z",
  "terminalStatus": "Failed",
  "terminalAt": "2026-04-26T10:42:00Z",

  "artefactsPath": "/abs/path/to/project/.uipath/artefacts/550e8400-.../"
}
```

`testCaseMap` maps each test's `displayName` to the `ObjKey` of the Test Case **TM auto-created on upload** — the skill does not create or link Test Cases itself.

## Phase → state-key gating

The skill skips a phase if its output keys are present in state. Drop the relevant keys to redo a phase.

| Phase | Reads from state | Writes to state | Skip condition |
|---|---|---|---|
| 0. Pre-flight | — | `tmProjectKey`, `folderKey` | Always runs (cheap); also sets project default folder |
| 1. Pack | `packageName`, `packageVersion`, `outputDir` | `nupkgPath`, `packedAt` | `nupkgPath` exists on disk for current `(name, version)` |
| 2. Publish | `nupkgPath` | `uploadedAt` | `uploadedAt` set for current `(name, version)` |
| 3. Confirm auto-created Test Cases | `tmProjectKey`, `packageName` | `testCaseMap`, `confirmedAt` | `confirmedAt > uploadedAt` AND `testCaseMap` count == package `testCount` |
| 4. Subset selection | `testCaseMap` | `selectedKeys` | `selectedKeys` non-empty |
| 5. Test set + run | `selectedKeys`, `tmProjectKey` | `testSetKey`, `testSetName`, `executionId`, `executionStartedAt` | `executionId` set |
| 6. Wait + fetch | `executionId`, `testSetKey`, `outputDir` | `terminalStatus`, `terminalAt`, `artefactsPath` | `terminalAt` set AND `artefactsPath` directory has files |

## Resume recipes

### Redo only the test execution (keep package + auto-created Test Cases)

```bash
jq 'del(.testSetKey, .testSetName, .executionId, .executionStartedAt, .terminalStatus, .terminalAt, .artefactsPath)' \
  "$OUTPUT_DIR/.demo-state.json" > "$OUTPUT_DIR/.demo-state.json.tmp" \
  && mv "$OUTPUT_DIR/.demo-state.json.tmp" "$OUTPUT_DIR/.demo-state.json"
```

### Redo upload + everything downstream (keep packed nupkg)

```bash
jq 'del(.uploadedAt, .confirmedAt, .testCaseMap, .selectedKeys, .testSetKey, .testSetName, .executionId, .executionStartedAt, .terminalStatus, .terminalAt, .artefactsPath)' \
  "$OUTPUT_DIR/.demo-state.json" > "$OUTPUT_DIR/.demo-state.json.tmp" \
  && mv "$OUTPUT_DIR/.demo-state.json.tmp" "$OUTPUT_DIR/.demo-state.json"
```

### Start fresh

```bash
rm "$OUTPUT_DIR/.demo-state.json"
# Optionally also remove old artefacts and packed nupkg:
rm -rf "$OUTPUT_DIR/artefacts" "$OUTPUT_DIR"/*.nupkg
```

### Bump version (treat as a new package)

```bash
NEW_VERSION="1.0.6"
jq --arg v "$NEW_VERSION" '
  .packageVersion = $v
  | del(.nupkgPath, .packedAt, .uploadedAt, .confirmedAt, .selectedKeys, .testSetKey, .testSetName, .executionId, .executionStartedAt, .terminalStatus, .terminalAt, .artefactsPath)
' "$OUTPUT_DIR/.demo-state.json" > "$OUTPUT_DIR/.demo-state.json.tmp" \
  && mv "$OUTPUT_DIR/.demo-state.json.tmp" "$OUTPUT_DIR/.demo-state.json"
```

`testCaseMap` is intentionally **kept** across version bumps. `uniqueId` is stable across re-packs, so re-uploading the bumped version updates the **same** TM Test Cases (no duplicates); Phase 3 just re-confirms the map.

## Idempotency rules

- **`testCaseMap` is keyed by `displayName`, not by version.** A `--package-version` bump re-uploads the same tests; because `uniqueId` is deterministic, TM updates the existing Test Cases and the `displayName → ObjKey` mapping still holds.
- **`testSetName` is per-run** (`_pw_run_<ts>`). Each fresh execution creates a new test set so historical runs stay distinct in TM.
- **`executionId` is per-run.** Once set, the run is committed; clearing it triggers a brand new execution against the existing test set.
- **`artefactsPath` is per-execution** (`<outputDir>/artefacts/<executionId>/`). Different execution IDs never collide.

## Cleanup recommendations

Per-run test sets named `_pw_run_<ts>` accumulate over time. Periodically clean them with:

```bash
uip tm testsets list --project-key "$TM_PROJECT_KEY" --filter "_pw_run_" --output json \
  | jq -r '.Data[] | select(.Name | startswith("_pw_run_")) | .ObjKey' \
  | while read key; do
      uip tm testsets delete --test-set-key "$key" --output json
    done
```

Do not auto-cleanup as part of the skill — the user may want to drill into TM UI on the just-finished run.
