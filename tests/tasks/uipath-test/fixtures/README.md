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
| `customfield_schema_multiscope_build` | its own throwaway project | the `EVFX-SCHEMA-*` namespace | Nothing seeded, nothing persists — see [Self-contained build tasks](#self-contained-build-tasks) |
| `link_automation_and_run` | CLAIM + an owned Orchestrator folder `EVFX-LINKRUN-FOLDER` | `EVFX-LINKRUN-TC1`, the folder | No execution; `pre_run` verifies the `Testcases.with.parameters` package has entry points published into the folder and fails fast (provisioning error, not a scored regression) if not — see *Automation-linked fixtures* below |

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

## Self-contained build tasks

The three `mode:build` tasks — `project_scaffold_build`,
`testset_curation_by_label_build`, `customfield_schema_multiscope_build` — sit
outside the seeded-fixture model entirely. Each one **creates its own throwaway
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
