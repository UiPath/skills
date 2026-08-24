# uipath-ixp smoke mock

Shape-only smoke tasks under `../../smoke/` must not authenticate or hit a live
tenant — the smoke harness injects a live alpha bot token, so a bare `uip ixp …`
would otherwise reach designtime-api on alpha (404-ing on fixture ids). Most
smoke tasks therefore mock `uip` with this template:

```yaml
sandbox:
  driver: tempdir
  mock_path_dirs: [mocks]
  template_sources:
    - {type: template_dir, path: ../_shared/mock_template}
```

`mocks/uip` PATH-shadows the real CLI and fails offline with no network call, so
grading sees the invocation while no real request is made. `mocks/curl` does the
same for raw `curl`, so a disobedient agent cannot reach the cloud with the
harness-injected token.

## Call log

Each invocation is recorded to **two sinks**, both seeded in this template so
they always exist, and neither dot-prefixed — CI's `upload-artifact` skips
hidden files, and both belong in the eval-report artifact.

| Sink | Shape | Use |
|------|-------|-----|
| `mocks/calls.log` | one flat `uip <args>` line per invocation | `file_matches_regex` criteria (every task today) |
| `mocks/calls.jsonl` | one JSON object per invocation | structured matching; seeded EMPTY, so "file missing" and "zero calls" stay distinguishable |

The flat line space-joins the arguments and folds CR/LF to spaces, so JSON built
with command substitution remains one record. That join is lossy — it cannot say
whether `--instructions "extract total, tax"` was one argument or two — which is
why the JSONL record keeps `argv` as a list:

```json
{"ts": 1785416844.987, "tool": "uip",
 "argv": ["ixp", "projects", "configure-model", "proj-ixp", "--model", "gemini_2_5_pro"],
 "exit": 1}
```

Record order is invocation order. Fields:

- `tool` — `uip` or `curl`; both mocks share the log.
- `argv` — arguments after the program name, verbatim, one element per argument.
  Deliberately NOT parsed into verb/flags here: splitting a verb from its
  positionals needs verb-depth knowledge and flag parsing needs to know which
  flags take values. Both are interpretation, and belong in the criterion.
- `exit` — the mock's exit status; `null` in the live wrapper, which `execv`s the
  real CLI and so never observes it.

**Standard input is not recorded**, and there is no field for it. Reading stdin
in the offline mock would block whenever the sandbox leaves it attached to an
open pipe, hanging the task until its timeout; in the live wrapper it would
consume the payload the real CLI needs. Nothing reads stdin today — the skill
passes payloads as flag VALUES (`--updates "$(cat f.json)"`), which `argv`
captures in full. Add the field when something needs it; a new key breaks no
existing criterion.

Grade CLI behavior from a log, not from regexes over agent-authored Bash text,
which can false-match commands merely quoted in heredocs, comments, or prose.

Log-based negative guards MUST pair with a positive control — a log line a
correct run is guaranteed to produce — otherwise re-pointing the mock's sink
makes every negative guard pass vacuously.

Where no invocation is GUARANTEED in a correct run, the guard carries no positive
control. Say so in a comment and add no criterion for it.

Exclude the specific verb a task traps, never every invocation. Both sinks are
seeded, so `calls.log` always exists (a file-absent check cannot stand in for
"made no call"), and correct runs call unrelated verbs while orienting.

Do NOT assert static text in `mocks/uip` — a `FLAT_LOG =`/`JSON_LOG =` line, or
the old `>> "$(dirname "$0")/calls.log"` redirect. It cannot tell a moved sink
from a reformat: the sh → Python rewrite deleted that redirect and pinned
`list_model_options` at 0.909 for six nightlies, never passing.

Integration/e2e tasks use `live_calls_template`; its wrapper writes the same two
sinks in the same format, then delegates unchanged to the real CLI.

## Not every task uses this template

Tasks graded with `cli_called` declare `sandbox.record_cli` instead, and the
framework generates the recorders, seeds the log and PATH-prepends `cli_mocks/`
itself — no `mock_path_dirs`, no `template_sources`, no `log:` on the criterion.
Prefer that for a new structured task. This template remains the answer whenever
a recorder is not enough: `file_matches_regex` over the flat `calls.log`, a read
that must return fixture data (`mock_template_taxonomy`), or per-invocation
responses, none of which `record_cli` serves. `calls.jsonl` here has no consumer
today for that reason — it is the structured sink for tasks that need this
template's other behavior too.

A task whose correct path reads before it writes cannot be graded on this mock
alone — the read fails, so there is nothing to carry into the graded write, and
an agent that declines to invent the values correctly stops. Overlay
`mock_template_taxonomy` (listed second) to serve that read.
