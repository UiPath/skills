# Studio Web Palette to BPMN XML Mapping

Studio Web's visual editor emits a specific combination of BPMN element class
and `uipath:type` value for each palette button. When authors hand-write XML
that does not match what a palette button would emit, Studio Web treats the
service task as a misconfigured external A2A activity, disables fields on the
node, and produces confusing validation noise. Use this table to pick the
exact element class and `uipath:type` for the palette button you intend, so
hand-written XML round-trips through Studio Web cleanly.

| Palette button | BPMN element | `uipath:type` value | Status |
| --- | --- | --- | --- |
| Task | `bpmn:task` | — (no UiPath type) | Verified - plain BPMN task |
| Agentic task | `bpmn:serviceTask` | TBD - verify against Studio Web output | Unverified |
| Sub-process | `bpmn:subProcess` | — | Verified |
| Service task (RPA) | `bpmn:serviceTask` | `Orchestrator.StartJob` | Verified |
| Service task (Agent job) | `bpmn:serviceTask` | `Orchestrator.StartAgentJob` | Draft - verify binding shape |
| Send task (Queue create) | `bpmn:sendTask` | `Orchestrator.CreateQueueItem` | Verified |
| Business rule task | `bpmn:businessRuleTask` | `Orchestrator.BusinessRules` | Verified |
| User task (HITL) | `bpmn:userTask` | `Actions.HITL` | Verified |

Rows marked Unverified or Draft are starting points only. The exact `uipath:type`
value, attribute shape, or binding requirements should be confirmed by exporting
a freshly-authored example from Studio Web and diffing against the row before
trusting it for production. Verified rows correspond to documented wrapper
shells in [wrapper-shells.md](wrapper-shells.md).

This file should grow as more palette buttons are observed against their
generated XML. Contributions adding a new row or upgrading a row from Draft or
Unverified to Verified are welcome - cite the Studio Web version used to
capture the mapping.
