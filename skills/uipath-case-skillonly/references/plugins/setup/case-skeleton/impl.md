# Case Skeleton — Implementation

## Step 1 — Scaffold Project Files (CLI)

The project directory requires several non-JSON files that must be scaffolded by CLI:

```bash
# Create solution
uip solution new <SolutionName>

# Create case project inside solution
cd <SolutionName>
uip case init <ProjectName>

# Add project to solution
uip solution project add <ProjectName> <SolutionName>.uipx
```

This creates the required project files alongside `caseplan.json`:
- `project.uiproj`
- `operate.json`
- `entry-points.json`
- `bindings_v2.json`
- `package-descriptor.json`

## Step 2 — Write caseplan.json Directly

Do **not** run `uip case cases add`. Write `caseplan.json` from scratch:

```json
{
  "root": {
    "id": "root",
    "name": "<Case Name>",
    "type": "case-management:root",
    "caseIdentifier": "<identifier>",
    "caseIdentifierType": "constant",
    "caseAppEnabled": true,
    "version": "v16",
    "publishVersion": 2,
    "description": "<case description>",
    "data": {
      "uipath": {
        "bindings": [],
        "variables": {
          "inputs": [],
          "outputs": [],
          "inputOutputs": []
        }
      },
      "slaRules": [],
      "intsvcActivityConfig": "v2"
    },
    "caseAppConfig": {
      "caseSummary": "",
      "sections": []
    },
    "caseExitConditions": []
  },
  "nodes": [],
  "edges": []
}
```

### Root field reference

| Field | Required | Notes |
|---|---|---|
| `version` | ✓ | Always `"v16"` for current schema |
| `publishVersion` | ✓ | Currently `2` (bumped per FE feature flag — keep aligned with FE default) |
| `caseAppEnabled` | ✓ | Default `true` — the UI assumes Case App is on for new cases. Set `false` only if the user explicitly opts out. |
| `caseAppConfig` | when `caseAppEnabled=true` | See [Case App Config](#case-app-config) below. Empty defaults are valid. |
| `data.intsvcActivityConfig` | ✓ | Currently `"v2"` (Integration Service activity schema version) |
| `data.slaRules` | optional | Case-level SLA + escalation, see `plugins/sla/setup` |
| `caseExitConditions` | ✓ | At least one — see `plugins/conditions/case-exit` |

### Case App Config

`caseAppConfig` populates the auto-generated Case App UI shown to case workers. Both fields are optional but valid:

```json
"caseAppConfig": {
  "caseSummary": "=string.Format(\"{0} - {1}\", vars.response.customerName, vars.response.policyId)",
  "sections": [
    {
      "id": "section-<uuid>",
      "title": "Applicant",
      "details": "{\"Name\":\"=vars.response.customerName\",\"Email\":\"=vars.response.customerEmail\"}"
    },
    {
      "id": "section-<uuid>",
      "title": "Claim details",
      "details": "{\"Loss date\":\"=vars.response.claimDate\",\"Cause\":\"=vars.response.claimCauseOfLoss\"}"
    }
  ]
}
```

| Field | Notes |
|---|---|
| `caseSummary` | Single expression rendered as the case header. Use `=string.Format(...)`, `=vars.x`, or any expression form (see [variables/global-vars](../../variables/global-vars/impl.md)). |
| `sections[]` | Each section is a card in the Case App. `id` is `section-<uuid>` (any unique string). |
| `sections[].title` | Card heading shown to case worker. |
| `sections[].details` | **JSON-encoded string** (not a JSON object) — keys are field labels, values are expressions. The string is parsed at render time. |

If the user does not specify case app fields, write empty defaults (`caseSummary: ""`, `sections: []`) — leaving `caseAppConfig` absent breaks the UI when `caseAppEnabled: true`.

## Step 3 — Read the Planning Document

If a planning document (`tasks.md`) is provided, follow the section order it defines:

| Planning section | What to build |
|---|---|
| `Create case file` | Populate root node fields (name, caseIdentifier, description) |
| `Create stage` | Add stage nodes to `nodes[]` — see [setup/stage](../stage/impl.md) |
| `Add edge` | Add edges to `edges[]` — see [setup/edge](../edge/impl.md) |
| `Add <type> task` | Look up resource, declare bindings, add task to stage — see [setup/task](../task/impl.md) |
| `Add stage/task entry/exit condition` | Add conditions inline in stage/task — see conditions plugins |
| `Set SLA` / `Add escalation rule` | Add slaRules — see [sla/setup](../../sla/setup/impl.md) |

Build the entire `caseplan.json` in one pass following this order. Do not make incremental partial writes.

## Minimal Binary (uip binary resolution)

If `uip` is not on PATH:

```bash
UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
$UIP --version
```
