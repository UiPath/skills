<!--skill-flavor:narration-cadence-table:start-->
| Situation | Rule |
|---|---|
| Start of logical step | Narrate one short line in plain English. |
| Multiple actions within a step | Do not add narration. |
| Step transition | Narrate the next step. |
| Decision point | Give a brief line before asking the user; explain the decision's consequence. |
| Failure/retry | Always narrate what failed and what will be tried next, even in silent mode. |
| Trivial probe (a repeated `registry get` for a shape already in context) | Skip. |
| Non-`uip` shell plumbing (`ls`, `cat`, `mkdir`, `cd`) | Skip; the step line covers it. |
| File reads/edits inside a step | Skip; the step line covers them. |
<!--skill-flavor:narration-cadence-table:end-->

<!--skill-flavor:flow-project-creation-narration:start-->
| Step | Narration |
|---|---|
| Flow project creation | "Creating the Flow project in the open Studio Web solution." |
| Locate generated project | "Opening the scaffolded `new.flow` before editing." |
| Registry discovery | "Looking up `<node-type>` in the registry so I can wire its inputs correctly…" |
| Node add | "Adding the `<node-type>` node and copying its registry definition into the file…" |
| Edit flow JSON | "Editing the flow JSON to add the `<thing>`." |
| Edge wiring | "Wiring `<from>` → `<to>` so data flows in the right order." |
| Variable mapping | "Mapping output variables on the End node — every reachable End needs them." |
| Script body update | "Updating the script body in the `<nodeId>` node." |
| Validate | "Running validate. This catches missing edges, bad expressions, and wiring mistakes." |
| Format | "Formatting the layout. Studio Web renders nodes correctly only after format normalizes their sizes." |
| Publish | "Publishing the solution to `<location>`…" |
| Debug consent | "Running debug end-to-end. Real systems will be hit (emails sent, Slack posts, API calls)." |
| Process run | "Triggering the deployed process now…" |
| Job status | "Checking the job's current status…" |
| Job traces | "Pulling traces — verbose execution timeline." |
| Instance pause | "Pausing the running instance…" |
| Instance resume | "Resuming the instance from where it paused…" |
| Instance cancel | "Cancelling the instance…" |
| Instance retry | "Retrying the faulted instance from the last successful checkpoint…" |
| Incident fetch | "Fetching the incident record — this is the structured error report from the failed run." |
| Variable inspection | "Reading the runtime variable state at the moment of failure…" |
| Flow correlation | "Mapping the faulting element ID back to a node in your `.flow` file…" |
| Traces, last resort | "Pulling traces. Last resort — the previous steps weren't enough." |
<!--skill-flavor:flow-project-creation-narration:end-->

<!--skill-flavor:progress-list-threshold-table:start-->
| Journey | Narration | Progress list |
|---|---|---|
| Single edit: 1–2 actions, no decisions | One line | None |
| Small edit: 3–5 actions or one decision | One line per step | Optional |
| Standard: greenfield, multi-node brownfield, publish, or full diagnose | One line per step | Required and granular |
| Complex: 10+ nodes, multiple resource bindings, or planning phase | Denser cadence | Required, granular, with sub-todos |
<!--skill-flavor:progress-list-threshold-table:end-->

<!--skill-flavor:valid-todos-list:start-->
Valid todos include: Flow project created; node added and wired; edges connected; variables defined and mapped; validate green; format applied; debug run completed; published; incident fetched and read; root cause classified.
<!--skill-flavor:valid-todos-list:end-->
