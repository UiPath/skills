# Case Plugin — sdd Fragment

Minimal sdd fragment exercising only the `case` plugin (root + initial Trigger). Used as input for the golden fixture.

## Minimal variant

```
Case name: MinimalProbe
```

Produces `cli-output-minimal.json` / `json-write-output-minimal.json`:
- `name = "MinimalProbe"`
- Defaults applied: `case-identifier = "MinimalProbe"`, `identifier-type = constant`, `case-app-enabled = false`, no description
- CLI omits the `root.description` key entirely; direct-JSON-write emits `description: ""`

## Full-flags variant

```
Case name: FullProbe
Case identifier: FP-123 (external)
Case App UI: enabled
Description: Full flags test
```

Produces `cli-output-full.json` / `json-write-output-full.json`:
- `name = "FullProbe"`, `caseIdentifier = "FP-123"`, `caseIdentifierType = "external"`, `caseAppEnabled = true`
- `root.description = "Full flags test"` (both CLI and JSON agree when value present)

Both variants always emit the hard-coded initial Trigger node `trigger_1`.
