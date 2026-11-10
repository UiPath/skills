<!--skill-flavor:progress-tasks:start-->
Studio Web has no task-creation tool, so `design` creates no progress tasks: skip this step.
<!--skill-flavor:progress-tasks:end-->

<!--skill-flavor:sdd-no-task-lists:start-->
Never put Task 1 / Task N templates or implementation tasks in the SDD. End the SDD with a `## Next Steps` section.
<!--skill-flavor:sdd-no-task-lists:end-->

<!--skill-flavor:solution-terminal-artifact:start-->
6. **In Studio Web the deliverable is the open solution.** The SDD's `## Next Steps` section tells the user each project is created inside the open Studio Web solution (`uip <family> init <ProjectName>` per project); there is no solution to create and no packing step. Plan each project by what Studio Web supports for its type: flow, case, agent, api-workflow and bpmn projects are created, built, run and debugged end to end here; an rpa project is created and run here, but its workflows are authored in the Studio Web designer or Studio Desktop, so its build tasks go to the user; function and coded-app projects cannot be created here — their existing files can be edited, but scaffolding, running and deploying go to the user's local CLI.
<!--skill-flavor:solution-terminal-artifact:end-->
