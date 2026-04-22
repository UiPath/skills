# Case Editing Operations — Strategy Selection

`caseplan.json` can be mutated via two strategies. This document is the single source of truth for which strategy to use for which plugin.

The skill is migrating from CLI-based mutation to direct JSON editing one plugin at a time. During migration, CLI remains the default — plugins opt in to JSON as they're migrated.

## Strategy Matrix

Default strategy is **CLI**. Plugins opt in to direct JSON when they've been migrated, tested, and have an `impl-json.md` file alongside their `impl-cli.md`.

| Plugin | Strategy | Notes |
|---|---|---|
| `case` (root + initial trigger) | CLI | `uip maestro case cases add` creates the file scaffolding and is out of scope for the JSON shift. |
| `stages` | **JSON** (pilot) | Migrated as the first pilot. See [plugins/stages/impl-json.md](plugins/stages/impl-json.md). |
| `edges` | **JSON** | Migrated after stages. See [plugins/edges/impl-json.md](plugins/edges/impl-json.md). |
| `triggers/manual` | **JSON** | Migrated. See [plugins/triggers/manual/impl-json.md](plugins/triggers/manual/impl-json.md). Also mutates sibling `entry-points.json` — see that file for the 2-file sync contract. |
| `triggers/timer` | **JSON** | Writes secondary Trigger node with `Intsvc.TimerTrigger` service type + `timeCycle` ISO 8601 string; adapts shape to initial (`trigger_1`) or secondary based on existing trigger count. See [plugins/triggers/timer/impl-json.md](plugins/triggers/timer/impl-json.md). |
| `triggers/event` | CLI | Migration queued. |
| `variables/global-vars` | **JSON** | No CLI exists for variable declaration — always written directly into `caseplan.json`. See [plugins/variables/global-vars/impl-json.md](plugins/variables/global-vars/impl-json.md). |
| `variables/io-binding` | **JSON** | Direct write to `task.data.inputs[i].value`. No CLI needed. See [plugins/variables/io-binding/impl-json.md](plugins/variables/io-binding/impl-json.md). |
| `tasks/process` | CLI | Migration queued. |
| `tasks/agent` | CLI | Migration queued. |
| `tasks/rpa` | CLI | Migration queued. |
| `tasks/action` | CLI | Migration queued. |
| `tasks/api-workflow` | CLI | Migration queued. |
| `tasks/case-management` | CLI | Migration queued. |
| `tasks/connector-activity` | CLI | Migration queued. Auto-injected default entry condition complicates the recipe. |
| `tasks/connector-trigger` | CLI | Migration queued. Same as connector-activity. |
| `tasks/wait-for-timer` | **JSON** | Writes full task with `timerType` + duration. See [plugins/tasks/wait-for-timer/impl-json.md](plugins/tasks/wait-for-timer/impl-json.md). |
| `conditions/stage-entry-conditions` | **JSON** | Write directly to the target stage's `data.entryConditions[]`. See [plugins/conditions/stage-entry-conditions/impl-json.md](plugins/conditions/stage-entry-conditions/impl-json.md). |
| `conditions/stage-exit-conditions` | **JSON** | Write directly to the target stage's `data.exitConditions[]`. See [plugins/conditions/stage-exit-conditions/impl-json.md](plugins/conditions/stage-exit-conditions/impl-json.md). |
| `conditions/task-entry-conditions` | **JSON** | Write directly to the target task's `entryConditions[]`. See [plugins/conditions/task-entry-conditions/impl-json.md](plugins/conditions/task-entry-conditions/impl-json.md). |
| `conditions/case-exit-conditions` | **JSON** | Write directly to `root.caseExitConditions[]`. See [plugins/conditions/case-exit-conditions/impl-json.md](plugins/conditions/case-exit-conditions/impl-json.md). |
| `sla` | CLI | Migration queued. |

## How agents consume this matrix

Before executing a T-entry from `tasks.md`:

1. Identify the plugin for the T-entry (task type, trigger type, condition scope, etc.).
2. Look up the plugin's row in the matrix above.
3. If **Strategy = JSON**:
   - Open the plugin's `impl-json.md` — authoritative for the JSON strategy.
   - Follow the primitive operations in [case-editing-operations-json.md](case-editing-operations-json.md) for splicing into `caseplan.json`.
   - Respect the Pre-flight Checklist before every write.
4. If **Strategy = CLI**:
   - Open the plugin's `impl-cli.md` — authoritative for the CLI strategy.
   - Follow the execution procedure in [case-editing-operations-cli.md](case-editing-operations-cli.md).

## Plugin self-declaration

Every migrated plugin ships an `impl-json.md` with this frontmatter:

```yaml
---
direct-json: supported
---
```

The matrix above is the primary source of truth. The per-file frontmatter is the secondary signal — an agent reading a plugin's `impl-json.md` in isolation can verify the migration status without cross-referencing this matrix.

## Updating the matrix

When a plugin's migration PR lands:

1. Update its row here from `CLI` to `JSON`.
2. Add `impl-json.md` to the plugin's folder with the `direct-json: supported` frontmatter.
3. Ensure `impl-json.md` has a complete JSON Recipe.
4. Manually validate the migrated plugin against a real CLI run — regenerate `caseplan.json` (and any sibling files the plugin mutates) via `uip maestro case ...` commands, then compare against the direct-JSON-write output. Document the comparison in the PR description.
5. Ensure a "Compatibility" section in the plugin's `impl-json.md` documents what passed.
