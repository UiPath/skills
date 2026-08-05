<!-- skill-flavor:author-surface:start -->
Capability index for creating and editing Flow projects inside the Studio Web browser workspace. Studio Web owns project creation, authentication, and solution membership. Authoring edits the host-generated `.flow` under `/solution/<project>/` and uses only file tools, live-advertised Flow CLI operations, and advertised project ProxyTools.

> For project creation, read `/skills/synthetic/proxy-tools-Solution/SKILL.md` and use its live `CreateProjects` schema. For an action on an existing Flow, first read `/skills/synthetic/proxy-tools-Flow/SKILL.md` when the per-turn directives advertise it. Do not infer either schema.

## When to use this capability

- Create a Flow project through Studio Web and then edit its generated `.flow`.
- Edit nodes, edges, variables, subflows, expressions, triggers, or layout in an existing `.flow`.
- Discover node types through a Flow registry command exposed by the live browser bundle.
- Validate or format with a live-advertised Flow capability.
- Configure connector, trigger, managed HTTP, and inline-agent nodes while preserving node ownership.
- Plan a complex Flow before building.
<!-- skill-flavor:author-surface:end -->

<!-- skill-flavor:project-creation-antipattern:start -->
- **Never use solution or Flow init commands in Studio Web.** Create the entity through live `CreateProjects`, inspect its generated tree, and preserve the scaffold. Do not create or repair a `.uipx`, manually register a project, or manufacture `/solution/<name>` as a directory.
<!-- skill-flavor:project-creation-antipattern:end -->
