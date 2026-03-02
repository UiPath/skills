# Process and Job Invocation Guide

How to invoke external processes and monitor job execution in LangGraph agents using UiPath automation capabilities.

> **First time here?** Read [Interrupt and Resume Patterns](interrupt-resume.md) for a conceptual overview of how agent pausing and resumption works.

## Overview

**Process Invocation** enables agents to delegate work to external RPA processes, API calls, or other agents, then resume automatically. This pattern is essential for:

- Delegating complex RPA workflows to processes
- Calling external services or APIs
- Agent-in-the-loop scenarios where multiple agents collaborate
- Decoupling agent logic from business process execution

## Core Models

The framework provides two primary models for process/job invocation:

1. **InvokeProcess** — Calls external processes and waits for completion
2. **WaitJob** — Monitors already-created job execution

## InvokeProcess — Invoke External Processes

Call an external process in Orchestrator and wait for it to complete automatically.

```python
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.types import Command
from uipath.platform.common import InvokeProcess

class GraphState(MessagesState):
    request: str
    process_result: dict | None = None

async def invoke_automation(state: GraphState) -> Command:
    """Invoke an external RPA process."""
    process_output = interrupt(InvokeProcess(
        name="MyProcess",
        process_folder_path="MyFolderPath",
        input_arguments={
            "argument1": "value1",
            "argument2": state.get("request")
        }
    ))

    return Command(update={
        "process_result": process_output,
        "messages": state["messages"] + [
            ToolMessage(
                content=f"Process completed: {process_output}",
                tool_call_id="invoke_process"
            )
        ]
    })

builder = StateGraph(GraphState)
builder.add_node("invoke", invoke_automation)
builder.add_edge(START, "invoke")
builder.add_edge("invoke", END)

graph = builder.compile()
```

## WaitJob — Monitor Existing Jobs

Wait for a previously-created job to complete. Use this when jobs are created externally or asynchronously.

```python
from uipath.platform.common import WaitJob
from langgraph.types import Command

async def wait_for_job(state: GraphState) -> Command:
    """Wait for an existing job to complete."""
    job_id = state.get("external_job_id")

    job_output = interrupt(WaitJob(job_id=job_id))

    return Command(update={
        "job_result": job_output,
        "messages": state["messages"] + [
            ToolMessage(
                content=f"Job {job_id} completed with result: {job_output}",
                tool_call_id="wait_job"
            )
        ]
    })
```

## InvokeProcess Parameters

### Basic Parameters

```python
InvokeProcess(
    name="ProcessName",                    # Required: Exact process name in Orchestrator
    process_folder_path="FolderPath",      # Required: Folder path in Orchestrator
    input_arguments={                      # Required: Dictionary of input arguments
        "arg1": "value1",
        "arg2": 123,
        "arg3": ["list", "values"]
    }
)
```

### Return Values

Process invocation returns output data from the process:

```python
{
    "status": "success|failed|faulted",
    "output_argument_1": "result_value",
    "output_argument_2": 42,
    "error": "error message if failed"
}
```

## Common Patterns

### Data Processing Pipeline

```python
async def data_processing_pipeline(state: GraphState) -> Command:
    """Invoke processes in sequence for data transformation."""

    # Step 1: Extract data
    extract_result = interrupt(InvokeProcess(
        name="DataExtraction",
        process_folder_path="DataPipeline",
        input_arguments={"source": state["data_source"]}
    ))

    # Step 2: Transform data
    transform_result = interrupt(InvokeProcess(
        name="DataTransformation",
        process_folder_path="DataPipeline",
        input_arguments={"extracted_data": extract_result["output_data"]}
    ))

    # Step 3: Load data
    load_result = interrupt(InvokeProcess(
        name="DataLoad",
        process_folder_path="DataPipeline",
        input_arguments={"transformed_data": transform_result["output_data"]}
    ))

    return Command(update={
        "pipeline_results": {
            "extract": extract_result,
            "transform": transform_result,
            "load": load_result
        }
    })
```

### Conditional Process Invocation

```python
async def conditional_automation(state: GraphState) -> Command:
    """Choose which process to invoke based on logic."""

    if state["request_type"] == "urgent":
        process_name = "UrgentProcess"
        folder = "SpecialHandling"
    else:
        process_name = "StandardProcess"
        folder = "StandardWorkflows"

    result = interrupt(InvokeProcess(
        name=process_name,
        process_folder_path=folder,
        input_arguments={
            "request_data": state["request_data"],
            "priority": "urgent" if state["request_type"] == "urgent" else "normal"
        }
    ))

    return Command(update={"automation_result": result})
```

### Agent-in-the-Loop

```python
async def delegate_to_process(state: GraphState) -> Command:
    """Delegate work to RPA process while agent waits."""

    # LLM analyzes request
    llm = UiPathAzureChatOpenAI()
    analysis = await llm.ainvoke([
        SystemMessage(content="Analyze this request and extract parameters."),
        HumanMessage(content=state["request"])
    ])

    # Invoke RPA process
    process_result = interrupt(InvokeProcess(
        name="RequestProcessor",
        process_folder_path="AutomationWorkflows",
        input_arguments={
            "analysis": analysis.content,
            "request_id": state["request_id"]
        }
    ))

    # Continue with LLM
    final_response = await llm.ainvoke(state["messages"] + [
        ToolMessage(
            content=f"Process result: {process_result}",
            tool_call_id="process"
        )
    ])

    return Command(update={"response": final_response.content})
```

### Parallel Process Invocation

```python
async def parallel_processing(state: GraphState) -> Command:
    """Invoke multiple processes in parallel."""

    results = []

    # Note: This demonstrates sequential invocation;
    # For true parallelism, use asyncio.gather with process invocations
    processes = [
        ("ProcessA", "FolderA", {"data": "value1"}),
        ("ProcessB", "FolderB", {"data": "value2"}),
        ("ProcessC", "FolderC", {"data": "value3"}),
    ]

    for process_name, folder, args in processes:
        result = interrupt(InvokeProcess(
            name=process_name,
            process_folder_path=folder,
            input_arguments=args
        ))
        results.append(result)

    return Command(update={"parallel_results": results})
```

### Error Handling with Retry

```python
async def invoke_with_retry(state: GraphState) -> Command:
    """Invoke process with automatic retry on failure."""

    max_retries = 3
    attempt = 0

    while attempt < max_retries:
        try:
            result = interrupt(InvokeProcess(
                name="CriticalProcess",
                process_folder_path="ProductionWorkflows",
                input_arguments=state.get("process_args", {})
            ))

            if result.get("status") == "success":
                return Command(update={"process_result": result})

        except Exception as e:
            attempt += 1
            if attempt >= max_retries:
                return Command(update={
                    "process_result": None,
                    "error": f"Process failed after {max_retries} attempts: {str(e)}"
                })

    return Command(update={"process_result": None})
```

### Long-Running Job Monitoring

```python
async def monitor_long_job(state: GraphState) -> Command:
    """Monitor a long-running job created externally."""

    job_id = state.get("background_job_id")

    # Wait for job with timeout handling
    try:
        job_result = interrupt(WaitJob(job_id=job_id))

        if job_result.get("status") == "completed":
            return Command(update={"job_status": "completed", "job_result": job_result})
        else:
            return Command(update={"job_status": job_result.get("status", "unknown")})

    except TimeoutError:
        return Command(update={
            "job_status": "timeout",
            "message": f"Job {job_id} did not complete within timeout"
        })
```

## Best Practices

### Process Design

- **Atomic Processes**: Keep invoked processes focused on single tasks
- **Input Validation**: Validate input arguments before invocation
- **Error Codes**: Have processes return consistent error indicators
- **Output Format**: Define clear output argument structure

### Agent Integration

- **Error Handling**: Handle process failures gracefully
- **Timeout Management**: Consider process execution time in agent flow
- **Context Passing**: Include necessary context in input arguments
- **Result Validation**: Verify process results before continuing

### Performance

- **Batch Operations**: Group related operations into single process calls
- **Async Patterns**: Use asyncio for parallel process invocations
- **Resource Management**: Monitor Orchestrator resource usage
- **Process Reuse**: Reuse processes instead of creating duplicates

## Advanced Scenarios

### Multi-Agent Coordination

```python
async def coordinate_agents(state: GraphState) -> Command:
    """Coordinate work between multiple agents via process invocation."""

    # Current agent processes request
    llm = UiPathAzureChatOpenAI()
    analysis = await llm.ainvoke(state["messages"])

    # Delegate to another process for specialized handling
    result = interrupt(InvokeProcess(
        name="SpecializedHandler",
        process_folder_path="AgentWorkflows",
        input_arguments={
            "analysis": analysis.content,
            "agent_id": state.get("agent_id")
        }
    ))

    # Incorporate result back into conversation
    return Command(update={
        "messages": state["messages"] + [
            ToolMessage(content=f"Specialized handler result: {result}", tool_call_id="delegate")
        ]
    })
```

### Dynamic Workflow Routing

```python
async def route_to_process(state: GraphState) -> Command:
    """Route to different processes based on request classification."""

    # Classify request
    classification = classify_request(state["request"])

    # Route to appropriate process
    routing_map = {
        "high_priority": ("HighPriorityWorkflow", "SpecialHandling"),
        "standard": ("StandardWorkflow", "StandardProcesses"),
        "escalation": ("EscalationWorkflow", "CriticalWork"),
    }

    process_name, folder = routing_map.get(
        classification,
        ("StandardWorkflow", "StandardProcesses")
    )

    result = interrupt(InvokeProcess(
        name=process_name,
        process_folder_path=folder,
        input_arguments={"request": state["request"]}
    ))

    return Command(update={"routing_result": result})
```

## Troubleshooting

**"Process not found" errors:**
- Verify the process name matches exactly in Orchestrator
- Check the `process_folder_path` is correct
- Ensure the process is published and available

**"Invalid input arguments":**
- Check argument names match process expectations
- Verify argument types (string, int, boolean, list, dict)
- Ensure required arguments are provided

**Job timeouts:**
- Check process execution time in Orchestrator
- Verify process is not stuck or waiting
- Consider increasing timeout or using WaitJob pattern

**Output parsing errors:**
- Verify process return types match expectations
- Check for null/empty output values
- Add logging in process for debugging

## Reference

For detailed API documentation, see the [UiPath Process Invocation documentation](https://uipath.github.io/uipath-python/langchain/human_in_the_loop/).