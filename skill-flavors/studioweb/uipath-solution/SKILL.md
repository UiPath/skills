<!--skill-flavor:when-to-use-create:start-->
- User wants to add or remove projects in the open solution, or refresh solution resources (Studio Web works on one open solution; creating another is not possible here)
<!--skill-flavor:when-to-use-create:end-->

<!--skill-flavor:cli-surface-probe:start-->
Studio Web runs the post-rename CLI: use the commands and flags as documented in the references, with no probe. The open solution is the only solution — creating another is not possible here.
<!--skill-flavor:cli-surface-probe:end-->

<!--skill-flavor:rename-row-init:start-->
<!--skill-flavor:rename-row-init:end-->

<!--skill-flavor:probe-rule:start-->
1. **Studio Web runs the post-rename CLI.** Use the documented commands directly; the fallback table does not apply.
<!--skill-flavor:probe-rule:end-->

<!--skill-flavor:develop-solution-row:start-->
| [Develop a Solution](references/develop-solution.md) | `uip solution project add / import / remove / resources refresh / resources add / resources remove / resources edit`; field-tested gotchas |
<!--skill-flavor:develop-solution-row:end-->
