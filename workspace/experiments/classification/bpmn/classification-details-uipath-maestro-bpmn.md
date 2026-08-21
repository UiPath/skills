# Classification Details — uipath-maestro-bpmn

**Classification: Partial**

---

## What the Skill Teaches

The skill covers five distinct work areas: authoring, validation, metadata management, operate (packaging / lifecycle), and diagnose. Below is a breakdown of each area and whether its procedures are codifiable.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | Registry discovery (pull / list / search / get, IS connections list) | No | CLI calls requiring user confirmation and intent mapping |
| 2 | Connector enrichment (`registry get --connection-id --object-name`) | No | CLI call; resource identifiers come from discovery or user |
| 3 | Template placeholder filling (`{id}`, `{name}`, `{incomingEdge}`, etc.) | No | Requires agent judgment for process structure and content |
| 4 | Structural BPMN authoring (process scaffold, sequence flows, gateways, events, boundary events, subprocesses, multi-instance markers) | No | Generative/creative; process shape comes from requirements |
| 5 | **Diagram generation (`bpmndi:BPMNDiagram`)** | **Yes — BUILD-MODEL** | Fixed sizes (tasks 100×80, events 36×36, gateways 50×50), left-to-right layout; fully deterministic given the process graph |
| 6 | **BPMN validation** | **Already scripted** | `validator/validate-bpmn.mjs` — runs all 19 PO.Frontend rules offline; this is an existing skill script, excluded per instructions |
| 7 | Expression authoring (`=vars.X`, `=bindings.X`, `=js:`, scoping rules) | Marginal | Rules are explicit but application is part of authoring; a post-hoc syntax checker is a VALIDATE, but minor value |
| 8 | **Package metadata scaffolding** (`project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`) | **Yes — FORMAT-CONVERT / BUILD-MODEL** | `local-metadata-regeneration-guide.md` gives exact JSON shapes and derivation rules from BPMN root elements |
| 9 | **Package metadata drift check** | **Yes — VALIDATE** | `local-metadata-regeneration-guide.md` §Drift Handling gives explicit rules: `entry-points.json` ids must match root `uipath:entryPointId`s; `bindings_v2.json` version must be `"2.0"`; `operate.json` must point at the correct BPMN file |
| 10 | Packaging (`uip maestro bpmn pack`) | No | CLI call |
| 11 | Upload / publish / deploy | No | CLI calls; require explicit user consent |
| 12 | Run / debug / manage instances | No | CLI calls; require explicit user consent and post-run judgment |
| 13 | Diagnose priority ladder (incidents → variables → deployed asset → element executions → package files → traces) | No | CLI reads requiring interpretation and analysis at each step |
| 14 | Agent wrapper selection (processType → extension type) | No (marginal) | A 4-row lookup table; too small to warrant a standalone script |

---

## Codifiable Procedures (not yet scripted)

the scripts are shipped as two cli commands: uip maestro bpmn format and uip maestro bpmn update-metadata