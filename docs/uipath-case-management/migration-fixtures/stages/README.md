# Stages Golden Fixtures

Compatibility fixture for the `stages` plugin direct-JSON-write migration. Asserts that JSON emitted by the direct-write path is structurally equivalent to JSON produced by `uip maestro case stages add`.

> **Temporary — developer verification only.** These fixtures live outside the skill on purpose: they exist to verify migration correctness during the CLI → JSON shift, and will be removed once every plugin has migrated. Runtime agents do not load them.

## Files

| File | Purpose |
|---|---|
| `input.sdd-fragment.md` | Minimal sdd fragment exercising only the stages plugin |
| `cli-output.json` | Captured from `uip maestro case cases add` + two `stages add` runs (CLI version used: 0.1.21) |
| `json-write-output.json` | Hand-written to match the direct-JSON-write spec in [`plugins/stages/impl-json.md`](../../../skills/uipath-case-management/references/plugins/stages/impl-json.md) |
| `diff.sh` | Normalizes stage IDs by `data.label`, then diffs; passes if structurally equivalent |

## Running the diff

```bash
./diff.sh
```

Exit 0 on equivalence; non-zero with a unified diff otherwise. Requires `jq` and `diff`.

## Validation parity

Both `cli-output.json` and `json-write-output.json` must produce the **same set of errors/warnings** from `uip maestro case validate`:

```
Found 3 error(s) and 3 warning(s):
  - [error] [nodes[trigger_1]] Trigger has no outgoing edges
  - [warning] [nodes[<stage>]] Stage <regular-stage> has no tasks
  - [error] [nodes[<stage>]] Stage <regular-stage> has no incoming edges
  - [warning] [nodes[<stage>]] Stage <exception-stage> has no tasks
  - [warning] [nodes[<stage>]] Secondary stage <exception-stage> has no entry conditions
  - [error] [nodes[<stage>]] Secondary stage <exception-stage> has no exit conditions
```

These are **expected** — the fixture intentionally exercises stages in isolation (no edges, tasks, conditions). The point is that both outputs produce the same failure profile, proving downstream CLI commands see them as equivalent.

## Regenerating `cli-output.json`

When the CLI version bumps:

```bash
WORK=$(mktemp -d)
cd "$WORK"
uip maestro case cases add --name "StagesProbe" --file caseplan.json --output json
uip maestro case stages add caseplan.json \
  --label "Submission Review" \
  --description "Initial submission review" \
  --output json
uip maestro case stages add caseplan.json \
  --label "Exception Handling" \
  --type exception \
  --description "Fallback for failed submissions" \
  --output json

cp caseplan.json <path-to-this-folder>/cli-output.json
```

Then re-run `./diff.sh` to confirm the direct-JSON-write fixture still matches. If the diff fails, the CLI output shape changed — update `json-write-output.json` and [`plugins/stages/impl-json.md`](../../../skills/uipath-case-management/references/plugins/stages/impl-json.md) to reflect the new spec.

## Regenerating `json-write-output.json`

Follow the JSON Recipe in [`plugins/stages/impl-json.md`](../../../skills/uipath-case-management/references/plugins/stages/impl-json.md). The two stage IDs in the current fixture (`Stage_jW8tRv` and `Stage_kQ4pLm`) are hand-picked to be distinct from any CLI output — they exercise the normalizer in `diff.sh`.

## Current status

Captured against CLI version `0.1.21`. Key observations from this run:

- `root.version: "v16"` (not v17 as the CLI source currently in `~/Documents/GitHub/cli` specifies — that branch is ahead of the installed binary)
- `root.data: {}` — empty on a fresh case; `intsvcActivityConfig` / `uipath.variables` / `uipath.bindings` appear only after their respective plugins run
- CLI `.unshift()`s new stages so the most recently added stage appears first in `nodes[]`. Our fixture preserves that order.
- **`data.isRequired` divergence.** The CLI's `stages add` has no `--is-required` flag and never emits the key. The direct-JSON-write always emits `isRequired: <bool>` (see [`plugins/stages/impl-json.md` § Known CLI divergences](../../../skills/uipath-case-management/references/plugins/stages/impl-json.md#known-cli-divergences)). `diff.sh` normalizes `isRequired: false` ↔ absent so the golden diff still asserts structural equivalence.
