# Critical Rules and Anti-Patterns

These rules are the canonical source for low-code agent authoring and apply to low-code autonomous and conversational agents. Capability files cross-reference this document. Also read [autonomous-critical-rules.md](autonomous-critical-rules.md) for autonomous agents and [conversational-critical-rules.md](conversational-critical-rules.md) for conversational agents.

## Critical Rules (20)

1. **Edit JSON files directly, except CLI-managed memory features.** Run `uip agent init` to scaffold, `uip agent refresh` to apply migrations and regenerate derived files, `uip agent validate` for a strict read-only check, and `uip agent memory` to write memory feature files. Edit configuration in `agent.json`; add tools, contexts, and escalations as `resources/{ResourceName}/resource.json`, not inline in `agent.json`. Add memory spaces with `uip agent memory`; they live in `features/{FeatureName}/feature.json`. Do not put `resources` or manually authored memory entries in root `agent.json`. `refresh` reads source files and generates `entry-points.json` and `bindings_v2.json`.

2. **Refresh and validate after every cohesive bulk of edits.** Run `uip agent refresh --output json`, then `uip agent validate --output json`. Refresh applies migrations and regenerates `entry-points.json` and `bindings_v2.json` only when all checks pass. Validate is strict read-only, never writes, and fails when migration is pending or derived files are out of sync.

3. **Use `--output json` on every `uip` command when parsing output.**

4. **Keep schemas in sync.** Make `inputSchema` and `outputSchema` in `agent.json` exactly mirror `input` and `output` in `entry-points.json`; update both when fields change.

5. **Use `{{input.fieldName}}` in message templates.** Never use `$vars` or `=js:` expressions; those are flow syntax.

6. **Keep `contentTokens` synchronized with `content`.** Every message requires both fields. See [agent-definition.md](../agent-definition.md) § contentTokens Construction.

7. **Never manually edit `entry-points.json` or `bindings_v2.json`.** Edit `agent.json` and `resources/{Name}/resource.json`, then run refresh.

8. **Obtain user consent before publishing or deploying.** Ask before running `uip solution upload`, `uip solution publish`, or `uip solution deploy`.

9. **Never modify `projectId`.** `uip agent init` generates it.

10. **Create a solution before scaffolding an agent.** Run `uip solution init` first.

11. **Set every required `folderPath` to the literal `Folder` returned by `uip solution resources list`.** Apply it to local (`Source: "Local"`) and external (`Source: "Remote"`) resources, tool `properties.folderPath`, context-index top-level `folderPath`, escalation `channel.properties.folderName`, and guardrail escalation `action.app.folderName`. Write it verbatim to `resource.json` or the guardrail action in `agent.json`. Local resources typically use `"solution_folder"`; external resources use the human-readable slash-separated Orchestrator folder, such as `"Shared"` or `"Shared/Sales/Region-EU"`. `uip agent refresh` propagates it to `bindings_v2.json`; App resources translate `folderName` to binding `folderPath`. See [capabilities/process/process.md](../capabilities/process/process.md) § Tool resource.json Shape.

12. **Set tool `location` explicitly.** Use `"solution"` for `Source: "Local"` and `"external"` for `Source: "Remote"`. Keep `type`, `referenceKey`, `folderPath`, schemas, and `exampleCalls` consistent in both cases. Connection (Integration Service) bindings use `connection.id` and do not propagate `folderPath`.

13. **Provide all required process-tool files.** For local or external process tools, create agent-level `resources/{ToolName}/resource.json`, solution-level files under `resources/solution_folder/`, and `userProfile/<userId>/debug_overwrites.json`. Run `uip solution resources refresh` to generate these from bindings. In-solution package and process declarations are pre-created when the project is registered with the solution: `uip agent init` registers with the parent `.uipx` inside a solution, or auto-scaffolds `<Name>Solution/` and registers outside one. If registration is `Skipped`, `Failed`, or `NotInSolution`, run `uip solution projects add`; `OptedOut` means `--skip-solution-registration` intentionally skipped both. Without these files, Studio Web reports “resource is missing in this environment”. See [capabilities/process/solution-files.md](../capabilities/process/solution-files.md).

14. **Never manually edit `storageVersion`.** `uip agent refresh` and Studio Web manage it. Validate reports `AgentValidationOutdated` when it is behind; run refresh. If it is newer than supported, upgrade uipcli.

15. **Never invoke other skills automatically.** For flow operations, tell the user to use the `uipath-maestro-flow` skill.

16. **Read [capabilities/guardrails/guardrails.md](../capabilities/guardrails/guardrails.md) before authoring guardrail JSON.** Its discriminator fields (`$guardrailType`, `$actionType`, `$parameterType`, `$ruleType`, `$selectorType`) are not guessable. Configure guardrails only in the root `agent.json` `guardrails` array.

17. **Treat `{{input.<file-field>}}` as metadata only.** For `job-attachment`, it exposes only `ID`, `FullName`, `MimeType`, and `Metadata`, not file contents. Add a file-handling built-in tool such as `analyze-attachments` and instruct the agent to call it. See [capabilities/built-in-tools/built-in-tools.md](../capabilities/built-in-tools/built-in-tools.md).

18. **Copy the canonical `job-attachment` schema verbatim.** Declare file fields as `{ "$ref": "#/definitions/job-attachment" }`, place the canonical block under `definitions`, and include `x-uipath-resource-kind: "JobAttachment"`. Use the same schema for input and output fields. See [agent-definition.md](../agent-definition.md) § File Attachments.

19. **Configure built-in tools explicitly.** Add each under `resources/{Name}/resource.json` with `type: "internal"` and `properties.toolType: "<kebab-lowercase-id>"`. Copy the fixed `toolType` discriminator from [capabilities/built-in-tools/built-in-tools.md](../capabilities/built-in-tools/built-in-tools.md); never invent it.

20. **Do not create solution-level files or run resource refresh for built-in tools.** `type: "internal"` tools are self-contained at the agent level. Validate the agent and bundle it.

## What NOT to Do (24)

1. **Do not manually edit `entry-points.json` or `bindings_v2.json`.** Edit `agent.json` and `resources/{ResourceName}/resource.json`; run `uip agent refresh`.

2. **Do not use `=js:` or `$vars` in agent messages.** Use `{{input.fieldName}}`.

3. **Do not leave schemas unsynchronized.** Make `agent.json` and `entry-points.json` match.

4. **Do not skip validation after a cohesive bulk of related edits.** Validate before moving to another capability or publishing.

5. **Do not publish or deploy without validating first.**

6. **Do not edit `content` without updating `contentTokens`.**

7. **Do not omit `uip solution resources refresh` after adding a process tool.** The agent-level resource is insufficient. After `uip agent refresh` generates `bindings_v2.json`, run `uip solution resources refresh` from the solution root. For `Connection`, refresh also generates `debug_overwrites.json`; for `Process`, `App`, and `Index`, it imports the resource but does not author rich solution-level files—check output and hand-author missing files per [capabilities/process/solution-files.md](../capabilities/process/solution-files.md).

8. **Do not treat `uip solution resources list` as full configuration.** It returns only `Source/Key/Name/Type/Folder/FolderKey`; run `uip solution resources get <KEY> --output json` and read `Data.spec`. For `--kind Process`, inspect argument schemas, package keys, and entry-point IDs; for `--kind Index`, inspect data source type and storage bucket reference. See [capabilities/process/process.md § Discovery](../capabilities/process/process.md#discovery) and [capabilities/context/index.md § Discovery](../capabilities/context/index.md#discovery).

9. **Do not reuse UUIDs between resources.** Give each resource, including each guardrail, a unique UUID.

10. **Do not bump `storageVersion` manually.** It breaks packager compatibility.

11. **Do not call raw Automation.Solutions REST APIs.** Use `uip solution` commands.

12. **Do not camelCase `contextType` or `retrievalMode` values.** Use `"datafabricentityset"`, `"deeprag"`, and `"batchtransform"` in lowercase; camelCase may validate but Studio Web silently drops the resource on import.

13. **Do not discover low-code connectors or activities with `uip is connectors list` or `uip is activities list`.** Run `uip is typecache packages` for connectors and `uip is typecache activities "<connector-key>"` for activities. These use Agent Builder typecache endpoints, default to `--project-type Agent`, filter empty-`objectName` deprecated stubs, include Preview file-operation and HTTP activities, return empty for connectors absent from the UI, and require no `--agent-id`; the general commands return the full Integration Service catalog.

14. **Do not omit guardrail discriminators.** Every action needs `$actionType` rather than `type`; every validator parameter needs `$parameterType` and `id` rather than `name`; every custom rule needs `$ruleType`; every field selector needs `$selectorType`.

15. **Do not use lowercase guardrail scope values.** Use `"Agent"`, `"Llm"`, and `"Tool"`.

16. **Do not expect `uip solution resources refresh` to wire non-StorageBucket index data sources.** GoogleDrive, OneDrive, Dropbox, Confluence, and Attachments indexes, `attachments` contexts, and `datafabricentityset` contexts are skipped with warnings; hand-author their solution-level files. See [capabilities/context/index.md](../capabilities/context/index.md).

17. **Do not add a Tool-scoped guardrail before its tool exists.** Run `uip agent tool list` and confirm every `selector.matchNames` name exists; validation fails otherwise.

18. **Do not omit `folderPath` on process tool resources.** Use the literal `Folder` from `uip solution resources list` for local and external resources. Validation reads the agent-level `resource.json`; refresh copies it to `bindings_v2.json`. Put the same value in the matching solution-level process declaration’s `folders[].fullyQualifiedName`.

19. **Do not hand-edit `bindings_v2.json`.** Edit the agent-level `resource.json` and run refresh.

20. **Do not pass attachments through the `uip` CLI.** `uip agent run` and solution-level CLI run paths do not support runtime file inputs. Test attachment-aware agents in Studio Web or through Orchestrator job invocation.

21. **Do not assume `{{input.<job-attachment>}}` provides file contents.** It provides metadata only; pair it with a file-handling built-in tool such as `analyze-attachments`.

22. **Do not run final inline-agent refresh or validation before flow graph edits.** For inline-in-flow agents, the `uipath-maestro-flow` skill owns direct `.flow` edits to the inline-agent node, capability-resource nodes, and edges. After those edits, run `uip agent refresh --inline-in-flow --bindings-target <FlowProjectDir>/bindings_v2.json`, then `uip agent validate --inline-in-flow`. Refresh propagates bindings into the flow project so `uip solution resources refresh` can discover them. Never hand-edit `bindings_v2.json`. See [capabilities/inline-in-flow/inline-in-flow.md](../capabilities/inline-in-flow/inline-in-flow.md).

23. **Do not switch autonomous and conversational variants by editing `agent.json` fields**, including `metadata.isConversational`. Re-initialize a new opposite-variant agent with `uip agent init`, using or omitting `--conversational`, then edit its `agent.json`. See [project-lifecycle.md](../project-lifecycle.md) § Agent Commands.

24. **Do not register a low-code conversational agent as another agent’s tool.** Conversational agents run through UiPath Conversational Service per exchange with threaded `messages`; they do not match the agent-tools input→output contract. Only autonomous agents may be tools of autonomous or conversational agents, both in-solution and deployed.
