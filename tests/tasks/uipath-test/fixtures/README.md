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
| `defect_lifecycle_smoke` | its own per-run project | the `EVFX-DEFECT-*` namespace | `pre_run` creates one `EVFX-DEFECT-<YYYYMMDD-HHMMSS>-<hex>` project per run (key in `project-key.txt`) holding `EVFX-DEFECT-SET`/`EVFX-DEFECT-TC1` and one Finished execution with TC1 `Failed` and no defect; it sweeps orphans stamped more than 6 hours ago, and `post_run` deletes the project. Per-run because a result holds one defect and several models run the nightly concurrently |
| `defect_traceability_integration` | its own per-run project | the `EVFX-DEFTRACE-*` namespace | Same per-run project pattern (`EVFX-DEFTRACE-<YYYYMMDD-HHMMSS>-<hex>`, key in `project-key.txt`): `EVFX-DEFTRACE-SET`/`TC1`/`REQ` with the requirement covering TC1, one Finished execution with TC1 `Failed`, and a defect on that result linked by hand to tracker issue `EVFX-DEFTRACE-1`; `post_run` deletes the project |
| `defect_full_lifecycle_e2e` | its own throwaway project | the `EVFX-DEFFLOW-*` namespace | Nothing seeded, nothing persists — see [Self-contained build tasks](#self-contained-build-tasks). Does not grade `defects attachments download`: a manual result gives the defect no evidence (a file uploaded to the result with `attachment upload --object-type testCaseLog` does not appear under `defects attachments list`), so there is nothing to download |
| `project_settings_smoke` | its own throwaway project | the `EVFX-PSET-*` namespace | `pre_run` creates one `EVFX-PSET-<YYYYMMDD-HHMMSS>-<hex>` project per run (key in `project-key.txt`) and sweeps orphans stamped more than 6 hours ago (so a concurrent run's project is never touched); `post_run` deletes it. The deliverable is a settings change, not the project, so the project is scratch (Rule 2). Unlike the self-contained build tasks, project create/delete is not under test here, so the hooks own the project's lifecycle and the agent never deletes it |
| `testcase_parameters_bulk_add_smoke` | HEALTH | `EVFX-PARAM-Login`, `EVFX-PARAM-Transfer` | Created if absent; `pre_run` clears their parameters each run and seeds `Username=keepme` on Transfer |
| `testcase_parameters_edit_integration` | HEALTH | `EVFX-PARAMEDIT-Login` | Created if absent; `pre_run` resets its parameters to `Username=admin` (with hint) and `Userid=u1` |
| `testcase_parameters_lifecycle_e2e` | HEALTH | `EVFX-PARAMLIFE-Login` | Created if absent; `pre_run` clears its parameters |
| `testcase_parameters_ask_first_integration` | HEALTH | `EVFX-PARAMASK-Login` | Created if absent; `pre_run` resets its parameters to `Username=admin` (with hint) |
| `requirement_ai_generate_smoke` | HEALTH | `EVFX-AIGEN-REQ` | Requirement with a fixed description and **no** linked test cases. `pre_run` also starts one generate job with a 3 s wait (it times out) and saves the output to `nightly/` in the sandbox. The test cases the task creates from that job are scratch: `pre_run` deletes every linked test case labelled `autopilot-generated` and unlinks the rest |
| `requirement_ai_evaluate_smoke` | HEALTH | `EVFX-AIEVAL-REQ` | Requirement whose description `pre_run` resets to the one-line `Users can reset their password.` every run (the task appends to it) |
| `requirement_ai_obsolete_smoke` | HEALTH | `EVFX-AIDEL-REQ`, `EVFX-AIDEL-TC{1,2,3,4}` | All four linked; TC3 and TC4 off-topic on purpose. `pre_run` recreates the one the task deleted and relinks the ones it unlinked |
| `requirement_ai_blocked_inputs_smoke` | HEALTH | `EVFX-AIBLOCK-NODESC` | No description, no attachments. `generate-testcases` fails with HTTP 400 before a job starts, so the task spends no AI units |
| `attachment_upload_smoke` | HEALTH | `EVFX-ATTUP-Checkout` | Created if absent; `pre_run` clears its attachments and writes a local `checkout-failure.png`; `post_run` clears its attachments |
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
| `testcase_lifecycle_e2e` | HEALTH | none shared; `EVFX-TCLIFE-<uuid8> Login`/`Logout`/`Login copy` per run | The agent deletes its copy; `post_run` deletes the rest, `pre_run` sweeps ones older than 6 hours |

The `requirement_ai_*` tasks share one helper, [`../_setup/req_ai_fixture.py`](../_setup/req_ai_fixture.py)
(`seed`, `check`). It knows no names: each task passes its own `EVFX-` names
on the command line, so they stay in the task YAML where `check-collisions.py`
sees them.
`seed --require-access <verb>` first calls that AI verb on a requirement id
that does not exist: an allowed login gets HTTP 404 before any job starts, a
refused one gets 403, and `seed` then exits `TENANT NOT READY` so smoke
excludes the task instead of failing it. Each AI route has its own feature
flag, licence policy and AI Trust Layer policy; on 2026-10-15 the eval tenant
allowed `generate-testcases` and `evaluate` but answered 403 to
`find-obsolete-testcases`.

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
