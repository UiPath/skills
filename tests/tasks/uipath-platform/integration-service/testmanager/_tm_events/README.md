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
| `_setup/cleanup.py` | `post_run`, pass or fail. Uninstalls `deployment_name`, deletes every record in `result.json` `created`, then sweeps TestSet / TestCase / Requirement still named with the marker. Always exits 0. |
| `check_trigger_run.py` | Grader, reached via `$REFERENCE_DIR`. `--artifact <surface>` checks the trigger is the workflow entry point; `--validate <surface>` runs the offline validator; `--live` finds a Successful Orchestrator job of `process_name` started after `started_at` and asserts its output payload. |

`--live` does not trust the agent's report of the run. It confirms through the connector that `record_id` is this run's record, then locates the job itself and checks the payload's `objectType`, `id` (or `testExecutionId` for TestCaseLog), `projectId`, and key fields: `name` / `description` for named records, `testSetId` / terminal `status` / `executionFinished` for TestExecution, `result` for a finished TestCaseLog.

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

The graders match the operation case-insensitively by containment (`Created` matches `RECORD_CREATED`), so the tasks need no edit after either fix.

## Enabling a task

Every task ships `skip: true`. Remove it once the task passes on `is_e2e_testmanager`.
