<!--skill-flavor:host-scope:start-->
> **Studio Web:** the coded app CLI, npm and a full Node.js runtime are not available here (see SKILL.md § Studio Web Command Scope). The design, rules and file shapes in this file still apply to files you edit directly. Its build, pack, publish, deploy and local-run commands do not run in this host: deploy from Studio Web, and hand the CLI steps to the user to run on their machine.

<!--skill-flavor:host-scope:end-->

<!--skill-flavor:solution-only-rule:start-->
1. **Solutions only.** A public app must live in a solution, as an in-solution AppV2 project (SKILL.md § Studio Web Command Scope). It cannot be deployed on its own.
<!--skill-flavor:solution-only-rule:end-->

<!--skill-flavor:project-setup:start-->
Create the app as an AppV2 project in the open solution (SKILL.md § Studio Web Command Scope) and write its sources under `/solution/<ProjectName>/source/`. In the steps below, `feedback-app/` is `/solution/<ProjectName>/`.
<!--skill-flavor:project-setup:end-->
