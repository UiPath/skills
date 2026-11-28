<!--skill-flavor:extraction-run-cases:start-->
Run every case, one call each, with the case's input object (`base` with its `inputs` laid over it and its `omit`
names removed) as inline JSON:

```bash
uip rules debug "<RULE_NAME>" --inputs '<INPUTS_JSON>'
```

`<RULE_NAME>` is the project name in the open solution, not a path; `@file` is not supported. The output is plain text:
`actual` is the decision's output it prints (SKILL.md, Verify). Write `test-results.json` next to `tests.json`: a JSON
list with one object per case, each with `name`, `expected`, `actual` and `pass`. A case that was not run is not a
pass. Fix the table and run all cases again; after 3 rounds with failures left, stop and list the failing cases
(SKILL.md rule 7).
<!--skill-flavor:extraction-run-cases:end-->
