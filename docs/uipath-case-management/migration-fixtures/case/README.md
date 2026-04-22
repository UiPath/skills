# Case (root) Golden Fixtures

Compatibility fixture for the `case` plugin direct-JSON-write migration. Asserts that JSON emitted by the direct-write path is structurally equivalent to JSON produced by `uip maestro case cases add`.

> **Temporary — developer verification only.** These fixtures live outside the skill on purpose: they exist to verify migration correctness during the CLI → JSON shift, and will be removed once every plugin has migrated. Runtime agents do not load them.

## Files

| File | Purpose |
|---|---|
| `input.sdd-fragment.md` | Minimal + full-flag sdd fragments exercising only the `case` plugin |
| `cli-output-minimal.json` | Captured from `uip maestro case cases add --name MinimalProbe --file caseplan.json` (no optional flags) — CLI 0.3.4 |
| `cli-output-full.json` | Captured from `uip maestro case cases add` with every optional flag set — CLI 0.3.4 |
| `json-write-output-minimal.json` | Hand-written to match the direct-JSON-write spec in [`plugins/case/impl-json.md`](../../../skills/uipath-case-management/references/plugins/case/impl-json.md) for the minimal variant |
| `json-write-output-full.json` | Same spec, full-flags variant |
| `diff.sh` | Normalizes the `description: ""` divergence + strips the CLI-emitted default `trigger_1` node, then diffs both variants; passes if structurally equivalent |

## Running the diff

```bash
./diff.sh
```

Exit 0 on equivalence; non-zero with a unified diff otherwise. Requires `jq` and `diff`.

## Validation profiles (diverge by design)

Because the JSON recipe emits a pure skeleton (`nodes: []`) while CLI `cases add` emits a hard-coded `trigger_1` node, the two outputs produce slightly different failure profiles from `uip maestro case validate`:

CLI output:
```
Found 2 error(s) and 0 warning(s):
  - [error] [nodes] The case definition has no stage nodes
  - [error] [nodes[trigger_1]] Trigger "Trigger 1" has no outgoing edges
```

JSON-write output:
```
Found 2 error(s) and 0 warning(s):
  - [error] [nodes] The case definition has no trigger node
  - [error] [nodes] The case definition has no stage nodes
```

Both are **expected-invalid** — the fixture intentionally exercises the root case in isolation (no triggers, stages, edges, tasks). Case-plugin validation is skipped at the T01 boundary per SKILL.md Rule #20; both profiles converge once the triggers plugin runs at T02 and the stages plugin at Step 7.

## Regenerating `cli-output-*.json`

When the CLI version bumps:

```bash
WORK=$(mktemp -d)
cd "$WORK"
uip solution new CaseProbeSolution
cd CaseProbeSolution
uip maestro case init CaseProbeProject
uip solution project add CaseProbeProject CaseProbeSolution.uipx
cd CaseProbeProject

# Minimal variant
uip maestro case cases add --name "MinimalProbe" --file caseplan.json --output json
cp caseplan.json <path-to-this-folder>/cli-output-minimal.json

# Full-flags variant (fresh scaffolding)
rm caseplan.json
uip maestro case cases add \
  --name "FullProbe" \
  --file caseplan.json \
  --case-identifier "FP-123" \
  --identifier-type external \
  --case-app-enabled \
  --description "Full flags test" \
  --output json
cp caseplan.json <path-to-this-folder>/cli-output-full.json
```

Re-run `./diff.sh` to confirm both variants still match. If the diff fails, the CLI output shape changed — update the `json-write-output-*.json` fixtures and [`plugins/case/impl-json.md`](../../../skills/uipath-case-management/references/plugins/case/impl-json.md) to reflect the new spec.

## Regenerating `json-write-output-*.json`

Follow the JSON Recipe in [`plugins/case/impl-json.md`](../../../skills/uipath-case-management/references/plugins/case/impl-json.md).

## Current status

Captured against CLI version `0.3.4`. Key observations from this run:

- `root.id` is the literal string `"root"` — **not** a generated shortId. Different from every other plugin (Stage, Edge, Task, etc. use random-suffix IDs).
- `root.version: "v17"` and `root.publishVersion: 2` (0.3.4 bumped from `v16`/absent in 0.1.21, matching design-doc §12a).
- `root.data` is pre-populated: `intsvcActivityConfig: "v2"`, `uipath.variables.inputOutputs: []`, `uipath.bindings: []`. Downstream plugins (notably `variables/global-vars`) append to those structures.
- `root.description` key is **omitted** by the CLI when `--description` is absent. Present (at root level, sibling of `data`) when `--description` is passed.
- CLI `cases add` emits a hard-coded initial Trigger node `{ id: "trigger_1", position: {x: 0, y: 0}, data: { label: "Trigger 1" } }` — no `style`, `measured`, `parentElement`, or `uipath.serviceType`. This differs from secondary triggers added via `triggers add-manual`.
- **`root.description` divergence.** The direct-JSON-write always emits `description: <value>` (empty string when sdd.md has no description). The CLI omits the key entirely in the minimal case. `diff.sh` strips `description: ""` from both sides so the golden diff still asserts structural equivalence. Non-empty descriptions are left untouched.
- **Trigger emission divergence.** The direct-JSON-write emits a pure skeleton with `nodes: []` — the primary trigger is the triggers plugin's responsibility at T02. CLI `cases add` always emits `trigger_1`. `diff.sh` strips `trigger_1` from the CLI side so the golden diff asserts skeleton-shape equivalence. Documented in [`plugins/case/impl-json.md` § Known CLI divergences](../../../skills/uipath-case-management/references/plugins/case/impl-json.md#known-cli-divergences) — includes the `entry-points.json` coupling note.
- **Collision behavior divergence.** CLI `cases add` refuses to run when `caseplan.json` already exists (routes to `cases edit`). Direct-JSON-write overwrites unconditionally, and creates the file when absent. Not exercised by this fixture; documented in the same section.
