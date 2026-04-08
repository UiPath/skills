# Build Plan: `uipath-lattice-flow` Skill — Phase 2 (Dynamic Resource Nodes)

## Context

Phase 1 (OOTB Nodes) shipped in commit `f921b21` — 35 files covering all 19 OOTB node types, 8 templates, 7 guides. Phase 2 adds support for dynamic resource nodes: RPA Workflow, Agent, API Workflow, and Agentic Process. These are nodes that reference external Orchestrator resources and require registry data for their `inputDefinition`/`outputDefinition`.

The goal is to document the static structure of each resource type (handleConfiguration, model shape, display properties) so the agent only needs registry data for the resource-specific parts (arguments, output schemas, resource keys).

## Canonical Resource Type Mapping

Source: `flow-workbench/packages/flow-core/src/manifest/shared/resource-type-metadata.ts`

| ResourceType | serviceType | categoryId | icon | nodeType pattern |
|---|---|---|---|---|
| `Process` | `Orchestrator.StartJob` | `rpa-workflow` | `rpa` | `uipath.core.rpa-workflow.<key>` |
| `Agent` | `Orchestrator.StartAgentJob` | `agent` | `autonomous-agent` | `uipath.core.agent.<key>` |
| `ProcessOrchestration` | `Orchestrator.StartAgenticProcess` | `agentic-process` | `agentic-process` | `uipath.core.agentic-process.<key>` |
| `Api` | `Orchestrator.ExecuteApiWorkflowAsync` | `api-workflow` | `api` | `uipath.core.api-workflow.<key>` |

Note: `uipath.core.process.<key>` is an older alias for `uipath.core.rpa-workflow.<key>` — both use `Process` resource type.

## Shared Structure (All Resource Types)

All four resource types share identical:
- `version`: `"1.0.0"`
- `supportsErrorHandling`: `true`
- `handleConfiguration`: left=`input` (target), right=`output` (source) + `error` (source, conditional)
- `model.type`: `"bpmn:ServiceTask"`
- `model.version`: `"v2"`
- `model.bindings.resource`: `"process"` (always)
- `model.context`: 3 entries (name, folderPath, _label)
- `debug`: `{ "runtime": "bpmnEngine" }`
- `toolbarExtensions`: open-workflow action
- Error output in `outputDefinition`
- Icon gradients (per type)

What varies per instance:
- `nodeType` (includes resource UUID/key)
- `model.serviceType`, `model.bindings.resourceSubType`, `model.bindings.orchestratorType`
- `model.bindings.resourceKey`, `model.bindings.values` (name, folderPath)
- `model.projectId`
- `inputDefinition`, `outputDefinition` (resource-specific arguments)
- `form` (generated from inputDefinition)
- `display.label`, `display.icon`, `display.iconBackground`

## Bindings Pattern

Each resource node contributes 2 entries to the top-level `bindings[]` array:

```json
{ "id": "bXXXXXXXX", "name": "name", "type": "string", "resource": "process",
  "resourceKey": "<UUID>", "default": "<ProcessName>", "propertyAttribute": "name",
  "resourceSubType": "<Process|Agent|...>" }
{ "id": "bYYYYYYYY", "name": "folderPath", "type": "string", "resource": "process",
  "resourceKey": "<UUID>", "default": "<FolderPath>", "propertyAttribute": "folderPath",
  "resourceSubType": "<Process|Agent|...>" }
```

The node instance's `model.context` references these via `"=bindings.bXXXXXXXX"`.

## File Manifest (6 new files + 3 edits)

### Phase 2a: Shared Structure + RPA Workflow (2 new + 1 edit)

| # | File | Source |
|---|---|---|
| 1 | `references/dynamic-nodes/resource-node-guide.md` | resource-type-metadata.ts + node-manifest-builder.ts + proposal |
| 2 | `references/dynamic-nodes/rpa-workflow-guide.md` | hr-onboarding reference flow RPA nodes |
| 3 | `SKILL.md` update | Add dynamic node workflow, update critical rules, remove `[PREVIEW]` |

### Phase 2b: Agent (1 new)

| # | File | Source |
|---|---|---|
| 4 | `references/dynamic-nodes/agent-guide.md` | hr-onboarding + devconnect-email agent nodes |

### Phase 2c: API Workflow (1 new)

| # | File | Source |
|---|---|---|
| 5 | `references/dynamic-nodes/api-workflow-guide.md` | Constructed from resource-type-metadata pattern |

### Phase 2d: Agentic Process (1 new)

| # | File | Source |
|---|---|---|
| 6 | `references/dynamic-nodes/agentic-process-guide.md` | Constructed from resource-type-metadata pattern |

### Phase 2e: Retire maestro-flow (2 edits)

| # | File | Change |
|---|---|---|
| 7 | `skills/uipath-maestro-flow/SKILL.md` | Update description to `"Retired→uipath-lattice-flow"` |
| 8 | `skills/uipath-planner/SKILL.md` | Replace `uipath-maestro-flow` references with `uipath-lattice-flow` |

## Guide Content Plan

### `resource-node-guide.md` (~250 lines)

The shared reference for all dynamic resource nodes:

1. **Resource Type Table** — all 4 types with serviceType, category, icon, nodeType pattern
2. **Shared Definition Template** — the static JSON skeleton with `<PLACEHOLDERS>` for variable fields
3. **Shared Node Instance Template** — the static JSON skeleton
4. **Handle Configuration** — verbatim JSON (same for all types)
5. **Bindings Pattern** — how to create the 2 binding entries per resource node, binding ID generation, how model.context references them
6. **Registry Interaction** — exact CLI commands:
   ```bash
   uip flow registry pull --force
   uip flow registry search "<NAME>" --output json
   uip flow registry get "<NODE_TYPE>" --output json
   ```
7. **Step-by-Step: Add a Resource Node** — numbered procedure
8. **`variables.nodes` for Resource Nodes** — outputs come from the registry's outputDefinition
9. **Placeholder Pattern** — use `core.logic.mock` when resource isn't published yet

### `rpa-workflow-guide.md` (~150 lines)

1. **Type Parameters** — serviceType, resourceSubType, orchestratorType, icon, category, gradients
2. **Complete Example** — full node instance + definition from hr-onboarding's `AO_HRO_HITLWrapper`
3. **Input/Output Patterns** — `in_*` / `out_*` prefix convention, .NET type mapping
4. **Common Mistakes**

### `agent-guide.md` (~150 lines)

1. **Type Parameters** — serviceType, resourceSubType, orchestratorType, icon, category, gradients
2. **Complete Example** — from hr-onboarding's `JobOfferAcceptanceDeciderAgent`
3. **Personal Workspace Agents** — resourceKey is path string (not UUID)
4. **Common Mistakes**

### `api-workflow-guide.md` (~100 lines)

1. **Type Parameters** — serviceType: `Orchestrator.ExecuteApiWorkflowAsync`, rest from pattern
2. **Constructed Example** — built from shared template with API-specific values
3. **Key Differences** — async execution

### `agentic-process-guide.md` (~100 lines)

1. **Type Parameters** — serviceType: `Orchestrator.StartAgenticProcess`, resourceSubType: `ProcessOrchestration`
2. **Constructed Example** — built from shared template
3. **Note** — Flow resources also use `StartAgenticProcess` with `flow` category

### SKILL.md Updates

1. Remove `[PREVIEW]` from description
2. Add "Workflow: Add a Resource Node" under Common Edits
3. Update Critical Rule 7 reference to dynamic-nodes guides
4. Update Reference Navigation table
5. Add dynamic node types to the OOTB Node Types table (new section: "Dynamic Resource Node Types")

### Planner Updates

Replace all `uipath-maestro-flow` references in `skills/uipath-planner/SKILL.md`:
- Skill catalog table row (line 32)
- Multi-skill workflow "Flow + missing resources" (lines 54-61)
- Multi-skill workflow "Flow → Orchestrator" (lines 68-76)
- Project detection table (line 142)

## Execution Strategy

- **Batch A** (parallel): resource-node-guide.md + rpa-workflow-guide.md + agent-guide.md
- **Batch B** (parallel): api-workflow-guide.md + agentic-process-guide.md
- **Batch C** (direct): SKILL.md update + maestro-flow retirement + planner update

## Verification

1. All new files linked from SKILL.md Reference Navigation
2. Resource type table matches `resource-type-metadata.ts` exactly
3. Example JSON in RPA/agent guides matches actual reference flow data
4. `description` field still under 250 chars after removing `[PREVIEW]`
5. maestro-flow description updated to redirect
6. Planner references all updated to `uipath-lattice-flow`
