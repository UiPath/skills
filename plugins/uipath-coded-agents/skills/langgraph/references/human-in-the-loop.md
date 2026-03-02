# Human-in-the-Loop Guide

How to implement human approval and intervention workflows in LangGraph agents using UiPath Action Center escalation.

> **First time here?** Read [Interrupt and Resume Patterns](interrupt-resume.md) for a conceptual overview of how agent pausing and resumption works.

## Overview

**Human-in-the-Loop** enables agents to pause execution and request human intervention before resuming. This is essential for workflows requiring human approval, review, or decision-making. The feature is implemented through the `interrupt(model)` function within the LangGraph framework.

## Core Concepts

The pattern enables two primary scenarios:

1. **Human Escalation** — Pause execution and route work to a human reviewer in Action Center
2. **Robot/Agent-in-the-Loop** — Pause execution while waiting for another agent or process to complete

## Implementation

### CreateTask — Escalate to Human Review

Create an escalation task in UiPath Action Center for human review and decision-making.

```python
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from uipath.platform.common import CreateTask

class GraphState(MessagesState):
    request: str
    approval_status: str | None = None
    result: str | None = None

async def process_request(state: GraphState) -> Command:
    """Process request and prepare for escalation."""
    # ... implement your processing logic ...
    return Command(update={"messages": state["messages"]})

async def escalate_to_human(state: GraphState) -> Command:
    """Create escalation task in Action Center."""
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
        "messages": state["messages"] + [
            ToolMessage(
                content=f"Task created: {task_output}",
                tool_call_id="escalate"
            )
        ]
    })

async def finalize(state: GraphState) -> Command:
    """Process human decision."""
    if state["approval_status"] == "approved":
        result = "Request approved and processed"
    else:
        result = "Request denied"

    return Command(update={"result": result})

builder = StateGraph(GraphState)
builder.add_node("process", process_request)
builder.add_node("escalate", escalate_to_human)
builder.add_node("finalize", finalize)

builder.add_edge(START, "process")
builder.add_edge("process", "escalate")
builder.add_edge("escalate", "finalize")
builder.add_edge("finalize", END)

graph = builder.compile()
```

### WaitTask — Monitor Existing Tasks

Wait for a previously-created task to complete. Use this when tasks are created outside the agent.

```python
from uipath.platform.common import WaitTask
from langgraph.types import Command

async def monitor_task(state: GraphState) -> Command:
    """Wait for an existing task to complete."""
    task_id = state.get("existing_task_id")

    task_output = interrupt(WaitTask(task_id=task_id))

    return Command(update={
        "task_result": task_output,
        "messages": state["messages"] + [
            ToolMessage(
                content=f"Task {task_id} completed with result: {task_output}",
                tool_call_id="wait_task"
            )
        ]
    })
```

## Action Center Configuration

### Task Fields

When creating tasks with `CreateTask`, you can specify:

- `app_name` — Name of the Action Center app
- `app_folder_path` — Folder path in Orchestrator
- `title` — Task title displayed in Action Center
- `data` — Dictionary of task data fields (custom fields)
- `assignee` — Email address of the assigned user (optional)

### Return Values

Task escalation returns task output data, which includes:

```python
{
    "status": "approved|rejected|pending",
    "assigned_to": "user@example.com",
    "completed_at": "2024-01-15T10:30:00Z",
    "custom_field_1": "value",
    # ... other task data fields ...
}
```

## Common Patterns

### Approval Workflow

```python
async def approval_workflow(state: GraphState) -> Command:
    """Request approval from a specific person."""
    task = interrupt(CreateTask(
        app_name="ApprovalProcess",
        app_folder_path="ApprovalFolder",
        title=f"Approve: {state['request_title']}",
        data={
            "amount": state.get("amount"),
            "description": state.get("description"),
            "requester": state.get("requester")
        },
        assignee="finance-lead@example.com"
    ))

    approved = task.get("status") == "approved"

    return Command(update={
        "approval_granted": approved,
        "approver": task.get("assigned_to")
    })
```

### Multi-Step Review

```python
async def multi_step_review(state: GraphState) -> Command:
    """Route through multiple reviewers."""
    reviewers = ["reviewer1@example.com", "reviewer2@example.com"]
    results = []

    for reviewer in reviewers:
        result = interrupt(CreateTask(
            app_name="ReviewProcess",
            app_folder_path="ReviewFolder",
            title=f"Review Item: {state['item_id']}",
            data=state.get("item_data", {}),
            assignee=reviewer
        ))
        results.append(result)

    all_approved = all(r.get("status") == "approved" for r in results)

    return Command(update={
        "review_results": results,
        "all_approved": all_approved
    })
```

### Exception Handling

```python
async def escalate_exception(state: GraphState) -> Command:
    """Escalate exceptions to human handler."""
    try:
        # ... agent processing ...
        pass
    except Exception as e:
        # Escalate to exception handler
        task = interrupt(CreateTask(
            app_name="ExceptionHandler",
            app_folder_path="ErrorHandling",
            title=f"Exception: {state['process_name']}",
            data={
                "error": str(e),
                "context": state.get("context"),
                "timestamp": str(datetime.now())
            },
            assignee="error-handler@example.com"
        ))

        if task.get("resolution") == "retry":
            return Command(update={"should_retry": True})
        else:
            return Command(update={"should_abort": True})
```

## Best Practices

### Task Design

- **Clear Titles**: Use specific, actionable task titles
- **Relevant Data**: Include all context needed for human decision
- **Assignee Selection**: Route to the appropriate person/team
- **Timeout Handling**: Consider SLAs for task completion

### Workflow Design

- **Minimal Context Switch**: Pass complete information to avoid back-and-forth
- **Clear Options**: Provide structured choices (approve/reject, not open-ended)
- **Audit Trail**: Log who approved what and when
- **Fallback Handling**: Define what happens if task is ignored or rejected

### Error Handling

```python
async def create_task_with_fallback(state: GraphState) -> Command:
    """Create task with fallback escalation."""
    try:
        task = interrupt(CreateTask(
            app_name="ReviewProcess",
            app_folder_path="ReviewFolder",
            title="Review Required",
            data=state.get("data", {}),
            assignee="primary-reviewer@example.com"
        ))
    except Exception as e:
        # Fallback escalation
        task = interrupt(CreateTask(
            app_name="ReviewProcess",
            app_folder_path="ReviewFolder",
            title="Review Required (Fallback)",
            data={
                **state.get("data", {}),
                "escalation_reason": str(e)
            },
            assignee="backup-reviewer@example.com"
        ))

    return Command(update={"task_result": task})
```

## Conversational Agents with Human-in-the-Loop

For chat-based agents that require human intervention:

```python
from pydantic import BaseModel, Field

class GraphInput(BaseModel):
    user_message: str = Field(description="User message")

class GraphOutput(BaseModel):
    response: str = Field(description="Agent response")

async def chat_with_escalation(state: GraphState) -> Command:
    """Process user message with optional human escalation."""
    llm = UiPathAzureChatOpenAI()

    # First attempt with LLM
    response = await llm.ainvoke(state["messages"])

    # Check if escalation needed
    if requires_escalation(response.content):
        task = interrupt(CreateTask(
            app_name="ChatEscalation",
            app_folder_path="Support",
            title="Chat Escalation",
            data={"conversation": state["messages"]},
            assignee="support-agent@example.com"
        ))
        final_response = task.get("agent_response", response.content)
    else:
        final_response = response.content

    return Command(update={
        "response": final_response,
        "messages": state["messages"] + [
            SystemMessage(content=final_response)
        ]
    })
```

## Integration with Other Patterns

Human-in-the-loop works well with:

- **Context Grounding** — Include relevant documents in escalation data
- **Process Invocation** — Escalate to human or invoke process based on logic
- **Tool Calling** — Make human approval a tool in tool-calling agents
- **Error Handling** — Escalate unexpected errors to human handlers

## Troubleshooting

**"Task not found" errors:**
- Verify the `app_name` and `app_folder_path` match your Action Center configuration
- Ensure the UiPath account has Action Center enabled

**"Assignee not found":**
- Check that the email address exists in your UiPath organization
- Verify the user has access to the Action Center app

**Tasks not completing:**
- Check Action Center UI for task status
- Verify the assignee can see the task
- Consider setting task deadlines/SLAs

## Reference

For detailed API documentation, see the [UiPath Human-in-the-Loop documentation](https://uipath.github.io/uipath-python/langchain/human_in_the_loop/).