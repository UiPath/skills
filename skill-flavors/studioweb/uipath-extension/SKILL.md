<!--skill-flavor:host-scope:start-->
## Studio Web Command Scope

**The `uip extension` tool is not available in Studio Web.** The browser bundle does not ship it and the host intercepts none of its verbs, so `validate`, `upload` and `submit` all fail here. The tool also needs a local function project, `uip function new`, a login on a developer machine, and the `gh` CLI for `submit`, and none of those exist in the browser.

Do not run any command in this skill here. Tell the user to run the workflow on a developer machine with `uip` installed. What you can do here is read the project files and explain the template, the adopt diff or a gate report the user pastes in.

<!--skill-flavor:host-scope:end-->
