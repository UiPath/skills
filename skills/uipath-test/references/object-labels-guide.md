# Object Labels — tag metadata on test entities

Load this when the task adds, gets, or removes **object labels** on Test Manager entities (`uip tm objectlabel …`). Command surface: `uip tm objectlabel <list|get|add|remove> --help`.

## Anti-patterns

1. **Never pass a label row's `Id` as `--object-id` / `--object-ids`.** `get` returns rows with both `Id` (the label assignment) and `ObjectId` (the labeled entity). These flags take the entity's UUID: `ObjectId`, or the `Id` from `uip tm testcases list`, `testsets list`, `requirements list`, `executions list`, or `testcaselog list`. A label id matches no object.
2. **Never use `add --remove-other-labels` to drop specific labels.** It deletes every non-system label not in `--labels`, including hidden internal labels that Studio package links, Insights and Heatmap rely on. `get` and `list` do not show them, so the loss is invisible. Use it only when the user explicitly asks to replace the label set; otherwise use `remove --labels`.
