# Edges Golden Fixtures

Compatibility fixture for the `edges` plugin direct-JSON-write migration. Asserts that JSON emitted by the direct-write path is structurally equivalent to JSON produced by `uip maestro case edges add`.

> **Temporary — developer verification only.** These fixtures live outside the skill on purpose: they exist to verify migration correctness during the CLI → JSON shift, and will be removed once every plugin has migrated. Runtime agents do not load them.

## Files

| File | Purpose |
|---|---|
| `input.sdd-fragment.md` | Minimal sdd fragment exercising only the edges plugin |
| `cli-output.json` | Captured from `uip maestro case cases add` + two `stages add` + two `edges add` runs (CLI version: 0.1.21) |
| `json-write-output.json` | Hand-written to match the direct-JSON-write spec in [`plugins/edges/impl-json.md`](../../../skills/uipath-case-management/references/plugins/edges/impl-json.md) |
| `diff.sh` | Normalizes stage + edge IDs, then diffs; passes if structurally equivalent |

## Running the diff

```bash
./diff.sh
```

Exit 0 on equivalence; non-zero with a unified diff otherwise. Requires `jq` and `diff`.

## Validation parity

Both `cli-output.json` and `json-write-output.json` should produce the **same set of errors/warnings** from `uip maestro case validate`:

```
Found 0 error(s) and 2 warning(s):
  - [warning] [nodes[Stage_<submission-review>]] Stage Submission Review has no tasks
  - [warning] [nodes[Stage_<approval>]] Stage Approval has no tasks
```

Edges are fully wired, so the orphan-stage errors from the stages fixture are gone — only the "no tasks" warnings remain. The fixture intentionally skips tasks to exercise edges in isolation.

## Regenerating `cli-output.json`

When the CLI version bumps:

```bash
WORK=$(mktemp -d)
cd "$WORK"

# Scaffold
uip maestro case cases add --name "EdgesProbe" --file caseplan.json --output json

# Stages — capture the generated IDs; order matters for the edges add.
S1=$(uip maestro case stages add caseplan.json \
  --label "Submission Review" \
  --description "Initial submission review" \
  --output json | jq -r '.Data.StageId')
S2=$(uip maestro case stages add caseplan.json \
  --label "Approval" \
  --description "Approve or reject the submission" \
  --output json | jq -r '.Data.StageId')

# Edges
uip maestro case edges add caseplan.json \
  --source "trigger_1" \
  --target "$S1" \
  --label "Start" \
  --output json

uip maestro case edges add caseplan.json \
  --source "$S1" \
  --target "$S2" \
  --label "Approved" \
  --output json

cp caseplan.json <path-to-this-folder>/cli-output.json
```

Then re-run `./diff.sh` to confirm the direct-JSON-write fixture still matches. If the diff fails, the CLI output shape changed — update `json-write-output.json` and [`plugins/edges/impl-json.md`](../../../skills/uipath-case-management/references/plugins/edges/impl-json.md) to reflect the new spec.

## Regenerating `json-write-output.json`

Follow the JSON Recipe in [`plugins/edges/impl-json.md`](../../../skills/uipath-case-management/references/plugins/edges/impl-json.md). The IDs in the current fixture are hand-picked to be distinct from the CLI output — they exercise the normalizer in `diff.sh`.

| Entity | CLI ID (example) | JSON-write ID (fixture) |
|---|---|---|
| Stage "Submission Review" | `Stage_aBc1De` | `Stage_jSnWrA` |
| Stage "Approval" | `Stage_pQr4Sv` | `Stage_jSnWrB` |
| Edge trigger → S1 | `edge_Tr1Gr2` | `edge_jWr001` |
| Edge S1 → S2 | `edge_Ap2Pr4` | `edge_jWr002` |

## Current status

Captured against CLI version `0.1.21`. Key observations from this run:

- `schema.edges.push(edge)` — CLI appends edges in insertion order. No `.unshift()` like stages.
- Edge object key insertion order: `id, source, target, sourceHandle, targetHandle, [zIndex], data, type`. `JSON.stringify` drops `zIndex: undefined` and `data.label: undefined` so absent optional fields leave no keys.
- Edge type inferred from source node type — Trigger → `TriggerEdge`, Stage → `Edge`. No `--type` flag on `edges add`.
- Handles always emit with defaults even when the CLI user passes nothing — `sourceHandle` defaults to `right`, `targetHandle` defaults to `left`.
- Stage `isRequired: false` divergence (from the stages fixture) persists — the edges fixture's stages are JSON-written with `isRequired: false`; the CLI-produced stages omit the key. `diff.sh` strips `isRequired: false` on both sides.
