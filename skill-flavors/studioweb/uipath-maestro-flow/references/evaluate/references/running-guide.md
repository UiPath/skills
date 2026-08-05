<!-- skill-flavor:evaluation-runs:start -->
Run evaluations only through the Flow eval surface advertised by the current browser bundle or project ProxyTool.

- Authentication is automatic; never run `uip login`.
- The open Studio Web project supplies solution and project identity; do not inspect `.uipx`, `SolutionStorage.json`, or upload a local solution.
- Use inline values and project-backed files supported by the live schema. Do not rely on local filesystem paths or unavailable runtimes.
- Poll or wait using one live-advertised method, not both concurrently.
- Compare runs from the same eval set and inspect per-evaluator scores, not only the aggregate.
- If start/status/results/compare is unavailable, report exactly which capability is missing.
<!-- skill-flavor:evaluation-runs:end -->
