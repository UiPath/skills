# Model Selection Guide — Inline Agents

How to pick the LLM for an inline agent's `inputs.model`. The tenant is the source of truth — discover at runtime, then select; never ship a copied example or manifest-default model name.

> The autonomous manifest's `inputDefaults` may seed a **stale** model (and the canvas seeds new nodes from a tenant suggestion). A hand-authored node has no seeding at all. **Always set `inputs.model` explicitly** from a discovered current model before validating.

## 1. Discover (primary path)

List the models the authenticated tenant actually offers (works from the flow project directory — no agent project needed):

```bash
uip agent model list --output json
```

`Data` is a **flat array of PascalCase objects** — not nested, not lowercase:

| Field | Meaning |
|-------|---------|
| `Provider` | `OpenAi` \| `AwsBedrock` \| `VertexAi` |
| `Name` | The exact string for `inputs.model` (e.g. `anthropic.claude-sonnet-4-6`, `gpt-5.4`) |
| `IsByo` | `true` = bring-your-own key registered for this tenant |
| `IsPreview` | `true` = preview/non-GA — avoid by default |
| `MaxTokens` | Output-token ceiling for this model — caps `inputs.maxTokenPerResponse` |

Filter to selectable GA models with `--output-filter` (a global flag applied to `Data` — write the JMESPath starting at `Data`, no `Data.` prefix):

```bash
uip agent model list --output json \
  --output-filter "[?IsByo==\`false\` && IsPreview==\`false\`].{Name:Name,Provider:Provider,MaxTokens:MaxTokens}"
```

Run discovery **before** choosing a model. Do not pick from this doc's examples without confirming the name appears in the live list — model availability differs per tenant and changes over time.

## 2. Select

1. Start from the GA-filtered list above (`IsByo=false`, `IsPreview=false`).
2. **Preview models are opt-in only.** Use an `IsPreview: true` model (e.g. `gpt-5.5-2026-04-23`, `gemini-3.1-pro-preview`, `anthropic.claude-opus-4-7`) **only when the user explicitly asks** for the bleeding edge — preview models can change behavior or availability without notice.
3. Pick the **newest GA model matching the task class** (§3).
4. Set `inputs.maxTokenPerResponse` from the chosen model's `MaxTokens` — never exceed the cap. Example: `gpt-4o-2024-11-20` caps at 16384, so `maxTokenPerResponse: 32768` is invalid for it; `anthropic.claude-sonnet-4-6` caps at 64000; `gpt-5.4` at 128000.

## 3. Task → model mapping

Express the choice as **selection criteria over the discovered list**, not a fixed ID:

| Task class | Selection criterion | Why |
|------------|---------------------|-----|
| Reasoning / judgment / multi-step tool use | Newest GA Anthropic Sonnet or Opus, or newest GA flagship OpenAI | Strongest instruction-following + tool-call discipline |
| Fast / cheap / high-volume classification or extraction | Newest GA `*-mini` (e.g. an OpenAI `*-mini`) or GA Haiku | Lower latency + cost; sufficient for narrow deterministic tasks |
| Long-context (large documents, big tool outputs) | GA model with the highest `MaxTokens` | Avoids truncated output |

Concrete GA examples observed on a live tenant — **illustrative only; verify against `uip agent model list`**:

- Reasoning: `anthropic.claude-sonnet-4-6`, `anthropic.claude-opus-4-6-v1`, `gpt-5.4`, `gpt-4.1-2025-04-14`
- Fast/cheap: `gpt-5.4-mini-2026-03-17`, `gpt-4.1-mini-2025-04-14`, `anthropic.claude-haiku-4-5-20251001-v1:0`

## 4. Fallback (discovery unavailable)

If `uip agent model list` fails (not logged in, offline, command unavailable), pick a curated GA default — currently `anthropic.claude-sonnet-4-6` for reasoning tasks — and **tell the user it was not tenant-verified** and may not exist on their tenant. This is the only situation where a hardcoded name is the operative choice; everywhere else, discover first.

## 5. Apply the choice

1. Set `inputs.model` on the agent node to the discovered `Name`.
2. Set `inputs.maxTokenPerResponse` ≤ the model's `MaxTokens`.
3. `uip maestro flow validate "<FILE>.flow" --output json`

Full node `inputs` reference: [impl.md § 2](impl.md#2-agent-node-inputs-spec).
