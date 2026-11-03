<!--skill-flavor:lifecycle-handoff:start-->
10. **Hand the project lifecycle to the uipath-rules skill when it is installed.** It owns `refresh`, `validate`, and the uipdm schema check. When it is absent, create the project with the `CreateProjects` host tool, run `uip rules refresh` and `uip rules validate` yourself, skip the schema check, and tell the user it was skipped. Never run `uip rules init` or `uip rules debug` here: `init` creates a folder that never becomes a Studio Web project, and `debug` is unavailable.
<!--skill-flavor:lifecycle-handoff:end-->
