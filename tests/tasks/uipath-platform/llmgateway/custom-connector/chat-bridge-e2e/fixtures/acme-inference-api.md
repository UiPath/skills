# Acme Inference API (fictional)

Base URL: `https://inference.acme.example.com`

## Authentication

Every request carries the customer's API key in the `x-api-key` header. There is no token exchange.

## POST /v2/generate

Generates one answer for a conversation. The endpoint does not stream.

Request body:

```json
{
  "model": "acme-large",
  "instructions": "System prompt text, optional",
  "turns": [
    { "speaker": "human", "text": "Hi" },
    { "speaker": "model", "text": "Hello! How can I help?" },
    { "speaker": "human", "text": "Tell me a joke" }
  ],
  "limits": { "max_new_tokens": 256 },
  "sampling": { "temperature": 0.2 }
}
```

- `speaker` is `human` for user turns and `model` for assistant turns.
- `instructions` holds the system prompt; there is no system turn.
- `limits` and `sampling` are optional.

Response body (HTTP 200):

```json
{
  "request_id": "req-0001",
  "model": "acme-large",
  "result": { "text": "Why did the robot cross the road?", "stop": "complete" },
  "metering": { "input_tokens": 21, "output_tokens": 9 }
}
```

- `result.stop` is `complete` when the model finished, `token_limit` when it hit `max_new_tokens`.

Errors use HTTP 401 (bad key), 404 (unknown model) and 429 (rate limited), with a body of the form `{"error": {"code": "...", "message": "..."}}`.
