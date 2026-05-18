# Stub package fixtures — for process-running E2E tests (O2, O4, O6, O7, R6, R10, R11)

**Status:** sources TBD — building a standalone `.nupkg` for a coded Python agent
requires `uip codedagent` (not installed by default) and a working `uip pack`
flow. Until that's wired:

- Process-running tests fall through to **TRACES_SMOKE_PROCESS_KEY** env var
  (same pattern as `tasks/uipath-platform/traces/traces_e2e.yaml`).
- CI provides this secret (`.github/workflows/smoke-skills.yml:250`).
- Locally, export `TRACES_SMOKE_PROCESS_KEY` from a known seeded process.

When ready, scaffold the stub agent under `e2e-stub/`:

```
tests/fixtures/packages/e2e-stub/
├── project.json        # name=e2e-stub, version 1.0.0
├── agent.json
├── main.py             # prints "ran", exits 0
└── pyproject.toml
```

`tests/fixtures/build_fixtures.sh` will then call `uip codedagent pack` (or the
equivalent) to produce `e2e-stub.1.0.0.nupkg` and `e2e-stub.1.0.1.nupkg` (bump
the version field between runs). Long-running variant: same source +
`time.sleep(30)` in `main.py` → `e2e-stub-long.1.0.0.nupkg`.

`seed_process.py` already handles the upload + process-create flow once the
`.nupkg` files exist.
