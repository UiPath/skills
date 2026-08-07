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

| Task | Project | Owns |
|------|---------|------|
| `execution_rerun_failed_integration` | CLAIM | `EVFX-RERUN-SET`, `EVFX-RERUN-TC{1,2,3}` |
| `flaky_tests_analysis` | CLAIM | `EVFX-FLAKY-SET`, `EVFX-FLAKY-TC{1,2,3}` |
| `release_signoff_wait_report_e2e` | CLAIM | `EVFX-SIGNOFF-SET`, `EVFX-SIGNOFF-TC1` |
| `organize_testcases_into_testsets` | CLAIM | `EVFX-ORG-TC*` source pool; creates `EVFX-ORG-<YYYYMMDD>` |
| `integration_release_readiness_qa_lead` | BANK | `EVFX-READY-SET`, `EVFX-READY-TC{1..4}` |

Tasks NOT listed here are pure readers of stable, non-mutated data and own
nothing.

## Rules

1. **Never delete.** No task removes a fixture — not in `post_run`, not in
   cleanup, not ever. Fixtures are permanent tenant state.
2. **Never collide.** A task must not create anything whose name matches
   another task's fixture, or any pre-existing tenant object. When a task's
   deliverable *is* a creation (`organize`), it creates into its own `EVFX-`
   namespace with a date suffix so repeat runs never produce an ambiguous
   duplicate.
3. **Create-if-absent.** `pre_run` is idempotent: it creates the fixture the
   first time it runs and reuses it on every subsequent run. There is no
   manual tenant bootstrap step.
4. **Append, don't mutate.** A task needing execution history appends a *new*
   execution with the exact result pattern it requires. It never rewrites an
   existing execution's logs — that is what let one task launder another
   task's seeded failures into passes.
5. **Pin the folder, don't guess.** `testsets run` and `testcases run` both
   require a default Orchestrator folder on the project (SKILL.md Critical
   Rule 10). `pre_run` probes for a folder that actually accepts a run and
   pins it as the project default, so no agent ever picks one. Guessing is
   what produced the `set-default-folder` HTTP 500 in the 2026-08-05 nightly.

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
