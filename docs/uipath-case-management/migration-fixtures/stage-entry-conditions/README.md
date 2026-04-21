# stage-entry-conditions Golden Fixtures

Compatibility fixture for the `stage-entry-conditions` plugin direct-JSON-write migration. Asserts that JSON emitted by the direct-write path is structurally equivalent to JSON produced by `uip maestro case stage-entry-conditions add` across all five stage-entry rule-types.

> **Temporary — developer verification only.** These fixtures live outside the skill on purpose: they exist to verify migration correctness during the CLI → JSON shift, and will be removed once every plugin has migrated. Runtime agents do not load them.

## Files

| File | Purpose |
|---|---|
| `input.sdd-fragment.md` | Minimal sdd fragment exercising all five stage-entry rule-types |
| `cli-output.json` | Captured from `uip maestro case cases add` + two `stages add` + five `stage-entry-conditions add` runs (CLI version used: 0.3.4 from `~/Documents/GitHub/cli` source build) |
| `json-write-output.json` | Hand-written to match the direct-JSON-write spec in [`plugins/conditions/stage-entry-conditions/impl-json.md`](../../../skills/uipath-case-management/references/plugins/conditions/stage-entry-conditions/impl-json.md) |
| `diff.sh` | Normalizes Stage / Condition / Rule IDs by slug, then diffs; passes if structurally equivalent |

## Running the diff

```bash
./diff.sh
```

Exit 0 on equivalence; non-zero with a unified diff otherwise. Requires `jq` and `diff`.

## Validation parity

Both `cli-output.json` and `json-write-output.json` produce the same expected failure profile from `uip maestro case validate`:

```
Found 3 error(s) and 2 warning(s):
  - [error] [nodes[trigger_1]] Trigger "Trigger 1" has no outgoing edges
  - [warning] [nodes[<target>]] Stage "Target" has no tasks
  - [error] [nodes[<target>]] Stage "Target" has no incoming edges
  - [warning] [nodes[<upstream>]] Stage "Upstream" has no tasks
  - [error] [nodes[<upstream>]] Stage "Upstream" has no incoming edges
```

These are expected — the fixture intentionally exercises entry conditions in isolation (no edges, no tasks, no exit conditions). The point is that both outputs produce the same failure profile, proving downstream CLI commands see them as equivalent.

## Regenerating `cli-output.json`

When the CLI version bumps:

```bash
WORK=$(mktemp -d)
cd "$WORK"
BIN=/Users/jundayin/Documents/GitHub/cli/packages/cli/dist/index.js  # or whichever uip binary

node "$BIN" maestro case cases add --name "StageEntryProbe" --file caseplan.json --output json
node "$BIN" maestro case stages add caseplan.json --label "Upstream" --description "Upstream stage" --output json
node "$BIN" maestro case stages add caseplan.json --label "Target"   --description "Target stage"   --output json

# Capture the Target and Upstream stage IDs from the output, then:
UPSTREAM=$(node -e "const d=require('$WORK/caseplan.json'); console.log(d.nodes.find(n=>n.data.label==='Upstream').id)")
TARGET=$(node -e   "const d=require('$WORK/caseplan.json'); console.log(d.nodes.find(n=>n.data.label==='Target').id)")

node "$BIN" maestro case stage-entry-conditions add caseplan.json "$TARGET" --display-name "From case start"          --rule-type case-entered                                                                                 --output json
node "$BIN" maestro case stage-entry-conditions add caseplan.json "$TARGET" --display-name "After Upstream completes" --rule-type selected-stage-completed --selected-stage-id "$UPSTREAM"                                    --output json
node "$BIN" maestro case stage-entry-conditions add caseplan.json "$TARGET" --display-name "After Upstream exits"     --is-interrupting true --rule-type selected-stage-exited --selected-stage-id "$UPSTREAM"              --output json
node "$BIN" maestro case stage-entry-conditions add caseplan.json "$TARGET" --display-name "User-routed"              --rule-type user-selected-stage                                                                        --output json
node "$BIN" maestro case stage-entry-conditions add caseplan.json "$TARGET" --display-name "Fraud detected"           --is-interrupting true --rule-type wait-for-connector --condition-expression "event.fraudScore > 0.8" --output json

cp caseplan.json <path-to-this-folder>/cli-output.json
```

Then re-run `./diff.sh` to confirm the direct-JSON-write fixture still matches. If the diff fails, the CLI output shape changed — update `json-write-output.json` and [`plugins/conditions/stage-entry-conditions/impl-json.md`](../../../skills/uipath-case-management/references/plugins/conditions/stage-entry-conditions/impl-json.md) to reflect the new spec.

## Regenerating `json-write-output.json`

Follow the JSON Recipe in [`plugins/conditions/stage-entry-conditions/impl-json.md`](../../../skills/uipath-case-management/references/plugins/conditions/stage-entry-conditions/impl-json.md). The Condition / Rule / Stage IDs in the current fixture are hand-picked to be distinct from any CLI output — they exercise the normalizer in `diff.sh`.

## Current status

Captured against CLI source build at `~/Documents/GitHub/cli` (package version `0.3.4`, ahead of the `0.1.21` binary on PATH, which lacks the `maestro case` subcommand).

Key observations from this run:

- `root.version: "v17"`, `root.publishVersion: 2`, `root.data.intsvcActivityConfig: "v2"`, `root.data.uipath.variables.inputOutputs: []`, `root.data.uipath.bindings: []` — all present on a fresh case. (Differs from the `stages` fixture README which captured against `0.1.21` and saw only `root.data: {}`.)
- CLI appends new entry conditions to `data.entryConditions` via `.push()` (not `unshift`). Order matches insertion order.
- `node.data.entryConditions` key does not exist on a regular Stage at creation time — it is created on first `stage-entry-conditions add`.
- Field order inside a condition object: `id, displayName, rules, isInterrupting` (isInterrupting trails because `buildRule` sets it conditionally after `rules` is populated).
- `displayName` is always emitted from `options.displayName` (string, even `undefined` would be serialized as missing — tested only with display names present).
- Rule shape per rule-type (captured):
    - `case-entered` → `{ rule, id }`
    - `selected-stage-completed` → `{ rule, id, selectedStageId }`
    - `selected-stage-exited` → `{ rule, id, selectedStageId }`
    - `user-selected-stage` → `{ rule, id }`
    - `wait-for-connector` → `{ rule, id, conditionExpression }`
- `conditionExpression` is serialized only when passed; JSON.stringify drops `undefined` fields.
