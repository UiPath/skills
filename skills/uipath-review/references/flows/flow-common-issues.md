# Flow Common Issues

Catalog of frequently found issues in UiPath Flow projects, with detection methods and recommended fixes.

## Structural Issues

### Missing targetPort on Edges

**Symptom:** Edge definitions lack the `targetPort` field.

**Impact:** Flow validation fails. The flow cannot be executed.

**Detection:** `uip flow validate` will catch this. Also check manually:
```bash
# In the .flow file, look for edges without targetPort
grep -c '"targetPort"' *.flow
# Compare to total edge count
```

**Fix:** Add `"targetPort": "input"` to every edge that's missing it. Most nodes use `"input"` as the standard target port.

### Hand-Written Definitions

**Symptom:** Node definitions in the `.flow` file were manually written instead of copied from the flow registry.

**Impact:** Incorrect schemas cause validation errors, runtime failures, or silent data loss. Hand-written definitions often miss required fields, have wrong types, or use outdated schemas.

**Detection:** Compare definitions entries against registry output:
```bash
uip flow registry get <node-type> --output json
```
If the definition in the .flow file doesn't match the registry output, it was likely hand-written.

**Fix:** Replace hand-written definitions with the exact output from `uip flow registry get`. Never modify registry definitions manually.

### Orphan Nodes

**Symptom:** Nodes exist in the `nodes` array but have no incoming edges (except the Start node) — they're unreachable.

**Impact:** Orphan nodes suggest incomplete implementation or leftover design artifacts. They won't execute but add confusion.

**Detection:** For each node (except Start), verify at least one edge targets it:
1. Collect all `targetNodeId` values from edges
2. Check each non-trigger node's ID appears in that list

**Fix:** Either connect the orphan node to the flow or remove it. If it's a placeholder for future work, replace with a comment or remove and note in documentation.

### Duplicate Node or Edge IDs

**Symptom:** Two or more nodes or edges share the same ID.

**Impact:** Validation fails. Runtime behavior is undefined — the engine may route to the wrong node.

**Detection:** `uip flow validate` catches this. Also check with:
```bash
# Extract all node IDs and check for duplicates
python3 -c "import json; f=json.load(open('*.flow')); ids=[n['id'] for n in f['nodes']]; print([x for x in ids if ids.count(x)>1])"
```

**Fix:** Assign unique UUIDs to duplicate nodes/edges.

## Design Issues

### Stale Mock Placeholder Nodes

**Symptom:** `core.logic.mock` nodes remain in the flow, used as stand-ins during development for resources that should now be published.

**Impact:** Mock nodes don't execute real logic. The flow appears to work but produces no real results.

**Detection:**
```bash
grep "core.logic.mock" *.flow
```

**Fix:** Replace each mock with the real resource node. Use `uip flow registry get <resource-type>` to get the correct definition, then update the node type, inputs, and definitions.

### Missing Output Mapping on End Nodes

**Symptom:** End nodes (`core.control.end`) don't map `out` variables from the flow's variable declarations.

**Impact:** Flow completes but output variables are empty/null. Callers of this flow receive no results.

**Detection:** Read the `.flow` file:
1. Identify all variables with `"direction": "out"` or `"direction": "inout"` in the `variables.globals` array
2. For each reachable End node, verify these variables are mapped in the End node's inputs

**Fix:** Add output variable mappings to every reachable End node. Each `out` variable must be explicitly set.

### In Variable Mutation

**Symptom:** Flow modifies a variable declared with `"direction": "in"`.

**Impact:** Runtime error or silent failure. Input variables are read-only by design.

**Detection:** Check variable directions in the `.flow` variables section. Then trace which nodes assign values to those variables. Any assignment to an `in` variable is a bug.

**Fix:** Change the variable direction to `inout` if it genuinely needs to be modified. Or create a separate working variable and copy the input value.

### console.log in Script Nodes

**Symptom:** Script nodes contain `console.log()` statements.

**Impact:** `console.log` output goes nowhere in the flow runtime. It's a debugging artifact that serves no purpose in production.

**Detection:**
```bash
grep "console.log" *.flow
```

**Fix:** Remove `console.log` statements. If logging is needed, use flow-level logging or output the value to a variable for inspection.

### Script Nodes Returning Bare Scalars

**Symptom:** Script node returns a plain string, number, or boolean instead of an object.

**Impact:** Downstream nodes may have difficulty accessing the value. Object returns are more extensible and consistent.

**Detection:** Check script node output configurations. Look for `return "string"` or `return 42` patterns instead of `return { result: "string" }`.

**Fix:** Wrap scalar returns in an object: `return { value: result }`.

## Orchestration Issues

### No Error Handling on Resource Nodes

**Symptom:** Resource nodes (RPA, agent, human task) have only success edges — no error/failure paths.

**Impact:** If the resource fails, the flow has no recovery path. It will fault entirely instead of handling the error gracefully.

**Detection:** For each resource node, check if there are edges on error/failure ports (not just success/output).

**Fix:** Add error edges from resource nodes to appropriate handling logic (retry, skip, escalate, terminate).

### Wrong Resource Type

**Symptom:** Agent node used for deterministic rule-based logic, or Script node used for tasks requiring AI reasoning.

**Example issues:**
- `uipath.agent.autonomous` node used to apply a fixed discount table (should be Script)
- `core.action.script` used to classify free-text customer complaints (should be Agent)

**Detection:** Review each node's purpose against its type. Agent nodes should handle ambiguity; Script nodes should handle deterministic logic.

**Fix:** Replace with the appropriate node type. This may require publishing a new resource if switching from script to agent.

### Stale Resource References

**Symptom:** Resource nodes reference processes, agents, or APIs that have been unpublished, renamed, or moved to a different folder.

**Impact:** Flow validation may pass (validates structure, not resource availability), but runtime execution fails when the resource is called.

**Detection:** Extract resource keys from node types (e.g., `uipath.core.rpa-workflow.invoice-processor`). Verify each resource is published and accessible.

**Fix:** Update resource references to point to current published resources. Re-run `uip flow registry list` to find available resources.

### Hardcoded Queue Names

**Symptom:** Queue node inputs contain literal queue names instead of variable references.

**Impact:** Cannot use different queues across environments. Requires flow modification for each deployment.

**Detection:** Check queue node inputs for literal string values.

**Fix:** Store queue name in a flow variable (preferably `in` direction) and reference it in the queue node.

## Subflow Issues

### Parent Variable Reference from Subflow

**Symptom:** Subflow nodes reference `$vars.parentNodeId.output` — accessing the parent flow's variable scope.

**Impact:** Subflows have their own variable scope by design. Parent `$vars` references are invalid and will fail.

**Detection:** Check subflow node expressions for `$vars` references that point to nodes outside the subflow.

**Fix:** Pass needed data as subflow input variables. Map parent data to subflow `in` globals.

### Missing Subflow Start/End Nodes

**Symptom:** Subflow body lacks a `core.trigger.manual` start or `core.control.end` end node.

**Impact:** Subflow cannot execute. Validation fails.

**Detection:** Check each subflow's nodes array for trigger and end types.

**Fix:** Add Start and End nodes to the subflow.

### Excessive Nesting

**Symptom:** Subflows nested more than 3 levels deep.

**Impact:** Difficult to understand, debug, and maintain. Variable mapping becomes complex and error-prone.

**Detection:** Count nesting levels by traversing subflow containment.

**Fix:** Flatten the hierarchy. Extract deeply nested logic into separate published flows that can be invoked as resource nodes.

## Performance Issues

### Sequential Processing of Independent Items

**Symptom:** Items that could be processed in parallel are processed sequentially in a loop.

**Impact:** Execution time scales linearly with item count. A 100-item batch takes 100x longer than it needs to.

**Detection:** Check loop nodes for `sequential` mode when the items have no ordering dependency.

**Fix:** Switch to parallel multi-instance mode. Note: parallel execution runs in batches of 50.

### Large Payloads Through Unnecessary Nodes

**Symptom:** Variables containing large data (full document content, large arrays) are carried through every node even when only a subset of nodes use them.

**Impact:** Increases memory usage and serialization overhead at every node transition.

**Detection:** Trace variable usage through the flow. Identify variables that are set early but only used much later.

**Fix:** Use transform nodes to extract only needed fields early. Pass minimal data between nodes. Fetch full data only where needed.

### Overly Complex Single Flows

**Symptom:** A single .flow file with 30+ nodes handling multiple distinct concerns.

**Impact:** Difficult to test, debug, and modify. Changes risk breaking unrelated logic.

**Detection:** Count nodes in the flow. Identify distinct functional areas.

**Fix:** Break into subflows by functional area. Or break into separate flows that call each other as resource nodes.

## Maestro / BPMN Deadlock Patterns

### Mixed Gateway Types on Merge (Deadlock)

**Symptom:** Flow splits with a Parallel Gateway but merges with an Exclusive Gateway (or vice versa, or Inclusive split with Exclusive merge).

**Impact:** Deadlock. Parallel split creates N tokens. Exclusive merge completes after the first token arrives and discards the rest — or hangs waiting for a condition that never satisfies. Orphaned tokens, flows hung forever.

**Detection:** In `.flow` files, find every gateway split (diverging) and trace forward to its corresponding merge. Gateway types MUST match: Parallel → Parallel, Inclusive → Inclusive, Exclusive → Exclusive.

**Fix:** Always use matching gateway types for split and merge. For "wait for all parallel branches", use a Parallel merge, not Exclusive.

**Severity:** Critical

### Variable Rename Without Fix-Variables Dialog

**Symptom:** Flow variable renamed directly in the variables list (not via Fix Variables dialog). Expressions referencing the old variable ID silently break.

**Impact:** Flow may save and validate but fails at runtime with "undefined variable" errors. Hard to diagnose because the variable appears to exist with the new name.

**Detection:** After a rename, grep expression fields in the `.flow` file for references to the old variable UUID (not the display name).

**Fix:** Use the Fix Variables dialog when renaming. If done manually, update every expression reference manually.

**Severity:** Warning

## API Workflow Antipatterns (Studio Web)

### No Input Schema Enforcement

**Symptom:** API workflow has input schema defined, but the first steps do not validate required inputs. Callers can send malformed payloads and the workflow tries to process them.

**Impact:** NullReferenceException deep in the logic instead of a clear 400 Bad Request. Consumers get unhelpful errors.

**Detection:** Inspect API workflow's initial activities. Check for explicit validation (required-field checks, type validation) before business logic begins.

**Fix:** Add input validation as the first step. Return structured 400 responses with field-specific error messages.

**Severity:** Warning

### Synchronous Long-Running API Workflow

**Symptom:** API workflow performing long-running logic (DB migrations, bulk processing, chained API calls) synchronously. Hard timeout: 10 minutes (5 min CPU for serverless).

**Impact:** Request times out with no result, no recovery path. Caller sees timeout error. Work may be partially complete with no rollback.

**Detection:** API workflow test execution exceeds 5 minutes.

**Fix:** Convert to async pattern — accept request, return job ID, process in background (via queue), let caller poll. Or use `Wait for Event and Resume` for suspend/resume.

**Severity:** Warning
