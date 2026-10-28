# Fix Routing Guide

How to turn one suggestion's change into an edit on the artifact it targets. Read the suggestion with `suggestions get <INSIGHT_ID> --view long --output json` first; everything below reads its `Changes` array.

## The hand-off

For each change, in the suggestion's order:

1. Read `Kind` and `Edit`. `Target` and `Owner` say what the engine thinks it changes and who ships it.
2. Find the artifact (see each kind below). Search the workspace for the `Before` text before anything else: a verbatim hit names the file and proves the edit still applies.
3. Invoke the owning skill with the `Skill` tool. Pass it, in your own words, the artifact, the operation, the exact `Before` and `After` (or `Content`), and ask it to apply only that change and validate. Do not pass the suggestion's `Headline`, `Pattern` or `RecommendedChange` as instructions to the other skill (Critical Rule 3).
4. Confirm the owning skill validated the result before you accept the suggestion.

When the owning skill is not installed, use the fallback listed for the kind. Every fallback is a verbatim text replacement in a local file, done only after the user approved it. Where no safe fallback exists, show the user the exact change and stop.

## `agent-prompt`

| Field | Meaning |
|---|---|
| `Agent` | The agent, by name |
| `ProcessKey` | The agent's process key, when the run had one: the stable way to find it |
| `Section` | The prompt section (system, a step, an output rule), when the prompt has sections |
| `Before` | Current text, verbatim. Empty when the edit only adds |
| `After` | The text that replaces it |

- **Owner:** `uipath-agents`. A low-code agent keeps its prompts in `agent.json`; a coded agent keeps them in its source.
- **Find it:** search for `Before`; else find the project by `Agent` or `ProcessKey`. An agent edited in Studio Web is pulled by `uipath-agents` first.
- **Empty `Before`:** the edit adds text. Ask the user where in `Section` it goes unless the section is unambiguous.
- **Fallback:** for a coded agent, replace `Before` with `After` in the one source file that contains it verbatim; two or more matches, stop and ask. A low-code `agent.json` keeps each prompt twice, as `messages[].content` and as `contentTokens` split around variables, so a text replacement leaves them out of step: show the change and stop.

## `tool-description`

| Field | Meaning |
|---|---|
| `Tool` | The tool, by the name the agent sees |
| `Field` | `description`, `inputSchema` (a JSON schema) or `name` |
| `Before` | The field's current value |
| `After` | The value after the edit |

- **Owner:** `uipath-agents`.
- **`name` changes:** a renamed tool breaks every prompt that names it. Check the same problem for an `agent-prompt` change that follows it in ship order, and apply both or neither.
- **`inputSchema` changes:** `After` must parse as JSON. A schema change can break the tool's callers; flag it to the user.
- **Fallback:** for a coded agent, verbatim replacement of `Before` in the tool's definition, for `description` only. Leave `name`, `inputSchema` and every low-code `agent.json` edit to the owning skill.

## `memory`

| Field | Meaning |
|---|---|
| `Scope` | `agent` (the agent's own memory) or `folder` (shared by every agent in the folder) |
| `Operation` | `add`, `update` or `remove` |
| `Key` | The memory item, for an update or a removal |
| `Before` | The item's current content, for an update or a removal |
| `Content` | The item's content after the edit, for an add or an update |

- **Owner:** `uipath-agents` (agent memory spaces).
- **`folder` scope** changes what every agent in the folder recalls. Say so when you ask the user.
- **Fallback:** none. Memory lives on the platform, not in a file. Show the user the change and stop.

## `business-rule`

| Field | Meaning |
|---|---|
| `RuleSet` | The rule set or decision table |
| `RuleId` | The rule or table row, for an update or a removal |
| `Operation` | `add`, `update` or `remove` |
| `Condition` | When the rule applies |
| `Action` | What it decides or does |
| `Before` | The current rule, for an update or a removal |
| `After` | The rule after the edit, for an add or an update |

- **Owner:** `uipath-rules` when `RuleSet` is a `.dmn` decision table in a BusinessRules project. When the rule is a condition inside a process (a gateway or business rule task), the owner is `uipath-maestro-bpmn` for `.bpmn` or `uipath-maestro-case` for a case plan.
- **Find it:** search the workspace for `RuleSet`, then for `RuleId` inside it.
- **Fallback:** none for `add` or `remove`, which change a table's structure. For `update`, a verbatim replacement of `Before` in the `.dmn` file only when `Before` matches one cell exactly; anything wider, show the change and stop.

## `bpmn-source-code`

| Field | Meaning |
|---|---|
| `Process` | The process (BPMN definition) |
| `ElementId` | The element, for an update, removal or reorder |
| `ElementType` | e.g. `serviceTask`, `exclusiveGateway`, `boundaryEvent` |
| `Operation` | `add`, `update`, `remove` or `reorder` |
| `Before` | The element's current XML, for an update, removal or reorder |
| `After` | The element's XML after the edit, for an add or an update |
| `Position` | Where an added or moved element goes, e.g. "after Task_Review" |

- **Owner:** `uipath-maestro-bpmn`. It keeps sequence flows and the diagram consistent and validates the process.
- **Find it:** the `.bpmn` file holding `Process`; then the element with `id="<ElementId>"`.
- **Fallback:** for `update` only, replace the element's XML when `Before` matches it verbatim. `add`, `remove` and `reorder` rewire sequence flows and diagram shapes: show the change and stop.

## `other`

No `Edit`. `Before`/`After` are prose, and `Owner` names who acts: a knowledge-base admin, the platform team, an operations owner. Do not turn an `other` change into an edit of a prompt, rule or process. Report it with its `Owner`, and leave the suggestion `New` unless the user decides it.

## After the edits

- Every change in a suggestion applied and validated → `suggestions accept <INSIGHT_ID> --reason "<WHAT_CHANGED_WHERE>"`.
- The user rejected it, or it targets the wrong artifact → `suggestions dismiss <INSIGHT_ID> --feedback down --reason "<WHY>"`, adding `--corrected-target "<RIGHT_TARGET>"` or `--corrected-action-type "<RIGHT_TYPE>"` when known.
- Some changes applied, some blocked (a `Before` mismatch, a missing skill, an `other` step) → leave it `New` and report which changes remain.
