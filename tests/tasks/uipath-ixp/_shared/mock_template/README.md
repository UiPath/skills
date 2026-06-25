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
grading sees the command shape while no real request is made. `mocks/curl` does
the same for raw `curl` (a smoke task may hint at a REST call the agent is graded
for refusing — shadowing `curl` ensures even a disobedient agent can't reach the
cloud with the harness-injected token). Integration/e2e tasks (which
intentionally exercise the live API) do **not** use this.
