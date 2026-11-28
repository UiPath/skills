<!--skill-flavor:progress-tasks:start-->
Studio Web has no task-creation tool, so `design` creates no progress tasks: skip this step.
<!--skill-flavor:progress-tasks:end-->

<!--skill-flavor:sdd-no-task-lists:start-->
Never put Task 1 / Task N templates or implementation tasks in the SDD. Its body ends with its Next Steps section; only the Action Required section may follow it, where the template places it there.
<!--skill-flavor:sdd-no-task-lists:end-->

<!--skill-flavor:solution-terminal-artifact:start-->
6. **In Studio Web the deliverable is the open solution.** Each project is created inside the open Studio Web solution, through the creation step of the skill that owns its type; there is no solution to create and no packing step, and the SDD names neither. Plan each project by what Studio Web supports for its type:
   - flow, case, agent, api-workflow and bpmn projects are created, built, run and debugged end to end here;
   - an rpa project is created and run here, but its workflows are authored in the Studio Web designer or Studio Desktop, so its build tasks go to the user;
   - function projects cannot be created here — their existing files can be edited, but scaffolding, running and deploying go to the user's local CLI;
   - a coded-app project is created and its source files are written here, but nothing builds or runs it in this host.
<!--skill-flavor:solution-terminal-artifact:end-->
