# Writing Simulations for Evaluations

Simulations replace real tool calls and external services with controlled outputs during eval runs. Use them to test agent logic without calling live APIs.

## When to Use Simulations

- The agent calls external APIs (email, payment, CRM) that shouldn't run during tests
- You need deterministic outputs from tools for reproducible eval results
- The external service is slow, rate-limited, or costs money per call
- You want to test how the agent handles specific tool responses (errors, edge cases)
- You want to test the agent's reasoning path without side effects

## Agent Tool Simulation (uip agent eval)

Low-code agents simulate tools at the test case level using flags on `uip agent eval add`. When `--simulate-tools` is set, the Agent Runtime intercepts tool calls during the eval run and returns simulated responses instead of calling the real tool.

### Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `--simulate-tools` | `false` | Simulate tool calls instead of executing them |
| `--simulate-input` | `false` | Generate synthetic input variations at runtime |
| `--simulation-instructions` | `""` | Natural language instructions guiding simulated tool behavior |
| `--input-generation-instructions` | `""` | Guide for synthetic input generation (used with `--simulate-input`) |

### Simulating agent tools

Use `--simulate-tools` with `--simulation-instructions` to control what simulated tools return:

```bash
# Simulate a weather tool call
uip agent eval add "weather-test" \
  --set "Default Evaluation Set" \
  --inputs '{"input": "What is the weather in NYC?"}' \
  --expected '{"content": "It is sunny and 72F in New York City."}' \
  --expected-agent-behavior "Agent calls the weather tool with location NYC and returns a formatted summary" \
  --simulate-tools \
  --simulation-instructions "When the agent calls the weather tool, return sunny weather, 72F for New York City." \
  --path ./my-agent --output json
```

```bash
# Simulate a database lookup tool
uip agent eval add "customer-lookup" \
  --set "Default Evaluation Set" \
  --inputs '{"input": "Find customer Acme Corp"}' \
  --expected '{"content": "Acme Corp is an enterprise customer."}' \
  --expected-agent-behavior "Agent calls the customer search tool with query 'Acme Corp' and returns account details" \
  --simulate-tools \
  --simulation-instructions "When the agent searches for a customer, return: Acme Corp, enterprise plan, active since 2020." \
  --path ./my-agent --output json
```

```bash
# Simulate an email sending tool
uip agent eval add "send-notification" \
  --set "Default Evaluation Set" \
  --inputs '{"input": "Send a welcome email to user@example.com"}' \
  --expected-agent-behavior "Agent calls the email tool with recipient user@example.com and a welcome message" \
  --simulate-tools \
  --simulation-instructions "When the agent calls the email tool, return success with messageId 'msg-12345'." \
  --path ./my-agent --output json
```

### Simulating tool errors

Test how the agent handles tool failures:

```bash
# Simulate a tool returning an error
uip agent eval add "api-failure" \
  --set "Error Handling" \
  --inputs '{"input": "Check order status for ORD-999"}' \
  --expected-agent-behavior "Agent calls the order API, receives a timeout error, and tells the user to try again later" \
  --simulate-tools \
  --simulation-instructions "When the agent calls the order status tool, return an error: 'Service temporarily unavailable, please try again later.'" \
  --path ./my-agent --output json
```

### Simulating multiple tools

When an agent uses multiple tools in sequence, write instructions that cover each tool:

```bash
uip agent eval add "multi-tool-test" \
  --set "Default Evaluation Set" \
  --inputs '{"input": "Book a flight from NYC to London for next Monday"}' \
  --expected-agent-behavior "Agent searches for flights, finds options, picks the cheapest, and books it" \
  --simulate-tools \
  --simulation-instructions "When the agent searches flights: return 3 options (Delta $450, United $520, BA $480). When the agent books a flight: return confirmation code BOOK-789." \
  --path ./my-agent --output json
```

### Generating synthetic inputs

Use `--simulate-input` to have the runtime generate input variations from a seed:

```bash
uip agent eval add "input-variation" \
  --set "Default Evaluation Set" \
  --inputs '{"input": "What time is it?"}' \
  --expected '{"content": "The current time is..."}' \
  --simulate-input \
  --input-generation-instructions "Generate variations asking about the current time in different phrasings, including typos and informal language" \
  --path ./my-agent --output json
```

### Combining simulation flags

Use both tool simulation and input simulation together:

```bash
uip agent eval add "full-simulation" \
  --set "Default Evaluation Set" \
  --inputs '{"input": "What is the weather?"}' \
  --expected-agent-behavior "Agent asks for a location if not provided, then calls the weather tool" \
  --simulate-tools \
  --simulation-instructions "Return sunny weather for any location" \
  --simulate-input \
  --input-generation-instructions "Generate weather queries with different cities and phrasings" \
  --path ./my-agent --output json
```

### How agent tool simulation works

1. The test case is sent to the Agent Runtime with simulation flags
2. The agent processes the input and decides to call a tool
3. Instead of calling the real tool, the runtime intercepts the call
4. The runtime uses `--simulation-instructions` to generate a plausible tool response
5. The agent receives the simulated response and continues its reasoning
6. Evaluators score the agent's output and trajectory as normal

The trajectory evaluator is especially useful with `--simulate-tools` because it can verify the agent called the right tools in the right order, even though the tools were simulated.

## Maestro Flow Simulations (uip maestro flow eval)

Flow simulations target specific components (nodes) in the flow graph. Each simulation replaces one node's execution with a controlled response.

### Simulation strategies

| Strategy | Behavior | Use when |
|---|---|---|
| `Static` | Returns a fixed JSON value every run | Output must be identical each time |
| `Llm` | LLM generates a plausible response guided by instructions | Output should be realistic but doesn't need to be exact |

### Static simulation

Returns a fixed JSON response for a flow component:

```bash
uip maestro flow eval simulation add <component-id> \
  --set "<eval-set-name>" \
  --data-point "<data-point-name>" \
  --strategy Static \
  --component-type connector \
  --mock-value '{"status": "sent", "messageId": "msg-12345"}' \
  --path <flow-project> --output json
```

The `<component-id>` is the node ID from the `.flow` file (e.g., `send_email_a1b2c3d4`).

`--component-type` can be: `connector`, `agent`, or other node types in the flow.

### LLM simulation

LLM generates a response based on instructions and output schema:

```bash
uip maestro flow eval simulation add <component-id> \
  --set "<eval-set-name>" \
  --data-point "<data-point-name>" \
  --strategy Llm \
  --component-type connector \
  --simulation-instructions "Pretend to send the email and return success with a realistic message ID." \
  --output-schema '{"type":"object","properties":{"status":{"type":"string"},"messageId":{"type":"string"}}}' \
  --path <flow-project> --output json
```

`--output-schema` is auto-resolved from the `.flow` file when omitted. Pass it explicitly only to override.

### Managing flow simulations

```bash
# List simulations on a data point
uip maestro flow eval simulation list \
  --set "<eval-set-name>" \
  --data-point "<data-point-name>" \
  --path <flow-project> --output json

# Remove a simulation
uip maestro flow eval simulation remove <component-id> \
  --set "<eval-set-name>" \
  --data-point "<data-point-name>" \
  --path <flow-project> --output json
```

### Flow simulation examples

**Email connector:**
```bash
uip maestro flow eval simulation add send_email_node \
  --set "Smoke Tests" \
  --data-point "invoice-notification" \
  --strategy Static \
  --component-type connector \
  --mock-value '{"status": "sent", "messageId": "mock-001"}' \
  --path ./MySolution/MyFlow --output json
```

**API connector with error:**
```bash
uip maestro flow eval simulation add api_call_node \
  --set "Error Tests" \
  --data-point "api-timeout" \
  --strategy Static \
  --component-type connector \
  --mock-value '{"error": "timeout", "statusCode": 504}' \
  --path ./MySolution/MyFlow --output json
```

**Sub-agent call:**
```bash
uip maestro flow eval simulation add classify_agent_node \
  --set "Smoke Tests" \
  --data-point "ticket-triage" \
  --strategy Llm \
  --component-type agent \
  --simulation-instructions "Classify the ticket as 'billing' priority 'high'." \
  --path ./MySolution/MyFlow --output json
```

**Database lookup:**
```bash
uip maestro flow eval simulation add db_query_node \
  --set "Smoke Tests" \
  --data-point "customer-lookup" \
  --strategy Static \
  --component-type connector \
  --mock-value '{"rows": [{"id": 1, "name": "Acme Corp", "plan": "enterprise"}], "count": 1}' \
  --path ./MySolution/MyFlow --output json
```

## Agent vs Flow Simulation Comparison

| Aspect | Agent (`uip agent eval`) | Flow (`uip maestro flow eval`) |
|---|---|---|
| Scope | All tool calls on a test case | Per-component in the flow graph |
| Granularity | Blanket (all tools) or none | Individual nodes |
| Configuration | Flags on `eval add` | Separate `simulation add` command |
| Strategies | LLM-guided (via instructions) | Static (fixed JSON) or LLM-guided |
| Error simulation | Via `--simulation-instructions` | Via `--mock-value` with error JSON |
| Determinism | Non-deterministic (LLM generates) | Static is deterministic, LLM is not |

## Choosing a Strategy

| Scenario | Agent approach | Flow approach |
|---|---|---|
| Test exact error path | `--simulation-instructions` describing the error | Static with error JSON |
| Test happy path with realistic data | `--simulate-tools` + instructions | Llm strategy with instructions |
| Reproducible regression tests | `--simulate-tools` (LLM varies) | Static strategy (fixed output) |
| Test one specific tool | `--simulation-instructions` targeting that tool | Simulation on that node only |
| Test tool call sequence | `--simulate-tools` + trajectory evaluator | Simulations on each node |

## Anti-patterns

- **Don't simulate every tool/component.** Only simulate external calls. Let the agent's own logic run — that's what you're testing.
- **Don't use LLM-based simulations for regression tests.** LLM outputs vary between runs, making score comparisons unreliable. Use Static (flow) or accept variance (agent).
- **Don't forget to remove simulations when testing real integrations.** Stale simulations hide real integration bugs.
- **Don't write vague `--simulation-instructions`.** "Return something reasonable" gives unpredictable results. Be specific about what the simulated tool should return.
- **Don't skip `--expected-agent-behavior` when using `--simulate-tools`.** Without it, the trajectory evaluator has nothing to score the tool call sequence against.
- **Running `simulation add` twice for the same component on the same data point replaces the existing simulation** (flow only). This is intentional — no need to remove first.
