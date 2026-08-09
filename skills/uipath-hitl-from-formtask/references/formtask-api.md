# Fetching FormTask Layouts from Orchestrator

## Login requirement

All API calls require an active `uip` session:
```bash
uip login status --output json
# Expect: "Status": "Logged in"
```

## Get the list of FormTask types

FormTask types live in the Orchestrator task catalog. Fetch them by querying the Forms endpoint:

```bash
uip login status --output json | python3 -c "
import json,sys,subprocess,os
d=json.load(sys.stdin)
base=d['Data']['CloudUrl']          # e.g. https://cloud.uipath.com
org=d['Data']['Organization']
tenant=d['Data']['Tenant']
print(f'{base}/{org}/{tenant}/orchestrator_/api/TaskForms/GetTaskForms')
"
```

Then call the endpoint with the bearer token from `uip`:
```bash
TOKEN=$(cat ~/.uipath/.auth | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['access_token'])")
curl -s -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "<URL_from_above>" | python3 -m json.tool
```

## GetTaskForms response shape

```json
{
  "value": [
    {
      "Id": 123,
      "Name": "Invoice Approval Form",
      "Key": "invoice-approval-form",
      "formLayout": "{\"components\":[...]}",   // JSON string — parse it
      "buttonNamesList": ["Approve", "Reject"],
      "tenantId": 1
    }
  ]
}
```

Note: `formLayout` is a **JSON string** (double-serialized) — you must `JSON.parse()` it to get the Formio components array.

## Extract specific FormLayout by name

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "<URL>?$filter=Name eq 'Invoice Approval Form'" | \
  python3 -c "
import json,sys
d=json.load(sys.stdin)
item=d['value'][0]
layout=json.loads(item['formLayout'])
print(json.dumps(layout, indent=2))
print('---BUTTONS---')
print(item.get('buttonNamesList', []))
"
```

## Alternative: User pastes the FormLayout JSON

If the user has access to Studio or Studio Web, they can export the FormLayout by:
1. Opening Action Center → Task Catalog
2. Finding the FormTask
3. Clicking "View JSON" or copying from the form designer

The pasted JSON is the Formio object: `{ "components": [...] }`.

## Auth token location

The `uip` CLI stores credentials at `~/.uipath/.auth`. The relevant fields:
- `access_token` — bearer token for Orchestrator API calls
- `base_url` — cloud URL (e.g. `https://cloud.uipath.com`)
- `organization_name` — slug for the org
- `tenant_name` — slug for the tenant

Full orchestrator base URL pattern:
```
{base_url}/{organization_name}/{tenant_name}/orchestrator_
```
