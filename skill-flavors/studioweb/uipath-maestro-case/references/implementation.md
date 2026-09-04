<!--skill-flavor:step-six-zero:start-->
1. **Step 6.0 (CLI)** — `uip maestro case init "<ProjectName>"` from `/solution`. Studio Web creates the project inside the open solution (`<SolutionDir>` is `/solution`; never create a solution) and seeds its scaffold. Studio Web owns the solution manifest, so there is no `<SolutionDir>/<SolutionName>.uipx` to check or register with — skip the `.uipx` existence checks and `uip solution projects add` wherever the steps below mention them.
<!--skill-flavor:step-six-zero:end-->

<!--skill-flavor:step-six-intro:start-->
The case file must live inside a project of the open Studio Web solution. `uip maestro case init` creates that project and seeds its scaffold; the case plugin owns the root caseplan write (and any scaffold file Studio Web did not seed). Project creation is the only CLI call. **Never use `uip maestro case cases add` (or another case mutation command) to create the root caseplan** — execute the T01 direct-JSON recipe so required root metadata such as `caseDirectlyPassTaskOutputs` is emitted.
<!--skill-flavor:step-six-intro:end-->
