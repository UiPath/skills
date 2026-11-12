<!--skill-flavor:planner-bpmn-row:start-->
| `uipath-maestro-bpmn` | `.bpmn` files — standards-based BPMN 2.0 process orchestration (gateways, events, boundary timeouts, subprocesses, multi-instance) over RPA, agents, APIs, HITL. Authors its own inline userTask/HITL nodes. | Yes (`uip login`) | **Yes** — packages, uploads, publishes/deploys, and runs via `uip maestro bpmn`; Orchestrator deploy of `.uipx`-wrapped solutions → `uipath-solution` |
<!--skill-flavor:planner-bpmn-row:end-->
<!--skill-flavor:bpmn-peer-orchestrator:start-->
> **BPMN is a peer orchestrator to Flow.** The same Pattern 2/3 structure applies to a Maestro BPMN process — swap `uipath-maestro-bpmn` for `uipath-maestro-flow`. As with Flow, inline `uipath:*` elements (scriptTask, businessRuleTask, connector, userTask/HITL) are authored by the BPMN specialist itself and are NOT separate components — only separate buildable projects (standalone RPA process, coded agent, coded app) fan out.
<!--skill-flavor:bpmn-peer-orchestrator:end-->
