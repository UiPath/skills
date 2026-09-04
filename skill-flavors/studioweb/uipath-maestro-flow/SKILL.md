<!--skill-flavor:project-creation-scope:start-->
- Create a new Flow project through Studio Web's solution-level project-creation capability
<!--skill-flavor:project-creation-scope:end-->

<!--skill-flavor:user-question-options-extra:start-->

   **Exception — the option set came from the host, not from you.** When a Studio Web command answers with the choices itself (`uip solution publish` with no destination lists every feed you can publish to, and its `--location` accepts only those keys or names), offer exactly the options it returned and omit "Something else". That list is authoritative and exhaustive: a free-form destination cannot match it, so the command rejects it and the user pays a round-trip to be shown the same list again. Everything else in this rule still applies — the enumerated options, the numbered-list fallback, the non-interactive behaviour, and the consent gates.

<!--skill-flavor:user-question-options-extra:end-->

<!--skill-flavor:project-creation:start-->
6. **Create Flow projects with the Studio Web project tool.** Before creating a project, inspect the live `CreateProjects` schema. Invoke that operation with the Flow project type using exactly the fields and enum values present in the current schema. Treat the live schema as the request contract.

   **Use Studio Web's project scaffold and solution metadata.** After `CreateProjects` succeeds, inspect the project files exposed by the Studio Web workspace/VFS and edit the generated `.flow` entrypoint. If the creation tool or Flow project type is unavailable, report that capability gap and await user direction.
<!--skill-flavor:project-creation:end-->

<!--skill-flavor:upload-scope-bullets:start-->
<!--skill-flavor:upload-scope-bullets:end-->

<!--skill-flavor:upload-eval-scope-bullet:start-->
<!--skill-flavor:upload-eval-scope-bullet:end-->
