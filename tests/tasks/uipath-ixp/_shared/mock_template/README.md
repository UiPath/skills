# uipath-ixp smoke mock

Shape-only smoke tasks under `../../smoke/` must not authenticate or hit a live
tenant — the smoke harness injects a live alpha bot token, so a bare `uip ixp …`
would otherwise reach designtime-api on alpha (404-ing on fixture ids). Every
smoke task therefore mocks `uip` with this template:

```yaml
sandbox:
  driver: tempdir
  mock_path_dirs: [mocks]
  template_sources:
    - {type: template_dir, path: ../_shared/mock_template}
```

`mocks/uip` PATH-shadows the real CLI and fails offline with no network call, so
grading sees the expanded invocation while no real request is made. Each invocation
is appended to `mocks/calls.log` (seeded in this template so it always exists; not
dot-prefixed so CI's `upload-artifact` — which skips hidden files — includes it
in the eval-report artifact). Embedded newlines in arguments are normalized to
spaces, so JSON loaded with command substitution remains one log record.

Grade CLI behavior from that log with the native `file_matches_regex` criterion,
not regexes over agent-authored Bash text, which can false-match commands merely
quoted in heredocs, comments, or prose.

Log-based negative guards MUST pair with a positive control — a log line a
correct run is guaranteed to produce — otherwise re-pointing the mock's sink
makes every negative guard pass vacuously. Only when no invocation is guaranteed
in a correct run, fall back to a harness-integrity criterion asserting `mocks/uip`
still contains `>> "$(dirname "$0")/calls.log"` (weaker: static text, and brittle
against cosmetic mock refactors). `mocks/curl` does the same for raw `curl`, so a
disobedient agent cannot reach the cloud with the harness-injected token.

Integration/e2e tasks use `live_calls_template`; its wrapper records the same log
format and delegates unchanged to the real CLI.
