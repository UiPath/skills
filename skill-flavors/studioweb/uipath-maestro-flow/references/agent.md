<!--skill-flavor:agent-scaffold:start-->
Studio Web cannot create a coded agent: it has no Python tooling (`uv`,
`uip codedagent`). Tell the user to create the coded agent in a terminal, or
reference an agent that exists:

- a published agent, found with the searches above;
- an agent project that is already in the open solution. From the Flow project
  folder, read its two identifiers with
  `uip maestro flow registry list --local --output json`. The generated
  `resources/solution_folder/process/*/<AgentProject>.json` carries the same
  pair: `resource.key` → `key`, `resource.projectKey` → `projectId`.

Then author the step with `location: 'in-solution'`:
<!--skill-flavor:agent-scaffold:end-->
