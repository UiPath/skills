# Conversational Agents

Chat-style coded agents where the UiPath runtime feeds **one message per turn** and threads history across turns.

Supported on **LangGraph** and **LlamaIndex**. Coded Function and OpenAI Agents are not conversational.

## Contract (framework-agnostic)

Two requirements:

1. **Flag the agent as conversational** — set `runtimeOptions.isConversational: true` in `uipath.json`:

   ```json
   {
     "runtimeOptions": {
       "isConversational": true
     }
   }
   ```

   Without it, Studio Web / Orchestrator render a single-shot input form and history is not threaded.

2. **Type the graph/workflow input as the framework's message envelope.** The runtime fills it with one new message per turn; prior turns are threaded in by the runtime. The exact shape is framework-specific — see the framework reference below.

Set `isConversational: true` in `uipath.json` **before** running `uip codedagent init` so the emitted `entry-points.json` reflects the chat shape.

### Wire Envelope (`--input-file` payload)

The minimal payload accepted by `uip codedagent run --input-file <file>.json`:

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

- `role` is `"user"` for client input.
- `data.inline` carries the text content; `mimeType` describes its format.
- `messageId` and `contentPartId` may be supplied as GUIDs to address specific entities in the conversation hierarchy; if omitted the runtime fills them with fresh UUIDs.

The same envelope is used for both LangGraph and LlamaIndex on the wire. Each framework's runtime converts it to the in-process shape its graph/workflow expects (`HumanMessage` for LangGraph, `user_msg: str` for LlamaIndex). `uip codedagent dev` builds this envelope automatically.

## Framework-Specific Implementation

| Framework | Reference |
|---|---|
| LangGraph | `../frameworks/langgraph-integration.md` § Conversational Agents |
| LlamaIndex | `../frameworks/llamaindex-integration.md` § Conversational Agents |

## Running Locally

Inline JSON payloads on the CLI are fragile across shells (single vs. double quotes, brace escaping on cmd.exe / PowerShell). Two cleaner options:

- **`--input-file`** on `uip codedagent run` — pass a `.json` file:

  ```bash
  uip codedagent run agent --input-file turn1.json --keep-state-file
  ```

- **`uip codedagent dev`** — opens a local chat window that wires up the runtime, lets you send turns interactively, and preserves thread state between messages. Preferred for iterative chat development.

### Preserving State Across Turns

Local CLI runs lose conversation state between invocations unless you keep the runtime's checkpoint / state file. Pass `--keep-state-file` on **every** turn (including the first) — without it, each `uip codedagent run` starts from scratch and history is dropped.

```bash
uip codedagent run agent --input-file turn1.json --keep-state-file
uip codedagent run agent --input-file turn2.json --keep-state-file
```

The state file is per-project; deleting it resets the conversation. `uip codedagent dev` handles this automatically — the flag is only needed for the headless `uip codedagent run` path.

## Gotchas

- `isConversational` lives under `runtimeOptions` in `uipath.json` — not in `langgraph.json` / `llama_index.json` / `pyproject.toml`.
- LangGraph and LlamaIndex per-message shapes differ — do not transplant a payload from one framework to the other.
