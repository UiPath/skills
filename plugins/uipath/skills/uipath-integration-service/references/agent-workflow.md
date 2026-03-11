# Agent Workflow: Performing Actions on a Service

This is the definitive guide for how a coding agent should execute Integration Service operations. Follow these steps in order every time the user asks to interact with an external service.

## Step 1: Find the Connector

```bash
# Search for the vendor by name
uipcli is connectors list --filter "<vendor>" --format json
# If no results, retry with --refresh (cache may be stale)
uipcli is connectors list --filter "<vendor>" --refresh --format json
```

| Outcome | Action |
|---|---|
| Native connector found (e.g., `uipath-salesforce-sfdc`) | Use it. Proceed to Step 2 with its connector key. |
| No native connector found | Fall back to HTTP connector (`uipath-uipath-http`). Proceed to Step 2. |

See [connectors.md](connectors.md) for full connector reference.

---

## Step 2: Find a Connection

### For Native Connectors (e.g., Salesforce, Jira, Slack)

```bash
uipcli is connections list "<connector-key>" --format json
# If no results, retry with --refresh
uipcli is connections list "<connector-key>" --refresh --format json
```

**Decision logic:**

```
Connections exist?
├── YES
│   ├── Pick the DEFAULT connection (IsDefault: Yes)
│   ├── Check if State is "Enabled"
│   │   ├── Enabled → proceed to Step 3
│   │   └── Not Enabled → prompt user to choose another enabled connection
│   └── No connections are enabled → prompt user to create a new one
└── NO
    └── Prompt user to create: is connections create "<connector-key>"
```

### For HTTP Fallback (No Native Connector)

```bash
uipcli is connections list "uipath-uipath-http" --refresh --format json
```

```
Look for a connection whose NAME matches the target vendor
(e.g., connection named "Apify" for Apify API calls)
├── Found → use that connection
└── Not Found
    └── Prompt user to either:
        a. Choose from existing HTTP connections
        b. Create a new one: is connections create "uipath-uipath-http"
```

> **Critical:** NEVER guess or hallucinate connection IDs or names. Always list connections and select from real data.

See [connections.md](connections.md) for full connection reference.

---

## Step 3: Verify the Connection (Always Required)

Every connection MUST be pinged before use, regardless of its reported state.

```bash
uipcli is connections ping "<connection-id>" --format json
```

| Ping Result | Action |
|---|---|
| Returns "Enabled" | Connection is healthy. Proceed to Step 4. |
| Fails or non-enabled | Try re-authenticating: `is connections edit <id>`. If still fails, prompt user to choose a different connection or create new. |

---

## Step 4: Discover Activities

Once the connection is verified, discover available actions.

```bash
uipcli is activities list "<connector-key>" --format json
# If no results, retry with --refresh
uipcli is activities list "<connector-key>" --refresh --format json
```

Activities are pre-built actions (e.g., "Send Message" for Slack, "Create Issue" for Jira). Review the list to find the activity matching the user's intent.

For resource-based CRUD operations, also explore resources. **Always pass `--connection-id` and `--operation`** to get accurate results in a single call:

- `--connection-id` — Returns custom objects/fields specific to that connection
- `--operation` — For `list`: filters to resources supporting that action. For `describe`: returns only the relevant field subset (required/optional) instead of the entire metadata.

Both commands cache results locally. If expected results are missing, retry with `--refresh`.

```bash
uipcli is resources list "<connector-key>" \
  --connection-id "<id>" \
  --operation <Create|List|Retrieve|Update|Delete|Replace> \
  --format json

uipcli is resources describe "<connector-key>" "<object-name>" \
  --connection-id "<id>" \
  --operation Create \
  --format json
```

See [activities.md](activities.md) and [resources.md](resources.md) for full references.

---

## Important Rules

| Rule | Rationale |
|---|---|
| **Use `--refresh` when results are missing** | Cache may be stale. Always retry with `--refresh` before concluding something doesn't exist. |
| **Always ping before any operation** | A connection may report "Enabled" but be expired or revoked. |
| **Never hallucinate IDs or names** | Always list real data first. Fabricated IDs cause silent failures. |
| **Prompt the user when multiple choices exist** | Don't assume which connection the user wants. Present options. |
| **Prefer the default connection** | Pick `IsDefault: Yes` first, then first enabled connection. |

---

## Step 5: Resolve Reference Fields (Before Execute)

After describing a resource, check the response for `referenceFields`. These are fields whose values must be looked up from another resource — **never guess or fabricate them**.

```
referenceFields present?
├── YES
│   ├── For EACH reference field:
│   │   ├── Execute: is resources execute list "<connector-key>" "<referencedObject>" --connection-id <id>
│   │   ├── Collect the lookupValue (e.g., "id") from results
│   │   └── If multiple values: present options to user (show name + id)
│   └── Build request body with resolved values → proceed to Execute
└── NO
    └── Build request body from user input → proceed to Execute
```

> **Critical:** Reference fields like `departmentId`, `contactId`, `accountId` etc. require real IDs from the referenced object. Fabricated IDs will cause silent failures or errors.

See [resources.md — Reference Fields](resources.md#reference-fields-critical) for detailed examples.

---

## Complete Example: Salesforce (Native Connector)

```bash
# Step 1: Find the connector
uipcli is connectors list --filter "salesforce" --format json
# → Found: "uipath-salesforce-sfdc"

# Step 2: Find a connection
uipcli is connections list "uipath-salesforce-sfdc" --refresh --format json
# → Found: ID "abc-123", IsDefault: Yes, State: Enabled

# Step 3: Verify the connection
uipcli is connections ping "abc-123" --format json
# → State: Enabled (healthy)

# Step 4: Discover activities
uipcli is activities list "uipath-salesforce-sfdc" --format json

# Step 5: List resources (always pass --connection-id and --operation)
uipcli is resources list "uipath-salesforce-sfdc" \
  --connection-id "abc-123" --operation Create --format json

# Step 6: Describe the resource to see required fields and references
uipcli is resources describe "uipath-salesforce-sfdc" "Account" \
  --connection-id "abc-123" --operation Create --format json

# Step 7: Resolve reference fields (if any in describe output)
# e.g., if "OwnerId" references "users":
# uipcli is resources execute list "uipath-salesforce-sfdc" "users" \
#   --connection-id "abc-123" --format json

# Step 8: Execute with resolved values
uipcli is resources execute create "uipath-salesforce-sfdc" "Account" \
  --connection-id "abc-123" \
  --body '{"Name": "Acme Corp", "Industry": "Technology"}' \
  --format json
```

## Complete Example: Apify (HTTP Fallback)

```bash
# Step 1: Find the connector
uipcli is connectors list --filter "apify" --refresh --format json
# → No native connector found. Fall back to HTTP.

# Step 2: Find an HTTP connection for Apify
uipcli is connections list "uipath-uipath-http" --refresh --format json
# → Found: ID "http-001", Name: "Apify", State: Enabled

# Step 3: Verify the connection
uipcli is connections ping "http-001" --format json
# → State: Enabled (healthy)

# Step 4: Discover activities
uipcli is activities list "uipath-uipath-http" --format json
# → HTTP Request activity available. Use with Apify API endpoints.
```
