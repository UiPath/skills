<!--skill-flavor:one-shot-offer:start-->
**One-shot level.** This host does not offer one-shot. List only the two review levels, and do not mention one-shot.
<!--skill-flavor:one-shot-offer:end-->
<!--skill-flavor:scaffold:start-->
**Write.** Create the project in the open solution with the `CreateProjects` host tool, project type BusinessRules. The rule is the one `.dmn` file in `/solution/<RULE_NAME>/`, and that folder is `<PROJECT_DIR>` below. Treat whatever table the seeded `.dmn` holds as a placeholder: keep its file name, root element, and decision `id`, then write the `.dmn` skeleton: DMN 1.5 namespaces, declared inputs with `uipdm:inputVariable`, outputs, an empty table per decision. Set the decision's `name` and `label`, and put the document title, version, effective date, and amendments applied from phase 2 in the decision's `description`. Never hand-write or delete `project.uiproj`, `entry-points.json`, or `bindings_v2.json`. Then `uip rules refresh <PROJECT_DIR> --output json`.
<!--skill-flavor:scaffold:end-->
<!--skill-flavor:verify:start-->
5. **Run.** `uip rules debug` is unavailable here; run the project with the `RunProject` host tool.
   - Pass one input object keyed by input-argument name for each sampled input set: one for the first-listed row, one for the default row, and for each threshold one just inside and one just outside.
   - Run the all-criteria-pass set first, then a set with an optional input omitted: FEEL errors on null inputs surface in those two runs.
   - Check that the omitted-input set returns the insufficient-information outcome, and read the run's trace to see which rules fired.
   - The runs show that the rule evaluates and that a missing input does not raise a FEEL error; they do not judge correctness (critical rule 15). Stop after 3 fix rounds on one failure (critical rule 12).
<!--skill-flavor:verify:end-->
