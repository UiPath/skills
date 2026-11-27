# Conversational Agent Chat Widget

React chat interface for UiPath **Conversational Agents**: streaming responses, file attachments, tool-call visualization, conversation history, and thumbs-up/down feedback — all prebuilt.

Package: [`@uipath/ui-widgets-conversational-agent-chat`](https://www.npmjs.com/package/@uipath/ui-widgets-conversational-agent-chat). Full prop/API surface lives in the package README — this file covers only the integration steps that are easy to get wrong inside a Coded App.

## When to Use

- User asks to **chat with / talk to / embed a chat for** a conversational agent inside a coded app.
- Replaces a hand-rolled chat UI over the SDK's session/exchange events. Do **not** rebuild streaming, attachments, history, or feedback from scratch — the widget already wires all of it. Hand-roll with [../sdk/conversational-agent.md](../sdk/conversational-agent.md) only when the widget's UI genuinely cannot fit (e.g., fully custom message rendering).

**Two exports.** `ConversationalAgentChat` — chat with a known agent (`agentId`). `ConversationalAgentPickerChat` — lists all agents the SDK session can access, user picks one, chat opens; use when `agentId`/`folderId` are not known up front.

## Critical Rules

1. **Peer versions are hard requirements.** `react >= 19.2.0`, `react-dom >= 19.2.0`, `@uipath/uipath-typescript >= 1.5.5` — note the SDK floor is **higher** than other widgets. Verify `package.json` before installing.
2. **Import the stylesheet once** or the chat renders unstyled: `import '@uipath/ui-widgets-conversational-agent-chat/ConversationalAgentChat.css'`.
3. **Body needs `light` or `dark` class** for theming.
4. **Reuse the app's initialized `UiPath` instance** (`useAuth()` in web apps). Do not construct a second SDK for the widget.
5. **Required scopes:** `OR.Execution OR.Folders OR.Jobs ConversationalAgents Traces.Api` — the Conversational Agent bundle in [../oauth-scopes.md](../oauth-scopes.md). `Traces.Api` covers the feedback (thumbs up/down) flow; omitting it breaks feedback silently.
6. **`agentId` is the numeric agent release id, not the agent name.** Pass `folderId` whenever known — when omitted, the widget lists all agents to resolve it (extra calls, slower first paint).
7. **Give the widget a bounded-height container.** It fills its parent; an auto-height parent collapses the chat. Wrap in a fixed-height or flex-sized element (e.g. `height: '80vh'` or a `flex: 1` pane).
8. **No special `vite.config.ts` setup.** Unlike Validation Station, no asset-copy plugins or `optimizeDeps.exclude` needed. PDF attachment previews run pdf.js on the main thread inside the widget — no worker config.

## Install

From inside the scaffolded app directory:

```bash
npm install @uipath/ui-widgets-conversational-agent-chat --@uipath:registry=https://registry.npmjs.org
```

Registry flag forces the public npm registry (skill default — users may have `@uipath` scoped to GitHub Packages).

## Key Props

Full tables in the package README. Inside a coded app you usually only touch:

### `ConversationalAgentChat`

| Prop | Required | Notes |
|------|----------|-------|
| `sdk` | Yes | Initialized `UiPath` instance from `useAuth()`. |
| `agentId` | No* | Numeric agent release id. *Required unless `existingConversationId` is provided. |
| `folderId` | No | Folder the agent lives in. Pass when known — avoids a resolve-by-listing round trip. |
| `existingConversationId` | No | Open an existing conversation instead of creating one on first message. |
| `inputSchema` | No | Overrides the schema derived from the resolved agent (e.g., in-progress draft agents). |
| `isDebugMode` | No | Debug flow: opens an empty conversation up front; submits update it instead of creating new ones. |
| `externalUserId` | No | Sent as `x-uipath-external-user-id`. Only for app-scoped external-app tokens; omit for standard user tokens. |

### `ConversationalAgentPickerChat`

| Prop | Required | Notes |
|------|----------|-------|
| `sdk` | Yes | Changing it refetches the agent list and resets the UI. |
| `theme` / `locale` / `readOnly` / `overrideLabels` | No | Passthrough to the inner chat. |
| `onAgentSelected` | No | `(agent) => void` — telemetry/routing hook when the user picks an agent. |

Picker behavior: lists agents via `new ConversationalAgent(sdk).getAll()`, one row per agent; clicking opens the chat with that agent's `id`/`folderId`; "Back" returns to the list without refetching. To switch tenants, rebuild the `UiPath` instance and pass the new one as `sdk`.

## Integration: Web App

```typescript
import { ConversationalAgentChat } from '@uipath/ui-widgets-conversational-agent-chat';
import '@uipath/ui-widgets-conversational-agent-chat/ConversationalAgentChat.css';
import { useAuth } from '../hooks/useAuth';

function AgentChatPage({ agentId, folderId }: { agentId: number; folderId: number }) {
  const { sdk } = useAuth();

  return (
    <div style={{ height: '80vh' }}>
      <ConversationalAgentChat sdk={sdk} agentId={agentId} folderId={folderId} />
    </div>
  );
}

export default AgentChatPage;
```

Agent id unknown at build time? Either render `ConversationalAgentPickerChat` (user picks), or resolve programmatically with the SDK (`new ConversationalAgent(sdk).getAll()` → match on name → pass `id` + `folderId`; import from `@uipath/uipath-typescript/conversational-agent`).

## Anti-patterns

- **Do not hand-roll the chat UI with `startSession()`/`onExchangeStart` when this widget fits.** [../sdk/conversational-agent.md](../sdk/conversational-agent.md) is for custom UIs the widget cannot express.
- **Do not construct a second `UiPath` SDK** for the widget. Reuse the app's authenticated instance.
- **Do not pass the agent name as `agentId`** — it is the numeric release id.
- **Do not skip the CSS import** — the widget renders but looks broken (unstyled Apollo components).
- **Do not set `externalUserId` for normal user-token sessions** — it is only for app-scoped external application auth.
- **Do not drop `Traces.Api` from the scope** because "the app doesn't use traces" — the widget's feedback buttons need it.
