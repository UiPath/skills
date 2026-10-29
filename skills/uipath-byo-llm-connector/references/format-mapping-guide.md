# Format Mapping Guide

Field-by-field correspondences between the request and response formats a BYO LLM connector bridges. Columns: **OpenAI** chat-completions, **Gemini** generateContent, **Anthropic** Messages (also the Bedrock *Invoke* body for Claude, with `anthropic_version` instead of `model`), **Converse** (Bedrock Converse). Check every mapping against the vendor's own documentation — this guide fixes the shapes, the vendor fixes the details.

## Messages

| Concept | OpenAI | Gemini | Anthropic | Converse |
|---|---|---|---|---|
| Message list | `messages[]` | `contents[]` | `messages[]` | `messages[]` |
| Roles | `system`, `developer`, `user`, `assistant`, `tool` | `user`, `model` | `user`, `assistant` | `user`, `assistant` |
| System prompt | a `system`/`developer` message | `systemInstruction.parts[].text` (`system_instruction` also accepted) | top-level `system` (string or `[{type:"text",text}]`) | top-level `system: [{text}]` |
| Text content | `content: "…"` or `[{type:"text",text}]` | `parts: [{text}]` | `content: [{type:"text",text}]` (string allowed on input) | `content: [{text}]` |

Consecutive messages of the same role must be merged for Anthropic, Converse and Gemini, which require strictly alternating turns (tool results count as `user`).

## Parameters

| Concept | OpenAI | Gemini | Anthropic | Converse |
|---|---|---|---|---|
| Max output tokens | `max_completion_tokens` (older: `max_tokens`) | `generationConfig.maxOutputTokens` | `max_tokens` (**required**) | `inferenceConfig.maxTokens` |
| Temperature | `temperature` | `generationConfig.temperature` | `temperature` | `inferenceConfig.temperature` |
| Top P | `top_p` | `generationConfig.topP` | `top_p` | `inferenceConfig.topP` |
| Stop sequences | `stop` (string or array) | `generationConfig.stopSequences` | `stop_sequences` | `inferenceConfig.stopSequences` |
| Choices | `n` | `generationConfig.candidateCount` | — (always 1) | — (always 1) |
| JSON output | `response_format: {type:"json_schema", json_schema:{name, schema}}` | `generationConfig.responseMimeType: "application/json"` + `responseSchema` | — (use a forced tool) | — (use a forced tool) |
| Streaming | `stream: true` (+ `stream_options.include_usage`) | the `:streamGenerateContent?alt=sse` path | `stream: true` | the `converse-stream` path |

Drop what the vendor does not support rather than forwarding it — an unknown field is a 400 on most endpoints. Return exactly as many choices as requested (`n`, default 1): an extra choice fails the probe.

## Tools

| Concept | OpenAI | Gemini | Anthropic | Converse |
|---|---|---|---|---|
| Definition | `tools: [{type:"function", function:{name, description, parameters}}]` | `tools: [{functionDeclarations:[{name, description, parameters}]}]` | `tools: [{name, description, input_schema}]` | `toolConfig.tools: [{toolSpec:{name, description, inputSchema:{json}}}]` |
| Choice: auto | `tool_choice: "auto"` | `toolConfig.functionCallingConfig.mode: "AUTO"` | `tool_choice: {type:"auto"}` | `toolConfig.toolChoice: {auto:{}}` |
| Choice: any tool | `"required"` | `mode: "ANY"` | `{type:"any"}` | `{any:{}}` |
| Choice: one tool | `{type:"function", function:{name}}` | `mode: "ANY"` + `allowedFunctionNames: [name]` | `{type:"tool", name}` | `{tool:{name}}` |
| Choice: none | `"none"` | `mode: "NONE"` | `{type:"none"}` | omit `toolConfig` |
| One call per turn | `parallel_tool_calls: false` | — | `tool_choice.disable_parallel_tool_use: true` | — |
| Call in the response | `choices[0].message.tool_calls: [{id, type:"function", function:{name, arguments}}]` — `arguments` is a **JSON string** | `parts: [{functionCall:{name, args}}]` — `args` is an **object**, no id | `content: [{type:"tool_use", id, name, input}]` — `input` is an object | `content: [{toolUse:{toolUseId, name, input}}]` |
| Result sent back | `{role:"tool", tool_call_id, content}` | `{role:"user", parts:[{functionResponse:{name, response:{…}}}]}` | `{role:"user", content:[{type:"tool_result", tool_use_id, content}]}` | `{role:"user", content:[{toolResult:{toolUseId, content:[{text}|{json}]}}]}` |

- `arguments` ↔ `input`/`args`: `JSON.stringify` toward OpenAI, `JSON.parse` away from it.
- Gemini has no call id: synthesise one (`call_${index}`) toward OpenAI and map it back by function name on the result.
- Gemini's `parameters` is an OpenAPI subset: remove keywords the endpoint rejects (`additionalProperties`, `$schema`, `$ref`, `$defs`), and if it rejects lowercase types, uppercase `type` values recursively.
- When a vendor ignores "one call per turn", keep only the first call — returning several when the caller forbade it fails the probe.

## Response

| Concept | OpenAI | Gemini | Anthropic | Converse |
|---|---|---|---|---|
| Answer container | `choices[].message` | `candidates[].content.parts[]` | `content[]` | `output.message.content[]` |
| Text | `message.content` (string) | concatenated `parts[].text` (skip `thought: true` parts) | concatenated `{type:"text"}` blocks | concatenated `{text}` blocks |
| Id / model | `id`, `model`, `object: "chat.completion"`, `created` (epoch seconds) | `responseId`, `modelVersion` | `id`, `model` | — (synthesise an id) |

### Finish reasons

| OpenAI | Gemini | Anthropic | Converse |
|---|---|---|---|
| `stop` | `STOP` | `end_turn`, `stop_sequence` | `end_turn`, `stop_sequence` |
| `length` | `MAX_TOKENS` | `max_tokens` | `max_tokens` |
| `tool_calls` | `STOP` with a `functionCall` part | `tool_use` | `tool_use` |
| `content_filter` | `SAFETY`, `RECITATION`, `PROHIBITED_CONTENT`, `BLOCKLIST` | `refusal` | `content_filtered`, `guardrail_intervened` |

### Usage

| Concept | OpenAI | Gemini | Anthropic | Converse |
|---|---|---|---|---|
| Input tokens | `usage.prompt_tokens` | `usageMetadata.promptTokenCount` | `usage.input_tokens` | `usage.inputTokens` |
| Output tokens | `usage.completion_tokens` | `usageMetadata.candidatesTokenCount` | `usage.output_tokens` | `usage.outputTokens` |
| Total | `usage.total_tokens` | `usageMetadata.totalTokenCount` | input + output | `usage.totalTokens` |
| Cached input | `usage.prompt_tokens_details.cached_tokens` | `usageMetadata.cachedContentTokenCount` | `usage.cache_read_input_tokens` | `usage.cacheReadInputTokens` |

Always map usage: the gateway meters from it.

## Media

| Part | OpenAI | Gemini | Anthropic | Converse |
|---|---|---|---|---|
| Inline image | `{type:"image_url", image_url:{url:"data:image/png;base64,<DATA>"}}` | `{inlineData:{mimeType:"image/png", data:"<DATA>"}}` | `{type:"image", source:{type:"base64", media_type:"image/png", data:"<DATA>"}}` | `{image:{format:"png", source:{bytes:"<DATA>"}}}` |
| Inline PDF | `{type:"file", file:{filename, file_data:"data:application/pdf;base64,<DATA>"}}` | `{inlineData:{mimeType:"application/pdf", data:"<DATA>"}}` | `{type:"document", source:{type:"base64", media_type:"application/pdf", data:"<DATA>"}}` | `{document:{format:"pdf", name, source:{bytes:"<DATA>"}}}` |

Split a `data:` URL at the first comma to get the MIME type and the base64 payload. A remote image URL works only if the vendor fetches URLs itself — never fetch it from the hook.

## OpenAI Responses API

| Concept | Request / response field |
|---|---|
| Input | `input`: a string, or items `[{role, content:[{type:"input_text", text} \| {type:"input_image", image_url} \| {type:"input_file", file_data, filename}]}]` |
| System prompt | `instructions` (or a `system`/`developer` input item) |
| Max output tokens | `max_output_tokens` |
| Tools | `tools: [{type:"function", name, description, parameters}]` (flat, no `function` wrapper) |
| Answer | `output[]`: `{type:"message", role:"assistant", content:[{type:"output_text", text}]}` and `{type:"function_call", call_id, name, arguments}` |
| Tool result back | input item `{type:"function_call_output", call_id, output}` |
| Status | `status: "completed"` / `"incomplete"` (+ `incomplete_details.reason: "max_output_tokens"`) |
| Usage | `usage.input_tokens`, `usage.output_tokens`, `usage.total_tokens` |

A response needs `id`, `object: "response"`, `created_at`, `model`, `status`, `output`, and `usage`.

## Embeddings

| Concept | OpenAI | Gemini (Vertex `:predict`) |
|---|---|---|
| Request | `{model, input: "<TEXT>" \| ["<TEXT>", …], dimensions?, encoding_format?}` | `{instances: [{content: "<TEXT>"}, …], parameters: {outputDimensionality?}}` |
| Response | `{object:"list", data:[{object:"embedding", index, embedding:[…]}], model, usage:{prompt_tokens, total_tokens}}` | `{predictions:[{embeddings:{values:[…], statistics:{token_count}}}]}` |

Keep one output vector per input, in input order. If `encoding_format: "base64"` is requested and the vendor returns floats, encode them as little-endian float32 before base64.
