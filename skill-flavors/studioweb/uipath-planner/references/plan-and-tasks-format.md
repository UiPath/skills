<!--skill-flavor:task-row-tool-fields:start-->
| `<skill-name>` | yes | One of `uipath-rpa`, `uipath-platform`, `uipath-solution`, `uipath-agents`, `uipath-coded-apps`, `uipath-functions`, `uipath-maestro-flow`, `uipath-maestro-bpmn`, `uipath-maestro-case`, `uipath-api-workflow`, `uipath-connector-builder`, `uipath-ixp`, `uipath-mcp-servers`, `uipath-human-in-the-loop`, `uipath-test`. The specialist the task loads; it also opens the task's title in the host plan. |
| `Identity` | yes | Stable tuple `<skill>:<project>:<subject>`. Used to match tasks across regenerations. **Parsing rule:** split on the first two colons only; `<subject>` may itself contain colons (typed-resource form `<kind>:<name>` for platform resources). Examples: `rpa:VendorInvoice_Performer:Process/CalculateTotal.xaml` (file-path subject), `platform:VendorInvoice:queue:VendorQueue` (typed-resource subject = `queue:VendorQueue`), `agents:InvoiceClassifier:tools/extract_amount.py` (file-path subject), `rpa:VendorInvoice:testing` (single-token subject). |
| `Status` | yes | One of `[ ]` pending, `[~]` in_progress, `[x]` completed, `[!]` blocked. |
| `Completed` | only when `[x]` | `YYYY-MM-DD by agent` or `YYYY-MM-DD by human`. `agent` when the agent flips the checkbox after finishing the task; `human` only when the user manually edits the file. |
| `Blocked by` | yes | Comma-separated task IDs, or `none`. In the host plan, a wait that is not the previous step becomes the step's `depends_on`. |
| `Skill prompt` | yes | Imperative prompt the specialist works from; in the host plan it is carried verbatim in the step's detail. Must end with the anti-hallucination rule (below). |
<!--skill-flavor:task-row-tool-fields:end-->

<!--skill-flavor:non-pdd-plan-reference:start-->
For the non-PDD lane, never write "this plan". In the simultaneous approach, reference the plan file **by path** — a resumed task must be able to find it:

```
Use values, mappings, and structure exactly as documented in the plan at <PLAN_FILE_PATH>. Do not infer or guess.
```

In plan mode (explore-first), reference the approved plan instead — the host renames the plan file once it completes and links every task back to it:

```
Use values, mappings, and structure exactly as documented in the approved plan. Do not infer or guess.
```
<!--skill-flavor:non-pdd-plan-reference:end-->

<!--skill-flavor:regenerate-emit:start-->
8. Continue at the lane's review step (PDD-driven lane Step 8)
<!--skill-flavor:regenerate-emit:end-->

<!--skill-flavor:live-tasks-and-plan-mode:start-->
## Plan-mode integration

Studio Web has no task-creation tool. A plan the user reviews goes through the host's plan mode, and the host derives the live task list from the approved plan. Create no tasks yourself.

- **Non-PDD lane explore-first:** call `EnterPlan` as soon as the user picks the approach, before any discovery. Discover read-only, author the host plan, then call `ExitPlan` with outcome `complete`. Approval → the host derives the task list and execution starts.
- **PDD-driven lane interactive:** write `<process>-tasks.md` (Step 7), call `EnterPlan`, author the host plan from it, then call `ExitPlan` with outcome `complete`. Approval → the host derives the task list.
- **Non-PDD lane simultaneous / PDD-driven autonomous:** no plan mode. Emit the file as text; the main agent works its tasks in order.

A rejection keeps plan mode active — revise and call `ExitPlan` again. If the user asks to stop planning, call `ExitPlan` with outcome `abandon`. While plan mode is active, the only files you may write are the host's two plan files.

The host's plan-authoring contract sets the plan's format and paths. Within it, carry the planner's content as follows:

| Planner content | Host plan |
|---|---|
| Header fields, Understanding, Decisions & Trade-offs, Stop conditions | `sections` |
| `Task T<N> — <skill> — <description>` | one step per task row, in row order; title `<skill> — <description>` |
| `Identity:`, `Skill prompt:`, sub-steps, `Validate:` | the step's detail, after its opening sentence, verbatim (including the anti-hallucination rule) |
| `Blocked by:` | the step's `depends_on`, only for a wait that is not the previous step |
| `Status: [x] completed` rows (resume / regenerate) | left out of the steps; listed as already done in a section |
<!--skill-flavor:live-tasks-and-plan-mode:end-->
