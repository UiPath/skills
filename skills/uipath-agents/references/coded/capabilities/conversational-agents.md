# Conversational Agents

> **Coded conversational agents are currently not intended for production use-cases.** For conversational use-cases, use **low-code conversational agents** by referring to [../../lowcode/lowcode.md](../../lowcode/lowcode.md). Only use coded conversational agents if the user is strongly requesting to use coded agents and the agent will only be tested and ran on a local machine.

Chat-style coded agents receive one message per turn from the UiPath runtime, which threads conversation history across turns. They are supported on **LangGraph** and **LlamaIndex**. Coded Function and OpenAI Agents are not conversational.

## Contract (framework-agnostic)

1. **Flag the agent as conversational.** Set `runtimeOptions.isConversational: true` in `uipath.json` before running `uip codedagent init`, so the emitted `entry-points.json` reflects the chat shape:

   ```json
   {
     "runtimeOptions": {
       "isConversational": true
     }
   }
   ```

   Without this setting, Studio Web / Orchestrator render a single-shot input form and history is not threaded.

2. **Type the graph/workflow input as the framework's message envelope.** The runtime supplies one new message per turn and threads prior turns. See the framework references below for the exact in-process shape.

### Wire Envelope (`--input-file` payload)

The minimal payload accepted by `uip codedagent run --input-file <file>.json` is:

```json
{
  "messages": [
    {
      "role": "user",
      "contentParts": [
        {
          "mimeType": "text/plain",
          "data": {"inline": "your message text"}
        }
      ]
    }
  ]
}
```

- Use `"user"` for client input in `role`.
- Put text in `data.inline`; `mimeType` describes its format.
- `messageId` and `contentPartId` may be supplied as GUIDs to address entities in the conversation hierarchy; if omitted, the runtime fills them with fresh UUIDs.
- Use this envelope on the wire for both LangGraph and LlamaIndex. The runtime converts it to `HumanMessage` for LangGraph and `user_msg: str` for LlamaIndex. `uip codedagent dev` builds it automatically.

## Framework-Specific Implementation

| Framework | Reference |
|---|---|
| LangGraph | `../frameworks/langgraph-integration.md` § Conversational Agents |
| LlamaIndex | `../frameworks/llamaindex-integration.md` § Conversational Agents |

## Running Locally

Avoid fragile inline JSON on the CLI, especially across cmd.exe and PowerShell. Use `--input-file` with `uip codedagent run` or run `uip codedagent dev`, which opens a local chat window, wires up the runtime, supports interactive turns, and preserves thread state. Prefer `uip codedagent dev` for iterative chat development.

### Preserving State Across Turns

Pass `--keep-state-file` on **every** `uip codedagent run` turn, including the first; otherwise each invocation starts from scratch and drops history:

```bash
uip codedagent run agent --input-file turn1.json --keep-state-file
uip codedagent run agent --input-file turn2.json --keep-state-file
```

The state file is per-project; delete it to reset the conversation. `uip codedagent dev` preserves state automatically, so the flag is needed only for the headless `uip codedagent run` path.

## Gotchas

- Put `isConversational` under `runtimeOptions` in `uipath.json`, not in `langgraph.json`, `llama_index.json`, or `pyproject.toml`.
- LangGraph and LlamaIndex per-message shapes differ; do not transplant an in-process payload from one framework to the other.
