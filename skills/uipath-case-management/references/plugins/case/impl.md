# case (root) — Implementation

## Prerequisites

The case file must live inside a solution + project structure. Run these **before** `cases add`:

```bash
mkdir -p <directory>
cd <directory> && uip solution new <SolutionName>
cd <SolutionName> && uip maestro case init <ProjectName>
uip solution project add <ProjectName> <SolutionName>.uipx
```

## CLI Command

```bash
uip maestro case cases add \
  --name "<name>" \
  --file "<SolutionDir>/<ProjectName>/caseplan.json" \
  --case-identifier "<identifier>" \
  --identifier-type <constant|external> \
  --case-app-enabled \
  --description "<description>" \
  --output json
```

### Required flags

| Flag | Required | Notes |
|------|----------|-------|
| `--name` | yes | Human-readable case name |
| `--file` | yes | **Literal filename `caseplan.json`** — do not substitute |

### Optional flags

| Flag | Default | Notes |
|------|---------|-------|
| `--case-identifier` | `<name>` | Runtime case identifier |
| `--identifier-type` | `constant` | `constant` \| `external` |
| `--case-app-enabled` | (flag not set = `false`) | Include the flag to enable |
| `--description` | *(empty)* | |

## Example

```bash
uip maestro case cases add \
  --name "Loan Approval" \
  --file "loan-approval-solution/loan-approval-project/caseplan.json" \
  --case-identifier "LOAN" \
  --identifier-type constant \
  --case-app-enabled \
  --description "End-to-end loan application processing with credit check, risk scoring, and manual review" \
  --output json
```

## Resulting JSON Shape

After the command runs, `caseplan.json` contains:

```json
{
  "root": {
    "id": "<shortId>",
    "name": "Loan Approval",
    "type": "case-management:root",
    "caseIdentifier": "LOAN",
    "caseIdentifierType": "constant",
    "caseAppEnabled": true,
    "version": "v17",
    "publishVersion": 2,
    "data": {
      "intsvcActivityConfig": "v2",
      "uipath": {
        "variables": {},
        "bindings": []
      }
    },
    "description": "End-to-end loan application processing..."
  },
  "nodes": [
    {
      "id": "<trigger-id>",
      "type": "case-management:Trigger",
      "position": { "x": 200, "y": 0 },
      "data": { "uipath": { "serviceType": "None" } }
    }
  ],
  "edges": []
}
```

> The implicit Trigger node is created automatically. Its ID is returned in the `--output json` response — capture it for use as an edge source in Step 8.

## Post-Add Validation

Capture from `--output json`:

- **File path** — confirm the file exists on disk.
- **Initial Trigger ID** — save it as the source for the first edge (Trigger → first stage).
- Confirm `root.type == "case-management:root"` and `root.version == "v17"`.

## Editing the Root Case

```bash
uip maestro case cases edit <file> \
  --name "<new-name>" \
  --case-identifier "<new-identifier>" \
  --identifier-type <constant|external> \
  --case-app-enabled
```

At least one flag is required for `edit`. Use when the sdd.md is updated post-build and re-runs planning.
