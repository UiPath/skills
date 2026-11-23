# Test Manager eval fixtures — the `EVFX-` contract

Every coder_eval task under `tests/tasks/uipath-test/` that depends on Test
Manager *state* (an execution with failures, an intermittent history, a
populated test set) owns that state outright. No two tasks share a mutable
fixture.

## Naming

```
EVFX-<TASK>-<ROLE>
```

`EVFX-` appears nowhere in human-created tenant data — unlike `Eval ` (already
used by requirements and custom fields), `UAT `, or `Disbursement `. A task
looks its fixtures up with `--filter EVFX-<TASK>-`, which is a **prefix** match
and therefore exact for this scheme.

| Task | Project | Owns | Seeded state |
|------|---------|------|--------------|
| `execution_rerun_failed_integration` | CLAIM | `EVFX-RERUN-SET`, `EVFX-RERUN-TC{1,2,3}` | 1 Finished execution, results `Passed, Passed, Failed` |
| `flaky_tests_analysis` | CLAIM | `EVFX-FLAKY-SET`, `EVFX-FLAKY-TC{1,2,3}` | 3 Finished executions; TC2 fails in one |
| `test_report_junit_export` | CLAIM | `EVFX-JUNIT-SET`, `EVFX-JUNIT-TC{1,2,3}` | 1 Finished execution, results `Passed, Failed, Passed` |
| `release_signoff_wait_report_e2e` | CLAIM | `EVFX-SIGNOFF-SET`, `EVFX-SIGNOFF-TC{1,2}` | No execution; both cases automation-linked |
| `organize_testcases_into_testsets` | CLAIM | the `EVFX-ORG-*` namespace: `EVFX-ORG-SRC-TC{1,2,3}` (inputs) + `EVFX-ORG-SET-*` (outputs) | 3 source test cases, no execution; the task creates `EVFX-ORG-SET-<YYYYMMDD-HHMMSS>-*` and `pre_run` seeds the sources create-if-absent and clears earlier days' sets |
| `integration_release_readiness_qa_lead` | BANK | the existing regression suite (no `EVFX-` names) | 1 Finished execution mixing `Passed`/`Failed`/`Restricted`/`None` |
| `project_scaffold_build` | its own throwaway project | the `EVFX-SCAFFOLD-*` namespace | Nothing seeded, nothing persists — see [Self-contained build tasks](#self-contained-build-tasks) |
| `testset_curation_by_label_build` | its own throwaway project | the `EVFX-CURATE-*` namespace | Nothing seeded, nothing persists — see [Self-contained build tasks](#self-contained-build-tasks) |
| `failed_run_triage_diagnose` | CLAIM | `EVFX-TRIAGE-SET`, `EVFX-TRIAGE-TC{1,2,3}` | 1 Finished execution, results `Passed, Failed, Passed` — a STABLE failure, not intermittency (that shape belongs to `flaky_tests_analysis`) |
| `executions_list_smoke` | CLAIM | `EVFX-EXLIST-SET`, `EVFX-EXLIST-TC{1,2}` | At least one Finished execution; a pure reader, so `pre_run` seeds one recorded run only when none finished exists and leaves a healthy fixture untouched |
| `manual_execution_record_integration` | CLAIM | `EVFX-MANUAL-SET`, `EVFX-MANUAL-TC{1,2,3}` | Set and cases only, no execution — the task opens one; `pre_run` sweeps earlier days' runs (sparing today's, so a concurrent run is never destroyed) and snapshots the survivors so the oracle grades the run the agent opens |
| `reporting_date_backdate_integration` | CLAIM | `EVFX-REPORT-SET`, `EVFX-REPORT-TC{1,2}` | One **open** execution (recorded per-run by id, executions cannot be named) — the premise is that it is not closed; `pre_run` sweeps earlier days' runs (sparing today's) and opens one fresh OPEN run, recording its ExecutionId for the oracle |
| `customfield_schema_multiscope_build` | its own throwaway project | the `EVFX-SCHEMA-*` namespace | Nothing seeded, nothing persists — see [Self-contained build tasks](#self-contained-build-tasks) |
| `schedule_lifecycle_e2e` | CLAIM | `EVFX-SCHEDLC-SET`, `EVFX-SCHEDLC-TC1`, and the `EVFX-SCHEDLC-*` **schedule** namespace | Set and one case only — **no schedules seeded**. The agent creates ONE per-run stamped schedule `EVFX-SCHEDLC-<STAMP>` and walks its whole life (create weekly Mon+Thu → next-runs → update to 03:00 → disable → enable → delete); `pre_run` sweeps only earlier-day `EVFX-SCHEDLC-` rows and writes the fixture set id to `.schedlc_setid` for the stored-state graders |
| `testcaselog_override_integration` | CLAIM | `EVFX-TCLOG-TC{1,2,3}` | per-run STAMPED manual execution `EVFX-TCLOG-<STAMP>-RUN` (via `testcases run`), results `Passed, Failed, Passed`, **nothing overridden**; the task writes an override onto the failed log, so `pre_run` stamps a fresh execution and sweeps only earlier-day ones |
| `testcaselog_read_smoke` | CLAIM | `EVFX-TCLOGRD-TC1` | 1 finished manual log, result `Passed`, create-if-absent and never deleted (read-only task) |
| `testcaselog_manual_record_e2e` | CLAIM | `EVFX-TCLOGMR-TC1` | just the test case; the agent opens its own per-run STAMPED manual execution `EVFX-TCLOGMR-<STAMP>-RUN` and records a manual result; `pre_run` sweeps only earlier-day executions |
| `customfield_definition_crud_smoke` | its own throwaway project | the `EVFX-CFIELD-*` namespace | `pre_run` creates one `EVFX-CFIELD-<YYYYMMDD-HHMMSS>-<hex>` project per run (key in `project-key.txt`) and sweeps orphans stamped more than 6 hours ago; `post_run` deletes it. The agent creates/renames/deletes an "Eval Reviewer" field inside it, so per-run isolation keeps concurrent gate runs from colliding on the field name |
| `project_permissions_preflight_smoke` | `EVFX-PERMPRE-PROJECT` | the `EVFX-PERMPRE-*` namespace | `pre_run` create-if-absent of the project; no test cases/sets/executions — the task only reads `project-permissions get` |
| `project_permissions_access_integration` | `EVFX-PERMAT-PROJECT` | the `EVFX-PERMAT-*` namespace | `pre_run` create-if-absent of the project; no test cases/sets/executions — the task only reads `project-permissions get` |
| `defect_lifecycle_smoke` | its own per-run project | the `EVFX-DEFECT-*` namespace | `pre_run` creates one `EVFX-DEFECT-<YYYYMMDD-HHMMSS>-<hex>` project per run (key in `project-key.txt`) holding `EVFX-DEFECT-SET`/`EVFX-DEFECT-TC1` and one Finished execution with TC1 `Failed` and no defect; it sweeps orphans stamped more than 6 hours ago, and `post_run` deletes the project. Per-run because a result holds one defect and several models run the nightly concurrently |
| `defect_traceability_integration` | its own per-run project | the `EVFX-DEFTRACE-*` namespace | Same per-run project pattern (`EVFX-DEFTRACE-<YYYYMMDD-HHMMSS>-<hex>`, key in `project-key.txt`): `EVFX-DEFTRACE-SET`/`TC1`/`REQ` with the requirement covering TC1, one Finished execution with TC1 `Failed`, and a defect on that result linked by hand to tracker issue `EVFX-DEFTRACE-1`; `post_run` deletes the project |
| `defect_full_lifecycle_e2e` | its own throwaway project | the `EVFX-DEFFLOW-*` namespace | Nothing seeded, nothing persists — see [Self-contained build tasks](#self-contained-build-tasks). Does not grade `defects attachments download`: a manual result gives the defect no evidence (a file uploaded to the result with `attachment upload --object-type testCaseLog` does not appear under `defects attachments list`), so there is nothing to download |
| `project_settings_smoke` | its own throwaway project | the `EVFX-PSET-*` namespace | `pre_run` creates one `EVFX-PSET-<YYYYMMDD-HHMMSS>-<hex>` project per run (key in `project-key.txt`) and sweeps orphans stamped more than 6 hours ago (so a concurrent run's project is never touched); `post_run` deletes it. The deliverable is a settings change, not the project, so the project is scratch (Rule 2). Unlike the self-contained build tasks, project create/delete is not under test here, so the hooks own the project's lifecycle and the agent never deletes it |
| `run_package_ci_smoke` | its own throwaway project | the `EVFX-RUNPKG-*` namespace | Same hooks as `project_settings_smoke`: `pre_run` creates one `EVFX-RUNPKG-<YYYYMMDD-HHMMSS>-<hex>` project per run (key in `project-key.txt`) and sweeps orphans older than 6 hours; `post_run` deletes it, which also removes the execution and hidden test set `tm run --type package` creates. Runs the package `TestCase_CrossPlatform_VB_Tests`, uploading it when the folder feed lacks it; exits TENANT NOT READY on a tenant that cannot run it (see [Run-package fixtures](#run-package-fixtures)) |
| `run_package_failing_smoke` | its own throwaway project | the `EVFX-RUNPKGFAIL-*` namespace | Same hooks as `run_package_ci_smoke`, in its own namespace so the two never sweep each other's projects. Runs the package `FailingTestCase_CrossPlatform_VB_Tests` |
| `project_default_testcases_smoke` | the tenant's default project | the `EVFX-DPTC-*` namespace | `pre_run` writes a per-run `EVFX-DPTC-<YYYYMMDD-HHMMSS>-<hex>` feature id to feature.md and `.run-tag`, records the visible default, and sweeps `EVFX-DPTC-*` test cases in it stamped more than 6 hours ago; `post_run` deletes the run's test cases. See [Default-project tasks](#default-project-tasks) |
| `project_default_discover_smoke` | the tenant's default project | no EVFX- name | Read-only: records the visible default before the run and fails if it changed. See [Default-project tasks](#default-project-tasks) |
| `testcase_parameters_bulk_add_smoke` | its own throwaway project | the `EVFX-PARAM-*` namespace | `pre_run` creates one `EVFX-PARAM-<YYYYMMDD-HHMMSS>-<hex>` project per run (key in `project-key.txt`) holding `EVFX-PARAM-Login` (no parameters) and `EVFX-PARAM-Transfer` (`Username=keepme`), sweeps orphans older than 6 hours, and `post_run` deletes it. Per-run because the agent mutates the cases and concurrent gate runs would corrupt a shared one |
| `testcase_parameters_edit_integration` | HEALTH | `EVFX-PARAMEDIT-Login` | Created if absent; `pre_run` resets its parameters to `Username=admin` (with hint) and `Userid=u1` |
| `testcase_parameters_lifecycle_e2e` | HEALTH | `EVFX-PARAMLIFE-Login` | Created if absent; `pre_run` clears its parameters |
| `testcase_parameters_ask_first_integration` | HEALTH | `EVFX-PARAMASK-Login` | Created if absent; `pre_run` resets its parameters to `Username=admin` (with hint) |
| `requirement_ai_generate_smoke` | its own throwaway project | the `EVFX-AIGEN-*` namespace | `pre_run` creates one `EVFX-AIGEN-<YYYYMMDD-HHMMSS>-<hex>` project per run (key in `project-key.txt`), seeds `EVFX-AIGEN-REQ`, pre-warms one generate job (saving the timed-out envelope to `nightly/`) and excludes the run as tenant-not-ready if the AI backend cannot finish it; `post_run` deletes the project. Per-run so concurrent runs never share the requirement or its AI-created cases |
| `requirement_ai_evaluate_smoke` | its own throwaway project | the `EVFX-AIEVAL-*` namespace | `pre_run` creates one `EVFX-AIEVAL-<YYYYMMDD-HHMMSS>-<hex>` project per run (key in `project-key.txt`) and seeds `EVFX-AIEVAL-REQ` with `Users can reset their password.`; `post_run` deletes the project |
| `requirement_ai_obsolete_smoke` | its own throwaway project | the `EVFX-AIDEL-*` namespace | `pre_run` creates one `EVFX-AIDEL-<YYYYMMDD-HHMMSS>-<hex>` project per run (key in `project-key.txt`) and seeds `EVFX-AIDEL-REQ` + `EVFX-AIDEL-TC{1,2,3,4}` (TC3/TC4 off-topic), all linked; `post_run` deletes the project. Per-run so a concurrent run never recreates the case this run deletes |
| `requirement_ai_blocked_inputs_smoke` | its own throwaway project | the `EVFX-AIBLOCK-*` namespace | `pre_run` creates one `EVFX-AIBLOCK-<YYYYMMDD-HHMMSS>-<hex>` project per run (key in `project-key.txt`) and seeds `EVFX-AIBLOCK-NODESC` with no description/attachments; `post_run` deletes the project. `generate-testcases` fails HTTP 400 before a job starts, so no AI units |
| `attachment_upload_smoke` | its own throwaway project | the `EVFX-ATTUP-*` namespace | `pre_run` creates one `EVFX-ATTUP-<YYYYMMDD-HHMMSS>-<hex>` project per run (key in `project-key.txt`) holding `EVFX-ATTUP-Checkout` with no attachments, writes the local `checkout-failure.png`, sweeps orphans older than 6 hours; `post_run` deletes the project. Per-run because the agent mutates attachments and a shared case would break the exactly-one check |
| `attachment_download_integration` | HEALTH | `EVFX-ATTDL-Login` | Created if absent; `pre_run` uploads `login-error.log` and `checkout-notes.txt` (local copies removed); `post_run` clears its attachments |
| `attachment_overwrite_ask_integration` | HEALTH | `EVFX-ATTASK-Login` | Created if absent; `pre_run` uploads `report.txt` and writes a different local `report.txt`; `post_run` clears its attachments |
| `attachment_lifecycle_e2e` | HEALTH | `EVFX-ATTLIFE-Checkout` | Created if absent; `pre_run` clears its attachments and writes a local `release-notes.txt`; `post_run` clears its attachments |
| `testset_clone_smoke` | HEALTH | `EVFX-TSCLONE-Regression`, `EVFX-TSCLONE-TC{1,2}` | Seeded once, never changed. Each run's copy is `EVFX-TSCLONE-<YYYYMMDD-HHMMSS>-<hex>` (agent-named); `pre_run`/`post_run` sweep copies older than 6 hours |
| `testset_order_integration` | its own project `EVTSORD` | `EVFX-TSORDER-Regression` = `EVTSORD:4` holding Alpha/Beta/Gamma = `EVTSORD:1-3` | Project seeded once so the keys the order criterion names never change; `pre_run` fails if the shape drifts and resets the source's enforce flag. Per-run copies `EVFX-TSORDER-<stamp>-<hex>`, swept after 6 hours |
| `testset_settings_ask_integration` | HEALTH | `EVFX-TSASK-Regression`, `EVFX-TSASK-TC1` | Seeded once; read-only for the agent (`pre_run` resets the enforce flag if a past run changed it) |
| `testset_lifecycle_e2e` | its own project `EVTSLIFE` | `EVFX-TSLIFE-Regression` = `EVTSLIFE:4` holding Alpha/Beta/Gamma = `EVTSLIFE:1-3` | Same as `EVTSORD`; the agent deletes its own copy, the 6-hour sweep catches any it leaves |
| `testcase_clone_smoke` | HEALTH | `EVFX-TCCLONE-Login` (label `EVFX-TCCLONE`, two steps) | Seeded once, never changed. Each run's copy is `EVFX-TCCLONE-<uuid8> Login copy` from its `seed.json`; `post_run` deletes it, `pre_run` sweeps copies older than 6 hours |
| `testcase_bulk_create_integration` | HEALTH | none shared; `EVFX-TCBULK-<uuid8> <title>` per run | `pre_run` writes `cases.json` and creates the first case; `post_run` deletes the run's cases, `pre_run` sweeps ones older than 6 hours |
| `testcase_lookup_integration` | HEALTH | `EVFX-TCLOOK-TC{1,2}` (label `EVFX-TCLOOK-Checkout`), `EVFX-TCLOOK-TC3` (label `EVFX-TCLOOK-Other`), `EVFX-TCLOOK-Set{A,B,C}` holding TC1, TC2, TC3 | Seeded once, read-only. `pre_run` deletes duplicates a concurrent first seed leaves (lowest key wins) and fails if the shape drifted |
| `testcase_inventory_lookup_smoke` | its own throwaway project | the `EVFX-TCINV-*` namespace | `pre_run` creates one `EVFX-TCINV-<YYYYMMDD-HHMMSS>-<hex>` project per run (key `EVTI<4 hex>` in `project-key.txt`) holding `EVFX-TCINV-Login` (a precondition, `Username=alice`, one uploaded attachment whose id is in `attachment-id.txt`, local copy removed) covered by `EVFX-TCINV-REQ-Login`, beside an uncovering `EVFX-TCINV-REQ-Other`; sweeps orphans older than 6 hours; `post_run` deletes the project. The agent only reads |
| `testcase_lifecycle_e2e` | HEALTH | none shared; `EVFX-TCLIFE-<uuid8> Login`/`Logout`/`Login copy` per run | The agent deletes its copy; `post_run` deletes the rest, `pre_run` sweeps ones older than 6 hours |
| `testcases_export_smoke` | HEALTH | `EVFX-FXEXP-Login` | Seeded once, read-only. The file goes to the run's own `exports/` |
| `export_job_download_integration` | HEALTH | `EVFX-FXJOB-Checkout` | Seeded once, read-only. `pre_run` starts a no-wait export and writes its job id to the run's `seed.json` |
| `export_overwrite_ask_integration` | HEALTH | `EVFX-FXASK-Login` | Seeded once, read-only. `pre_run` writes the user's `exports/report.xlsx` in the run's folder |
| `testcases_export_by_label_e2e` | HEALTH | `EVFX-FXLAB-TC{1,2}` (label `EVFX-FXLAB-Payments`), `EVFX-FXLAB-TC3` (label `EVFX-FXLAB-Other`) | Seeded once, read-only; `pre_run` deletes duplicates a concurrent first seed leaves and fails if the labels drifted |
| `report_export_integration` | HEALTH | `EVFX-FXRPT-Login`, `EVFX-FXRPT-Checkout`, `EVFX-FXRPT-Set` holding both, with exactly one finished manual run (one Passed, one Failed) | Seeded once. `pre_run` keeps the oldest finished run and deletes any other run of the set; `post_run` deletes runs the agent started |
| `project_export_smoke` | its own project `EVMXEXP` (`EVFX-MXEXP-Project`) | test cases `MX Alpha`, `MX Beta` | Seeded once, never changed; `pre_run` removes duplicates a concurrent first seed leaves and fails if the shape drifted. The package goes to the run's own `backup/` |
| `project_import_ask_integration` | its own project `EVMXASK` (`EVFX-MXASK-Project`) | test cases `MX Alpha`, `MX Beta` | Same as `EVMXEXP`; `package.tmh` comes from its latest completed export (one export if none) |
| `project_migration_e2e` | source `EVMXLIF` (`EVFX-MXLIFE-Project`); a new project per run, key `EVMX<4 hex>`, name `EVFX-MXLIFE-<uuid8>` from the run's `seed.json` | test cases `MX Alpha`, `MX Beta` in the source | `post_run` deletes the run's project; `pre_run` sweeps `EVFX-MXLIFE-<uuid8>` projects older than 6 hours |
| `perf_scenario_cleanup_smoke` | CLAIM | the `EVFX-PERF-*` namespace | `pre_run` creates two per-run scenarios, `EVFX-PERF-<YYYYMMDD-HHMMSS>-<hex>-OLD` (the agent deletes it; name in `old-scenario.txt`) and `-KEEP` (must survive; name in `keep-scenario.txt`), and sweeps `EVFX-PERF-` scenarios stamped more than 6 hours ago; `post_run` deletes whatever this run left |
| `perf_scenario_setup_integration` | its own project per run (`EVFX-PERFSET-*`, key `EVPL<4 hex>`) | `EVFX-PERFSET-TC1` + a per-run scenario | `pre_run` runs `_setup/run_package_fixture.py seed` (see [Run-package fixtures](#run-package-fixtures)), then creates `EVFX-PERFSET-TC1` in the project, links it to `TestCase_CrossPlatform_VB_Tests` in `uipath-test-folder-feed` and writes the scenario name to `scenario-name.txt`; `post_run` deletes the project |
| `perf_scenario_dryrun_e2e` | its own project per run (`EVFX-PERFDRY-*`, key `EVPD<4 hex>`) | `EVFX-PERFDRY-TC1` + a per-run scenario | As `perf_scenario_setup_integration`; the agent also dry-runs the scenario on the folder's serverless robot, and `post_run` stops a dry run still in flight before deleting the project. **Skipped** until a cross-platform package built with `UiPath.Testing.Activities` >= 25.10.0 exists: perf dry runs refuse older ones |
| `prompts_create_smoke` | its own throwaway project | the `EVFX-PROMPT-*` namespace | `pre_run` creates one `EVFX-PROMPT-<YYYYMMDD-HHMMSS>-<hex>` project per run (key in `project-key.txt`) and sweeps orphans older than 6 hours; `post_run` deletes it. Per-run because the CLI has no prompt delete: only a project delete removes the prompt the agent creates |
| `prompts_library_setup_integration` | its own throwaway project | the `EVFX-PROMPTSET-*` namespace | Same hooks as `prompts_create_smoke` (`EVFX-PROMPTSET-<YYYYMMDD-HHMMSS>-<hex>`, key in `project-key.txt`); `pre_run` also seeds the user-defined prompt `Checkout edge cases` (GenerateTestsFromRequirement) and writes `release-audit.md` |
| `perf_scenario_history_integration` | its own project per run (`EVFX-PERFHIST-*`, key `EVPH<4 hex>`) | `EVFX-PERFHIST-TC1` + a per-run scenario | As `perf_scenario_setup_integration`, but `pre_run` also creates the scenario (name in `scenario-name.txt`) with one load group for `EVFX-PERFHIST-TC1`. The legacy `link-automation` link leaves no `AutomationId`, so `list-dry-run-reports` cannot resolve the scenario. Nothing is executed and no licence units are spent; the agent only reads. `post_run` deletes the project |

The `requirement_ai_*` tasks share one helper, [`../_setup/req_ai_fixture.py`](../_setup/req_ai_fixture.py)
(`seed`, `check`). It knows no names: each task passes its own `EVFX-` names
on the command line, so they stay in the task YAML where `check-collisions.py`
sees them.
`seed --require-access <verb>` first calls that AI verb on a requirement id
that does not exist: an allowed login gets HTTP 404 before any job starts, a
refused one gets 403, and `seed` then exits `TENANT NOT READY`. The PR smoke
gate (smoke-skills.yml) drops such a task from its pass rate; the nightly has
no such filter and records it as ERROR (tagged infra on the evalboard) until
the tenant is fixed. `find-obsolete-testcases` is the refused one on the eval
tenant: on Cloud, Test Manager's `findObsoleteTests` requires a Test Cloud
licence on the user or `A4TMasterFFEnabled` on the org, while
`generate-testcases` and `evaluate` check that only on Automation Suite and
dedicated clouds. `coder-eval-bot` on org `codereval` (alpha) has neither, so
`requirement_ai_obsolete_smoke` errors in the nightly until one of them is
granted (as of 2026-10-16). The fix is on the tenant, not in this repo.

`release_readiness` deliberately owns no `EVFX-` name: the task grades the
agent's ability to FIND the regression suite, so renaming it would delete the
thing under test. BANK is referenced by no other task, so it is already
collision-free.

Tasks NOT listed here are pure readers of stable, non-mutated data and own
nothing.

Keep this table in step with the hooks. `check-collisions.py` verifies that no
two tasks share an `EVFX-` name, but it does NOT validate this table — a stale
row here misleads the next maintainer into reusing or removing live state.

## Rules

1. **Never touch another task's state.** A fixture is permanent to everyone
   except its owner: no other task may delete it, rewrite its executions, or
   reuse its name. This is the rule the whole contract exists to enforce —
   cross-task writes are what let one task launder another's seeded failures
   into passes.
2. **A task may repair, and clean up after, its own namespace.** Inside the
   namespace it owns, a task may re-close its own execution's logs to restore
   the state it needs (`testcaselog finish` overwrites a recorded result).
   Where a task's *deliverable* is a creation, that output is **scratch, not a
   fixture** — `organize` sweeps its own `EVFX-ORG-*` sets in `post_run`,
   because nothing depends on them and leaving them is how CLAIM accumulated
   the duplicate sets that made agents stop and ask which to use.
3. **Create-if-absent.** `pre_run` is idempotent: it creates the fixture the
   first time it runs and reuses it on every subsequent run. There is no
   manual tenant bootstrap step.
4. **Bounded growth — guard on the property, not a count.** A seeding hook
   must leave a healthy fixture completely untouched, and it must assert the
   condition the task actually reads rather than a proxy for it. Counting
   executions is not enough: `flaky` once guarded on "three exist", so a
   momentarily `Running` execution made it top up with an all-pass run that
   pushed the intermittency out of the three-most-recent window the task
   reads. It now asserts "at least one of the newest three finished
   executions carries a failure" and appends at most one. Likewise a pure
   reader seeds once, never per run — an unguarded hook adds an execution
   every nightly and grows without bound.
5. **Pin the folder, don't guess.** `testsets run` and `testcases run` both
   require a default Orchestrator folder on the project (SKILL.md Critical
   Rule 10). `pre_run` attempts the run first and only pins a folder if that
   genuinely fails, so a working project default is never overwritten.

## Why `organize` owns its INPUTS, not just its outputs

`organize_testcases_into_testsets` used to read unowned CLAIM data: the prompt
asked it to filter test cases by `disbursement`, matching
`Claim Payout - ACH Disbursement` and `Claim Payout - Check Disbursement`. That
combination cannot work, because **`tm testcases list --filter` is a PREFIX
match** (verified: `--filter sync` against `Auto-sync Test …` returns 0) and
`disbursement` is a *suffix* of those names. The filtered lookup the task grades
could never return the cases it needed.

So the task passed or failed on which recovery branch the model happened to
pick: abandon `--filter` and list the whole project (passes), or retry a shorter
prefix like `d` and stop when that is also empty (fails). It failed the
2026-08-24 codex nightly that way and passed 2026-08-25 by listing unfiltered —
same code, same tenant, opposite outcome.

It now seeds `EVFX-ORG-SRC-TC{1,2,3}` and filters on `EVFX-ORG-SRC-TC`, which is
a genuine prefix of names the task owns. Every model takes the same single path,
and the graded `--filter` call returns exactly three cases every run.

**Authoring rule this generalises to:** a `--filter` term in a prompt MUST be a
real prefix of the target names. Never use a distinguishing word that appears
mid-name or at the end — it turns the task into a coin flip on model recovery
behaviour.

## Steady state

Eight persistent `EVFX-` test sets and their cases — `EVFX-RERUN-SET`,
`EVFX-FLAKY-SET`, `EVFX-SIGNOFF-SET`, `EVFX-JUNIT-SET`, `EVFX-TRIAGE-SET`,
`EVFX-EXLIST-SET`, `EVFX-MANUAL-SET` and `EVFX-REPORT-SET`. `organize` also uses
`EVFX-ORG-SRC-TC*` cases, but the `EVFX-ORG-SET-<timestamp>-*` sets it creates
are scratch, swept in its own `post_run`, and are not steady state.

The sets and cases never accrete. Executions are the exception, and there are
two shapes. Most tasks hold the count at zero growth by construction:
`execution_rerun` repairs one execution rather than appending, `junit_export`
and `release_readiness` seed once, `executions_list` tops up a single
run only when no finished execution exists, `flaky` appends only to restore
intermittency, and `organize` sweeps its own scratch. `manual_execution_record`
and `reporting_date_backdate` instead open one execution per run and sweep
earlier days' runs — sparing today's, so a concurrent variant run's in-flight
execution is never destroyed — so growth is bounded to one day's runs rather
than zero. That is deliberate, because both tasks consume the execution they are
given, and it is only possible because `executions delete` exists. Neither
grades a recency pick over the shared set: `reporting_date_backdate` records the
exact run its `pre_run` opened, and `manual_execution_record` snapshots the set
before the agent runs and grades the single new run the agent then opens —
failing safe if a concurrent variant leaks a second new run in, rather than
picking a winner by recency.

`schedule_lifecycle_e2e` adds `EVFX-SCHEDLC-SET` and its one case. It seeds **no
schedules**: the agent creates one itself, stamped with the run's date
(`EVFX-SCHEDLC-<STAMP>`), so there is no fixed-name schedule for a concurrent
variant run to collide on. `pre_run` sweeps only *earlier-day* `EVFX-SCHEDLC-`
schedules — sparing today's stamp lets two models run the nightly at once — and
writes the fixture set id to `.schedlc_setid` in the sandbox cwd. Correctness is
graded on the **stored state** of the agent's own schedule: it snapshots its real
server-side row to `schedule-paused.json` (after disable) and `schedule-live.json`
(after enable), and the graders read those back plus live Test Manager to assert
the Mon+Thu 03:00 cadence, the disabled→enabled transition, and final deletion —
each scoped to the agent's stamp/id, so the grade is per-run isolated without a
reseeded pre-state. The `command_executed` checks are advisory only.

`schedule_list_smoke` is the one remaining read-only smoke; it seeds and asserts
a single enabled `EVFX-SCHEDSMOKE-DAILY` schedule so the list is never empty.
The three `testcaselog` tasks all open executions with a manual run, because
this CLI has **no `executions create`** — `uip tm testcases run --name <NAME>
--execution-type manual` returns the new execution under `Data.Id` and opens a
Pending log per case. Those executions sit on an ad-hoc test set hidden from
`testsets list`, so they never pollute the test-set list an agent sees, and
`executions list` cannot find them either — a sweep enumerates the task's own
logs (`testcaselog list --search`) and groups them by `TestExecutionId`.

Concurrency drove the shape of all three (two model variants share CLAIM):

- `testcaselog_override_integration` stamps a fresh execution
  `EVFX-TCLOG-<STAMP>-RUN` every run and sweeps only executions whose logs were
  all last touched **before today**, so a concurrent run's in-flight execution
  is never deleted (an earlier fixed-name delete-and-recreate raced). `pre_run`
  writes the stamped execution's id to `target_execution.txt` in the sandbox
  cwd; the prompt scopes the agent to that one run and the oracle grades **that
  execution's** failing log (now `Passed` over an `OriginalResult` of `Failed`,
  with a non-empty override reason), not any `EVFX-TCLOG` log in the project —
  so a concurrent variant's correction or a historical corrected row cannot
  false-pass it. `pre_run`'s guard is on the property, not a count (Rule 4): it
  asserts **exactly one** log on the stamped execution reports `Failed` and that
  **no** log starts with `OriginalResult` already differing from `Result`.
- `testcaselog_read_smoke` is a pure reader: it seeds one finished
  `Passed` log create-if-absent and never deletes, so growth is flat at one
  execution. `Passed` (not `Failed`) also keeps the log off the override task's
  `--results Failed` discovery, since the three namespaces share the
  `EVFX-TCLOG` stem.
- `testcaselog_manual_record_e2e` seeds only the test case; the agent opens its
  own stamped execution, so nothing fixed-name exists to collide on. `pre_run`
  sweeps only earlier-day executions, then snapshots the surviving
  `EVFX-TCLOGMR` execution ids into `baseline_executions.txt` (sandbox cwd). The
  agent creates its execution during the run, so `pre_run` cannot know that id,
  and a log row carries no run name while the ad-hoc executions are invisible to
  `executions list` — so the oracle isolates this run by crediting only a
  `Passed` log on an execution **not** in the baseline, which rules out a
  historical pass.

The `-TC` in each task's `--search` prefix (`EVFX-TCLOG-TC`, `EVFX-TCLOGRD-TC`,
`EVFX-TCLOGMR-TC`) is load-bearing: `--search` is a prefix match, and without
the dash `EVFX-TCLOG` would also match the `TCLOGRD`/`TCLOGMR` siblings.

## Why

Before this contract, four tasks shared CLAIM's `UAT Smoke Suite` and two of
them wrote to it. `execution_rerun` consumed the failures that
`flaky_tests_analysis` needed, cleanup closed reopened logs as `Passed`, and
the suite converged on 3-pass/0-fail — so both tasks failed for reasons that
had nothing to do with the skill under test. Scores moved every night while
the code under test never changed.

## Self-contained build tasks

The three `mode:build` tasks — `project_scaffold_build`,
`testset_curation_by_label_build`, `customfield_schema_multiscope_build` — and
the `defect_full_lifecycle_e2e` task sit outside the seeded-fixture model entirely. Each one **creates its own throwaway
project, does all its work inside it, and deletes it as the final graded step.**
They read and write nothing in CLAIM, HEALTH or BANK.

This is the pattern tests/README.md prescribes: *"There is no `post_run`. The
agent creates and deletes its own ephemeral resources as part of the test
scenario."* Deleting the project removes the test cases, labels, test sets and
custom field definitions inside it in one call, so cleanup is a single command
rather than a per-object sweep.

Consequences worth knowing before you edit one:

1. **The delete is graded, not a hook.** It is both the cleanup mechanism and the
   only coverage of `project delete` in this directory. Removing that criterion
   silently turns the task into a tenant-litterer.
2. **The prompt must pre-authorize the delete.** SKILL.md Critical Rule 6 tells
   the agent to confirm before any delete, and the eval agent is
   non-interactive — nobody can answer, so an unauthorized delete is a
   guaranteed fail. This is the exact failure mode that took
   `testcase-steps-lifecycle-integration` down on the 2026-08-19 nightly. Each
   prompt therefore grants approval for that specific project in as many words.
3. **`pre_run` seeds nothing.** It is an orphan sweep for the run that dies
   between create and delete, which would otherwise strand a project forever. It
   spares today's stamp, because two models run the nightly concurrently and a
   whole-prefix sweep would delete the other run's project mid-run.
4. **Names still carry the `EVFX-` prefix** even though nothing persists. A run
   that dies leaves a project behind, and the prefix is what makes that residue
   identifiable and sweepable. The namespaces are registered in
   `check-collisions.py` like any other.

## Per-run scratch projects (hook-owned)

`project_settings_smoke` grades a change *inside* a project, not the
project itself, so it fits neither the self-contained build pattern above (where the agent's own delete is
graded) nor create-if-absent seeding (Rule 3), which would let one run's writes leak into the next.
Instead `pre_run` creates a fresh `EVFX-<NS>-<YYYYMMDD-HHMMSS>-<hex>` project per run and writes its key
to `project-key.txt`, the criteria read its live state, and `post_run` deletes it (coder_eval grades
before `post_run`). The `pre_run` sweep deletes only projects stamped more than 6 hours ago, so
concurrent runs never remove each other's project.

## Automation-linked fixtures

`EVFX-SIGNOFF-TC1` needs a real automation link to support
`--execution-type automated`:

```bash
uip tm testcases link-automation --project-key CLAIM \
  --test-case-key <EVFX-SIGNOFF-TC1 key> --folder-key <FOLDER_KEY> \
  --package-name <PACKAGE_NAME> --test-name <TEST_NAME> --output json
```

This is the one step `pre_run` cannot bootstrap on its own: it requires a
package published to Orchestrator and a robot able to serve the folder. Until
that exists, the signoff task's `pre_run` seeds a **manual** execution so the
wait/report half of the task stays gradeable.

## The `uipath-test-folder-feed` folder

Every task that needs an Orchestrator package uses this one folder, so do not
rename, delete or empty it. It has its own package feed (`FolderHierarchy`),
so packages uploaded to it stay out of the tenant feed.

| Task | Uses | Package |
|---|---|---|
| `link_automation_and_run` | folder name, in the prompt | `Testcases.with.parameters` |
| `release_signoff_wait_report_e2e` | folder key, in `pre_run` | `Testcases.with.parameters` |
| `run_package_ci_smoke` | folder name, in `pre_run` and the prompt | `TestCase_CrossPlatform_VB_Tests` |
| `run_package_failing_smoke` | folder name, in `pre_run` and the prompt | `FailingTestCase_CrossPlatform_VB_Tests` |
| `perf_scenario_setup_integration` | folder name, in `pre_run` and the prompt | `TestCase_CrossPlatform_VB_Tests` |
| `perf_scenario_dryrun_e2e` | folder name, in `pre_run` and the prompt | `TestCase_CrossPlatform_VB_Tests` |
| `perf_scenario_history_integration` | folder name, in `pre_run` | `TestCase_CrossPlatform_VB_Tests` |

`Testcases.with.parameters` is a Windows package. The folder's serverless
robot runs cross-platform packages only, so runs of it start but never finish
(see [Automation-linked fixtures](#automation-linked-fixtures)). A new task
that needs a run to finish must use a cross-platform package.

## Run-package fixtures

`run_package_ci_smoke` and `run_package_failing_smoke` run a real package, so
the tenant must be able to run one. Both call
`_setup/run_package_fixture.py seed`, which checks the tenant the run is
logged in to:

1. **Folder** `uipath-test-folder-feed` is visible to the login.
2. **Runtime:** a machine assigned to that folder has an Unattended or Test
   Automation runtime. On Automation Cloud the simplest setup is the folder's
   serverless machine with one Unattended runtime, plus a robot account in the
   folder as Automation User. Serverless robots need no machine credentials,
   but they run cross-platform packages only.
3. **Unattended account:** a member of that folder may hold an unattended
   session (`MayHaveUnattendedSession`), such as that robot account.
4. **Package:** `TestCase_CrossPlatform_VB_Tests` or
   `FailingTestCase_CrossPlatform_VB_Tests` is in the folder feed. When it is
   missing, the script uploads it from `_setup/packages/`. These are the
   cross-platform fixtures from UiPath/cli
   (`packages/test-manager-tool/tests/test-data/ported-run-tests/`).

When the folder, the runtime or the unattended account is missing, or the
upload is refused, `pre_run`
exits with `TENANT NOT READY` on stderr, naming the tenant and what is missing,
and the pass-rate gate in `smoke-skills.yml` drops the task. Automation Suite
has no serverless robots, so it needs a self-hosted machine with an unattended
robot and credentials before these tasks can run there.

The alpha `codereval` / `DefaultTenant` eval tenant is set up this way: the
`Default Serverless` machine has one Unattended runtime and the robot account
`tm-eval-robot` is in the folder. With one runtime, parallel runs queue for it;
a run takes one to three minutes, well inside the prompts' 10-minute budget.

## Default-project tasks

`project_default_discover_smoke` and `project_default_testcases_smoke` use the
tenant's default project (one per tenant, for work with no project named).
Each `pre_run` records the default this login sees in `.default-before.json`,
and each task fails if the default afterwards is a different project.

The discover task never creates a default. The test-case task lets the agent
run `uip tm project get-default`, which **creates** `Default Project` (key
`TMDP`) when the tenant has none: a lasting change, owned by the org admins and
open to the tenant's Everyone group as Test Managers. The alpha `codereval` /
`DefaultTenant` eval tenant already has it (created by this task's first run),
so runs there only read it. On a tenant without one, the first run creates it,
and a discover task running at that moment can see the default appear and fail
its unchanged check; re-run it.

The default project is shared by every run, so it is never deleted; the
test-case task deletes the test cases it adds.

