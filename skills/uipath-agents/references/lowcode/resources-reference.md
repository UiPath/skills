# Low-Code Agent Resources Reference

> **Agent type: Low-code agents only.** Coded agents access platform resources via the Python SDK (`from uipath.platform import UiPath`) and configure overridable resource bindings in `bindings.json` — see [lifecycle/bindings-reference.md](../lifecycle/bindings-reference.md).

Resources are the external capabilities an agent can use during execution — tools it can call, knowledge it can retrieve, humans it can escalate to, and external servers it can connect to. All resources are declared in the `"resources"` array of `agent.json`.

Every resource object has at minimum:

| Field | Type | Description |
|---|---|---|
| `$resourceType` | string | Discriminator: `"tool"`, `"context"`, `"escalation"`, `"mcp"`, or `"a2a"` |
| `name` | string | Display name; also used as the tool name the LLM sees |
| `description` | string | Explains to the LLM what the resource does and when to use it |
| `isEnabled` | boolean | Whether the resource is active (default `true`) |

---

## 1. Tool Resources (`$resourceType: "tool"`)

Tool resources give the agent callable actions. The `type` field selects the subtype.

---

### 1.1 Api — API Workflow Tool

Calls an **API-triggered UiPath workflow** (an Orchestrator process started via API). Use this for automation workflows that return a structured result synchronously.

**Key fields:**

| Field | Path | Description |
|---|---|---|
| `type` | — | `"Api"` (also: `"Process"`, `"Agent"`, `"Integration"`, `"Internal"`, `"Ixp"`) |
| `folderPath` | `properties.folderPath` | Orchestrator folder containing the process |
| `processName` | `properties.processName` | Name of the Orchestrator process |
| `inputSchema` | — | JSON Schema for the arguments passed to the workflow |
| `outputSchema` | — | JSON Schema for the value returned by the workflow |

```json
{
  "$resourceType": "tool",
  "type": "Api",
  "name": "Get Customer Data",
  "description": "Retrieves customer account details from the CRM system given a customer ID. Returns name, email, account status, and contract tier.",
  "isEnabled": true,
  "location": "solution",
  "guardrail": { "policies": [] },
  "settings": {},
  "argumentProperties": {},
  "properties": {
    "folderPath": "Finance/CRM",
    "processName": "GetCustomerData"
  },
  "inputSchema": {
    "type": "object",
    "properties": {
      "customerId": {
        "type": "string",
        "description": "The unique customer identifier (e.g. CUST-00123)."
      }
    },
    "required": ["customerId"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "name": { "type": "string" },
      "email": { "type": "string" },
      "accountStatus": { "type": "string", "enum": ["active", "suspended", "closed"] },
      "contractTier": { "type": "string" }
    }
  }
}
```

---

### 1.2 Process — RPA Process Tool

Triggers a **job-based UiPath RPA process** (long-running or robot-executed). The structure is identical to `Api` but uses `type: "Process"`. Use this when the automation runs on an unattended robot and may take longer to complete.

```json
{
  "$resourceType": "tool",
  "type": "Process",
  "name": "Generate Invoice",
  "description": "Runs an RPA process that generates a PDF invoice in the ERP system and returns the document URL. Use this after all invoice line items have been confirmed.",
  "isEnabled": true,
  "location": "solution",
  "guardrail": { "policies": [] },
  "settings": {},
  "argumentProperties": {},
  "properties": {
    "folderPath": "Finance/Invoicing",
    "processName": "GenerateInvoicePDF"
  },
  "inputSchema": {
    "type": "object",
    "properties": {
      "orderId": {
        "type": "string",
        "description": "The order ID for which to generate the invoice."
      },
      "recipientEmail": {
        "type": "string",
        "description": "Email address to send the invoice to."
      }
    },
    "required": ["orderId", "recipientEmail"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "invoiceUrl": {
        "type": "string",
        "description": "Public URL of the generated PDF invoice."
      },
      "invoiceNumber": {
        "type": "string"
      }
    }
  }
}
```

---

### 1.3 Agent — Call Another Agent as a Tool

Delegates a sub-task to **another UiPath agent**. The called agent runs independently and returns its output schema as the tool result. Use this for modular, multi-agent architectures.

```json
{
  "$resourceType": "tool",
  "type": "Agent",
  "name": "Summarisation Agent",
  "description": "Calls a specialised summarisation agent that condenses long documents into structured bullet-point summaries. Use this when the input text exceeds 2000 words.",
  "isEnabled": true,
  "location": "solution",
  "guardrail": { "policies": [] },
  "settings": {},
  "argumentProperties": {},
  "properties": {
    "folderPath": "Shared/Agents",
    "processName": "SummarisationAgent"
  },
  "inputSchema": {
    "type": "object",
    "properties": {
      "documentText": {
        "type": "string",
        "description": "The full text of the document to summarise."
      },
      "maxBullets": {
        "type": "integer",
        "description": "Maximum number of bullet points in the summary.",
        "default": 5
      }
    },
    "required": ["documentText"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "summary": {
        "type": "array",
        "items": { "type": "string" },
        "description": "List of summary bullet points."
      }
    }
  }
}
```

---

### 1.4 Integration — Integration Service Connector Tool

Calls an action exposed by an **Integration Service connector** (e.g. Salesforce, ServiceNow, Jira). Requires `connectorKey` (the connector type identifier) and `elementInstanceId` (the specific authenticated connection).

```json
{
  "$resourceType": "tool",
  "type": "Integration",
  "name": "Create ServiceNow Incident",
  "description": "Creates a new incident ticket in ServiceNow. Use this when the user requests IT support or when an automated check detects a system issue that requires human follow-up.",
  "isEnabled": true,
  "location": "solution",
  "guardrail": { "policies": [] },
  "settings": {},
  "argumentProperties": {},
  "properties": {
    "connectorKey": "ServiceNow",
    "elementInstanceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "actionName": "CreateIncident"
  },
  "inputSchema": {
    "type": "object",
    "properties": {
      "shortDescription": {
        "type": "string",
        "description": "One-line summary of the incident."
      },
      "description": {
        "type": "string",
        "description": "Full description of the issue."
      },
      "urgency": {
        "type": "string",
        "enum": ["1", "2", "3"],
        "description": "1 = High, 2 = Medium, 3 = Low."
      },
      "assignmentGroup": {
        "type": "string",
        "description": "ServiceNow assignment group name."
      }
    },
    "required": ["shortDescription", "urgency"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "ticketNumber": { "type": "string" },
      "ticketUrl": { "type": "string" }
    }
  }
}
```

---

### 1.5 Internal — Built-In Platform Tools

References a **built-in UiPath platform capability** rather than an external process. The `toolName` field selects the capability. No `properties.folderPath` or `processName` is needed.

Available built-in tool names:

| `toolName` | Description |
|---|---|
| `analyze-attachments` | Extracts and interprets content from attached files (PDF, DOCX, images) |
| `deep-rag` | Performs a deep retrieval-augmented generation search over a knowledge index |
| `batch-transform` | Applies a transformation prompt to multiple items in parallel |

```json
{
  "$resourceType": "tool",
  "type": "Internal",
  "name": "Analyse Attachments",
  "description": "Extracts text, tables, and structured data from file attachments provided by the user. Use this whenever the user uploads a PDF, Word document, or image that contains information relevant to the task.",
  "isEnabled": true,
  "location": "solution",
  "guardrail": { "policies": [] },
  "settings": {},
  "argumentProperties": {},
  "toolName": "analyze-attachments"
}
```

---

### 1.6 Ixp — IXP Document Understanding Tool

Calls a workflow hosted on the UiPath IXP (Intelligent Document Processing) platform. Used when the agent needs to extract data from documents (PDFs, forms, invoices) using UiPath's Document Understanding service.

Structure is identical to `Api` — uses `properties.folderPath` and `properties.processName`. Use `type: "Ixp"` when the target process is an IXP extraction workflow.

```json
{
  "$resourceType": "tool",
  "type": "Ixp",
  "name": "Extract Invoice Data",
  "description": "Extracts structured data from an invoice PDF using Document Understanding. Use this when the user uploads an invoice or provides a document path to process. Returns line items, totals, vendor details, and dates.",
  "isEnabled": true,
  "location": "solution",
  "guardrail": { "policies": [] },
  "settings": {},
  "argumentProperties": {},
  "properties": {
    "folderPath": "Finance/DocumentProcessing",
    "processName": "InvoiceExtractionWorkflow"
  },
  "inputSchema": {
    "type": "object",
    "properties": {
      "documentPath": {
        "type": "string",
        "description": "Path or URL to the invoice document to process."
      }
    },
    "required": ["documentPath"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "vendor": { "type": "string" },
      "totalAmount": { "type": "number" },
      "invoiceDate": { "type": "string" },
      "lineItems": {
        "type": "array",
        "items": { "type": "object" }
      }
    }
  }
}
```

---

## 2. Context Resources (`$resourceType: "context"`)

Context resources provide the agent with **retrieval-augmented knowledge** — documents, databases, or file attachments that the agent can query before or during reasoning.

---

### Context Types

| `contextType` | Source |
|---|---|
| `"index"` | Context Grounding index (vector/keyword search over indexed documents) |
| `"attachments"` | Files attached to the conversation at runtime |
| `"datafabricentityset"` | UiPath Data Fabric structured entity data |

### Retrieval Modes (`settings.retrievalMode`)

| Mode | Description |
|---|---|
| `Semantic` | Vector similarity search — best for natural language queries |
| `Structured` | Keyword/filter-based retrieval — best for exact matches |
| `DeepRAG` | Multi-step retrieval with re-ranking — best for complex queries |
| `BatchTransform` | Bulk transformation of retrieved chunks |
| `DataFabric` | Structured query against Data Fabric entity sets |

```json
{
  "$resourceType": "context",
  "name": "Product Knowledge Base",
  "isEnabled": true,
  "description": "Internal product documentation including feature specs, pricing, and FAQs. Query this whenever the user asks about product capabilities, limitations, or pricing.",
  "contextType": "index",
  "folderPath": "MyFolder",
  "indexName": "product-docs-index",
  "settings": {
    "retrievalMode": "Semantic",
    "resultCount": 5,
    "threshold": 0.75,
    "query": { "variant": "dynamic" }
  }
}
```

> **`settings` fields:**
> - `resultCount` — Maximum number of chunks or documents to retrieve (integer, default: 5).
> - `threshold` — Minimum relevance score (0–1) for a result to be included. Lower values return more results with potentially lower relevance.

---

## 3. Escalation Resources (`$resourceType: "escalation"`)

Escalation resources enable **Human-in-the-Loop (HITL)** workflows. When the agent determines it cannot or should not proceed autonomously, it routes the task to a human via Action Center.

**Key fields:**

| Field | Path | Description |
|---|---|---|
| `channels` | — | Array of channel objects (typically one). Each channel defines a separate escalation path. |
| `channels[].type` | — | Must be `"actionCenter"` |
| `channels[].inputSchema` | — | JSON Schema for data sent to the human reviewer |
| `channels[].outputSchema` | — | JSON Schema for the reviewer's response |
| `channels[].outcomeMapping` | — | Maps human choices (e.g. `"approve"`, `"reject"`) to agent actions (`"continue"`) |
| `channels[].recipients` | — | Array of `{type, value, displayName}` objects. `type`: `1`=UserId, `2`=GroupId, `3`=UserEmail |
| `channels[].properties` | — | Action Center app config: `appName`, `appVersion`, `resourceKey`, `isActionableMessageEnabled` |
| `isAgentMemoryEnabled` | — | If `true`, resolved escalations are stored for future auto-resolution |
| `escalationType` | — | Set to `0` (default) |

```json
{
  "$resourceType": "escalation",
  "name": "Manager Approval",
  "description": "Escalates to a human manager for approval when the action exceeds the agent's scope.",
  "escalationType": 0,
  "isAgentMemoryEnabled": false,
  "channels": [
    {
      "name": "Channel",
      "type": "actionCenter",
      "description": "Approval channel for high-value actions.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "Content": { "type": "string" },
          "Comment": { "type": "string", "description": "Reviewer comments" }
        }
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "Comment": { "type": "string", "description": "Reviewer response" }
        }
      },
      "outcomeMapping": {
        "approve": "continue",
        "reject": "continue"
      },
      "recipients": [
        { "type": 1, "value": "user-or-group-uuid", "displayName": "Review Team" }
      ],
      "properties": {
        "appName": "HITL App",
        "appVersion": 1,
        "resourceKey": "action-center-app-uuid",
        "isActionableMessageEnabled": false
      }
    }
  ]
}
```

> **When to use `isAgentMemoryEnabled: true`:** Enable this when the agent should learn from resolved escalations and auto-resolve similar cases in the future. Disable for privacy-sensitive workflows.

---

## 4. MCP Resources (`$resourceType: "mcp"`)

MCP resources connect the agent to an external **Model Context Protocol (MCP) server** — a standardised interface that exposes tools to LLM agents. Use this to integrate third-party MCP-compatible servers (e.g. GitHub MCP, Brave Search MCP, custom internal servers).

**Key fields:**

| Field | Description |
|---|---|
| `slug` | Unique identifier for this MCP connection |
| `folderPath` | Orchestrator folder where the MCP server connection is registered |
| `dynamicTools` | How the agent discovers tools from the server: `"none"` (use `availableTools` list only), `"schema"` (discover tools with schemas at runtime), `"all"` (discover all tools dynamically) |
| `availableTools` | Tool filter list. Format depends on `dynamicTools`: when `"none"`, provide an array of tool **objects** with `name`, `description`, `inputSchema`, `outputSchema`; when `"schema"` or `"all"`, provide an array of tool **name strings** as a filter. |

```json
{
  "$resourceType": "mcp",
  "slug": "github-mcp",
  "name": "GitHub MCP Server",
  "description": "Provides tools for interacting with GitHub repositories: reading files, listing issues, creating pull requests, and searching code. Use these tools when the user's request involves source code, repository management, or CI/CD workflows.",
  "folderPath": "Engineering/Integrations",
  "dynamicTools": "schema",
  "availableTools": [
    "list_repositories",
    "get_file_contents",
    "create_issue",
    "list_pull_requests",
    "search_code"
  ],
  "serverConfig": {
    "timeoutSeconds": 30
  }
}
```

> **`dynamicTools` guidance:**
> - Use `"none"` + `availableTools` for stable, well-known tool sets where you want explicit control.
> - Use `"schema"` when the MCP server may add tools over time and you want the agent to discover them automatically with type safety.
> - Use `"all"` only in trusted environments — it exposes every tool the server publishes without filtering.

---

## 5. A2A Resources (`$resourceType: "a2a"`)

A2A resources use the **Agent-to-Agent (A2A) protocol** to connect to agents hosted on external systems (outside UiPath Automation Cloud). Unlike `type: "Agent"` tool resources which call UiPath-native agents, A2A uses a standardised HTTP-based protocol with an **Agent Card** that describes the remote agent's capabilities.

**Key fields:**

| Field | Description |
|---|---|
| `id` | UUID identifier for this A2A resource |
| `slug` | Unique string identifier for this A2A connection |
| `agentCardUrl` | URL where the remote agent publishes its Agent Card (capability manifest) |
| `isActive` | Whether this A2A connection is active (default `true`) |
| `cachedAgentCard` | Inline copy of the Agent Card JSON, used when the remote URL is not accessible at design time or for performance |

```json
{
  "$resourceType": "a2a",
  "id": "a2a-resource-uuid",
  "slug": "legal-review-agent",
  "isEnabled": true,
  "name": "Legal Review Agent",
  "description": "An external legal AI agent that reviews contract clauses for compliance risks and suggests redlines. Use this when the user submits a contract for review or when generated content includes legal commitments.",
  "isActive": true,
  "agentCardUrl": "https://legal-ai.company.com/.well-known/agent.json",
  "cachedAgentCard": {
    "name": "Legal Review Agent",
    "description": "Reviews contracts and flags compliance issues.",
    "version": "2.1.0",
    "capabilities": {
      "streaming": false,
      "pushNotifications": false
    },
    "skills": [
      {
        "id": "review-contract",
        "name": "Review Contract",
        "description": "Analyses contract text and returns a risk assessment with suggested redlines.",
        "inputModes": ["text"],
        "outputModes": ["text"]
      }
    ],
    "url": "https://legal-ai.company.com/a2a"
  }
}
```

> **`cachedAgentCard` vs `agentCardUrl`:** Always provide `agentCardUrl` for live environments so the agent picks up capability updates automatically. Provide `cachedAgentCard` as a fallback for offline development, testing, or when the remote agent is in a different network zone.

---

## Combining Resources in `agent.json`

Resources are listed in the `"resources"` array. The agent's LLM uses the `description` field of each resource to decide when to invoke it — write descriptions as clear instructions to the model.

```json
{
  "resources": [
    { "$resourceType": "tool",      "type": "Api",       "name": "Get Customer Data",    "..." : "..." },
    { "$resourceType": "context",   "name": "Product Knowledge Base", "..." : "..." },
    { "$resourceType": "escalation","name": "Manager Approval",       "..." : "..." },
    { "$resourceType": "mcp",       "slug": "github-mcp",             "..." : "..." },
    { "$resourceType": "a2a",       "slug": "legal-review-agent",     "..." : "..." }
  ]
}
```

---

## See Also

- [setup.md](./setup.md) — Project setup and directory structure
- [agent-json-reference.md](./agent-json-reference.md) — Full `agent.json` schema reference
- [../../assets/templates/agent.json](../../assets/templates/agent.json) — Minimal starter template
