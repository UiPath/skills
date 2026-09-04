<!--skill-flavor:solution-commands-row:start-->
| `solution resources refresh` | Resource sync for the open Studio Web solution (never create a solution — there is only the open one) | Yes |
<!--skill-flavor:solution-commands-row:end-->

<!--skill-flavor:solution-init-section:start-->
## Solution

Studio Web works on one open solution, already scaffolded as the workspace root (`/solution`); never create another. The case project is created inside it with `uip maestro case init "<ProjectName>"` (see below).
<!--skill-flavor:solution-init-section:end-->

<!--skill-flavor:cd-mandatory-note:start-->
> **Run `case init` from the solution root (`/solution`).** Studio Web creates the project in the open solution at `/solution/<ProjectName>/`; there is no solution to create first and no second solution can be scaffolded by accident.
<!--skill-flavor:cd-mandatory-note:end-->

<!--skill-flavor:case-init-command:start-->
```bash
uip maestro case init <ProjectName>   # from the solution root, /solution
```
<!--skill-flavor:case-init-command:end-->

<!--skill-flavor:case-init-semantics:start-->
`case init` creates the project in the open Studio Web solution at `/solution/<ProjectName>/` and seeds its scaffold. There is no auto-scaffolded sibling solution, no `.uipx` on disk, and no registration step — Studio Web owns the solution manifest — so `--skip-solution-registration` and `uip solution projects add` have nothing to do here.
<!--skill-flavor:case-init-semantics:end-->

<!--skill-flavor:projects-add-scenarios:start-->
Not used in Studio Web: there is no `.uipx` on disk and Studio Web owns project registration — `uip maestro case init` already places the project in the open solution.
<!--skill-flavor:projects-add-scenarios:end-->
