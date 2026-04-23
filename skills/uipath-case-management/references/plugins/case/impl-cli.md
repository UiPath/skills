# case (root) — CLI Implementation (Fallback)

> **Fallback path.** The `case` plugin is on the JSON strategy per [`case-editing-operations.md`](../../case-editing-operations.md). Use [`impl-json.md`](impl-json.md) by default — this file is the CLI fallback for when the JSON path fails empirically. The JSON recipe covers both scaffold (replaces `uip maestro case init`) and the root caseplan write (replaces `cases add`) in a single plugin invocation.

## Prerequisites

The case file must live inside a solution + project structure. Run these **before** `cases add`:

```bash
mkdir -p <directory>
cd <directory> && uip solution new <SolutionName>
cd <SolutionName> && uip maestro case init <ProjectName>
uip solution project add <ProjectName> <SolutionName>.uipx
```

> When falling back from the JSON path, `uip solution new` + `uip solution project add` are the **same** commands run by the JSON path's Step 6.0 and Step 6.2 — only `uip maestro case init` differs (CLI invokes it here; JSON writes the 5 files directly in [`impl-json.md`](impl-json.md) § Scaffold).

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

After the command runs, `caseplan.json` contains (CLI 0.3.4):

```json
{
    "root": {
        "id": "root",
        "name": "Loan Approval",
        "type": "case-management:root",
        "caseIdentifier": "LOAN",
        "caseAppEnabled": true,
        "caseIdentifierType": "constant",
        "version": "v17",
        "publishVersion": 2,
        "data": {
            "intsvcActivityConfig": "v2",
            "uipath": {
                "variables": {
                    "inputOutputs": []
                },
                "bindings": []
            }
        },
        "description": "End-to-end loan application processing..."
    },
    "nodes": [
        {
            "id": "trigger_1",
            "type": "case-management:Trigger",
            "position": { "x": 0, "y": 0 },
            "data": { "label": "Trigger 1" }
        }
    ],
    "edges": []
}
```

> The implicit Trigger node is hard-coded: `id = "trigger_1"`, `position = { x: 0, y: 0 }`, `data.label = "Trigger 1"`. No `style`, `measured`, `parentElement`, or `uipath.serviceType` fields. Secondary triggers added via `triggers add-manual` have a different shape.
>
> `root.description` is present only when `--description` is passed; omitted otherwise. When present, it appears as a sibling of `data` at root level (not inside `data`).
>
> `root.data` starts pre-populated with `intsvcActivityConfig: "v2"` and `uipath.variables.inputOutputs: []` + `uipath.bindings: []`. Downstream plugins (notably `variables/global-vars`) append to those structures.

## Post-Add Validation

Capture from `--output json`:

- **File path** — confirm the file exists on disk.
- **Initial Trigger ID** — the literal string `"trigger_1"`. Use as the source for the first edge (Trigger → first stage).
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
