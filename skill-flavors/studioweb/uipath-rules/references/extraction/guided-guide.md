<!--skill-flavor:scaffold:start-->
**Write.** Find or create the project as uipath-rules Quick Start step 1 says, looking under `/solution/` first: an existing project that still holds the placeholder is used, and one with rules of its own needs the user's choice, which joins the call for blocking questions above. Create one with the `CreateProjects` host tool, project type BusinessRules, only when that step says to. The rule is the one `.dmn` file in the project's folder under `/solution/`, and that folder is `<PROJECT_DIR>` below. Keep the `.dmn` file name, root element, and decision `id`, then write the `.dmn` skeleton: DMN 1.5 namespaces, declared inputs with `uipdm:inputVariable`, outputs, and an empty table. Set the decision's `name` and `label`, and put the base document's title, version, and effective date, the as-of date, and every other registered document with its status (applied, not yet effective, or read and not used) in the decision's `description`: it is the record a later reviewer reads. Never hand-write or delete `project.uiproj`, `entry-points.json`, or `bindings_v2.json`. Do not validate the skeleton on its own; the first section's check covers it.
<!--skill-flavor:scaffold:end-->
<!--skill-flavor:verify:start-->
5. **Run, only when asked.** `uip rules debug` is unavailable here; run the project with the `RunProject` host tool, only when the request asked for sampled runs or the user asks for them after the Finish result; do not ask whether to run.
   - Pass one input object keyed by input-argument name for each sampled input set: one for the first-listed row, one for the default row, and for each threshold one just inside and one just outside.
   - Run the all-criteria-pass set first, then a set with an optional input omitted: FEEL errors on null inputs surface in those two runs.
   - Check that the omitted-input set returns the insufficient-information outcome, and read the run's trace to see which rules fired.
   - The runs show that the rule evaluates and that a missing input does not raise a FEEL error; they do not judge correctness (extraction rule 11). Stop after 3 fix rounds on one failure (uipath-rules critical rule 7).
<!--skill-flavor:verify:end-->
<!--skill-flavor:section-rows:start-->
**Show.** Do not print the rows: the designer beside the chat shows them. After each batch of sections, say in one line how many rows each section added and whether earlier rows changed.
<!--skill-flavor:section-rows:end-->
<!--skill-flavor:finish-result:start-->
**What the result holds.** Only what the designer beside the chat cannot show: a link to the rule file; one line with the `validate` and uipdm check results and that the rule has not been run; every assumption recorded as `qualityWarning`; any finding of the table check that the user must act on; and the limits below. Do not print the table, the inputs, the outputs, the decision question, or the outcomes.
<!--skill-flavor:finish-result:end-->
