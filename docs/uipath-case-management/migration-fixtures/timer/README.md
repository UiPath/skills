# Timer Trigger Golden Fixtures

Compatibility fixture for the `triggers/timer` plugin direct-JSON-write migration. Asserts that JSON emitted by the direct-write path is structurally equivalent to JSON produced by `uip maestro case triggers add-timer`, across **both** `caseplan.json` and the sidecar `entry-points.json`.

> **Temporary — developer verification only.** These fixtures live outside the skill on purpose: they exist to verify migration correctness during the CLI → JSON shift, and will be removed once every plugin has migrated. Runtime agents do not load them.

## Files

| File | Purpose |
|---|---|
| `input.sdd-fragment.md` | Minimal sdd fragment exercising only the timer trigger plugin |
| `cli-output/caseplan.json` | Captured from `uip case init` + `uip maestro case cases add` + `uip maestro case triggers add-timer --time-cycle ...` (CLI version: 0.1.21) |
| `cli-output/entry-points.json` | Sidecar written by the same CLI commands |
| `json-write-output/caseplan.json` | Hand-written to match the direct-JSON-write spec in [`plugins/triggers/timer/impl-json.md`](../../../skills/uipath-case-management/references/plugins/triggers/timer/impl-json.md) |
| `json-write-output/entry-points.json` | Hand-written sidecar per the same spec |
| `diff.sh` | Normalizes trigger IDs by displayName slug + strips `uniqueId` UUIDs; diffs both files; passes if structurally equivalent |

## Running the diff

```bash
./diff.sh
```

Exit 0 on equivalence; non-zero with a unified diff otherwise. Requires `jq` and `diff`.

## Validation parity

Both `cli-output/` and `json-write-output/` must produce the **same set of errors/warnings** from `uip maestro case validate`:

```
Found 2 error(s) and 0 warning(s):
  - [error] [nodes[trigger_1]] Trigger has no outgoing edges
  - [error] [nodes[<timer-trigger>]] Trigger has no outgoing edges
```

These are **expected** — the fixture intentionally exercises triggers in isolation (no stages, edges, or tasks). Both triggers lack outgoing edges. The point is that both outputs produce the same failure profile, proving downstream CLI commands see them as equivalent.

## Regenerating `cli-output/`

When the CLI version bumps:

```bash
WORK=$(mktemp -d)
cd "$WORK"
uip solution new --name TimerProbeSolution
cd TimerProbeSolution
uip maestro case init --name TimerProbe --no-git
cd TimerProbe
uip maestro case cases add \
  --name "TimerProbe" \
  --file caseplan.json \
  --description "Probe case exercising the timer trigger migration." \
  --output json
uip maestro case triggers add-timer caseplan.json \
  --time-cycle "R12/2026-04-21T22:00:00.000-07:00/PT10M" \
  --display-name "10-min Poll" \
  --output json

cp caseplan.json      <path-to-this-folder>/cli-output/caseplan.json
cp entry-points.json  <path-to-this-folder>/cli-output/entry-points.json
```

Then re-run `./diff.sh` to confirm the direct-JSON-write fixture still matches. If the diff fails, the CLI output shape changed — update `json-write-output/*` and [`plugins/triggers/timer/impl-json.md`](../../../skills/uipath-case-management/references/plugins/triggers/timer/impl-json.md) to reflect the new spec.

## Regenerating `json-write-output/`

Follow the JSON Recipe in [`plugins/triggers/timer/impl-json.md`](../../../skills/uipath-case-management/references/plugins/triggers/timer/impl-json.md). The trigger IDs in the current fixture are hand-picked to be distinct from `cli-output/` — they exercise the normalizer in `diff.sh`:

- CLI: `trigger_Q3mNp7` + UUIDs `11111...` / `22222...`
- JSON-write: `trigger_K8fLr2` + UUIDs `aaaa...` / `bbbb...`

Both normalize to `trigger_10minPoll` with `uniqueId: "UUID"`.

## Current status

Captured against CLI version `0.1.21`. Key observations from this run:

- `root.version: "v16"` — same as the stages fixture; installed CLI binary is behind the `~/Documents/cli/` source tree that currently writes `v16` as well.
- `root.data: {}` — empty on a fresh case; `intsvcActivityConfig` / `uipath.variables` / `uipath.bindings` appear only after their respective plugins run.
- `root.description` is emitted when `--description` is passed to `cases add`.
- Initial `trigger_1` from `cases add` is minimal: no `style`, `measured`, `width`/`height`, or `data.parentElement`. Studio Web hydrates missing fields on load.
- Secondary timer trigger appended (not prepended) — `triggers add-timer` calls `schema.nodes.push(node)`. Position `{x: -100, y: 140}` because `trigger_1` sits at `y: 0` and `TRIGGER_Y_STEP = 140`.
- `entry-points.json` has two entries — one seeded by `uip case init` for `trigger_1`, one appended by `triggers add-timer`. `uniqueId` is `crypto.randomUUID()` per entry; `filePath` embeds the trigger id after `#`.
