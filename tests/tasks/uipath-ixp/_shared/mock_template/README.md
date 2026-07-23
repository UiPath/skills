# uipath-ixp smoke mock

Shape-only smoke tasks under `../../smoke/` must not authenticate or hit a live
tenant. They PATH-shadow `uip` with this template:

```yaml
sandbox:
  driver: tempdir
  mock_path_dirs: [mocks]
  template_sources:
    - {type: template_dir, path: ../_shared/mock_template}
```

`mocks/uip` fails offline with no network call and appends each expanded
invocation as one line in `mocks/calls.log`. Embedded newlines in arguments are
normalized to spaces, so JSON loaded with command substitution stays on the same
record. The seeded, non-hidden log is included in CI artifacts.

Use the native `file_matches_regex` criterion to match readable regular
expressions against the log. Negative guards must pair with a positive
logged invocation so a missing or misdirected log cannot pass vacuously.
`mocks/curl` similarly prevents raw REST traffic.

Integration/e2e tasks use `live_calls_template`, whose wrapper records the same
log format and delegates unchanged to the real CLI.
