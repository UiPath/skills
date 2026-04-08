# Human-in-the-Loop & Interrupt/Resume

> **Agent type: Both coded and low-code agents.** Coded agents use LangGraph's `interrupt()` with UiPath platform models (`CreateTask`, `WaitTask`, `InvokeProcess`, `WaitJob`) — see the [Coded Agents](#coded-agents) sections below. Low-code agents declare an `escalation` resource in `agent.json` — see the [Low-Code Agents](#low-code-agents) section.

Pause agent execution for human approval, external processes, or job monitoring using LangGraph's `interrupt()` function.

## Coded Agents

## How Interrupts Work

> **Required: compile the graph with a `checkpointer`.** Without a checkpointer, `interrupt()` will pause execution but the graph cannot resume — the state is lost. Use `MemorySaver` for local development and testing:
> ```python
> from langgraph.checkpoint.memory import MemorySaver
> graph = builder.compile(checkpointer=MemorySaver())
> ```
> UiPath's managed runtime provides a production checkpointer automatically when the agent is deployed — `MemorySaver` is for local `uip codedagent run` only.

```
Agent Running → interrupt(model) → Pause → External Work → Resume with Result
```

```python
from langgraph.types import interrupt
result = interrupt(SomeModel(...))  # Agent pauses here, resumes with result
```

## Interrupt Models

| Model | Import | Purpose |
|-------|--------|---------|
| `CreateTask` | `uipath.platform.common` | Create escalation in Action Center |
| `WaitTask` | `uipath.platform.common` | Wait for existing task completion |
| `InvokeProcess` | `uipath.platform.common` | Call RPA process and wait |
| `WaitJob` | `uipath.platform.common` | Monitor existing job |

## CreateTask — Escalate to Human

```python
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.types import Command, interrupt
from langchain_core.messages import ToolMessage
from uipath.platform.common import CreateTask

class GraphState(MessagesState):
    request: str
    approval_status: str | None = None

async def escalate_to_human(state: GraphState) -> Command:
    task_output = interrupt(CreateTask(
        app_name="RequestReview",
        app_folder_path="MyFolderPath",
        title=f"Review Request: {state['request'][:50]}",
        data={
            "request": state["request"],
            "timestamp": str(datetime.now())
        },
        assignee="approver@example.com"
    ))
    return Command(update={
        "approval_status": task_output.get("status", "pending"),
    })
```

**CreateTask fields:** `app_name`, `app_folder_path`, `title`, `data` (dict), `assignee` (email, optional)

**Return value:**
```python
{"status": "approved|rejected|pending", "assigned_to": "user@example.com", "completed_at": "...", ...}
```

## WaitTask — Monitor Existing Task

```python
from uipath.platform.common import WaitTask

async def monitor_task(state: GraphState) -> Command:
    task_output = interrupt(WaitTask(task_id=state["existing_task_id"]))
    return Command(update={"task_result": task_output})
```

## InvokeProcess — Call RPA Automation

```python
from uipath.platform.common import InvokeProcess

result = interrupt(InvokeProcess(
    name="MyProcess",
    process_folder_path="Workflows",
    input_arguments={"data": request_data}
))
```

## WaitJob — Monitor Existing Job

```python
from uipath.platform.common import WaitJob

output = interrupt(WaitJob(job_id=background_job_id))
```

## Patterns

### Conditional Interrupt

```python
async def conditional_workflow(state: GraphState) -> Command:
    if state["amount"] > 10000:
        result = interrupt(CreateTask(
            assignee="finance-director@example.com",
            title="Approve Large Request",
            app_name="ApprovalProcess",
            app_folder_path="Finance",
            data={"amount": state["amount"]}
        ))
    else:
        result = interrupt(InvokeProcess(name="AutoApprovalProcess"))
    return Command(update={"approval": result})
```

### Chained Interrupts

```python
async def multi_step_workflow(state: GraphState) -> Command:
    task1 = interrupt(CreateTask(...))  # Step 1: human input
    process_result = interrupt(InvokeProcess(
        input_arguments={"decision": task1.get("decision")}
    ))  # Step 2: RPA based on input
    task2 = interrupt(CreateTask(...))  # Step 3: final approval
    return Command(update={"result": task2})
```

### Error Handling

```python
result = interrupt(InvokeProcess(...))
if result.get("status") != "success":
    return Command(update={"error": result.get("error")})
```

## State Management

Track interrupt context in graph state:

```python
class GraphState(MessagesState):
    request: str
    task_id: str | None = None
    task_result: dict | None = None
    final_response: str | None = None
```

## Best Practices

- Pass complete context in `data` to avoid human back-and-forth
- Use specific, actionable task titles
- Provide structured choices (approve/reject), not open-ended questions
- Handle all possible return statuses in resumption logic
- Route to appropriate assignees based on task type

## Low-Code Agents

For low-code agents, human-in-the-loop is configured declaratively by adding an `escalation` resource to the `"resources"` array in `agent.json`. No Python code or `interrupt()` is required — the agent runtime handles pausing and resuming automatically when it decides to escalate.

```json
{
  "$resourceType": "escalation",
  "name": "Manager Approval",
  "description": "Escalate to a human manager when the action exceeds the agent's authority or confidence. Provide a summary of what you are asking to approve.",
  "escalationType": 0,
  "isAgentMemoryEnabled": false,
  "channels": [
    {
      "name": "Channel",
      "type": "actionCenter",
      "description": "Approval channel for sensitive actions.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "Content": { "type": "string" },
          "Comment": { "type": "string", "description": "Context for the reviewer" }
        }
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "Comment": { "type": "string", "description": "Reviewer's response or decision" }
        }
      },
      "outcomeMapping": { "approve": "continue", "reject": "continue" },
      "recipients": [
        { "type": 1, "value": "user-or-group-uuid", "displayName": "Review Team" }
      ],
      "properties": {
        "appName": "HITL App",
        "appVersion": 1,
        "resourceKey": "action-center-app-uuid",
        "isActionableMessageEnabled": false
      }
    }
  ]
}
```

**`isAgentMemoryEnabled`:** Set to `true` to have the agent learn from resolved escalations and auto-resolve similar cases in the future. Keep `false` for privacy-sensitive workflows.

**`recipients[].type`:** `1` = User ID, `2` = Group ID, `3` = User email.

For the full `escalation` resource schema and all options, see [lowcode/resources-reference.md](../lowcode/resources-reference.md).

---

## Troubleshooting

- **"Task not found"**: Verify `app_name` and `app_folder_path` match Action Center config
- **"Assignee not found"**: Check email exists in UiPath org with Action Center access
- **Tasks not completing**: Check Action Center UI; verify assignee can see the task
- **Agent doesn't resume**: Ensure resumption logic handles all return values

## Reference

- [UiPath Human-in-the-Loop docs](https://uipath.github.io/uipath-python/langchain/human_in_the_loop/)
