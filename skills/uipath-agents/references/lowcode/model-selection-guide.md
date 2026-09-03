# Model Selection Guide

Choose `settings.model` from the authenticated tenant's live model list. Never retain a scaffold default without verification. Autonomous-agent scaffolds may default to a 128000 output cap; conversational-agent scaffolds may default to 64000. Discover and select a current model before validating unless discovery is unavailable.

## 1. Discover

Run:

```bash
uip agent model list --output json
```

`Data` is a flat array of PascalCase objects, not nested or lowercase:

| Field | Meaning |
|---|---|
| `Provider` | `OpenAi` \| `AwsBedrock` \| `VertexAi` |
| `Name` | Exact value for `settings.model` |
| `IsByo` | `true` = bring-your-own key registered for this tenant |
| `IsPreview` | `true` = preview/non-GA; avoid by default |
| `MaxTokens` | Output-token ceiling; caps `settings.maxTokens` |

To filter selectable GA models, run:

```bash
uip agent model list --output json \
  --output-filter "[?IsByo==\`false\` && IsPreview==\`false\`].{Name:Name,Provider:Provider,MaxTokens:MaxTokens}"
```

`--output-filter` is a global flag applied to `Data`; write the JMESPath starting at `Data`, with no `Data.` prefix. Discover before choosing: do not use an example or remembered name unless it appears in the live list, because availability varies by tenant and changes over time.

## 2. Select

1. Start with `IsByo=false` and `IsPreview=false`.
2. Use `IsPreview: true` only when the user explicitly requests bleeding-edge behavior; preview models may change behavior or availability without notice.
3. Choose the newest GA model matching the task class in §3.
4. Set `settings.maxTokens` from the selected model's `MaxTokens`; never exceed it.

## 3. Task-to-model criteria

Express the choice as criteria over the discovered list, not as a fixed ID:

| Task class | Selection criterion | Why |
|---|---|---|
| Reasoning, judgment, or multi-step tool use | Newest GA Anthropic Sonnet or Opus, or newest GA flagship OpenAI | Strong instruction-following and tool-call discipline |
| Fast, cheap, high-volume classification or extraction | Newest GA `*-mini` or GA Haiku | Lower latency and cost for narrow deterministic tasks |
| Long-context work with large documents or tool outputs | GA model with the highest `MaxTokens` | Reduces truncated output |
| Conversational | Newest GA Anthropic Sonnet or the user's preference | Strong conversational responses and instruction-following |

## 4. Fallback when discovery is unavailable

If `uip agent model list` fails because the user is not logged in, offline, or the command is unavailable, use a curated GA default appropriate to the task, currently `anthropic.claude-sonnet-4-6` for reasoning tasks. Tell the user it was not tenant-verified and may not exist on their tenant. This is the only situation where a hardcoded name is operative; otherwise, discover first.

## 5. Apply and validate

Edit `settings.model` and `settings.maxTokens` in `agent.json`, then:

1. Set `settings.model` to the discovered `Name`.
2. Set `settings.maxTokens` to a value `≤` the model's `MaxTokens`.
3. Run:

   ```bash
   uip agent refresh --output json
   ```

4. Run:

   ```bash
   uip agent validate --output json
   ```

For inline-in-flow agents, add `--inline-in-flow` to both commands. Full field reference: [agent-definition.md](agent-definition.md#change-model-settings).
