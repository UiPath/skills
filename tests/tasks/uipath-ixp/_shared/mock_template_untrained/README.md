# Untrained-project metrics mock

Overlay for `../../smoke/diagnose_metrics_not_trained.yaml`. List it **second**
in `template_sources`, after `../mock_template`, so `mocks/uip` here wins the
PATH shadow while the base template's `mocks/curl` and seeded `calls.log` /
`calls.jsonl` remain.

## Why it exists

`projects get-metrics` has three documented response shapes and the skill
prescribes stopping on two of them:

| Project state | Response | Skill's instruction |
|---|---|---|
| validated | flat `Data` with `ProjectScore`, `Fields[]`, … | report the numbers |
| trained, not validated | `Data` is exactly `{ Metrics: null }` | report "no metrics yet" and stop |
| no trained model | failure envelope, `Result: Failure` / `ErrorCode: not_found`, no `Data` | report "no metrics yet" and stop |

`../mock_template_drift` serves only the first shape. The base `mock_template`
fails every call, and the smoke prompts frame that as an auth error — so on it
an agent never has to tell "no metrics yet" apart from "the CLI could not reach
the tenant", which is the whole distinction being graded.

## Fixture

| Project | `get-metrics` | `list-models` |
|---|---|---|
| `fresh_contracts-8c21b4d3-ixp` | `Result: Failure`, `ErrorCode: not_found`, **exit 1** | Success, `Models: []`, `Tags: []` |
| `pending_invoices-4f77e9a1-ixp` | Success, `Data: { Metrics: null }`, exit 0 | Success, one version 3, `Tags: []` |

`projects list` and `projects get` are served for both so an agent can orient.
Everything else falls through to the base mock's offline failure.

## Two deliberate choices

**The failure envelope exits 1.** A real CLI failure is not exit 0, and an agent
that reads the exit code without reading `ErrorCode` is exactly the one that
treats a permanent `not_found` as a transient blip and loops. Exiting 0 here
would hide that.

**The task prompt does not carry the usual "commands will fail with auth errors,
do not retry" line for reads.** That boilerplate is correct for shape-only smoke
tasks, but here it would pre-empt the mistake — an agent told in advance not to
retry cannot be caught re-polling.

Neither response is fixed by `configure-model`, `publish`, or another upload, so
the task guards those verbs negatively. The re-poll bound is enforced by
`../check_metrics_stop.py`, not by a regex — `file_matches_regex` has no upper
count.

Fixture values are hard-coded into the task's criteria and its judge prompt.
Change a project name or a response shape here and update both.
