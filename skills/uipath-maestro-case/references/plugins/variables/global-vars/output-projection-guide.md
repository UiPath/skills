# Output Projection

Read this guide only when a task or connector-condition-rule output uses `->`, `=`, reassignment, or needs a Case-variable root companion. Do not load it for basic Variable/In/Out/InOut creation, trigger Pattern C or auto-emit, argument bridges, or a task/rule whose outputs are all ordinary spec/schema outputs.

The selected task or condition plugin remains the owner of its persisted output array and current resource/spec descriptor. This guide owns only the conditional projection dispatch.

## Task and rule ownership

| Owner | Output array | Descriptor source | Output `elementId` |
|---|---|---|---|
| Non-connector task | `task.data.outputs[]` | That task owner's current Step 0 `tasks describe` result | `<stageId>-<taskId>` for schema outputs and `->`; task `=` uses `root` |
| Connector task | `task.data.outputs[]` | The selected connector owner's persisted `case spec --input-details` CaseShape outputs | `<stageId>-<taskId>` for schema outputs and `->`; task `=` uses `root` |
| Stage-entry, stage-exit, or task-entry connector rule | `rule.uipath.outputs[]` | The selected condition/connector owner's persisted spec outputs | `<stageId>-<ruleId>` for every retained/projected rule output |
| Case-exit connector rule | `rule.uipath.outputs[]` under `metadata.caseExitRules[]` | The selected condition/connector owner's persisted spec outputs | `root-<ruleId>` for every retained/projected rule output |

The owner invokes this dispatch only after it has emitted/resolved its current descriptor-backed outputs and before its root-binding step. Do not reconstruct connector envelopes or replace owner-specific fields. A placeholder task with `data: {}` emits nothing. A connector-rule stub with absent or empty `uipath.outputs[]` is `SKIPPED`; it contributes no projection or companion until its connector resolves.

## Descriptor resolution and bare outputs

For each explicit `<source-path> -> <case-var>` row, resolve the path against that exact owner's current descriptor before selecting a shape:

1. Match the first path segment exactly to a top-level output, using its `source` without the leading `=` and then `name` as fallback.
2. Walk remaining dot segments exactly through the descriptor's normalized `body.properties`. The final match is the leaf descriptor. Array indexing is unsupported.
3. Emit the leaf display name when present, otherwise its exact final segment. Copy its `type` and type-refining attributes such as `options` verbatim. Never inherit a parent object's `body`, `jsonSchema`, `options`, or type onto a scalar leaf.
4. If a segment is missing, log `ERROR` and skip that binding; never fall back to the last parent.

An explicit operator is dispatched before comparing names. A bare schema-discovered item has no SDD operator and retains the ordinary auto-mint shape: `{name, type, id, var: id, value: id, source: <descriptor source>, target: "=<id>", elementId}` with no `originalVar`. The same shape is the fallback for an unreferenced top-level descriptor output. An explicit nested `->` consumes its top-level parent; do not also auto-mint that parent unless `tasks.md` contains a separate schema-discovered bare item. This prevents a nested leaf projection from creating an unrelated parent output.

## Extract reassignment

For `<source-path> -> <case-var>`, the target Case variable must already exist. Let `baseId = camelCase(final source segment)`, then allocate the independently owned source-side `id` against the complete [global uniqueness pool](impl-json.md#pool-composition-what-to-scan). Emit on the owner's output array:

```json
{ "name": "<resolved leaf name>", "type": "<resolved leaf type>",
  "id": "<allocated source id>", "var": "<target Case-variable id>",
  "originalVar": "<allocated source id>", "value": "<target Case-variable id>",
  "source": "=<source-path>", "target": "=<allocated source id>",
  "elementId": "<owner elementId>" }
```

Keep the SDD left side verbatim after the `=` prefix. `type` is required. `originalVar` is load-bearing: it mirrors `id`, marks reassignment, and prevents frontend root mirroring from replacing or duplicating the existing companion. Copy other refining fields from the resolved descriptor only.

The global-variable owner emits or preserves the target companion in top-level `variables.inputOutputs[]` with `id: <target Case-variable id>`, `elementId: "root"`, and `custom: true`; the task/rule output points to it through `var`/`value`. Out arguments always have that companion, even without a Default.

### Equal-name controlled alias

`greeting -> greeting` is still an explicit reassign shape, never bare. During source-side allocation only, exclude the one matching root companion whose `id` equals the target and whose `elementId` is `root`. Exclude nothing else from the global pool.

- With no unrelated owner, emit `id == var == value == originalVar == "greeting"`, `source: "=greeting"`, and `target: "=greeting"`; preserve the companion.
- After a real unrelated collision, suffix only the independently owned source slot: `id`, `originalVar`, and `target` become `greeting2`/`=greeting2`; `var`, `value`, and the companion remain `greeting`.

Never suffix the Case-variable pointer or companion. Apply the same rule to task and connector-rule outputs.

## Custom assignment

For `<case-var> = <expression>`, the target Case variable must already exist. This is a custom write, not response extraction. Normalize once:

- Strip SDD delimiter quotes from a quoted string (`status = "InReview"` stores `InReview`, not an escaped quoted payload).
- Preserve native literal values and canonical `=vars...` or `=js:...` expressions.
- Rewrite `=metadata.X` to `=js:metadata.X`.
- Store the same normalized value in `value` and `source`; keep the SDD-natural row in `tasks.md`.

For a task, emit:

```json
{ "name": "<case-var>", "custom": true,
  "var": "<target Case-variable id>",
  "value": "<normalized value>", "source": "<same normalized value>",
  "target": "", "body": "", "type": "<Case-variable type>",
  "elementId": "root" }
```

Omit `id` and `originalVar`; `target` and `body` are present as empty strings. A connector rule uses the same custom fields but preserves its rule-scoped `elementId` from the ownership table. The output does not create a second root mirror: the existing Case-variable declaration/companion remains the only root slot, and the custom output points to it by `var`. Do not copy schema `options` onto a computed/literal assignment.

## Final dispatch checks

- Apply the complete global allocator to every independently minted bare or `->` source ID, including task, trigger, all four connector-rule scopes, and root entries. Keep `source` and display `name` unchanged when suffixing.
- For every `->`, require `id == originalVar == stripLeadingEquals(target)` and require `var == value == target Case-variable id`.
- For every `=`, require `custom: true`, matching `source`/`value`, empty `target`/`body`, and no `id` or `originalVar`.
- Preserve the selected owner's output array and `elementId`. Rules remain stage-scoped except case-exit rules, which remain root-scoped.
- Do not route trigger Pattern C, trigger auto-emit, or argument bridges through this guide.
