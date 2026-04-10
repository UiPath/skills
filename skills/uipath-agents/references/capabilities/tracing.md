# UiPath Tracing Guide

Understand and implement tracing in your agents for monitoring, debugging, and auditing.

## What is Tracing?

Tracing is a monitoring feature that automatically captures function execution details. With the `@traced()` decorator, you can:
- 📊 Record function arguments and return values
- 🔍 Track execution flow for debugging
- 📋 Audit code behavior in Orchestrator
- 🔒 Redact sensitive data before logging

Trace data appears in:
- **UiPath Orchestrator**: Jobs page → Trace tab
- **UiPath Maestro**: For larger process orchestrations

## How Tracing Works

The `@traced()` decorator automatically monitors your functions. Apply it to any function:

```python
from uipath.tracing import traced

@traced()
def my_function(input_data):
    """This function's execution will be traced."""
    return process_data(input_data)
```

**Supported Function Types:**
- Regular synchronous functions
- Async functions (`async def`)
- Generator functions (`yield`)
- Async generators (`async yield`)

## Basic Usage

### Simple Tracing

```python
from pydantic import BaseModel
from uipath.tracing import traced

class Input(BaseModel):
    user_id: int
    action: str

@traced()
async def main(input: Input) -> dict:
    """Main agent function with tracing enabled."""
    result = process_user_action(input.user_id, input.action)
    return {"status": "success", "result": result}
```

### Custom Span Names

Organize traces by giving them meaningful names:

```python
@traced(name="validate_user_input")
def validate_input(user_id: int, action: str) -> bool:
    """Custom span name for better trace organization."""
    return user_id > 0 and action in ["create", "update", "delete"]
```

### Custom Run Types

Categorize traces by function purpose:

```python
@traced(run_type="data_processing")
def process_csv_file(file_path: str) -> list:
    """Mark this as a data processing operation."""
    # Processing logic
    return processed_data
```

## Data Protection & Privacy

### Redacting Sensitive Data

Use input/output processors to mask sensitive information before logging:

```python
@traced(
    input_processor=lambda x: {**x, "password": "***"},
    output_processor=lambda x: {**x, "token": "***"}
)
def authenticate_user(username: str, password: str) -> dict:
    """Password is redacted before tracing."""
    token = generate_token(username, password)
    return {"username": username, "token": token}
```

### Hide Input/Output

Completely hide sensitive parameters from traces:

```python
@traced(hide_input=True, hide_output=True)
def process_api_key(api_key: str) -> bool:
    """API key is not recorded in traces at all."""
    return validate_api_key(api_key)
```

## Advanced Configuration

### Combining Parameters

Create comprehensive tracing for complex operations:

```python
@traced(
    name="payment_processing",
    run_type="financial_transaction",
    input_processor=lambda x: {
        "amount": x["amount"],
        "currency": x["currency"],
        "customer_id": "***"
    },
    hide_output=False  # Show output but redact sensitive input
)
async def process_payment(customer_id: str, amount: float, currency: str) -> dict:
    """Process payment with full tracing and privacy."""
    result = call_payment_api(customer_id, amount, currency)
    return result
```

## Integration Patterns

### With LangChain Agents

LangChain agents handle tracing automatically—no additional configuration needed.

## Common Use Cases

### 1. Production Monitoring

Track function execution in production agents to monitor performance and catch errors.

```python
@traced(name="user_lookup")
async def get_user_details(user_id: int) -> dict:
    """Monitor user lookup operations."""
    return await database.find_user(user_id)
```

### 2. Data Pipeline Auditing

Record all transformations for compliance and debugging.

```python
@traced(
    name="data_transformation",
    input_processor=lambda x: {"record_count": len(x), "schema_version": "1.0"}
)
def transform_batch(records: list) -> list:
    """Audit data transformation without logging raw data."""
    return [transform_record(r) for r in records]
```

### 3. API Integration Debugging

Track external API calls for troubleshooting.

```python
@traced(name="call_external_api", run_type="integration")
async def fetch_from_third_party(endpoint: str, params: dict) -> dict:
    """Monitor third-party API interactions."""
    response = await call_api(endpoint, params)
    return response
```

### 4. Security & Compliance

Trace actions while protecting sensitive data for audit logs.

```python
@traced(
    hide_input=True,
    hide_output=True,
    name="sensitive_operation"
)
def verify_credentials(username: str, password: str) -> bool:
    """Audit sensitive operations without logging credentials."""
    return authenticate(username, password)
```

## Viewing Traces

### In Orchestrator

1. Go to **Jobs** page
2. Select a completed job
3. Click **Trace** tab to view captured data
4. Expand trace spans to see details

### Trace Information Available

- Function name and custom span name
- Input arguments (or "hidden" if redacted)
- Return value (or "hidden" if redacted)
- Execution time
- Exceptions and errors

## Best Practices

✅ **Do:**
- Use meaningful `name` values for organization
- Apply `@traced()` to all public functions
- Use processors for sensitive data instead of `hide_*` flags (you get partial visibility)
- Test tracing locally before deploying to production
- Combine with logging for comprehensive observability

❌ **Don't:**
- Forget `wait_for_tracers()` in plain Python agents
- Log raw passwords or API keys
- Use `hide_*` for all sensitive data if you need partial visibility
- Assume tracing adds no performance overhead (it's minimal but measurable)

## Troubleshooting

### Traces Not Appearing

1. Verify agent ran to completion
2. Check that `@traced()` decorator is applied
3. Ensure `wait_for_tracers()` is called (plain Python only)
4. Confirm Orchestrator has the job data

### Performance Concerns

Tracing has minimal overhead. If performance is critical:
- Use `name` parameter for cleaner traces
- Apply `@traced()` only to key functions (not every small helper)
- Use `input_processor` to reduce data volume in traces

## Documentation

For more details, visit: https://uipath.github.io/uipath-python/core/traced/
