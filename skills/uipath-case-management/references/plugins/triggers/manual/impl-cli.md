# manual trigger — CLI Implementation

> **Not the default path.** `triggers/manual` is on the **JSON strategy** — see [`impl-json.md`](impl-json.md). Use this CLI doc only as the fallback when `uip maestro case triggers add-manual` is the only option (e.g., probing CLI output, regenerating goldens).

## CLI Command

```bash
uip maestro case triggers add-manual <file> \
  --display-name "<display-name>" \
  --description "<description>" \
  --output json
```

### Optional flags

| Flag | Notes |
|------|-------|
| `--display-name` | Auto-generated as `Trigger N` if omitted, where `N = existingTriggerCount + 1` (including the initial `trigger_1` from `cases add`). First secondary trigger therefore defaults to `"Trigger 2"`. |
| `--description` | Conditionally emitted — CLI writes `data.description` only when this flag is passed. |
| `--position "<x>,<y>"` | Explicit `x,y` coordinates. Omit to auto-compute (see Position below). |

## Example

```bash
uip maestro case triggers add-manual caseplan.json \
  --display-name "Start Manually" \
  --description "Operator kicks off a case from the portal" \
  --output json
```

## Position (auto-computed)

CLI counts every `case-management:Trigger` node in `schema.nodes` (including the initial `trigger_1` at `{x:0, y:0}`).

```text
existingTriggers = schema.nodes.filter(type == "case-management:Trigger")
if existingTriggers.length == 0:  position = { x: -100, y: 200 }
else:                             position = { x: -100, y: max(existingY) + 140 }
```

**In practice**, `cases add` always seeds `trigger_1` at y=0, so `existingTriggers.length >= 1` whenever `triggers add-manual` runs. The first secondary trigger therefore lands at **y=140** (`max(0) + 140`), not y=200. The y=200 branch is only reachable on a schema that has zero triggers, which does not occur via normal scaffolding.

## Resulting JSON Shape

> **Initial `trigger_1` vs secondary triggers are different shapes.**
>
> Initial trigger (from `uip maestro case cases add`):
> `{ id: "trigger_1", type, position: {x:0, y:0}, data: { label: "Trigger 1" } }` — no `style`, no `measured`, no `parentElement`, no `uipath` key.
>
> Secondary triggers (from `triggers add-manual` — this plugin) carry `style`, `measured`, `data.parentElement`, and a random `trigger_` + 6-char ID.

> **ID format.** `trigger_` + 6 random chars from `[A-Za-z0-9]` (e.g. `trigger_xY2mNp`).

Node appended to `caseplan.json.nodes` (CLI uses `.push()` — appends):

```json
{
  "id": "trigger_xY2mNp",
  "type": "case-management:Trigger",
  "position": { "x": -100, "y": 140 },
  "style": { "width": 96, "height": 96 },
  "measured": { "width": 96, "height": 96 },
  "data": {
    "parentElement": { "id": "root", "type": "case-management:root" },
    "label": "Start Manually",
    "description": "Operator kicks off a case from the portal"
  }
}
```

**Manual triggers do NOT emit `data.uipath`.** The `uipath` key (with `serviceType`) is only set by the `add-timer` and `add-event` branches of `triggers.ts`. A manual trigger is identified by the **absence** of `data.uipath`, not by `serviceType: "None"`.

## Sibling file — `entry-points.json`

`triggers add-manual` also appends to `entry-points.json` (sibling of `caseplan.json` in the project directory). This file must already exist — `uip maestro case init` creates it. Every trigger-add call fails hard if it's missing.

Entry appended to `entry-points.json.entryPoints`:

```json
{
  "filePath": "/content/caseplan.json.bpmn#trigger_xY2mNp",
  "uniqueId": "<crypto.randomUUID()>",
  "type": "CaseManagement",
  "input":  { "type": "object", "properties": {} },
  "output": { "type": "object", "properties": {} },
  "displayName": "Start Manually"
}
```

- `filePath` fragment = the new trigger's id.
- `displayName` = the trigger's `data.label` (falls back to trigger id if label absent — unusual for this plugin).
- Written with 4-space indent (note: `init.ts` writes the file with 2-space indent; `appendEntryPoint` in `triggers.ts` rewrites with 4-space — CLI is inconsistent with itself).

## Post-Add Validation

Capture `TriggerId` from `--output json`. Use it as the `--source` when adding an edge from the trigger to the first stage (via `uip maestro case edges add`).

Confirm:
- Node appended to `schema.nodes` with the expected `trigger_XXXXXX` id.
- `data.parentElement`, `style`, `measured` all present.
- `data.uipath` **absent** (manual triggers have no `uipath` key).
- Matching entry appended to `entry-points.json.entryPoints` with `filePath: /content/<basename>.bpmn#<triggerId>`.
