<!--skill-flavor:upload-safety-guide-gate:start-->
> **Before running any of these:** Studio Web owns the solution, so the "solution must be in Studio Web" prerequisite is already satisfied. Never attempt `uip solution upload`.
<!--skill-flavor:upload-safety-guide-gate:end-->

<!--skill-flavor:upload-safety-resolution-failure:start-->
If the auto-resolution fails AND you have not passed explicit IDs, the start command will error. Read the solution and project IDs from the host-exposed project instead; never attempt `uip solution upload`.
<!--skill-flavor:upload-safety-resolution-failure:end-->

<!--skill-flavor:upload-safety-recipe-comment:start-->
# 1. The solution already exists in Studio Web — the host owns it
<!--skill-flavor:upload-safety-recipe-comment:end-->

<!--skill-flavor:upload-safety-guide-antipattern:start-->
- **Don't attempt `uip solution upload`** when `eval run start` errors with a missing-solution error. Report the host gap instead.
<!--skill-flavor:upload-safety-guide-antipattern:end-->
