<!--skill-flavor:upload-safety-critical-rule:start-->
2. **Never attempt `uip solution upload`.** Studio Web owns the solution, so the eval run's "solution must exist in Studio Web" prerequisite is already satisfied by the host. If a run still reports the solution as missing, report the host capability gap — do not try to push local state.
<!--skill-flavor:upload-safety-critical-rule:end-->

<!--skill-flavor:upload-safety-workflow-comment:start-->
# 4. The solution already exists in Studio Web — the host owns it
<!--skill-flavor:upload-safety-workflow-comment:end-->

<!--skill-flavor:upload-safety-workflow-row:start-->
<!--skill-flavor:upload-safety-workflow-row:end-->

<!--skill-flavor:upload-safety-task-row:start-->
<!--skill-flavor:upload-safety-task-row:end-->

<!--skill-flavor:upload-safety-antipattern:start-->
- **Don't attempt `uip solution upload`.** Studio Web owns solution state. When an eval run errors with "solution not found in Studio Web", report the host gap instead of pushing the working tree.
<!--skill-flavor:upload-safety-antipattern:end-->

<!--skill-flavor:upload-safety-next-step:start-->
4. **Suggested next step** — fix the agent/flow, re-run, or accept the result.
<!--skill-flavor:upload-safety-next-step:end-->

<!--skill-flavor:upload-safety-reference-entry:start-->
<!--skill-flavor:upload-safety-reference-entry:end-->
