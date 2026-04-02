# <Category Name> Nodes

<!--
  AWAY TEAM CONTRIBUTION TEMPLATE

  Instructions:
  1. Copy this file to references/nodes/<category>.md (kebab-case, e.g., ixp.md)
  2. Fill in the Implementation and Debug sections below
  3. Add a summary row to planning-phase-architectural.md in the appropriate catalog section
  4. Submit a PR with both files
  5. Add your team to CODEOWNERS for this file

  The planning guide (host-owned) contains the summary the agent reads during
  Phase 1 planning. This file contains the implementation details and debug
  guidance the agent reads during Phase 2 and build steps.

  Keep it prescriptive — the audience is an AI coding agent, not a human.
  Use exact CLI commands, numbered steps, and tables.
-->

## Implementation

<!--
  How the agent configures and uses this node type in a flow.

  Include:
  - Node type pattern (e.g., `uipath.core.<category>.{key}`)
  - Service type and category values
  - How to discover the node via registry (`uip flow registry search/get`)
  - Required inputs, their types, and descriptions
  - Output variables and structure (`$vars.{nodeId}.output`, `$vars.{nodeId}.error`)
  - Ports (input/output port names for edge wiring)
  - JSON structure example for the node instance in the .flow file
  - Any connection/binding requirements
  - Category-specific CLI commands or configuration steps
  - Gotchas or non-obvious configuration steps
  - When to use a mock placeholder vs the real node
  - Which skill to use to create the resource if it doesn't exist yet
-->

## Debug

<!--
  Common errors and how to fix them.

  Include a table of errors:
  | Error | Cause | Fix |
  |---|---|---|

  Then add debug tips:
  - What to check first when this node type fails
  - Validation errors specific to this node type
  - Runtime errors and their causes
  - Known limitations
  - Differences between what `flow validate` catches vs what only appears at runtime
-->
