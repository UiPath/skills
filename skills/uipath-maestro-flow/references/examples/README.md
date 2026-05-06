# Flow Examples

This directory contains complete `.flow` files that can be copied into a
scaffolded Flow project and validated locally. Use them as known-good baselines
when building common patterns directly in JSON.

## Decision Branch

`decision-branch.flow` demonstrates:

- manual trigger
- script output captured in `$vars`
- decision node with `true` and `false` branches
- two branch-specific script nodes
- separate End nodes with workflow output mappings
- registry-derived definitions for every node type
- horizontal layout entries for every node

Validate the example before using it:

```bash
uip maestro flow validate skills/uipath-maestro-flow/references/examples/decision-branch.flow --output json
```

To use it as a starting point, scaffold a Flow project with
`uip maestro flow init`, replace the generated `<ProjectName>.flow` contents
with this file, then update the top-level `name` and any node labels or scripts.
Keep the `.flow` file extension; `uip maestro flow validate` rejects copied
examples that are renamed with a `.json` suffix.
