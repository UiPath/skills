# Wait and Trigger Planning

Use this reference when planning process starts or pauses that wait for time, messages, signals, schedules, or external events.

## When to use

- Timer starts or timer intermediate events.
- Message, signal, conditional, or connector-backed starts.
- Intermediate waits for messages, signals, or external connector events.
- Timeout branches and boundary timers.

## Planning steps

1. Identify whether the wait begins the process, pauses the current path, or interrupts an activity.
2. Choose timer, message, signal, conditional, receive task, event-based gateway, or connector trigger shape.
3. Define correlation inputs and outputs in public-safe terms.
4. Plan timeout and cancellation behavior.
5. Mark Integration Service trigger or wait enrichment as CLI-owned.
6. Confirm whether the process may resume with stale data and how outputs update variables.

## Model may draft

- Standard timer, message, signal, conditional, and boundary event structure.
- Receive/wait task wrappers for non-connector message waits.
- `uipath:event` shells for documented non-Integration-Service events.
- Entry point IDs and variable mappings.

## Stop conditions

Stop before Operate when schedule, trigger properties, correlation contract, connector metadata, or dynamic event schema is unresolved.
