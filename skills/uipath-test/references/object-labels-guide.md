# Object Labels — tag metadata on test entities

Load for adding, getting, or removing **object labels** on Test Manager entities. Run `uip tm objectlabel <list|get|add|remove> --help`.

## Anti-patterns

1. **Never pass a label row's `Id` as `--object-id` / `--object-ids`.** `get` returns `Id` (the label assignment) and `ObjectId` (the labeled entity); these flags require the entity UUID: `ObjectId`, or the `Id` from `uip tm testcases list`, `testsets list`, `requirements list`, `executions list`, or `testcaselog list`. A label id matches no object.
2. **Never use `add --remove-other-labels` to drop specific labels.** It deletes every non-system label not in `--labels`, including hidden internal labels used by Studio package links, Insights, and Heatmap; `get` and `list` do not show them, making the loss invisible. Use it only when the user explicitly asks to replace the label set; otherwise run `remove --labels`.