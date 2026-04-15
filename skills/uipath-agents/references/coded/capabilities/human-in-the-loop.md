# Human-in-the-Loop & Interrupt/Resume

Pause agent execution for human approval, external processes, or job monitoring.

## Pause Patterns

**HITL pattern selection MUST be an interactive question unless the user named a specific pattern.** "Human in the loop", "approval", "confirmation", "review", "escalation" alone do NOT name a pattern.

If the user has not named one, your ENTIRE response must be a question that lists ONLY the patterns available for the already-selected framework (use the column matching the framework in the table below). Do NOT wrap it in headers, status summaries, or "I'll go with X". Just ask and stop.

| Pattern | When | LangGraph | LlamaIndex |
|---|---|---|---|
| API trigger | Resumed via an Orchestrator inbox URL; no Action Center involved | `interrupt({...})` | `InputRequiredEvent(...)` |
| Action Center task | Structured form for a human reviewer | `interrupt(CreateTask(...))` | `CreateTaskEvent(...)` |
| Escalation task | Task flagged as escalation | `interrupt(CreateEscalation(...))` | use `CreateTaskEvent` (no event-level distinction) |
| Wait for existing task | A task was already created elsewhere; resume when it completes | `interrupt(WaitTask(...))` | `WaitTaskEvent(...)` |
| Invoke a process | Trigger an RPA process; resume on completion | `interrupt(InvokeProcess(...))` | `InvokeProcessEvent(...)` |
| Wait for existing job | A job is running elsewhere; resume on its completion | `interrupt(WaitJob(...))` | `WaitJobEvent(...)` |

OpenAI Agents has no first-class HITL support. Coded Function (no framework) has no checkpoint/resume — call `sdk.actions.create()` then `sdk.actions.wait()` synchronously if a synchronous human step is needed.

LangGraph models live in `uipath.platform.common`; LlamaIndex events live in `uipath_llamaindex.models.events`.

## API Trigger

No Action Center app, no platform resource — pass a plain payload. The runtime allocates an inbox UUID and exposes it via an Orchestrator API URL; resume by POSTing JSON to that URL or via `--resume`.

### LangGraph

```python
from langgraph.types import interrupt

result = interrupt({"prompt": "Approve?", "category": state["category"]})
# Resume locally: uip codedagent run <ENTRYPOINT> --resume '{"approved": true}'
```

### LlamaIndex

```python
from llama_index.core.workflow import InputRequiredEvent, HumanResponseEvent

ctx.write_event_to_stream(InputRequiredEvent(prefix="Approve?"))
response = await ctx.wait_for_event(HumanResponseEvent)
```

## CreateTask — Send Work to a Human

```python
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.types import Command, interrupt
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

**Fields:**
- `title` — short task title
- `data` — payload shown to the human (dict). Keys must match the Action Center app's input schema, otherwise Orchestrator renders empty fields in the "Human review required" view.
- `app_name`, `app_folder_path` — target Action Center app and folder (use `app_folder_key` / `app_key` when the GUIDs are known)
- `assignee` — email of the user to assign (optional)
- `recipient`, `priority`, `labels`, `source_name`, `is_actionable_message_enabled`, `actionable_message_metadata` — optional metadata

**Return value:**
```python
{"status": "approved|rejected|pending", "assigned_to": "user@example.com", "completed_at": "...", ...}
```

### Escalation Variant

Swap `CreateTask` for `CreateEscalation` when the task is an escalation. Fields and return value are identical:

```python
from uipath.platform.common import CreateEscalation

task_output = interrupt(CreateEscalation(
    app_name="EscalationReview",
    app_folder_path="Finance",
    title="Threshold exceeded — needs director approval",
    data={"amount": state["amount"], "reason": state["flag_reason"]},
    assignee="director@example.com",
    priority="High",
))
```

**LlamaIndex equivalent:** `ctx.write_event_to_stream(CreateTaskEvent(app_name=..., app_folder_path=..., title=..., data={...}))` — same fields as `CreateTask`.

## WaitTask — Monitor Existing Task

```python
from uipath.platform.common import WaitTask

async def monitor_task(state: GraphState) -> Command:
    task_output = interrupt(WaitTask(task_id=state["existing_task_id"]))
    return Command(update={"task_result": task_output})
```

**LlamaIndex equivalent:** `ctx.write_event_to_stream(WaitTaskEvent(task_id=...))`

## InvokeProcess — Call RPA Automation

```python
from uipath.platform.common import InvokeProcess

result = interrupt(InvokeProcess(
    name="MyProcess",
    process_folder_path="Workflows",
    input_arguments={"data": request_data}
))
```

**LlamaIndex equivalent:** `ctx.write_event_to_stream(InvokeProcessEvent(name=..., process_folder_path=..., input_arguments={...}))`

## WaitJob — Monitor Existing Job

```python
from uipath.platform.common import WaitJob

output = interrupt(WaitJob(job_id=background_job_id))
```

**LlamaIndex equivalent:** `ctx.write_event_to_stream(WaitJobEvent(job_id=...))`

## Composite Examples

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

## Troubleshooting

- **"Task not found"**: Verify `app_name` and `app_folder_path` match Action Center config
- **"Assignee not found"**: Check email exists in UiPath org with Action Center access
- **Tasks not completing**: Check Action Center UI; verify assignee can see the task
- **Agent doesn't resume**: Ensure resumption logic handles all return values

## Reference

- [UiPath Human-in-the-Loop docs](https://uipath.github.io/uipath-python/langchain/human_in_the_loop/)
