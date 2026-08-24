<!--skill-flavor:project-creation-scope:start-->
- Create a new Flow project through Studio Web's solution-level project-creation capability
<!--skill-flavor:project-creation-scope:end-->

<!--skill-flavor:project-creation:start-->
6. **Create Flow projects with the Studio Web project tool.** Before creating a project, inspect the live `CreateProjects` schema. Invoke that operation with the Flow project type using exactly the fields and enum values present in the current schema. Treat the live schema as the request contract.

   **Use Studio Web's project scaffold and solution metadata.** After `CreateProjects` succeeds, inspect the project files exposed by the Studio Web workspace/VFS and edit the generated `.flow` entrypoint. If the creation tool or Flow project type is unavailable, report that capability gap and await user direction.
<!--skill-flavor:project-creation:end-->

<!--skill-flavor:upload-scope-bullets:start-->
<!--skill-flavor:upload-scope-bullets:end-->

<!--skill-flavor:upload-eval-scope-bullet:start-->
<!--skill-flavor:upload-eval-scope-bullet:end-->
