# Common tasks — direct routing

For the most-frequent named journeys, this index points straight at the file that handles the task. Use it to skip the four `CAPABILITY.md` indexes when you already know what you want to do. For navigation that explores tradeoffs, start from [SKILL.md](../SKILL.md) → the relevant `CAPABILITY.md`.

## Index

| I want to... | Go to |
|---|---|
| **Create a brand-new flow project** | [author/references/greenfield.md](author/references/greenfield.md) |
| **Edit an existing flow** | [author/references/brownfield.md](author/references/brownfield.md) |
| **Add a script node** | [author/references/plugins/script/impl.md](author/references/plugins/script/impl.md) |
| **Add an HTTP node (Managed HTTP Request)** | [author/references/plugins/http/impl.md](author/references/plugins/http/impl.md) |
| **Add a connector activity** | [author/references/plugins/connector/impl.md](author/references/plugins/connector/impl.md) |
| **Add a connector trigger** | [author/references/plugins/connector-trigger/impl.md](author/references/plugins/connector-trigger/impl.md) |
| **Add a decision (if/else)** | [author/references/plugins/decision/impl.md](author/references/plugins/decision/impl.md) |
| **Add a switch (multi-way branch)** | [author/references/plugins/switch/impl.md](author/references/plugins/switch/impl.md) |
| **Add a loop over a collection** | [author/references/plugins/loop/impl.md](author/references/plugins/loop/impl.md) |
| **Add an end node** | [author/references/plugins/end/impl.md](author/references/plugins/end/impl.md) |
| **Add a terminate node (abort on error)** | [author/references/plugins/terminate/impl.md](author/references/plugins/terminate/impl.md) |
| **Add a subflow** | [author/references/plugins/subflow/impl.md](author/references/plugins/subflow/impl.md) |
| **Call a published RPA process** | [author/references/plugins/rpa/impl.md](author/references/plugins/rpa/impl.md) |
| **Call a published AI agent** | [author/references/plugins/agent/impl.md](author/references/plugins/agent/impl.md) |
| **Embed an inline AI agent** | [author/references/plugins/inline-agent/impl.md](author/references/plugins/inline-agent/impl.md) |
| **Pause for human input (HITL)** | [author/references/plugins/hitl/impl.md](author/references/plugins/hitl/impl.md) |
| **Add a data transform** | [author/references/plugins/transform/impl.md](author/references/plugins/transform/impl.md) |
| **Add an LLM batch transform over CSV rows** | [author/references/plugins/batch-transform/impl.md](author/references/plugins/batch-transform/impl.md) |
| **Summarize a document with citations** | [author/references/plugins/summarize/impl.md](author/references/plugins/summarize/impl.md) |
| **Add a queue node** | [author/references/plugins/queue/impl.md](author/references/plugins/queue/impl.md) |
| **Add a scheduled trigger** | [author/references/plugins/scheduled-trigger/impl.md](author/references/plugins/scheduled-trigger/impl.md) |
| **Add or update a variable** | [shared/variables-and-expressions.md](shared/variables-and-expressions.md) |
| **Write an `=js:` expression** | [shared/node-output-wiring.md](shared/node-output-wiring.md) + [shared/variables-and-expressions.md](shared/variables-and-expressions.md) |
| **Wire one node's output into another's input** | [shared/node-output-wiring.md](shared/node-output-wiring.md) |
| **Fetch and bind an IS connection** | [author/references/plugins/connector/impl.md](author/references/plugins/connector/impl.md) Step 1 |
| **Look up the `.flow` JSON shape** | [shared/file-format.md](shared/file-format.md) |
| **Look up a `uip` CLI command** | [shared/cli-commands.md](shared/cli-commands.md) |
| **Validate the flow** | `uip maestro flow validate <ProjectName>.flow` — see [author/CAPABILITY.md](author/CAPABILITY.md) rule #9 |
| **Format / normalize layout** | `uip maestro flow format <ProjectName>.flow` — see [author/CAPABILITY.md](author/CAPABILITY.md) rule #13 |
| **Publish to Studio Web** | [operate/references/ship.md](operate/references/ship.md) (Path 1) |
| **Deploy to Orchestrator** | [operate/references/ship.md](operate/references/ship.md) (Path 2) |
| **Run a flow via `flow debug`** | [operate/references/run.md](operate/references/run.md) |
| **Check job status / stream traces** | [operate/references/run.md](operate/references/run.md) |
| **Pause / resume / cancel / retry an instance** | [operate/references/manage.md](operate/references/manage.md) |
| **Diagnose a failed run** | [diagnose/references/troubleshooting-guide.md](diagnose/references/troubleshooting-guide.md) |
| **Look up MST-9107 / MST-9061 / HITL-stuck / etc.** | [diagnose/references/failure-modes.md](diagnose/references/failure-modes.md) |
| **Create an evaluator** | [evaluate/references/evaluators-guide.md](evaluate/references/evaluators-guide.md) |
| **Create an eval set / add data points** | [evaluate/references/eval-sets-guide.md](evaluate/references/eval-sets-guide.md) |
| **Run a Studio Web eval** | [evaluate/references/running-guide.md](evaluate/references/running-guide.md) |

## When to use a `CAPABILITY.md` instead

If the task isn't in the table above, or you need to make a tradeoff decision (e.g., "Studio Web vs Orchestrator publish", "inline agent vs published agent", "decision vs switch"), start from the relevant capability:

- [author/CAPABILITY.md](author/CAPABILITY.md) — create or edit a `.flow` file
- [operate/CAPABILITY.md](operate/CAPABILITY.md) — publish, run, manage runs
- [diagnose/CAPABILITY.md](diagnose/CAPABILITY.md) — investigate failures
- [evaluate/CAPABILITY.md](evaluate/CAPABILITY.md) — design and run evaluations
