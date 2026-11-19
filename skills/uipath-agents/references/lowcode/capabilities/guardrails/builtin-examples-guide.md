# Built-in Validator Guardrail Examples

Complete `builtInValidator` guardrail objects to copy and adapt. Schema, validator discovery, scoping, and the numbered rules are in [guardrails.md](guardrails.md); read it first. Generate a fresh UUID for each `id`.

### Example 1: Block PII in Agent and Tool Outputs

```json
{
  "$guardrailType": "builtInValidator",
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "PII detection guardrail",
  "description": "This validator is designed to detect personally identifiable information using Azure Cognitive Services",
  "validatorType": "pii_detection",
  "validatorParameters": [
    {
      "$parameterType": "enum-list",
      "id": "entities",
      "value": ["Email", "PhoneNumber", "CreditCardNumber", "USSocialSecurityNumber"]
    },
    {
      "$parameterType": "map-enum",
      "id": "entityThresholds",
      "value": {
        "Email": 0.8,
        "PhoneNumber": 0.7,
        "CreditCardNumber": 0.9,
        "USSocialSecurityNumber": 0.9
      }
    }
  ],
  "action": {
    "$actionType": "block",
    "reason": "PII detected in output — execution blocked."
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Agent", "Tool"],
    "matchNames": ["MyToolName"]
  }
}
```

### Example 2: Log Harmful Content at Agent Level

```json
{
  "$guardrailType": "builtInValidator",
  "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "name": "Harmful content guardrail",
  "description": "Logs harmful content violations at agent level without blocking",
  "validatorType": "harmful_content",
  "validatorParameters": [
    {
      "$parameterType": "enum-list",
      "id": "harmfulContentEntities",
      "value": ["Hate", "SelfHarm", "Sexual", "Violence"]
    },
    {
      "$parameterType": "map-enum",
      "id": "harmfulContentEntityThresholds",
      "value": {
        "Hate": 2,
        "SelfHarm": 2,
        "Sexual": 4,
        "Violence": 2
      }
    }
  ],
  "action": {
    "$actionType": "log",
    "severityLevel": "Warning"
  },
  "enabledForEvals": false,
  "selector": {
    "scopes": ["Agent"]
  }
}
```

### Example 3: Prompt Injection Detection

```json
{
  "$guardrailType": "builtInValidator",
  "id": "e5f6a7b8-c9d0-1234-efab-567890123456",
  "name": "Prompt injection guardrail",
  "description": "This validator is provided by Noma Security and is built to detect malicious attack attempts (e.g. prompt injection, jailbreak) in LLM calls.",
  "validatorType": "prompt_injection",
  "validatorParameters": [
    {
      "$parameterType": "number",
      "id": "threshold",
      "value": 0.5
    }
  ],
  "action": {
    "$actionType": "log",
    "severityLevel": "Info"
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Llm"]
  }
}
```

### Example 4: User Prompt Attack Detection — Block Jailbreaks

No required parameters — binary detection via Azure Prompt Shield; `detectionScope` is the only optional one (see [Files and attachments](guardrails.md#files-and-attachments-detectionscope)). Llm PreExecution only.

```json
{
  "$guardrailType": "builtInValidator",
  "id": "f1a2b3c4-d5e6-7890-abcd-ef0123456789",
  "name": "User prompt attack guardrail",
  "description": "Detects jailbreak attempts and indirect prompt injection via Azure Prompt Shield",
  "validatorType": "user_prompt_attacks",
  "validatorParameters": [],
  "action": {
    "$actionType": "block",
    "reason": "Adversarial input detected — execution blocked."
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Llm"]
  }
}
```

### Example 5: Intellectual Property Detection — Block Copyrighted Text and Code

PostExecution only — no content exists to check before the LLM generates output. To check a file the agent produces instead of its text, see [files-guide.md § Recipe 3](files-guide.md#recipe-3--guard-a-file-the-agent-produces).

```json
{
  "$guardrailType": "builtInValidator",
  "id": "a2b3c4d5-e6f7-8901-bcde-f01234567890",
  "name": "IP detection guardrail",
  "description": "Detects copyrighted text and licensed GitHub code in LLM output",
  "validatorType": "intellectual_property",
  "validatorParameters": [
    {
      "$parameterType": "enum-list",
      "id": "ipEntities",
      "value": ["Text", "Code"]
    }
  ],
  "action": {
    "$actionType": "block",
    "reason": "Protected material detected in output — execution blocked."
  },
  "enabledForEvals": true,
  "selector": {
    "scopes": ["Llm"]
  }
}
```

### Example 6: Block PII Inside Attached Files

`detectionScope: "Files"` — only the run's attachments are evaluated; Agent PreExecution blocks before the model runs. Requires a `job-attachment` input field ([../../agent-definition.md](../../agent-definition.md) § File Attachments). Full recipe and variants: [files-guide.md](files-guide.md).

```json
{
  "$guardrailType": "builtInValidator",
  "id": "<UUID>",
  "name": "PII in uploaded documents",
  "description": "Blocks runs whose attached files contain customer identifiers",
  "validatorType": "pii_detection",
  "validatorParameters": [
    { "$parameterType": "enum-list", "id": "entities", "value": ["Email", "CreditCardNumber"] },
    { "$parameterType": "enum", "id": "detectionScope", "value": "Files" }
  ],
  "action": { "$actionType": "block", "reason": "An attached file contains personal data." },
  "enabledForEvals": true,
  "selector": { "scopes": ["Agent"] }
}
```

### Custom-rule, filter, and escalation examples

Moved to the owning guides:

- Custom word rules (block / log / specific fields with titles) and the filter redaction example → [custom-rules-guide.md § Examples](custom-rules-guide.md#examples)
- Escalate PII violations to Action Center → [escalation-guide.md](escalation-guide.md#example-escalate-pii-violations-to-action-center--multiple-tool-targets)
