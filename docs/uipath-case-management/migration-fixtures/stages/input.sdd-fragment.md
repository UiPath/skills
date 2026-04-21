# Stages Golden — SDD Fragment

Minimal sdd fragment that exercises only the `stages` plugin. Used to generate both the CLI output and the direct-JSON-write output for compatibility diffing.

## Case

- **Name:** StagesProbe
- **Case identifier:** StagesProbe (constant)
- **Case App Enabled:** false

## Stages

1. **Submission Review** (regular stage)
   - Description: Initial submission review

2. **Exception Handling** (exception stage)
   - Description: Fallback for failed submissions

## Not covered by this fragment

- Edges (stages pilot scope only — edges are a separate plugin migration)
- Triggers (default trigger `trigger_1` is created by `cases add`, not by this plugin)
- Tasks, conditions, SLA, variables

## Equivalent CLI invocation

```bash
uip maestro case cases add --name "StagesProbe" --file caseplan.json --output json
uip maestro case stages add caseplan.json \
  --label "Submission Review" \
  --description "Initial submission review" \
  --output json
uip maestro case stages add caseplan.json \
  --label "Exception Handling" \
  --type exception \
  --description "Fallback for failed submissions" \
  --output json
```

## Equivalent direct-JSON-write outcome

Same outcome, starting from the CLI-scaffolded `caseplan.json` (the `cases add` step remains CLI — `case` plugin is out of scope for the JSON shift). The two subsequent stages are added by splicing into `schema.nodes` per [`plugins/stages/impl-json.md`](../../../skills/uipath-case-management/references/plugins/stages/impl-json.md).
