<!--
COPY THIS FILE TO: references/author/references/plugins/<PLUGIN_NAME>/impl.md

Implementation half of a plugin pair. Answers "how do I author, validate and
fix this node?" — never "should I use it" (that is planning.md).

Section contract, derived from the existing plugins:
  REQUIRED  Registry Validation   — every plugin has it; never hand-write definitions[]
  REQUIRED  Debug                 — every plugin has it; error/cause/fix table
  COMMON    Adding / Editing
  COMMON    JSON Structure        — may be per-node "### Node JSON — <name>" blocks
  COMMON    Accessing Output
  OPTIONAL  Prerequisite — <scaffold step>, Configure <file>, Validate and Pack,
            Repair Recipes, What NOT to Do

Delete every instructional comment (including this block) once filled in.

Rules that bite here:
- Every CLI command that gets parsed carries `--output json`.
- Placeholders are `<UPPER_SNAKE_CASE>` in angle brackets.
- Unix shell syntax only; no Windows commands.
- `bash .maintenance/check-uip-commands.sh` rejects verbs the CLI does not ship —
  run it, do not trust memory for command spelling.

Before opening a PR, from the skill root:
  bash .maintenance/check-plugin-registration.sh   # index rows this plugin still needs
  bash .maintenance/check-all.sh                   # links, anchors, depth, pairs, commands
-->

# <NODE_FAMILY_NAME> — Implementation

<!-- One paragraph: what this file covers. When fundamentals live in a sibling
     plugin, say which sections of it to open and when — so the reader does not
     load that file for the common case:
     "<X> mechanics are identical to [<other>/impl.md](../<other>/impl.md) — the
      deltas below are complete on their own; open that file only when <case>." -->

## Prerequisite — <SCAFFOLD_STEP>

<!-- Delete this section when the node needs no scaffolding. Otherwise: the one
     command, then what the author must record from its output. -->

```bash
uip <command> "<PROJECT_DIR>" --output json
```

<!-- Name the field to carry forward and where it must match, e.g.
     "**Record the returned `ProjectId`** — `inputs.source` must match it exactly." -->

## Registry Validation

<!-- Read definitions during Phase 2 to copy into definitions[]. Fetch only the
     types the topology uses. Say whether the types ship in the CLI's bundled
     registry (answers offline, no login) or need `registry pull`. -->

```bash
uip maestro flow registry get <node.type> --output json
```

<!-- Call out the fields worth confirming (ports, model.source hoisting,
     model.serviceType / model.version) and end with the rule: -->

Never hand-write `definitions[]` entries — copy them from `registry get`.

<!-- When `registry get` succeeding does NOT prove the tenant can run the node
     (enablement, licensing, provisioned resources), say so explicitly here and
     tell the reader to raise it as an Open Question. -->

## Adding / Editing

<!-- Link the shared procedures rather than restating them: -->

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md).

<!-- State the ownership rule: is this node authored directly in the `.flow` JSON
     with Edit / Write, or is it a Flow CLI carve-out? Do not leave it implicit. -->

### <BINDING_OR_WIRING_RULE>

<!-- One subsection per rule an agent gets wrong: which node originates a value,
     which nodes must consume it, and the exact binding shape. -->

## JSON Structure

<!-- One fenced block per node type in the family. First block carries the full
     shape; later blocks may omit repeated scaffolding. Use real-looking ids. -->

```json
{
  "id": "<nodeId>",
  "type": "<node.type>",
  "typeVersion": "1.0",
  "display": { "label": "<Label>", "icon": "<icon>" },
  "inputs": {}
}
```

<!-- After each block, name which inputs are required and which are plain
     strings vs binding objects — that distinction is a frequent failure. -->

### Wire edges with Edit / Write

<!-- Source and target ports for each edge in the family's topology. -->

Edge object shape: [editing-operations-json.md § Add an edge](../../editing-operations-json.md#add-an-edge).

## Accessing Output

```javascript
// In a Script node after the node
const <name> = $vars.<nodeId>.output.<field>;
```

- `$vars.{nodeId}.output.<field>` — <what it carries>
- `$vars.{nodeId}.error` — error details if the node fails

## Validate and Pack

<!-- Delete unless this node family adds checks beyond the standard ones. -->

```bash
uip maestro flow format <FLOW_NAME>.flow --output json
uip maestro flow validate <FLOW_NAME>.flow --output json
```

<!-- What extra validation this family gets, and what pack does differently.
     Anything that fails only at deploy/runtime belongs in Debug, not here. -->

## Debug

<!-- Every observed failure mode. One row per error the agent will actually see;
     Error column = the literal message or rule id, not a paraphrase. Order:
     validate errors, then pack, then deploy/runtime. -->

| Error | Cause | Fix |
| --- | --- | --- |
| `<literal error text or rule id>` | <root cause> | <the exact repair, or the command that repairs it> |

## What NOT to Do

<!-- Delete unless there are real, expensive mistakes. Each bullet: the wrong
     move in bold, then why it is wrong and what is correct instead. Deprecated
     contracts an agent may have seen elsewhere belong here. -->

- **Do not <wrong move>** — <why; what to do instead>
