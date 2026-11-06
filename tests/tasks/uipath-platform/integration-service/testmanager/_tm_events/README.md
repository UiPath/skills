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
| `_setup/seed.py` | `pre_run`. Writes `seed.json`: unique `marker`, `project_key`, trigger under test, unique `deployment_name` / `process_name`, `started_at`; `updated_description` for Updated tasks; `execution_test_set` for TestExecution / TestCaseLog tasks. |
| `_setup/cleanup.py` | `post_run`, pass or fail, within the 300 s hook cap. Uninstalls `deployment_name`, deletes every record in `result.json` `created`, then sweeps TestSet / TestCase / Requirement still named with the marker. Always exits 0. The marker sweep reads only the first page of each list, and TestExecutions are not swept by marker, so a run that crashed before writing `result.json` can leave executions behind. |
| `check_trigger_run.py` | Grader, reached via `$REFERENCE_DIR`. `--artifact <surface>` checks the trigger is the workflow entry point; `--validate <surface>` runs the offline validator; `--live` polls up to 120 s for a Successful Orchestrator job of `process_name` started after `started_at` that the trigger started, and asserts its output payload. |

`--live` does not trust the agent's report of the run:

1. It confirms through the connector that the record is this run's: named records carry the seeded marker; a TestExecution (or a TestCaseLog's execution) ran `execution_test_set` and started after `started_at`. Deployed workflows see every execution in the project, so this stops a concurrent run's execution from counting.
2. It locates the jobs itself and tries each one whose payload is about the record: `id` (plus `testExecutionId` for TestCaseLog). It passes on the first that holds, because Updated events fire several jobs per record.
3. That job must be Successful and must not have a manual `Source` / `SourceType`. Each task also fails the agent for running `uip or jobs start|restart`.
4. The payload must match `objectType`, `projectId` and the key fields: `name` / `description` for named records; `testSetId` for TestExecution, with `status` past its initial value for Updated and terminal `status` / `executionFinished` for Finished; `testCaseId` for TestCaseLog, with `result` for Finished.

Object types and operations match as whole tokens, case-insensitively: `TestCase` does not match `TestCaseLog`, and `Updated` does not match `updatedAt`. The RPA check reads only the trigger activity's own attributes, not the output schema in its child elements.

## Tenant prerequisites

| Variable | Purpose |
|---|---|
| `UIPATH_*` auth variables | Same as every live task (see `run-coder-eval.yml`), pointed at `is_e2e_testmanager` |
| `TM_EVAL_PROJECT_KEY` | Test Manager project prefix (default `HEALTH`, as `_tm_shared`) |
| `TM_EVAL_EXECUTION_TESTSET` | Runnable automated test set (key or id) with a robot. Required by TestExecution and TestCaseLog tasks; `seed.py` fails the task as ERROR when unset. The connector cannot create an automation, so this fixture is the one hardcoded dependency. |

A `uipath-uipath-testmanager` connection must answer a ping; `preflight_connections.py` (from `uipath-maestro-bpmn/_setup`) fails the task as ERROR otherwise.

## Known blocker — mixed-case trigger operations

`uip is triggers` and `registry get` uppercase the trigger operation. Test Manager's operations are mixed case (`Created`, `Updated`, `Finished`), so those calls return HTTP 404 / `IS enrichment error`, and the connector has no reachable trigger from the CLI (recorded in `skills/uipath-maestro-bpmn/references/registry-workflow.md` § connector triggers, CLI 1.204.0). Every other connector in that table uses uppercase operations (`CREATED_V3`, `EMAIL_RECEIVED`, `ISSUE_CREATED`).

Until one of these lands, expect every task here to fail at trigger discovery:

1. Connector: rename the `TestManagerEvents` operations to uppercase (e.g. `RECORD_CREATED`, `RECORD_UPDATED`, `RECORD_FINISHED`) in `TestManagerEvents.json` and the `webhook.json` adapter's `event.eventType` rewrite.
2. CLI: stop uppercasing the operation in `is triggers` / `registry get`.

The graders match the operation as a whole token, case-insensitively (`Created` matches `RECORD_CREATED`), so the tasks need no edit after either fix.

## Enabling a task

Every task ships `skip: true`. Remove it once the task passes on `is_e2e_testmanager`.
