---
direct-json: supported
---

# case (root) — JSON Implementation

Authoritative when the matrix in [`case-editing-operations.md`](../../case-editing-operations.md) lists `case = JSON`. Cross-cutting direct-JSON rules live in [`case-editing-operations-json.md`](../../case-editing-operations-json.md). For the CLI fallback, see [`impl-cli.md`](impl-cli.md).

## Purpose

Create `caseplan.json` from scratch as a pure skeleton — `root` definition plus empty `nodes: []` and `edges: []` arrays. Runs exactly once per project as T01 in every `tasks.md`. Solution and project scaffolding (`uip solution new`, `uip maestro case init`, `uip solution project add`) remain CLI — see [`impl-cli.md`](impl-cli.md) § Prerequisites.

**No trigger emitted at T01.** The primary trigger is created by the triggers plugin at T02 — either via direct JSON write (when migrated) or `uip maestro case triggers add-<manual|timer|event>` (current CLI path). This is a deliberate divergence from CLI `cases add`, which always emits a default `trigger_1` node.

## Scope

**Add only.** `cases edit` is out of scope for this recipe and stays on the CLI path. Phase 2 always regenerates `caseplan.json` from scratch after approval of `tasks.md`, so the edit code-path is not exercised at runtime.

## Input spec (from `tasks.md`)

| Field | Required | Notes |
|---|---|---|
| `file` | yes | Target path. Literal filename MUST be `caseplan.json`. |
| `name` | yes | Human-readable case name. |
| `case-identifier` | no | Defaults to `name`. |
| `identifier-type` | no | `constant` \| `external`. Defaults to `constant`. |
| `case-app-enabled` | no | Boolean. Defaults to `false`. |
| `description` | no | Defaults to empty string. Always emitted (see Known CLI divergences). |

See [`planning.md`](planning.md) for how these fields are sourced from `sdd.md`.

## Pre-write checks

1. **Scaffolding complete.** The target directory must already contain `project.uiproj` + `package-descriptor.json` from a successful `uip maestro case init` run. If not, halt and run [`impl-cli.md`](impl-cli.md) § Prerequisites first.
2. **Collision behavior: overwrite.** If `caseplan.json` already exists, overwrite it. When the file is absent, create it. Skill Phase 2 re-runs regenerate `tasks.md` from scratch per SKILL.md Rule #8, so a collision here means a genuine re-run and overwriting is correct. This diverges from CLI `cases add`, which refuses when the file exists — see Known CLI divergences.

## ID generation

- `root.id` is the literal string `"root"` — **not** a generated shortId. Divergent from every other plugin.
- **No trigger ID emitted at T01.** The triggers plugin owns primary-trigger creation at T02.

Record in `id-map.json` for downstream cross-reference:

```json
{
  "T01": { "kind": "case", "id": "root" }
}
```

## Recipe — Skeleton (no trigger)

Pure skeleton: `root` definition, empty `nodes: []`, empty `edges: []`. The primary trigger is the triggers plugin's responsibility at T02.

### Minimal variant (no description)

When `description` is absent in the T01 input, emit `description: ""` (always-emit; see Known CLI divergences).

```json
{
    "root": {
        "id": "root",
        "name": "<name>",
        "type": "case-management:root",
        "caseIdentifier": "<case-identifier — defaults to <name>>",
        "caseAppEnabled": <true|false — defaults to false>,
        "caseIdentifierType": "<constant|external — defaults to constant>",
        "version": "v17",
        "publishVersion": 2,
        "data": {
            "intsvcActivityConfig": "v2",
            "uipath": {
                "variables": {
                    "inputOutputs": []
                },
                "bindings": []
            }
        },
        "description": ""
    },
    "nodes": [],
    "edges": []
}
```

### With description

Same as above with `description` value populated from sdd.md:

```json
{
    "root": {
        "id": "root",
        "name": "<name>",
        "type": "case-management:root",
        "caseIdentifier": "<case-identifier>",
        "caseAppEnabled": <true|false>,
        "caseIdentifierType": "<constant|external>",
        "version": "v17",
        "publishVersion": 2,
        "data": {
            "intsvcActivityConfig": "v2",
            "uipath": {
                "variables": {
                    "inputOutputs": []
                },
                "bindings": []
            }
        },
        "description": "<description>"
    },
    "nodes": [],
    "edges": []
}
```

## Formatting

- Indent: 4 spaces.
- Key order (root): `id, name, type, caseIdentifier, caseAppEnabled, caseIdentifierType, version, publishVersion, data, description`.
- Trailing newline: single `\n` at end of file.

Use the Write tool. File did not exist before — Edit does not apply.

## Post-write validation

Cheap sanity checks only — full validation runs after all plugins are done, per SKILL.md Rule #20.

1. **File parses.** `JSON.parse(readFile('caseplan.json'))` succeeds.
2. **Root shape.**
   - `root.id === "root"`
   - `root.type === "case-management:root"`
   - `root.version === "v17"`
   - `root.publishVersion === 2`
   - `root.data.intsvcActivityConfig === "v2"`
   - `root.data.uipath.variables.inputOutputs` is an array (empty at T01)
   - `root.data.uipath.bindings` is an array (empty at T01)
3. **Empty node/edge arrays.**
   - `nodes` is an array of length 0
   - `edges` is an array of length 0

If any check fails, halt and report — do not proceed to downstream plugins.

**Do NOT run `uip maestro case validate` here.** A case-only caseplan will fail validation by design (no stage nodes, trigger has no outgoing edges). Validation runs once after the full build per Rule #20.

## Known CLI divergences

Direct-JSON-write is a superset of the CLI's `cases add`. The divergences below are deliberate.

- **No trigger at T01.** CLI `cases add` emits a hard-coded initial Trigger node `{ id: "trigger_1", ..., data: { label: "Trigger 1" } }`. The JSON recipe emits `nodes: []`. Primary-trigger creation is the triggers plugin's responsibility at T02 (via `uip maestro case triggers add-<type>` today; direct-JSON-write once the triggers plugin migrates). A structural comparison between the two shapes converges after stripping `trigger_1` from the CLI side.
   - **Side effect on `entry-points.json`.** The scaffold file `<ProjectName>/entry-points.json` written by `uip maestro case init` hard-codes `filePath: "/content/caseplan.json.bpmn#trigger_1"` — that stale reference persists until the triggers plugin writes a primary trigger whose ID is `trigger_1`, or until a future milestone reconciles `entry-points.json` management. Single-trigger cases using the current CLI triggers plugin produce a random `trigger_<6>` ID that does NOT match the scaffold reference — accept the dangling entry until the triggers plugin migration addresses it.
- **`root.description` is always emitted.** `cases add` omits the `description` key entirely when `--description` is not passed, and emits it at the root level (sibling of `data`) when passed. The JSON recipe always writes `"description": "<value>"` (empty string when sdd.md has no description) so downstream consumers read a consistent shape.
- **Collision behavior.** CLI `cases add` fails with `"File already exists: <file>. Use 'cases edit' to modify it."` when `caseplan.json` already exists. Direct-JSON-write overwrites unconditionally — and creates the file if absent. This is intentional — Phase 2 re-runs regenerate the full file from scratch after re-approval of `tasks.md` (SKILL.md Rule #8). The CLI's refuse-on-exist behavior assumed a `cases edit` follow-up that direct-JSON-write does not need.
- **`description` placement.** Both CLI and JSON place `root.description` at the root level (sibling of `data`), NOT inside `root.data`. The JSON recipe matches CLI placement exactly — only the always-emit behavior differs.
- **Pre-populated `root.data`.** CLI 0.3.4 emits `root.data.intsvcActivityConfig: "v2"` and `root.data.uipath.variables.inputOutputs: [] / bindings: []` on a fresh `cases add`. The JSON recipe matches this shape. Downstream plugins (notably `variables/global-vars`) append to those structures — do not overwrite them at T01.

## Compatibility

Captured against CLI version `0.3.4`.

- [x] **Structural equivalence:** direct-JSON-write skeleton (`root` + `nodes: []` + `edges: []`) matches the CLI `cases add` output after stripping the CLI-side `trigger_1` node and normalizing the `description: ""` divergence.
- [x] **Validation:** JSON-write output produces a known-invalid failure profile (`no trigger node` + `no stage nodes`). Different from CLI's profile (`no stage nodes` + `trigger has no outgoing edges`) because CLI emits `trigger_1` and JSON does not. Both are expected-invalid for a case-only caseplan; validation at this boundary is skipped per SKILL.md Rule #20.
- [ ] **Downstream CLI trigger append:** `uip maestro case triggers add-manual` on a direct-JSON-written skeleton succeeds — exercised separately; verified in the `entry-points.json` coupling note above.
- [ ] **Downstream CLI mutation append:** `uip maestro case stages add` on a direct-JSON-written skeleton caseplan succeeds — not yet exercised.
- [ ] **Round-trip:** direct-JSON-write → `uip maestro case cases edit` accepts the file → subsequent mutations succeed — not yet exercised.
- [ ] **Studio Web render:** `uip solution upload` and visual confirmation — not yet exercised.
