<!--skill-flavor:maintenance-capability-boundary:start-->
- **Author** = on disk in the open solution, **without `uip login`** (`flow init`, `validate`, `format`, registry, JSON edits)
- **Operate** = touches the cloud, **requires `uip login`** (`solution publish`, `flow debug`, `process run`, `instance ...`); there is no `solution upload` and no local pack in Studio Web
- **Diagnose** = postmortem on a failed run, **requires `uip login`** (`instance incidents`, `instance variables`, `instance asset`, `incident get`, `job traces`)
- **Evaluate** = evaluations against the open solution; local eval-set/evaluator CRUD needs no login, **`eval run *` requires `uip login`** plus `--solution-id`/`--project-id` from the context (`eval set`, `eval evaluator`, `eval run`)

Author terminates at `validate` + `format` and hands off to Operate. Operate hands off to Diagnose when a run faults. Diagnose hands off back to Author for the underlying fix. Evaluate attaches to the flow project in the open solution — nothing is uploaded first.
<!--skill-flavor:maintenance-capability-boundary:end-->
