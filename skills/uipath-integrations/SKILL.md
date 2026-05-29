---
name: uipath-integrations
description: "UiPath integration assistant for connecting automations to popular SaaS tools — Zapier, Notion, Airtable, HubSpot, Slack, and other third-party APIs. Covers webhook triggers, REST API calls from coded workflows and RPA workflows, credential management via Orchestrator assets, and common solopreneur integration patterns. TRIGGER when: User wants to connect UiPath automation to a SaaS tool (Zapier, Notion, Airtable, HubSpot, Slack, Trello, Calendly, Typeform, etc.); User wants to send Slack notifications from a workflow; User wants to read/write Airtable or Notion data; User wants to trigger UiPath from a Zapier zap or webhook; User wants to push data to HubSpot CRM; User asks about calling a REST API from a workflow; User wants to use HTTP activities or HttpClient in a workflow. DO NOT TRIGGER when: User is working with built-in UiPath Integration Service connectors (Jira, Salesforce, ServiceNow — use uipath-coded-workflows or uipath-platform instead), or asking about Orchestrator deployment/setup (use uipath-platform instead)."
metadata:
   allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath SaaS Integration Assistant

Connect UiPath automations to popular SaaS tools and third-party APIs — covering webhooks, REST calls, credential management, and common solopreneur integration patterns.

## When to Use This Skill

- User wants to **send a Slack message** from a workflow (e.g., job completion alerts, error notifications)
- User wants to **read or write Airtable records** (e.g., sync data between Airtable and an internal system)
- User wants to **create or update Notion pages/databases** from an automation
- User wants to **push contacts or deals to HubSpot CRM** automatically
- User wants to **trigger a UiPath job from Zapier** (inbound webhook)
- User wants to **call any REST API** using `HttpClient` or `system.http` activities
- User wants to **store API keys securely** in Orchestrator assets
- User wants to **handle webhook payloads** received by an automation

## Quick Start

### Step 1 — Store API credentials in Orchestrator

Never hardcode API keys. Store them as Orchestrator assets and read at runtime:

```bash
# Create a Text asset for an API key
uip resources assets create --name "SlackBotToken" --type Text --value "xoxb-..." --folder "<FOLDER>" --format json

# Create a Credential asset for username/password-based APIs
uip resources assets create --name "HubSpotCredential" --type Credential --username "api" --password "<API_KEY>" --folder "<FOLDER>" --format json

# Read an asset value at runtime (use in workflow)
uip resources assets get --name "SlackBotToken" --folder "<FOLDER>" --format json
```

In a coded workflow, retrieve assets using the `system` service:

```csharp
var token = system.GetAsset("SlackBotToken");
```

### Step 2 — Choose your integration approach

| Integration | Recommended Approach |
|---|---|
| **Slack** | HTTP POST to Incoming Webhook URL or Bot API |
| **Airtable** | Airtable REST API v0 via `HttpClient` |
| **Notion** | Notion REST API v1 via `HttpClient` |
| **HubSpot** | HubSpot REST API v3 via `HttpClient` |
| **Zapier (outbound)** | POST to Zapier Webhook trigger URL |
| **Zapier (inbound)** | Zapier calls `uip` CLI via Webhooks action |
| **Generic REST API** | `system.http` activities or `HttpClient` |

### Step 3 — Make the API call

See the integration-specific sections below for patterns.

## Task Navigation

| I need to... | Read these |
|---|---|
| **Send a Slack notification** | [Slack Integration](#slack-integration) |
| **Read/write Airtable records** | [Airtable Integration](#airtable-integration) |
| **Create/update Notion pages** | [Notion Integration](#notion-integration) |
| **Push data to HubSpot CRM** | [HubSpot Integration](#hubspot-integration) |
| **Trigger UiPath from Zapier** | [Zapier Inbound Trigger](#zapier-inbound-trigger) |
| **Call UiPath from Zapier or webhook** | [Zapier Inbound Trigger](#zapier-inbound-trigger) |
| **Make a generic REST API call** | [Generic REST API Calls](#generic-rest-api-calls) |
| **Store API credentials securely** | [Credential Management](#credential-management) |
| **Handle webhook payloads** | [Webhook Input Handling](#webhook-input-handling) |

---

## Slack Integration

Send messages, alerts, and reports to Slack channels from any workflow.

### Option A — Incoming Webhook (simplest, no OAuth)

Create an Incoming Webhook in Slack (Apps → Incoming Webhooks → Add to Slack).
Store the webhook URL as an Orchestrator asset named `SlackWebhookUrl`.

**Coded Workflow:**

```csharp
using System.Net.Http;
using System.Text;
using Newtonsoft.Json;

[Workflow]
public void Execute()
{
    var webhookUrl = system.GetAsset("SlackWebhookUrl");
    var payload = JsonConvert.SerializeObject(new { text = "✅ Automation completed successfully!" });

    using var client = new HttpClient();
    var response = client.PostAsync(webhookUrl, new StringContent(payload, Encoding.UTF8, "application/json")).Result;
    Log($"Slack response: {response.StatusCode}");
}
```

### Option B — Slack Bot API (for reading channels, DMs, file uploads)

Store `SlackBotToken` as an Orchestrator Text asset.

```csharp
var token = system.GetAsset("SlackBotToken");
using var client = new HttpClient();
client.DefaultRequestHeaders.Authorization =
    new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);

var payload = JsonConvert.SerializeObject(new {
    channel = "#notifications",
    text = $"Job finished at {DateTime.Now:HH:mm}",
    username = "UiPath Bot"
});

var response = client.PostAsync(
    "https://slack.com/api/chat.postMessage",
    new StringContent(payload, Encoding.UTF8, "application/json")).Result;
```

---

## Airtable Integration

Read records from and write records to an Airtable base.

Store these Orchestrator assets:
- `AirtableApiKey` (Text) — Personal Access Token from airtable.com/create/tokens
- `AirtableBaseId` (Text) — found in the Airtable API docs for your base (starts with `app`)

### List records from a table

```csharp
var apiKey = system.GetAsset("AirtableApiKey");
var baseId = system.GetAsset("AirtableBaseId");
var tableName = "Leads"; // URL-encode if it has spaces

using var client = new HttpClient();
client.DefaultRequestHeaders.Authorization =
    new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);

var url = $"https://api.airtable.com/v0/{baseId}/{Uri.EscapeDataString(tableName)}?maxRecords=100";
var response = client.GetAsync(url).Result;
var json = response.Content.ReadAsStringAsync().Result;
// Parse json with Newtonsoft.Json or System.Text.Json
```

### Create a record

```csharp
var payload = JsonConvert.SerializeObject(new {
    fields = new {
        Name = "Acme Corp",
        Status = "New Lead",
        Email = "contact@acme.com"
    }
});

var response = client.PostAsync(
    $"https://api.airtable.com/v0/{baseId}/Leads",
    new StringContent(payload, Encoding.UTF8, "application/json")).Result;
```

---

## Notion Integration

Read and write Notion databases from a workflow.

Store `NotionApiKey` (Text asset) — Integration token from notion.so/my-integrations.
Grant the integration access to your database in Notion (Share → Invite integration).

### Query a database

```csharp
var apiKey = system.GetAsset("NotionApiKey");
var databaseId = "your-database-id"; // from the Notion URL

using var client = new HttpClient();
client.DefaultRequestHeaders.Authorization =
    new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);
client.DefaultRequestHeaders.Add("Notion-Version", "2022-06-28");

var response = client.PostAsync(
    $"https://api.notion.com/v1/databases/{databaseId}/query",
    new StringContent("{}", Encoding.UTF8, "application/json")).Result;
var json = response.Content.ReadAsStringAsync().Result;
```

### Create a page in a database

```csharp
var payload = JsonConvert.SerializeObject(new {
    parent = new { database_id = databaseId },
    properties = new {
        Name = new {
            title = new[] { new { text = new { content = "New Automation Task" } } }
        },
        Status = new {
            select = new { name = "In Progress" }
        }
    }
});

var response = client.PostAsync(
    "https://api.notion.com/v1/pages",
    new StringContent(payload, Encoding.UTF8, "application/json")).Result;
```

---

## HubSpot Integration

Create and update contacts, deals, and companies in HubSpot CRM.

Store `HubSpotApiKey` (Text asset) — Private App token from HubSpot Settings → Integrations → Private Apps.

### Create a contact

```csharp
var token = system.GetAsset("HubSpotApiKey");
using var client = new HttpClient();
client.DefaultRequestHeaders.Authorization =
    new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);

var payload = JsonConvert.SerializeObject(new {
    properties = new {
        firstname = "Jane",
        lastname = "Doe",
        email = "jane@example.com",
        phone = "+1-555-0100",
        company = "Acme Corp"
    }
});

var response = client.PostAsync(
    "https://api.hubapi.com/crm/v3/objects/contacts",
    new StringContent(payload, Encoding.UTF8, "application/json")).Result;
```

### Search for existing contact before creating

```csharp
var searchPayload = JsonConvert.SerializeObject(new {
    filterGroups = new[] {
        new { filters = new[] { new { propertyName = "email", @operator = "EQ", value = "jane@example.com" } } }
    }
});

var searchResponse = client.PostAsync(
    "https://api.hubapi.com/crm/v3/objects/contacts/search",
    new StringContent(searchPayload, Encoding.UTF8, "application/json")).Result;
```

---

## Zapier Inbound Trigger

Allow Zapier zaps to trigger a UiPath job via webhook.

### Approach: Zapier Webhooks → Orchestrator REST API

In Zapier, use the **Webhooks by Zapier** action (POST) targeting the Orchestrator Start Jobs endpoint:

```
URL: https://cloud.uipath.com/{org}/{tenant}/orchestrator_/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs
Headers:
  Authorization: Bearer <access_token>
  X-UIPATH-OrganizationUnitId: <folder_id>
  Content-Type: application/json
Body:
  {
    "startInfo": {
      "ReleaseKey": "<release_key>",
      "Strategy": "ModernJobsCount",
      "JobsCount": 1,
      "RuntimeType": "Unattended",
      "InputArguments": "{\"LeadEmail\": \"{{email}}\"}"
    }
  }
```

Get the `ReleaseKey` via:
```bash
uip or releases list --format json
```

For CI/CD or machine-token auth, use client credentials:
```bash
uip login --client-id "<ID>" --client-secret "<SECRET>" --tenant "<TENANT>" --format json
```

---

## Generic REST API Calls

For any REST API not covered above.

### Using HttpClient in coded workflows (recommended)

```csharp
using System.Net.Http;
using System.Net.Http.Headers;

[Workflow]
public void Execute(string apiUrl, string bearerToken)
{
    using var client = new HttpClient();
    client.DefaultRequestHeaders.Authorization =
        new AuthenticationHeaderValue("Bearer", bearerToken);
    client.DefaultRequestHeaders.Accept.Add(
        new MediaTypeWithQualityHeaderValue("application/json"));

    var response = client.GetAsync(apiUrl).Result;
    response.EnsureSuccessStatusCode();
    var body = response.Content.ReadAsStringAsync().Result;
    Log($"Response: {body}");
}
```

### Using HTTP Request activity (RPA/XAML workflows)

In XAML workflows, use the `UiPath.Web.Activities` package:
```bash
uip rpa install-or-update-packages --packages '[{"id":"UiPath.Web.Activities"}]' --project-dir "<PROJECT_DIR>" --format json
```

Activities available: `HTTP Request`, `Deserialize JSON`, `Serialize JSON`.

---

## Credential Management

Best practices for API keys, tokens, and secrets in UiPath automations.

### Asset types for different credential scenarios

| Secret Type | Asset Type | Example |
|---|---|---|
| API token / key | `Text` | Slack bot token, Airtable PAT |
| Username + password | `Credential` | Basic auth APIs |
| OAuth client secret | `Secret` | Encrypted high-sensitivity values |
| Connection string | `HttpConnectionString` | API base URL + auth combined |

### Retrieve at runtime (coded workflow)

```csharp
// Text asset
var apiKey = system.GetAsset("MyApiKey");

// Credential asset
var cred = system.GetAsset("MyCredential"); // returns NetworkCredential
var username = cred.UserName;
var password = cred.Password;
```

### Never do this

```csharp
// ❌ NEVER hardcode credentials
var apiKey = "sk-abc123...";

// ❌ NEVER log credential values
Log($"Token: {apiKey}");
```

---

## Webhook Input Handling

When a UiPath job is triggered via webhook with input arguments, access them as workflow parameters:

```csharp
[Workflow]
public void Execute(string leadEmail, string leadName, string source)
{
    // leadEmail, leadName, source are passed via InputArguments JSON
    Log($"Processing lead: {leadEmail} from {source}");
    // ... process the lead
}
```

Pass input arguments as JSON when starting the job:
```json
{"leadEmail": "jane@example.com", "leadName": "Jane Doe", "source": "Zapier"}
```

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| API returns 401 Unauthorized | Check asset name spelling; verify token hasn't expired; re-read asset value |
| `HttpClient` not disposed | Always use `using var client = new HttpClient()` or inject a singleton |
| JSON serialization fails | Use `Newtonsoft.Json` (already in UiPath projects) or `System.Text.Json` |
| Zapier webhook fires but job doesn't start | Verify `ReleaseKey` and folder ID are correct; check robot availability |
| Airtable 422 on create | Field names must match exactly (case-sensitive); check field types |
| Rate limits | Add `Delay` activity between batch calls; respect API rate limits (e.g., Airtable: 5 req/s) |

## References

- **[UiPath Platform Skill](../uipath-platform/SKILL.md)** — Authentication, Orchestrator assets, job management
- **[Coded Workflows Skill](../uipath-coded-workflows/SKILL.md)** — C# workflow patterns, NuGet packages, validation
- **[Integration Service](../uipath-platform/references/integration-service/integration-service.md)** — Built-in connectors (Jira, Salesforce, ServiceNow, Slack via IS)
