# UiPath Test Manager — P&E Validation Scenarios

Behavioural eval scenarios for the **`uipath-test`** skill (the `uip tm` command surface), mapped to the Confluence *P&E Evaluation Scenarios* matrix. Each file is a [coder_eval](https://github.com/UiPath/coder_eval) task: a natural-language prompt plus `command_executed` success criteria.

> **Local-only.** These carry `skip: true` and run outside CI against a live tenant (`codereval` / `DefaultTenant`).

## Running
```bash
cd tests
SKILLS_REPO_PATH=$(cd .. && pwd) \
  .venv/bin/coder-eval run "tasks/uipath-test/local-sanity/**/*.yaml" \
  -j 6 --no-preserve
```

Execution/link-automation scenarios use the published [`fixtures/TestManagerSmoke/`](fixtures/TestManagerSmoke/README.md) automation (folder `Shared/uipath-test`, key `fcf79fe1-147b-4000-82b3-9eb81b165452`, serverless robot pre-assigned).

## Legend
- **Tier** — `Smoke` (`gating:must-pass`) · `Edge` (`gating:edge-case`)
- **Type** — `Read` · `Write` · `Error/boundary`
- **Surface area** — the `uip` command(s) the scenario's criteria assert. Every scenario also verifies `uip login status` first (the skill's connectivity check), so that's omitted from the column below.

## Project & configuration

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 1.1 | What projects can I get to in Test Manager? | Smoke | Read | `tm project list` |
| 1.2 | I'm trying to get a full picture of our HEALTH project in Test Manager. What's the de… | Smoke | Read | `tm project` (get) |
| 1.3 | Open up the project HEALTH-NOPE-999 in Test Manager and show me its details. | Edge | Error/boundary | `tm project` (get, invalid key) |

## Test cases — read

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 2.1 | Need the test cases in the HEALTH project in Test Manager. | Smoke | Read | `tm testcases list` |
| 2.2 | Pick a test case from the HEALTH project in Test Manager and talk me through what it … | Smoke | Read | `tm testcases` (get / list-steps) |
| 2.3 | Which test cases in the HEALTH project in Test Manager have the smoke label on them? | Smoke | Read | `tm testcases list` + `tm objectlabel` (label filter) |
| 2.4 | We've been reworking the login flow and I want to make sure the tests still cover it.… | Smoke | Read | `tm testcases list` |
| 2.5 | Can you check what test cases are sitting in the HEALTH-SANDBOX project in Test Manag… | Edge | Error/boundary | `tm testcases list` (invalid project) |

## Test cases — write

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 3.1 | Just finished the invoice-total calculation flow. I need a test case in Test Manager,… | Smoke | Write | `tm testcases create` |
| 3.2 | The 'PE - Validate invoice total calculation' case in our Test Manager HEALTH project… | Smoke | Write | `tm testcases update` |
| 3.3 | We changed the vendor lookup so it returns accountCode now, not vendorId. The test ca… | Smoke | Write | `tm testcases update` |
| 3.4 | The invoice-total test case in our Test Manager HEALTH project covers one of our requ… | Smoke | Read | `tm requirements testcases` |
| 3.5 | In Test Manager, we've published a test automation called 'TestManagerSmoke' to the S… | Smoke | Write | `tm testcases list-automations` + `link-automation` |
| 3.6 | Add a test case in Test Manager, in the HEALTH project, named 'PE - Validate invoice … | Edge | Error/boundary | `tm testcases create` (duplicate name) |
| 3.7 | End-to-end: discover TestManagerSmoke entry points, link PassCase to a HEALTH test ca… | Smoke | Write | `tm testcases list-automations` + `link-automation` + `tm testsets run` + `tm executions` |

## Requirements

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 4.1 | What requirements do we have in the HEALTH project in Test Manager right now? Just gi… | Smoke | Read | `tm requirements list` |
| 4.2 | In Test Manager, grab any requirement from the HEALTH project and tell me which test … | Smoke | Read | `tm requirements list-testcase-ids` |
| 4.3 | I want to find gaps in the HEALTH project in Test Manager. Are there any requirements… | Smoke | Read | `tm requirements list` (coverage gap) |
| 4.4 | In Test Manager, our HEALTH project requirements that originate from Jira carry an ex… | Smoke | Read | `tm requirements list` (external ref) |

## Test sets

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 5.1 | Need the test sets in the HEALTH project in Test Manager. | Smoke | Read | `tm testsets list` |
| 5.2 | I want a new 'PE Regression' test set in the HEALTH project in Test Manager. Put a co… | Smoke | Write | `tm testsets create` |
| 5.3 | In Test Manager, swap one of the cases on the 'PE Regression' set in the HEALTH proje… | Smoke | Read | `tm testcases add` / `remove` |
| 5.4 | In Test Manager, add case TC-DOESNOTEXIST-9999 to the 'PE Regression' set in the HEAL… | Edge | Error/boundary | `tm testcases add` (invalid case) |

## Test execution

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 6.1 | In Test Manager, kick off an automated run of one of the HEALTH project's test sets o… | Smoke | Read | `tm testsets run` (automated) |
| 6.2 | How's the 'Healthcare Compliance Suite - 20260513.2035' run in the HEALTH project in … | Smoke | Read | `tm executions` (get-stats / list) |
| 6.3 | Break down the 'Healthcare Compliance Suite - 20260513.2035' run in the HEALTH projec… | Smoke | Read | `tm executions testcaselogs` |
| 6.4 | A case failed in the 'Healthcare Compliance Suite - 20260513.2035' run in the HEALTH … | Smoke | Read | `tm executions testcaselogs` + `tm attachment download` |
| 6.5 | In Test Manager, start a manual run of one of the HEALTH project's test sets, then ma… | Smoke | Write | `tm testsets run` (manual) + `tm testcaselog finish` |
| 6.6 | In Test Manager, start a manual run of one of the HEALTH project's test sets, then go… | Smoke | Write | `tm testcaselog finish` (bulk) |
| 6.7 | In Test Manager, run 'PE Regression' in the HEALTH project on the staging robot. I ha… | Edge | Error/boundary | `tm testsets run` (wrong environment) |
| 6.8 | In Test Manager, run one of the HEALTH project's test sets on the serverless robot. T… | Edge | Error/boundary | `tm testsets run` (no available robot) |

## Defects (object-label based)

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 7.1 | In Test Manager, the PDF generation case in the HEALTH project is throwing a 500. Fla… | Smoke | Read | `tm objectlabel add` |
| 7.2 | In Test Manager, which test cases in the HEALTH project are currently flagged as open… | Smoke | Read | `tm objectlabel list` |
| 7.3 | That PDF generation case in the HEALTH project in Test Manager is failing again after… | Smoke | Write | `tm objectlabel add` + `tm attachment upload` |
| 7.4 | In Test Manager, I want to flag the PDF 500 case in the HEALTH project as a bug, but … | Smoke | Read | `tm objectlabel` (add / get) |
| 7.5 | Walk me through the bug history on the PDF generation case in the HEALTH project in T… | Smoke | Read | `tm objectlabel list` |

## Labels & tags

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 8.1 | One of the cases in the HEALTH project over in Test Manager keeps going green then re… | Smoke | Read | `tm objectlabel add` |
| 8.2 | In Test Manager I've got a handful of cases in the HEALTH project nobody's touched in… | Smoke | Read | `tm objectlabel add` (bulk) |
| 8.3 | Good news, that case in the HEALTH project is stable again. Drop the 'flaky' tag off … | Smoke | Read | `tm objectlabel remove` |

## Attachments

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 9.1 | In Test Manager, grab the latest execution in the HEALTH project, write a small error… | Smoke | Read | `tm attachment upload` (to execution) |
| 9.2 | In Test Manager, I've got a screenshot of the PDF export bug. Make a small placeholde… | Smoke | Read | `tm attachment upload` |
| 9.3 | In Test Manager, create a ~500MB file and try to attach it to the latest HEALTH proje… | Edge | Error/boundary | `tm attachment upload` (size limit) |

## Custom fields

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 10.1 | New on this team. In Test Manager, which custom fields does the HEALTH project have c… | Smoke | Read | `tm customfield list` |
| 10.2 | In Test Manager, pick a test case from the HEALTH project and tell me what its Sprint… | Smoke | Read | `tm customfield value` (list / get) |
| 10.3 | In Test Manager, which cases in the HEALTH project are tagged for Sprint-12? Need the… | Smoke | Read | `tm testcases list` (custom-field filter) |
| 10.4 | We just shipped 4.7.1. In Test Manager, update the Deployment Version field on that t… | Smoke | Write | `tm customfield value update` |
| 10.5 | Sprint-12 wrapped up. In Test Manager, roll all those cases in the HEALTH project for… | Smoke | Write | `tm customfield value update` (bulk) |
| 10.6 | Need to know which cases in the HEALTH project are pinned to the Staging environment.… | Smoke | Read | `tm customfield value` (filter) |
| 10.7 | In Test Manager, bump the Priority field to Urgent on a test case in the HEALTH proje… | Edge | Error/boundary | `tm customfield value update` (invalid value) |
| 10.8 | In Test Manager, check the Deployment Version on a case in the HEALTH project that ha… | Edge | Error/boundary | `tm customfield value` (no value set) |

## Traceability

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 11.1 | In Test Manager, pick a requirement from the HEALTH project and walk me through the f… | Smoke | Read | `tm requirements list-testcase-ids` |
| 11.2 | In Test Manager, I need a traceability matrix mapping requirements to test cases, but… | Smoke | Read | `tm requirements` + `tm testcases` (matrix) |
| 11.3 | We probably have some orphaned tests in the HEALTH project in Test Manager. Can you f… | Smoke | Read | `tm testcases list` + `tm requirements` (orphans) |

## Orchestrator integration

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 12.1 | Before I kick off a Test Manager run, what robots do we have available right now? I w… | Smoke | Read | `or machines list` |
| 12.2 | In Test Manager, kick off an automated run of a HEALTH project test set on the server… | Smoke | Read | `tm testsets run` (automated) + `or machines` |
| 12.3 | In Test Manager, start an automated run of a HEALTH project test set on the serverles… | Smoke | Read | `tm testsets run` (automated) + `or machines` |
| 12.4 | In Test Manager, run one of the HEALTH project's test sets on the serverless robot. I… | Edge | Error/boundary | `tm testsets run` (no robot) |

## Jira integration (via requirements)

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 13.1 | In Test Manager, flag the failing PDF case in the HEALTH project as a bug, and remind… | Smoke | Read | `tm objectlabel add` + `tm requirements list` |
| 13.2 | We closed the PDF issue in Jira this week. In Test Manager, have the Jira-linked requ… | Smoke | Read | `tm requirements list` (external ref) |
| 13.3 | In Test Manager, pull up the Jira-linked requirements in the HEALTH project that chan… | Edge | Error/boundary | `tm requirements list` (external ref) |

## Authentication & permissions

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 14.1 | Quick check before I jump into Test Manager: am I logged in, and as who? | Smoke | Read | `login status` + `tm user get` |
| 14.2 | Before I dig into Test Manager, can you make sure my session's still good? If it's ti… | Edge | Error/boundary | `login status` (session validity) |
| 14.3 | Add a new test case to the HEALTH project in Test Manager for me. I think I've only g… | Edge | Error/boundary | `tm testcases create` (insufficient permissions) |
| 14.4 | In Test Manager, pull up the test cases in the EXTERNAL-999 project. That project liv… | Edge | Error/boundary | `tm testcases list` (cross-tenant isolation) |

## CLI invocation & error handling

| # | Scenario | Tier | Type | Surface area |
|---|----------|------|------|--------------|
| 15.1 | I'm new to the Test Manager CLI. Run its built-in help and show me the list of comman… | Smoke | Read | `tm --help` |
| 15.2 | Run the regression suite in Test Manager. | Edge | Error/boundary | `tm testsets list` / `run` (ambiguous request) |
| 15.3 | We've got a pile of old test cases in the HEALTH project in Test Manager I want tagge… | Edge | Error/boundary | `tm objectlabel add` (bulk) |
| 15.4 | In Test Manager, go ahead and fire off an automated run of a HEALTH project test set … | Edge | Error/boundary | `tm testsets run` (automated) |
| 15.5 | I need the full list of test cases from the HEALTH project in Test Manager, not just … | Smoke | Read | `tm testcases list` (pagination) |

## Summary

- **69 scenarios** across 15 areas of the `uip tm` surface: project, test cases (read + write), requirements, test sets, execution, defects/labels, attachments, custom fields, traceability, Orchestrator integration, Jira-linked requirements, auth/permissions, and CLI/error handling.
- All execution + link-automation scenarios run against the published [`TestManagerSmoke`](fixtures/TestManagerSmoke/README.md) automation (Shared folder, serverless robot).
