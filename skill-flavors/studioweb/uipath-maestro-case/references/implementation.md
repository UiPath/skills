<!--skill-flavor:step-six-zero:start-->
1. **Step 6.0 (CLI)** — `uip maestro case init "<ProjectName>"` from `/solution`. Studio Web creates the project inside the open solution (`<SolutionDir>` is `/solution`; never create a solution), seeds its scaffold, and registers it — Studio Web owns the solution manifest, so there is no `.uipx` on disk and no registration step.
<!--skill-flavor:step-six-zero:end-->

<!--skill-flavor:step-six-intro:start-->
The case file must live inside a project of the open Studio Web solution. `uip maestro case init` creates that project and seeds its scaffold; the case plugin owns the root caseplan write (and any scaffold file Studio Web did not seed). Project creation is the only CLI call. **Never use `uip maestro case cases add` (or another case mutation command) to create the root caseplan** — execute the T01 direct-JSON recipe so required root metadata such as `caseDirectlyPassTaskOutputs` is emitted.
<!--skill-flavor:step-six-intro:end-->

<!--skill-flavor:step-six-t01-scaffold:start-->
   - § Scaffold writes only the boilerplate files (`project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`) that Step 6.0 did not seed, directly into `<SolutionDir>/<ProjectName>/`; seeded files stay untouched.
<!--skill-flavor:step-six-t01-scaffold:end-->

<!--skill-flavor:step-six-zero-b:start-->
<!--skill-flavor:step-six-zero-b:end-->

<!--skill-flavor:step-six-zero-c:start-->
<!--skill-flavor:step-six-zero-c:end-->
