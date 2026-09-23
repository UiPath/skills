# Flow → BPMN eval porting: live-tier handoff

Branch `test/bpmn-port-live` (PR #3502) holds the live-tier and field-shape ports that pass CI. Branch `test/bpmn-port-parked`, stacked on it, holds the eight that do not, each `skip: true` with its evidence in the YAML. The structural bucket is PR #3426. Per-task history, run ids and iteration notes are in `parity-ledger.md`; methodology in `PORTING-BRIEF.md`, `BATCH1-ADDENDUM.md`, `NORMALIZATION.md` and `LIVE-ADDENDUM.md` beside this file.

## Where it stands (2026-09-23)

| Bucket | Ported | Green | Parked | Not started |
|---|---|---|---|---|
| Live (Flow grader runs `flow debug`) | 21 | 15 | 6 | 0 |
| Field-shape probes (Integration Service parameters) | 9 | 7 | 2 | 0 |
| Fixture-dependent probes | 0 | 0 | 0 | 4 |

Parked, with the gap each hits (details in the ledger): bellevue_weather and bellevue_weather_simulated (managed-HTTP response shape), jira_search_triage (multi-instance over a connector response, 400008), jira_lifecycle (three different runtime failures; Flow flaky too), billing_discrepancy_detector (Data Service where clause from a process variable), slack_channel_description_simulated (Slack channel pagination), ceql_where (Flow filter tree has no BPMN carrier), enhanced_enum (no WooCommerce connector node).

Not started: billing_dispute_analyst / _resolution / _writer need a published agent to stand in for Flow's inline agents; single_node/file_attachment needs a file-typed process variable. Also undecided: generate_schema (opaque `jsonSchema` output contract) and dtl_load_by_default ×2 (design-time metadata, not wire XML).

## Methodology

1. One Sonnet subagent per task with the brief and addenda; ports are born normalized (every grader assertion tagged F, I or T in the module docstring; nothing else is written).
2. Review is a mechanical cross-check (criteria type/order/weight/threshold/timeout, run_limits, tags, prompt literals, pre_run/post_run, relative paths) plus reading the assertion map. Sanctioned deviations: CLI verbs, grader implementation, live criterion timeouts sized to the BPMN CLI sequence, `task_timeout` = turn_timeout + grading + 60.
3. One CI dispatch per batch: `gh workflow run run-coder-eval.yml --ref <branch> -f task_globs='…'`, codex driver, alpha tenant. Read results with `gh run download <id>` → `**/task.json`; agent artifacts under `**/00/artifacts/` feed grader regression replays.
4. Fix only port defects; three graded iterations at most; a repeat runtime or skill failure parks the task with evidence. Never weaken a Flow assertion.

## Live-grader recipe

Canonical: `_shared/check_jira_get_issue.py`, via `_shared/bpmn_live.py`: `uip solution init` under the sandbox CWD → `uip solution projects import` (assert the imported `.bpmn` sha256 equals the submitted one) → `run_debug(project, inputs, log, timeout)` → `debug-instance variables-all` → `debug-instance incidents`. Grade from root-scope globals plus every element's `Outputs` (root public outputs have read back null). post_run `_setup/cleanup_solutions.py` sweeps the ephemeral solution; a later criterion in the same task must pass `resolve_project(exclude_under=[LIVE_RUN_DIR])` so that import is not read as a second project.

Budget: `_shared/test_criterion_budgets.py` prices every `run_debug` call; one debug run needs criterion `timeout` ≥ 90 + 180 + 480 + 120 + 120 + 60 = 1050.

## Runtime and grader facts

- `uip maestro bpmn debug` polls at most 300 times; `run_debug` sizes `--poll-interval` to 80% of its budget and surfaces the CLI's own timeout envelope.
- Incident 102010 "Parameter 'Folder' null" on a Slack node = missing `folderKey` binding; 102009 = missing activity parameter; 400008 on a multi-instance marker = input collection over a connector response.
- Connector nodes come in two forms (curated `objectName` with path/query inputs, or generic entity-CRUD with the verb in `operation`/`method`); request bodies in two forms (one JSON `target="body"` blob, or one typed input per field). Graders use `bpmn_check.body_object`, `context_value`, `context_inputs` and accept both.
- Managed HTTP is `Intsvc.HttpExecution` or `Intsvc.UnifiedHttpRequest`; connector-mode HTTP is `Intsvc.ActivityExecution`. Wait-for-event may be a `receiveTask` or an `intermediateCatchEvent`; classify by the `uipath:type` wrapper, never the BPMN tag.
- `find_bpmn_file` treats byte-identical copies as one artifact and drops drafts with no registry-typed node; `validate_bpmn.py` validates every `.bpmn` in the sandbox.
- Actions.HITL needs a deployed Action App to pass `bpmn validate`; the curated Data Fabric query template has no sort-field parameter.

## Skill findings to report upstream

Slack channel-id resolution and pagination (three tasks); Slack `folderKey` binding omitted; connector trigger parameters (Data Fabric entity, Outlook `parentFolderId`) omitted and `uip is triggers` discovery not taught; managed-HTTP response shape unclear to downstream scripts; Data Service where-clause grammar from variables; multi-instance over connector output; fixed literal values parametrised into unbound variables; no "existing solutions → ask" greenfield rule; WooCommerce connector node not produced.

## Resuming

1. Rebase `test/bpmn-port-parked` onto main after #3502 merges; unskip a task when its gap closes and re-dispatch it.
2. For the four fixture-dependent probes, build the tenant fixture first (published agent, file-typed variable), then port with the same brief.
3. New ports: spawn "read PORTING-BRIEF, BATCH1-ADDENDUM, LIVE-ADDENDUM; port <task>; gates; report with assertion map", cross-check, dispatch as one batch, iterate per rule 4.
