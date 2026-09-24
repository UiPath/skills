# Live-tier addendum — ports whose Flow grader runs `flow debug`

Read `PORTING-BRIEF.md` (Grading contract is mandatory) and `BATCH1-ADDENDUM.md` first. This file adds the rules for ports whose Flow criteria execute the artifact. Everything here is a **T** translation of Flow's `flow_check.run_debug` + output assertions; it is not licence to add assertions Flow does not make.

## The canonical live pattern (copy it)

`_shared/check_jira_get_issue.py` is the canonical live BPMN grader. Its sequence, all via `_shared/bpmn_live.py`:

1-2. `import_exact(bpmn_path, project_dir, LIVE_RUN_DIR / <Name>)`: ephemeral `uip solution init` under the sandbox CWD (so the standard post_run sweep finds the `.uipx`) + `uip solution projects import`, asserting the imported `.bpmn` bytes equal the submitted ones.
3. `debug_data, instance_id = run_debug(imported_project_dir, inputs, log_file, timeout=…)` — `bpmn debug` returns an instance id, not inline variables. `--inputs` JSON is honoured (the escalation run seeded correlationId this way and found it in Jira).
4. `fetch_variables(id)` (`debug-instance variables-all`) → `root_scope(variables_data)` for root variables; `element_output_records(variables_data, element_id)` for a node's `Outputs`; `connector_response_values(outputs, name)` for connector response fields.
5. Side-effect ids go to a flat journal the moment they are visible, before any status check; post_run replays it (teardown) — mirror the Flow task's `_setup/teardown_*.py`.
6. `fetch_incidents(id)` then `require_clean_run(debug_data, evidence)`; a completed run with incidents is a failure. `debug_evidence(id)` does 4 and 6 together for a grader with no side effects.

Known runtime facts (grade around them, do not fight them):
- Element-level `Outputs` (a script task's mapped output, a connector's `response`) are reliably readable in `variables-all`. Root **public output values** have been read back as `null` even when correctly mapped (see `debug/live_debug_e2e/check_live_debug.py` docstring). So when Flow asserted "some output equals X" (`assert_output_value` / `assert_outputs_contain` over `variables.globals` + element outputs), translate to: read the declared output first, and only when it reads back null search `output_leaves(variables, skip=input_echo_ids(process))`, narrowed with `elements=` to the nodes that produce the value when the task names them.
- Variables are addressed by **id**, and the runtime may re-case ids — use `resolve_runtime_key`.
- Debug instances are ephemeral; read variables-all immediately after the run.

## Budgets (the test suite enforces this)

`_shared/test_criterion_budgets.py` statically prices every `run_debug(...)` call in a grader and requires the calling criterion's `timeout:` ≥ `debug_budget(timeout, retries, backoff) + bpmn_live.CRITERION_MARGIN_SECONDS` (plus the other CLI steps you run — the escalation grader sums `STEP_TIMEOUTS` and its unit test pins the YAML timeout to that sum). Keep Flow's criterion `timeout:` if it fits; if the BPMN sequence (solution init + import + debug + variables-all + incidents) needs more, raise ONLY that criterion's `timeout` and say so in the description — this is the one sanctioned deviation from "criteria identical", because the budget is a property of the CLI surface, not of what is graded. `run_limits.task_timeout` must cover the agent's turn budget plus all grading, as the escalation YAML documents.

## Fixtures, seeds, teardown, cleanup

- Copy the Flow task's `_setup/` scripts (seed, teardown, `jira_is.py`-style helpers) into the BPMN task's own `_setup/` and mount them the same way; change only what is suite-specific (none of the `uip is` plumbing is). Keep tenant targets (connection names, folder `Shared/uipath-maestro-flow`, project keys, channel ids) verbatim — they are shared tenant fixtures, not Flow vocabulary.
- post_run: `python3 _setup/cleanup_solutions.py` (mounted from `tests/tasks/uipath-maestro-bpmn/_setup/`) first, then the task's teardown, with Flow's timeouts or larger if the BPMN sweep has more to delete.
- Prompts keep Flow's wording about running ("Validate the flow" stays validate; if Flow's prompt told the agent to debug/run, keep that instruction with the `bpmn debug` verb). Live ports do NOT get the structural "Do NOT upload/debug/run" closing line — the grader itself runs the process, and the Flow prompt's own scope stands.

## Assertion map tags for live ports

Add these T rows as needed and cite the Flow helper you translate:
- `T flow_check.run_debug(inputs=…)` → ephemeral solution + `bpmn_live.run_debug(project, inputs, log)`
- `T assert_output_value / assert_outputs_contain / assert_named_equals` → value-leaf search over `variables-all` root scope + element `Outputs` (declared inputs excluded, as Flow excluded them)
- `T assert_node_type_executed / completed_node_ids_of_type` → the element's record in `variables-all` (or `debug_data.ElementExecutions[].Status == Completed`)
- `T assert_slack_message_posted / assert_connector_send_identity` → `connector_response_values` on the connector element's outputs, then the same tenant re-read Flow did
- `T assert_connector_error_handlers` → boundary error event / error path presence — only if Flow asserted it

If a Flow assertion has no readable runtime evidence on the BPMN side (e.g. a root-output-only value that the runtime returns as null and no element output carries it), STOP and report "parked: <evidence>" rather than loosening the assertion.
