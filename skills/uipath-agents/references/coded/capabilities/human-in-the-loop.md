# Human-in-the-Loop & Interrupt/Resume

Pause agent execution for human approval, external processes, or job monitoring.

> **Guardrail-triggered escalation is separate.** For automatic review on a guardrail violation (for example, PII or harmful content), use `EscalateAction` as a guardrail action — see [guardrails § Escalation action (HITL)](guardrails/guardrails.md#escalation-action-human-in-the-loop). This page covers **manual** pause points placed in agent code with `interrupt(...)`.

## Choose a pause pattern

**HITL pattern selection MUST be an interactive question unless the user named a specific pattern.** “Human in the loop”, “approval”, “confirmation”, “review”, and “escalation” alone do **not** name a pattern.

If no pattern was named, make your ENTIRE response a question listing ONLY the patterns available for the already-selected framework, using that framework’s column below. Do not add headers, status summaries, or “I’ll go with X”; ask and stop.

| Pattern | When | LangGraph | LlamaIndex |
|---|---|---|---|
| API trigger | Resume via an Orchestrator inbox URL; no Action Center involved | `interrupt({...})` | `InputRequiredEvent(...)` |
| Action Center task | Structured form for a human reviewer | `interrupt(CreateTask(...))` | `CreateTaskEvent(...)` |
| Escalation task | Task flagged as escalation | `interrupt(CreateEscalation(...))` | `CreateTaskEvent` (no event-level distinction) |
| Wait for existing task | A task was created elsewhere; resume when it completes | `interrupt(WaitTask(...))` | `WaitTaskEvent(...)` |
| Invoke a process | Trigger an RPA process; resume on completion | `interrupt(InvokeProcess(...))` | `InvokeProcessEvent(...)` |
| Wait for existing job | A job is running elsewhere; resume when it completes | `interrupt(WaitJob(...))` | `WaitJobEvent(...)` |

OpenAI Agents has no first-class HITL support. Coded Function (no framework) has no checkpoint/resume; call `sdk.tasks.create()` then `sdk.tasks.retrieve()` synchronously when a synchronous human step is needed.

LangGraph models are in `uipath.platform.common`; LlamaIndex events are in `uipath_llamaindex.models.events`.

## API Trigger

Use a plain payload: no Action Center app or platform resource. The runtime allocates an inbox UUID and exposes it through an Orchestrator API URL. Resume by POSTing JSON to that URL or with `--resume` for local runs.

### LangGraph

```python
from langgraph.types import interrupt

result = interrupt({"prompt": "Approve?", "category": state["category"]})
# Resume locally: uip codedagent run <ENTRYPOINT> --resume
```

### LlamaIndex

```python
from llama_index.core.workflow import InputRequiredEvent, HumanResponseEvent

ctx.write_event_to_stream(InputRequiredEvent(prefix="Approve?"))
response = await ctx.wait_for_event(HumanResponseEvent)
```

## CreateTask — Send Work to a Human

```python
from langgraph.types import Command, interrupt
from uipath.platform.common import CreateTask

task_output = interrupt(CreateTask(
    app_name="RequestReview",
    app_folder_path="MyFolderPath",
    title=f"Review Request: {state['request'][:50]}",
    data={"request": state["request"], "timestamp": str(datetime.now())},
    assignee="approver@example.com",
))
return Command(update={"approval_status": task_output.get("status", "pending")})
```

Fields:

- `title` — short task title.
- `data` — dict shown to the human. Keys must match the Action Center app’s input schema; otherwise Orchestrator renders empty fields in the “Human review required” view.
- `app_name`, `app_folder_path` — target Action Center app and folder. Use `app_folder_key` / `app_key` when GUIDs are known.
- `assignee` — optional email of the assigned user.
- Optional metadata: `recipient`, `priority`, `labels`, `source_name`, `is_actionable_message_enabled`, `actionable_message_metadata`.

Normal-task resume output:

```python
{"status": "approved|rejected|pending", "assigned_to": "user@example.com", "completed_at": "...", ...}
```

LlamaIndex equivalent:

```python
ctx.write_event_to_stream(CreateTaskEvent(
    app_name=..., app_folder_path=..., title=..., data={...}
))
```

Use the same fields as `CreateTask`.

### Escalation variant

Use `CreateEscalation` for an escalation. It extends `CreateTask` with the same fields. An escalation resumes with the full `Task`; a normal task resumes with `task.data`.

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

LlamaIndex uses `CreateTaskEvent` because it has no event-level escalation distinction.

## WaitTask — Monitor an Existing Task

```python
from uipath.platform.common import WaitTask

task_output = interrupt(WaitTask(action=state["existing_task"]))
return Command(update={"task_result": task_output})
```

LlamaIndex: `ctx.write_event_to_stream(WaitTaskEvent(action=...))`.

## InvokeProcess — Call RPA Automation

```python
from uipath.platform.common import InvokeProcess

result = interrupt(InvokeProcess(
    name="MyProcess",
    process_folder_path="Workflows",
    input_arguments={"data": request_data},
))
```

LlamaIndex: `ctx.write_event_to_stream(InvokeProcessEvent(name=..., process_folder_path=..., input_arguments={...}))`.

## WaitJob — Monitor an Existing Job

```python
from uipath.platform.common import WaitJob

output = interrupt(WaitJob(job=background_job, process_folder_path="Workflows"))
```

LlamaIndex: `ctx.write_event_to_stream(WaitJobEvent(job=..., process_folder_path=...))`.

## Composition

### Conditional interrupt

```python
if state["amount"] > 10000:
    result = interrupt(CreateTask(
        assignee="finance-director@example.com",
        title="Approve Large Request",
        app_name="ApprovalProcess",
        app_folder_path="Finance",
        data={"amount": state["amount"]},
    ))
else:
    result = interrupt(InvokeProcess(name="AutoApprovalProcess"))
return Command(update={"approval": result})
```

### Chained interrupts

```python
task1 = interrupt(CreateTask(...))
process_result = interrupt(InvokeProcess(
    input_arguments={"decision": task1.get("decision")}
))
task2 = interrupt(CreateTask(...))
return Command(update={"result": task2})
```

### Error handling

```python
result = interrupt(InvokeProcess(...))
if result.get("status") != "success":
    return Command(update={"error": result.get("error")})
```

## State management

Track interrupt context in graph state:

```python
class GraphState(MessagesState):
    request: str
    task_id: str | None = None
    task_result: dict | None = None
    final_response: str | None = None
```

## Best practices

- Pass complete context in `data` to avoid human back-and-forth.
- Use specific, actionable task titles.
- Provide structured choices such as approve/reject, not open-ended questions.
- Handle every possible return status in resumption logic.
- Route work to appropriate assignees based on task type.

## Troubleshooting

- **“Task not found”**: Verify `app_name` and `app_folder_path` match Action Center configuration.
- **“Assignee not found”**: Confirm the email exists in the UiPath organization and has Action Center access.
- **Tasks not completing**: Check the Action Center UI and verify the assignee can see the task.
- **Agent does not resume**: Ensure resumption logic handles all return values.

## Reference

- [UiPath Human-in-the-Loop docs](https://uipath.github.io/uipath-python/langchain/human_in_the_loop/)