# Task Recipes

Use these recipes after the BPMN skeleton is chosen. They describe how confirmed
UiPath resource-backed work maps onto standard BPMN task classes during pass 2.
Individual recipe files assume the pass-1 model is already selected; they are
not process-modeling guidance.

> Copyable minimal XML shell per wrapper: [../../../shared/wrapper-shells.md](../../../shared/wrapper-shells.md). Each recipe below describes when to use it and what fields are model- versus CLI-owned; copy the matching shell from `wrapper-shells.md` for the exact XML.

| Need | BPMN element | Recipe |
| --- | --- | --- |
| Start an RPA process | `bpmn:serviceTask` | [rpa-job.md](rpa-job.md) |
| Start a UiPath agent or A2A agent | `bpmn:serviceTask` | [agent-job.md](agent-job.md) |
| Invoke a deployed Python coded agent end-to-end | `bpmn:serviceTask` | [python-coded-agent.md](python-coded-agent.md) |
| Execute an API workflow | `bpmn:serviceTask` | [api-workflow.md](api-workflow.md) |
| Implement confirmed request-and-continue plain HTTP | `bpmn:sendTask` | [http-request.md](http-request.md) |
| Create a queue item | `bpmn:sendTask` | [queue.md](queue.md) |
| Create and wait for a queue item | `bpmn:serviceTask` | [queue.md](queue.md) |
| Execute a business rule | `bpmn:businessRuleTask` | [business-rule.md](business-rule.md) |
| Create an Action Center human task | `bpmn:userTask` | [hitl.md](hitl.md) |
| Call an agentic or case-management process | `bpmn:callActivity` | [call-activity.md](call-activity.md) |

Rules:

- Do not create Flow-style peer nodes in BPMN. Keep the BPMN element class visible in the XML.
- Pass 1 still owns process modeling. Apply these recipes only after the BPMN
  skeleton is chosen and the resource-backed node is ready for implementation.
- Resource identity, folder binding, and dynamic schemas are resolved by CLI/operator unless this skill has a documented public-safe shell contract.
- Keep resource names synthetic or placeholder-safe in examples.
- Put routing logic on sequence flows and gateways after the task, not inside the resource recipe.
