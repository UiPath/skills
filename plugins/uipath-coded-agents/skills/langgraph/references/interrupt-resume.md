# Interrupt and Resume Patterns

Understanding how LangGraph agents pause and resume execution for external work, human intervention, or process delegation.

## Overview

The **interrupt/resume mechanism** is a core LangGraph pattern that enables agents to:

1. **Pause execution** at decision points
2. **Wait for external work** to complete (human decisions, process execution, job monitoring)
3. **Resume automatically** with results from the external work

This pattern is essential for building real-world agents that need to interact with humans, delegate tasks, or coordinate with external systems.

## How It Works

```
Agent Running → Hit Interrupt Point → Pause Execution
                                          ↓
                        External Work (Human, Process, Job)
                                          ↓
                        Work Completes → Get Results
                                          ↓
                        Resume Execution → Continue Agent Logic
```

### The Interrupt Function

Interrupts are triggered using the `interrupt()` function with a model representing the external work:

```python
from langgraph.types import interrupt

# Pause agent and request external work
result = interrupt(SomeModel(
    # Configuration for external work
))

# When external work completes, resume and get result
# Agent continues with 'result'
```

## Interrupt Models

UiPath LangChain provides four primary interrupt models for different scenarios:

### Human Intervention

| Model | Purpose | When to Use |
|-------|---------|------------|
| **CreateTask** | Create escalation in Action Center | Need human approval/review |
| **WaitTask** | Wait for existing task completion | Task created externally |

→ **Learn more:** [Human-in-the-Loop Guide](human-in-the-loop.md)

### External Automation

| Model | Purpose | When to Use |
|-------|---------|------------|
| **InvokeProcess** | Call RPA process and wait | Need to delegate RPA automation |
| **WaitJob** | Monitor existing job | Job created by external system |

→ **Learn more:** [Process Invocation Guide](process-invocation.md)

## Quick Comparison

### When to Use Each Pattern

**CreateTask** — Human approval needed:
```python
approval = interrupt(CreateTask(
    app_name="ApprovalApp",
    title="Review Request",
    assignee="manager@example.com"
))
```

**InvokeProcess** — RPA automation needed:
```python
result = interrupt(InvokeProcess(
    name="MyProcess",
    process_folder_path="Workflows",
    input_arguments={"data": request_data}
))
```

**WaitTask** — Monitor external task:
```python
outcome = interrupt(WaitTask(task_id=external_task_id))
```

**WaitJob** — Monitor external job:
```python
output = interrupt(WaitJob(job_id=background_job_id))
```

## Common Workflows

### Simple Approval Flow

```
User Request → Agent Analysis → CreateTask (Escalate) → Wait for Approval
                                      ↓
                              Manager Reviews in Action Center
                                      ↓
                        Resume with Approval Decision → Process Accordingly
```

### Data Processing Pipeline

```
Start → Extract Data (InvokeProcess) → Transform Data (InvokeProcess)
            ↓                               ↓
         Wait                           Wait
            ↓                               ↓
        Receive Data → Load Data (InvokeProcess) → End
                            ↓
                         Wait
                            ↓
                    Receive Confirmation
```

### Agent-in-the-Loop

```
Agent A → Analyzes Request → InvokeProcess (Delegate) → Agent B (via Process)
                                      ↓
                              RPA Automation Runs
                                      ↓
                        Resume Agent A with Results → Final Response
```

## Implementation Pattern

All interrupts follow the same pattern:

```python
from langgraph.graph import StateGraph
from langgraph.types import Command, interrupt
from uipath.platform.common import CreateTask  # or other model

async def my_node(state: GraphState) -> Command:
    """Node that uses interrupt/resume pattern."""

    # Prepare interrupt model
    interrupt_model = CreateTask(
        app_name="MyApp",
        title="Do Something",
        data={"key": "value"}
    )

    # Execute interrupt - agent pauses here
    result = interrupt(interrupt_model)

    # Resume here when external work completes
    # result contains the output from external work

    return Command(update={
        "field_name": result.get("status")
    })
```

## Key Concepts

### Pause Points

Interrupts are natural checkpoints where:
- Agent has enough information to request external work
- Agent cannot proceed without external input
- Clear completion criteria exist for external work

### Return Values

All interrupt models return structured data:

```python
{
    "status": "completed|success|approved|rejected",
    "output_field_1": "value",
    "output_field_2": 123,
    "error": "error message if failed"
}
```

### State Management

Use state to coordinate between pause and resume:

```python
class GraphState(MessagesState):
    request: str                           # Original request
    task_id: str | None = None            # Created during interrupt
    task_result: dict | None = None       # Populated after resume
    final_response: str | None = None     # Generated after resume
```

## Design Principles

### 1. **Clear Exit/Entry Points**
Define exactly what information is needed to interrupt and what will be returned:

```python
# Clear inputs and outputs
interrupt_model = CreateTask(
    app_name="ReviewApp",
    title="Review and Approve",
    data={
        "amount": state["amount"],
        "justification": state["justification"],
    }
)
result = interrupt(interrupt_model)
# Known return: {"status": "approved|rejected", "reviewer": "..."}
```

### 2. **Minimal Context Switch**
Include all necessary information in the interrupt to avoid human back-and-forth:

```python
# Good - provide complete context
data={
    "request_summary": state["summary"],
    "supporting_documents": state["docs"],
    "business_impact": state["impact"],
    "recommended_action": state["recommendation"]
}

# Bad - missing context, requires clarification
data={"request": state["request"]}
```

### 3. **Error Handling**
Handle cases where external work fails or times out:

```python
try:
    result = interrupt(InvokeProcess(...))
    if result.get("status") != "success":
        # Process failed
        return Command(update={"error": result.get("error")})
except Exception as e:
    # Timeout or communication error
    return Command(update={"error": f"Process failed: {str(e)}"})
```

### 4. **Resumption Logic**
Ensure agent can continue meaningfully based on external result:

```python
result = interrupt(CreateTask(...))

if result.get("status") == "approved":
    # Execute approval
    final_response = "Request approved"
elif result.get("status") == "rejected":
    # Handle rejection
    final_response = "Request rejected"
else:
    # Handle other cases
    final_response = "Request pending"

return Command(update={"response": final_response})
```

## Advanced Patterns

### Chained Interrupts

Multiple interrupts in sequence:

```python
async def multi_step_workflow(state: GraphState) -> Command:
    # Step 1: Get human input
    task1 = interrupt(CreateTask(...))

    # Step 2: Execute process based on input
    process_result = interrupt(InvokeProcess(
        input_arguments={"decision": task1.get("decision")}
    ))

    # Step 3: Get final approval
    task2 = interrupt(CreateTask(...))

    return Command(update={"result": task2})
```

### Conditional Interrupts

Choose interrupt type based on logic:

```python
async def conditional_workflow(state: GraphState) -> Command:
    if state["amount"] > 10000:
        # Large amounts need human approval
        result = interrupt(CreateTask(
            assignee="finance-director@example.com",
            title="Approve Large Request"
        ))
    else:
        # Small amounts can be auto-processed
        result = interrupt(InvokeProcess(
            name="AutoApprovalProcess"
        ))

    return Command(update={"approval": result})
```

### Fallback Patterns

Handle interrupt failure with fallback:

```python
async def workflow_with_fallback(state: GraphState) -> Command:
    try:
        result = interrupt(CreateTask(
            assignee="primary-approver@example.com",
            title="Request Approval"
        ))
    except Exception:
        # Primary approver unavailable, escalate
        result = interrupt(CreateTask(
            assignee="backup-approver@example.com",
            title="Request Approval (Escalated)"
        ))

    return Command(update={"approval": result})
```

## Best Practices

### Design Checklist

- ✅ Clear purpose for interrupt (why pause execution?)
- ✅ Complete information passed to external work
- ✅ Defined return value structure
- ✅ Error handling for failures
- ✅ Timeout/timeout strategy
- ✅ Clear resumption logic
- ✅ State tracking for audit/troubleshooting
- ✅ User-friendly task/process names

### Monitoring

Track interrupts for observability:

```python
from uipath.tracing import traced

@traced(name="escalation", span_type="tool")
async def escalate_with_tracing(state: GraphState) -> Command:
    result = interrupt(CreateTask(...))
    # Trace automatically captures:
    # - When interrupt occurred
    # - What was requested
    # - How long external work took
    # - Final result
    return Command(update={"result": result})
```

## Troubleshooting

**Interrupt never completes:**
- Check external system (Action Center, Orchestrator) for issues
- Verify timeout settings
- Check logs for error messages

**Wrong return value type:**
- Verify external work returns expected structure
- Add defensive parsing: `result.get("field", default_value)`
- Log actual result for debugging

**Agent doesn't resume properly:**
- Ensure resumption logic handles all possible return values
- Check error handling covers all failure cases
- Add logging at resume point to track execution flow

## See Also

- **[Human-in-the-Loop Guide](human-in-the-loop.md)** — Detailed CreateTask and WaitTask patterns
- **[Process Invocation Guide](process-invocation.md)** — Detailed InvokeProcess and WaitJob patterns
- **[Context Grounding Guide](context-grounding.md)** — Combining interrupts with document search