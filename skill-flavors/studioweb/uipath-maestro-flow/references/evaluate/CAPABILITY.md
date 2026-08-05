<!-- skill-flavor:evaluation-contract:start -->
Use Flow evaluations in Studio Web only when the per-turn browser-bundle list exposes a Flow eval command or an advertised project ProxyTool provides an evaluation capability.

## Workflow

1. Inspect the live Flow command/tool schema; never assume the desktop `uip maestro flow eval` prefix exists.
2. Store evaluator, eval-set, and data-point files only in locations already present or documented by the generated Flow project.
3. Start, inspect, and compare runs with the live-advertised surface. Authentication and solution/project identity come from Studio Web.
4. Preserve consent before an evaluation can execute a Flow with real external side effects.
5. If evaluation support is absent, report the capability gap. Do not install a CLI, upload the solution, or switch to a local runtime.

The active solution already exists in Studio Web. Never use `uip solution upload`, `.uipx`, or local project IDs as an eval prerequisite.
<!-- skill-flavor:evaluation-contract:end -->
