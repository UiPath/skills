# Bindings & Expressions Reference

How to wire values into task inputs — expression prefixes, cross-task output references, and direct JSON editing.

## Two Binding Modes

Every task input is wired using one of two modes. Pick based on the source of the value.

| Mode | Tasks.md syntax | Implementation |
|------|-----------------|----------------|
| **Literal or expression** | `input = "<value>"` | Write `"<value>"` to `task.data.inputs[i].value` in caseplan.json |
| **Cross-task reference** | `input <- "Stage"."Task".output` | Resolve source output's `var` → write `"=vars.<var>"` to target input's `value` |

For the full JSON shapes and binding procedure, see [plugins/variables/io-binding/impl.md](plugins/variables/io-binding/impl.md).

For connector tasks, pass expressions inline in `--input-values` at creation time — see [plugins/tasks/connector-activity/impl.md](plugins/tasks/connector-activity/impl.md).

## Expression Prefixes

When using the literal/expression mode, the `--value` string can start with one of these prefixes to resolve dynamically at runtime. Plain strings without a prefix are treated as literals.

| Prefix | Meaning | Example |
|--------|---------|---------|
| `=metadata.` | Case metadata field | `=metadata.amount` |
| `=js:` | Inline JavaScript expression | `=js:new Date().toISOString()` |
| `=vars.` | Case-level variable | `=vars.inbox_config` |
| `=bindings.` | Resource binding (connection, queue, trigger) | `=bindings.slackConnection` |
| `=datafabric.` | Data Fabric entity field | `=datafabric.Customer.id` |
| `=orchestrator.JobAttachments` | Orchestrator job attachments | `=orchestrator.JobAttachments[0]` |
| `=response` | The response object from a previous HTTP step | `=response.body` |
| `=result` | The result of the previous task | `=result.status` |
| `=Error` | Error object from a failed step | `=Error.message` |
| `=jsonString:` | Serialize the following expression to a JSON string | `=jsonString:vars.config` |

> Plain strings (no prefix) are literal values. `"hello"` is literally the string `hello`, not an expression.

## Cross-Task References

Cross-task references wire the output of an earlier task into an input of a later task. The planning syntax uses **names** (human-readable), which the implementation phase resolves to variable IDs via direct JSON lookup.

### Planning syntax (in `tasks.md`)

```
input_name <- "Stage Name"."Task Name".output_name
```

- `Stage Name` — the `display-name` of the containing stage (exactly as written in a `Create stage "<name>"` task)
- `Task Name` — the `display-name` of the source task (exactly as written in an `Add <type> task "<name>"` task)
- `output_name` — a named output field from the source task

### Discovering output names

Run `tasks describe` during planning to list available outputs for a given task type:

```bash
uip case tasks describe --type <type> --id "<taskTypeId>" --output json
# for connectors: also pass --connection-id
```

Output names appear in the response under the output schema. Record them in the source task's `outputs:` field in `tasks.md` so downstream references can be validated.

### Validation rule

Every cross-task reference in `tasks.md` MUST point to:
1. A stage that exists (created by an earlier `Create stage "..."` task).
2. A task inside that stage that exists (created by an earlier `Add ... task "..." to "<stage>"` task).
3. An output name listed in that task's `outputs:` field.

Missing any of the three → halt planning and ask the user; do not fabricate.

### Implementation translation

The execution phase resolves names to IDs by reading caseplan.json:

```python
# Pseudo-code:
src_stage = find_node_by_label(nodes, "Stage Name")
src_task  = find_task_by_name(src_stage, "Task Name")
src_output = find_output_by_name(src_task, "output_name")
target_input.value = f"=vars.{src_output['var']}"
# Write updated caseplan.json back to disk
```

See [plugins/variables/io-binding/impl.md](plugins/variables/io-binding/impl.md) for the full procedure.

## Examples

### Literal and expression inputs

```markdown
## T10: Add api-workflow task "Fetch Inbox" to "Triage"
- inputs:
  - inbox_config = "=vars.inbox_config"
  - po_patterns  = "=vars.po_patterns"
  - max_results  = "50"
  - requested_at = "=js:new Date().toISOString()"
```

### Cross-task reference

```markdown
## T11: Add agent task "Classify Emails" to "Triage"
- inputs:
  - emails <- "Triage"."Fetch Inbox".emails
  - customer_id <- "Triage"."Fetch Inbox".customer_id
- outputs: category, priority_score
```

### Mixed inputs (HITL/action)

```markdown
## T12: Add action task "Review Classification" to "Triage"
- recipient: approver@corp.com
- priority: High
- inputs:
  - classification <- "Triage"."Classify Emails".category
  - priority       <- "Triage"."Classify Emails".priority_score
  - deadline       = "=js:new Date(Date.now() + 86400000).toISOString()"
- outputs: decision, comments
```

## Anti-Patterns

- **Mixing `--value` and `--source-*` in the same bind.** The CLI rejects this. Pick one mode per input.
- **Referencing a future task's output.** Cross-task references must target an earlier task in execution order.
- **Fabricating output names.** Always discover via `tasks describe`. A typo becomes a runtime null, not a validation error.
- **Plain-string where expression was intended.** `"metadata.amount"` (no `=`) is the literal string `metadata.amount`, not a reference. Always include the `=` prefix for dynamic values.
- **Nesting expressions inside literals.** `"$metadata.amount"` or `"{{ amount }}"` do not work. Use `=metadata.amount` directly as the full value.
