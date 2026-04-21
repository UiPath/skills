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
| `diff.sh` | Normalizes the `description: ""` divergence, then diffs both variants; passes if structurally equivalent |

## Running the diff

```bash
./diff.sh
```

Exit 0 on equivalence; non-zero with a unified diff otherwise. Requires `jq` and `diff`.

## Validation parity

Both `cli-output-minimal.json` and `json-write-output-minimal.json` produce the same failure profile from `uip maestro case validate`:

```
Found 2 error(s) and 0 warning(s):
  - [error] [nodes] The case definition has no stage nodes
  - [error] [nodes[trigger_1]] Trigger "Trigger 1" has no outgoing edges
```

These are **expected** — the fixture intentionally exercises the root case in isolation (no stages, edges, tasks). The point is that both outputs produce the same failure profile, proving downstream CLI commands see them as equivalent.

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
- Initial Trigger is hard-coded `{ id: "trigger_1", position: {x: 0, y: 0}, data: { label: "Trigger 1" } }` — no `style`, `measured`, `parentElement`, or `uipath.serviceType`. This differs from secondary triggers added via `triggers add-manual`.
- **`root.description` divergence.** The direct-JSON-write always emits `description: <value>` (empty string when sdd.md has no description). The CLI omits the key entirely in the minimal case. `diff.sh` strips `description: ""` from both sides so the golden diff still asserts structural equivalence. Non-empty descriptions are left untouched.
- **Collision behavior divergence.** CLI `cases add` refuses to run when `caseplan.json` already exists (routes to `cases edit`). Direct-JSON-write overwrites unconditionally. Not exercised by this fixture; documented in [`plugins/case/impl-json.md` § Known CLI divergences](../../../skills/uipath-case-management/references/plugins/case/impl-json.md#known-cli-divergences).
