---
direct-json: supported
---

# case (root) — JSON Implementation

Authoritative when the matrix in [`case-editing-operations.md`](../../case-editing-operations.md) lists `case = JSON`. Cross-cutting direct-JSON rules live in [`case-editing-operations-json.md`](../../case-editing-operations-json.md). For the CLI fallback, see [`impl-cli.md`](impl-cli.md).

## Purpose

Create `caseplan.json` from scratch with the root case definition and the hard-coded initial Trigger node. Runs exactly once per project as T01 in every `tasks.md`. Solution and project scaffolding (`uip solution new`, `uip maestro case init`, `uip solution project add`) remain CLI — see [`impl-cli.md`](impl-cli.md) § Prerequisites.

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
2. **`caseplan.json` does not exist.** If the file exists, overwrite is permitted (direct-JSON-write collision behavior; see Known CLI divergences) — but only after the user has re-approved `tasks.md`. Runtime code path: re-runs regenerate `tasks.md` from scratch per SKILL.md Rule #8, so a collision here means a genuine re-run and overwriting is correct.

## ID generation

- `root.id` is the literal string `"root"` — **not** a generated shortId. Divergent from every other plugin.
- Initial Trigger `id` is the literal string `"trigger_1"`.

Record in `id-map.json` for downstream cross-reference:

```json
{
  "T01": "root",
  "T01.trigger": "trigger_1"
}
```

Edges plugin resolves `"Trigger"` / `"Trigger 1"` / the sdd.md's trigger label to `trigger_1` via this map.

## Recipe — Minimal variant

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
    "nodes": [
        {
            "id": "trigger_1",
            "type": "case-management:Trigger",
            "position": {
                "x": 0,
                "y": 0
            },
            "data": {
                "label": "Trigger 1"
            }
        }
    ],
    "edges": []
}
```

## Recipe — With description

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
    "nodes": [
        {
            "id": "trigger_1",
            "type": "case-management:Trigger",
            "position": {
                "x": 0,
                "y": 0
            },
            "data": {
                "label": "Trigger 1"
            }
        }
    ],
    "edges": []
}
```

## Formatting

- Indent: 4 spaces.
- Key order (root): `id, name, type, caseIdentifier, caseAppEnabled, caseIdentifierType, version, publishVersion, data, description`.
- Key order (nodes[0]): `id, type, position, data`.
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
3. **Initial trigger present.**
   - `nodes[0].id === "trigger_1"`
   - `nodes[0].type === "case-management:Trigger"`

If any check fails, halt and report — do not proceed to downstream plugins.

**Do NOT run `uip maestro case validate` here.** A case-only caseplan will fail validation by design (no stage nodes, trigger has no outgoing edges). Validation runs once after the full build per Rule #20.

## Known CLI divergences

Direct-JSON-write is a superset of the CLI's `cases add`. The divergences below are deliberate.

- **`root.description` is always emitted.** `cases add` omits the `description` key entirely when `--description` is not passed, and emits it at the root level (sibling of `data`) when passed. The JSON recipe always writes `"description": "<value>"` (empty string when sdd.md has no description) so downstream consumers read a consistent shape. The golden-diff normalizer in [`docs/uipath-case-management/migration-fixtures/case/diff.sh`](../../../../../docs/uipath-case-management/migration-fixtures/case/diff.sh) strips `description: ""` from both sides so equivalence still holds.
- **Collision behavior.** CLI `cases add` fails with `"File already exists: <file>. Use 'cases edit' to modify it."` when `caseplan.json` already exists. Direct-JSON-write overwrites unconditionally. This is intentional — Phase 2 re-runs regenerate the full file from scratch after re-approval of `tasks.md` (SKILL.md Rule #8). The CLI's refuse-on-exist behavior assumed a `cases edit` follow-up that direct-JSON-write does not need.
- **`description` placement.** Both CLI and JSON place `root.description` at the root level (sibling of `data`), NOT inside `root.data`. The JSON recipe matches CLI placement exactly — only the always-emit behavior differs.
- **Pre-populated `root.data`.** CLI 0.3.4 emits `root.data.intsvcActivityConfig: "v2"` and `root.data.uipath.variables.inputOutputs: [] / bindings: []` on a fresh `cases add`. The JSON recipe matches this shape. Downstream plugins (notably `variables/global-vars`) append to those structures — do not overwrite them at T01.

## Compatibility

Captured against CLI version `0.3.4`. See [`docs/uipath-case-management/migration-fixtures/case/`](../../../../../docs/uipath-case-management/migration-fixtures/case/) for fixtures.

- [x] **Golden diff (minimal):** normalized `json-write-output-minimal.json` matches `cli-output-minimal.json` after stripping `description: ""` — `diff.sh` passes
- [x] **Golden diff (full flags):** normalized `json-write-output-full.json` matches `cli-output-full.json` — `diff.sh` passes
- [x] **Validation parity:** both outputs produce the same 2 errors + 0 warnings from `uip maestro case validate` (expected failure profile for a case-only caseplan: no stage nodes + trigger has no outgoing edges)
- [ ] **Downstream CLI mutation append:** `uip maestro case stages add` on a direct-JSON-written caseplan succeeds — not yet exercised (requires stages plugin run; already covered by stages pilot against CLI output, equivalence holds by fixture)
- [ ] **Round-trip:** direct-JSON-write → `uip maestro case cases edit` accepts the file → subsequent mutations succeed — not yet exercised
- [ ] **Studio Web render:** `uip solution upload` and visual confirmation — not yet exercised
