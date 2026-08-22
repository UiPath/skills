<!--
COPY THIS FILE TO: references/author/references/plugins/<PLUGIN_NAME>/planning.md

Planning half of a plugin pair. Answers "should I use this node, and what does
the architect write down?" — never "how do I author the JSON" (that is impl.md).

Section contract, derived from the existing plugins:
  REQUIRED  Node Type(s)          — one of: "Node Type" | "Node Types" | "Node Type Pattern"
  REQUIRED  When to Use
  REQUIRED  Ports
  COMMON    Output Variables      — omit only when the node emits nothing
  COMMON    Planning Annotation   — what the architect records in the plan
  OPTIONAL  Prerequisites / Scaffolding Prerequisite, Discovery, Topologies,
            Key Constraints / Key Properties / Key Inputs

Delete every instructional comment (including this block) once filled in.

Before opening a PR, from the skill root:
  bash .maintenance/check-plugin-registration.sh   # index rows this plugin still needs
  bash .maintenance/check-all.sh                   # links, anchors, depth, pairs, commands
-->

# <NODE_FAMILY_NAME> — Planning

<!-- One paragraph: what this node family does and the single sentence that
     decides whether a flow needs it. Name the centerpiece node type. -->

<!-- When this plugin builds on another plugin's fundamentals, say so here and
     link once, so the reader loads that file instead of you restating it:
     "For <topic> fundamentals, see [<other>/planning.md](../<other>/planning.md)
      — everything there applies. This plugin covers what <X> adds on top." -->

## Node Type<!-- or: Node Types / Node Type Pattern -->

<!-- Single node → prose + backticked type. Several → this table. -->

| Node Type | Role | When to Select |
| --- | --- | --- |
| `<node.type>` | <Trigger \| Agent \| Action> | <the one condition that selects it> |

<!-- State whether these are fixed OOTB types or a discovered/dynamic pattern.
     If discovery is needed, add a `## Discovery` section with the command. -->

## When to Use

<!-- The affirmative case in one or two sentences. -->

### <THIS_NODE> vs <CLOSEST_ALTERNATIVE>

<!-- Only when agents confuse this node with a sibling. Rows = situations,
     columns = the two candidates, cells = Yes/No + the reason. -->

| Situation | <THIS_NODE> | [<ALTERNATIVE>](../<other>/planning.md) |
| --- | --- | --- |
| <situation> | Yes | No — <why not> |

### When NOT to Use

- **<situation>** — use [<other-plugin>](../<other>/planning.md) instead
- **<situation>** — <why this node cannot serve it>

## Ports

| Port | Position | Direction | Use |
| --- | --- | --- | --- |
| `input` | left | target | Flow sequence input |
| `success` | right | source | Normal flow output |
| `error` | right | source | Implicit error port — see [Implicit error port on action nodes](../../../../shared/file-format.md#implicit-error-port-on-action-nodes) |

<!-- Triggers have no `input`. Agent nodes add bottom/top artifact ports
     (`tool`, `context`, `escalation`). Fold single-port plumbing nodes into
     one prose line rather than giving each its own table. -->

## Output Variables

- `$vars.{nodeId}.output.<field>` — <what it carries; link impl.md for the field shape>
- `$vars.{nodeId}.error` — error details (`code`, `message`, `detail`, `category`, `status`)

## Planning Annotation

<!-- What Phase 1 writes into the architectural plan. Placeholders for anything
     that only exists after a Phase 2 command runs. Anything the tenant must
     already provide and the CLI cannot verify → tell the reader to raise it as
     an Open Question rather than guessing. -->

- `<annotation-key>: <value>` — <what it pins down>
