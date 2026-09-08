<!--skill-flavor:maintenance-capability-boundary:start-->
- **Author** = on disk in the open solution, no login step at all (`flow init`, `validate`, `format`, registry, JSON edits) — the host injects auth on every `uip` call
- **Operate** = touches the cloud (`flow debug` through the host, `solution publish`, `process run`, `instance ...`); there is no `solution upload` and no local pack in Studio Web
- **Diagnose** = postmortem on a failed run (`instance incidents`, `instance variables`, `instance asset`, `incident get`, `job traces`)
- **Evaluate** = evaluations against the open solution; local eval-set/evaluator CRUD is offline, and `eval run *` needs `--solution-id`/`--project-id` from the context (`eval set`, `eval evaluator`, `eval run`)

Author terminates at `validate` + `format` and hands off to Operate. Operate hands off to Diagnose when a run faults. Diagnose hands off back to Author for the underlying fix. Evaluate attaches to the flow project in the open solution — nothing is uploaded first.
<!--skill-flavor:maintenance-capability-boundary:end-->
