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
| `organize_testcases_into_testsets` | CLAIM | the `EVFX-ORG-*` namespace | Nothing pre-created; the task creates `EVFX-ORG-<YYYYMMDD-HHMMSS>-*` and `pre_run` clears earlier days |
| `integration_release_readiness_qa_lead` | BANK | the existing regression suite (no `EVFX-` names) | 1 Finished execution mixing `Passed`/`Failed`/`Restricted`/`None` |
| `project_scaffold_build` | its own scratch project | the `EVFX-SCAFFOLD-*` namespace | Nothing pre-created; the task creates `EVFX-SCAFFOLD-<YYYYMMDD-HHMMSS>-*` and `pre_run` clears earlier days |
| `testset_curation_by_label_build` | CLAIM | `EVFX-CURATE-TC{1,2,3}`, labels `EVFX-CURATE-tier{1,2}`, the `EVFX-CURATE-SET-*` namespace | 3 test cases, labelled tier1/tier1/tier2, no execution; the task creates `EVFX-CURATE-SET-<YYYYMMDD-HHMMSS>-*` and `pre_run` clears earlier days |
| `customfield_schema_multiscope_build` | HEALTH | the `EVFX-SCHEMA-*` namespace | Nothing pre-created; the task creates one multi-scope definition and `pre_run` clears earlier days |

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

## Steady state

Four test sets and eleven test cases, fixed — `EVFX-RERUN-SET`,
`EVFX-FLAKY-SET`, `EVFX-SIGNOFF-SET`, `EVFX-JUNIT-SET` and their cases. Nothing
accretes: `execution_rerun` repairs one execution rather than appending,
`junit_export` and `release_readiness` seed once, `flaky` appends only to
restore intermittency, and `organize` sweeps its own scratch.

## Why

Before this contract, four tasks shared CLAIM's `UAT Smoke Suite` and two of
them wrote to it. `execution_rerun` consumed the failures that
`flaky_tests_analysis` needed, cleanup closed reopened logs as `Passed`, and
the suite converged on 3-pass/0-fail — so both tasks failed for reasons that
had nothing to do with the skill under test. Scores moved every night while
the code under test never changed.

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
