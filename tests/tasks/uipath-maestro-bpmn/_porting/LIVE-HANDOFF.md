# Flow → BPMN eval porting: live tier

Methodology is in `PORTING-BRIEF.md`, `BATCH1-ADDENDUM.md`, `NORMALIZATION.md` and `LIVE-ADDENDUM.md` beside this file; per-task history and run ids in `parity-ledger.md`. Ports that never went green live on `test/bpmn-port-parked`, each `skip: true` with its evidence.

## Rules

1. Every grader assertion is tagged F (Flow translation), I (plumbing) or T (listed tolerance) in its module docstring.
2. Criteria keep Flow's type, order, weight and threshold. Sanctioned deviations: CLI verbs, grader implementation, live criterion timeouts sized to the BPMN CLI sequence, and `task_timeout` = turn_timeout + every criterion and pre_run timeout + 60.
3. Dispatch: `gh workflow run run-coder-eval.yml --ref <branch> -f task_globs='…'`, codex driver, alpha tenant. Read results with `gh run download <id>` → `**/task.json`; agent artifacts under `**/00/artifacts/` feed grader regression replays.
4. Fix only port defects; three graded iterations at most; a repeat runtime or skill failure parks the task with evidence. Never weaken a Flow assertion.

## Live-grader recipe

Canonical: `_shared/check_jira_get_issue.py`. From `_shared/bpmn_live.py`: `import_exact` (ephemeral `uip solution init` + `projects import`, sha256-pinned) → `run_debug(project, inputs, log, timeout)` in the grader itself, so `test_criterion_budgets.py` can price it → `debug_evidence` (`variables-all`, `incidents`) → `require_clean_run`. Read a declared output first; when it reads back null (root public outputs have), fall back to `output_leaves(variables, skip=input_echo_ids(process), elements=…)` over the nodes that produce it. An unskipped input reads as an output. A grader with side effects journals their ids before `require_clean_run`, so a faulted run still cleans up.

post_run `_setup/cleanup_solutions.py` sweeps the ephemeral solution; a later criterion in the same task passes `resolve_project(exclude_under=[LIVE_RUN_DIR])` so that import is not read as a second project.

Budget: the guard enforces criterion `timeout` ≥ `debug_budget(...)` + 60. Size it to cover the whole sequence: 90 (init) + 180 (import) + `debug_budget(...)` + 120 (variables-all) + 120 (incidents) + 60, e.g. 1050 for one default debug.

## Runtime and grader facts

- `uip maestro bpmn debug` polls at most 300 times; `run_debug` sizes `--poll-interval` to 80% of its budget and raises `CheckFailure` on timeout after writing the CLI output to its log file.
- Incident 102010 "Parameter 'Folder' null" on a Slack node = missing `folderKey` binding; 102009 = missing activity parameter; 400008 on a multi-instance marker = input collection over a connector response.
- Connector nodes come in two forms: curated `objectName` with path/query inputs, or generic entity-CRUD with the verb in `operation`/`method`. A request body is one JSON `target="body"` input; several do not merge at runtime, and `bpmn_check.body_object` raises `BodyShapeError` on them.
- Managed HTTP is `Intsvc.HttpExecution` or `Intsvc.UnifiedHttpRequest`; connector-mode HTTP is `Intsvc.ActivityExecution`. Wait-for-event may be a `receiveTask` or an `intermediateCatchEvent`; classify by the `uipath:type` wrapper, never the BPMN tag.
- `find_bpmn_file` treats byte-identical copies as one artifact and fails on any other ambiguity; `validate_bpmn.py` validates every `.bpmn` in the sandbox.
- Actions.HITL needs a deployed Action App to pass `bpmn validate`; the curated Data Fabric query template has no sort-field parameter.

## Skill findings to report upstream

Slack channel-id resolution and pagination (three tasks); Slack `folderKey` binding omitted; connector trigger parameters (Data Fabric entity, Outlook `parentFolderId`) omitted and `uip is triggers` discovery not taught; managed-HTTP response shape unclear to downstream scripts; Data Service where-clause grammar from variables; multi-instance over connector output; fixed literal values parametrised into unbound variables; no "existing solutions → ask" greenfield rule; WooCommerce connector node not produced.

## Not yet ported

billing_dispute_analyst / _resolution / _writer need a published agent to stand in for Flow's inline agents; single_node/file_attachment needs a file-typed process variable. Undecided: generate_schema (opaque `jsonSchema` output contract) and dtl_load_by_default ×2 (design-time metadata, not wire XML).
