# Test Manager connector event-trigger e2e

Shared tooling for the 33 `testmanager_trigger_<op>_<object>` tasks. Each task builds a workflow that starts on a `uipath-uipath-testmanager` trigger, deploys it, fires the event, and is graded on a live re-query of the run.

| Surface | Tasks |
|---|---|
| API Workflow | `tests/tasks/uipath-api-workflow/connector/testmanager_trigger_*` |
| RPA | `tests/tasks/uipath-rpa/connector/testmanager_trigger_*` |
| Maestro BPMN | `tests/tasks/uipath-maestro-bpmn/connector_features/testmanager_trigger_*` |

## Coverage

| Trigger | Object types |
|---|---|
| Record Created | Requirement, TestCase, TestSet, TestExecution |
| Record Updated | Requirement, TestCase, TestSet, TestExecution, TestCaseLog |
| Record Finished | TestExecution, TestCaseLog |

Source: `TestManagerEvents.json` event types and the `webhook.json` payload adapter in `cloud-elements/periodic-uipath-uipath-testmanager`, which maps the Test Manager `EventType` enum (`6` = TestCaseLogFinished, `10` = TestExecutionFinished).

Not covered, because Test Manager never emits the event: TestCaseLog Created, Defect Created. Adding them needs a Test Manager emit change plus a connector event-type change.

## Files

| File | Role |
|---|---|
| `_setup/seed.py` | `pre_run`. Writes `seed.json`: unique `marker`, `project_key`, trigger under test, unique `deployment_name` / `process_name`, `started_at`; `updated_description` for Updated tasks. For TestExecution / TestCaseLog tasks it clones `TM_EVAL_EXECUTION_TESTSET` into a marker-named copy (`uip tm testsets clone`), sets the copy's folder and robot when configured, and records `execution_test_set` (the copy's key) and `execution_test_set_id`. |
| `_setup/preflight_connections.py` | `pre_run`. Fails the task as ERROR when no `uipath-uipath-testmanager` connection answers a ping. Copied from `uipath-maestro-bpmn/_setup`, so these tasks mount no other surface's test folder. |
| `_setup/cleanup.py` | `post_run`, pass or fail, within the 300 s hook cap. Deletes only what it can prove this run created; see [Cleanup ownership](#cleanup-ownership). Always exits 0. |
| `check_trigger_run.py` | Grader, reached via `$REFERENCE_DIR`. `--artifact <surface>` checks the trigger is the workflow entry point; `--validate <surface>` runs the offline validator; `--live` polls up to 120 s for a Successful Orchestrator job of `process_name` that the trigger started, and asserts its output payload. |

`--live` does not trust the agent's report of the run:

1. It confirms through the connector that the record is this run's: named records carry the seeded marker; a TestExecution (or a TestCaseLog's execution) ran this run's own test set copy, `execution_test_set_id`, whose name carries the marker. Deployed workflows see every execution in the project, and concurrent runs each execute their own copy, so another run's execution cannot match.
2. It pages through the jobs itself (`uip or jobs list --offset`) and tries each one whose payload is about the record: `id` (plus `testExecutionId` for TestCaseLog). It passes on the first that holds, because Updated events fire several jobs per record.
3. That job must be Successful and must not have a manual `SourceType`. `Source` is not read: it says `Manual` even for Flow-started jobs. Each task also fails the agent for running `uip or jobs start|restart`.
4. The payload must match `objectType`, `projectId` and the key fields: `name` / `description` for named records; `testSetId` for TestExecution, with `status` past its initial value for Updated and terminal `status` / `executionFinished` for Finished; `testCaseId` for TestCaseLog, with `result` for Finished.

Object types and operations match as whole tokens, case-insensitively: `TestCase` does not match `TestCaseLog`, and `Updated` does not match `updatedAt`. The RPA check reads only the trigger activity's own attributes, not the output schema in its child elements.

## Cleanup ownership

`result.json` is written by the agent and `seed.json` sits in its sandbox, so cleanup trusts neither on its own:

1. Uninstall `deployment_name`.
2. Refuse record cleanup unless `marker` has seed.py's shape (`DataEval-<8 hex>`), so an edited marker cannot match other runs' records.
3. Delete this run's test set copy and every execution of it, but only after fetching the copy and confirming its name starts with the marker.
4. For each record in `result.json` `created`: delete a Requirement / TestCase / TestSet only if its fetched name starts with the marker, and a TestExecution only if it ran this run's copy. Anything else, including the shared fixture test set, is kept and logged.
5. Sweep TestSet / TestCase / Requirement still named with the marker, following the connector's next-page token when the list returns one (up to 20 pages). `is resources run list` has no paging flag, so without a token the sweep reads one page.

## Windows (RPA)

The RPA tasks carry the `windows` tag, so `run-coder-eval.yml` routes them to the Windows host that `uip rpa build` needs. Commands there may run under `cmd.exe`: the RPA tasks call `python` (not `python3`) and read `REFERENCE_DIR` inside Python, and every script resolves `uip` with `shutil.which` so the `uip.cmd` shim is found.

## Tenant prerequisites

| Variable | Purpose |
|---|---|
| `UIPATH_*` auth variables | Same as every live task (see `run-coder-eval.yml`), pointed at `is_e2e_testmanager` |
| `TM_EVAL_PROJECT_KEY` | Test Manager project prefix (default `HEALTH`, as `_tm_shared`) |
| `TM_EVAL_EXECUTION_TESTSET` | Key of a runnable automated test set (e.g. `HEALTH:12`). Required by TestExecution and TestCaseLog tasks; `seed.py` clones it per run and fails the task as ERROR when unset or when the clone fails. The connector cannot create an automation, so this fixture is the one hardcoded dependency. |
| `TM_EVAL_EXECUTION_FOLDER` | Optional. Orchestrator folder path for the per-run copy (`uip tm testsets set-folder`); a clone does not copy the folder, so without it the project's default folder is used. |
| `TM_EVAL_EXECUTION_ROBOT` | Optional. Robot account name for the per-run copy (`uip tm testsets set-robot`); a clone does not copy the robot. |

A `uipath-uipath-testmanager` connection must answer a ping; `_setup/preflight_connections.py` fails the task as ERROR otherwise.

## Known blocker — mixed-case trigger operations

`uip is triggers` and `registry get` uppercase the trigger operation. Test Manager's operations are mixed case (`Created`, `Updated`, `Finished`), so those calls return HTTP 404 / `IS enrichment error`, and the connector has no reachable trigger from the CLI (recorded in `skills/uipath-maestro-bpmn/references/registry-workflow.md` § connector triggers, CLI 1.204.0). Every other connector in that table uses uppercase operations (`CREATED_V3`, `EMAIL_RECEIVED`, `ISSUE_CREATED`).

Until one of these lands, expect every task here to fail at trigger discovery:

1. Connector: rename the `TestManagerEvents` operations to uppercase (e.g. `RECORD_CREATED`, `RECORD_UPDATED`, `RECORD_FINISHED`) in `TestManagerEvents.json` and the `webhook.json` adapter's `event.eventType` rewrite.
2. CLI: stop uppercasing the operation in `is triggers` / `registry get`.

The graders match the operation as a whole token, case-insensitively (`Created` matches `RECORD_CREATED`), so the tasks need no edit after either fix.

## Enabling a task

Every task ships `skip: true`. Remove it once the task passes on `is_e2e_testmanager`. Before unskipping, confirm on the tenant:

1. The `SourceType` an event-triggered job reports. If it is `Manual`, drop `manual` from `MANUAL_SOURCES` in `check_trigger_run.py`; the `or jobs start|restart` criterion still guards hand-started jobs.
2. That the per-run test set copy runs with `TM_EVAL_EXECUTION_FOLDER` / `TM_EVAL_EXECUTION_ROBOT` set.
