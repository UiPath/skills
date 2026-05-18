# Stub library fixture — for the library lifecycle E2E test (R8)

**Status:** TBD — `e2e-stub-lib.1.0.0.nupkg` not yet built.

Until present, R8 (`tasks/uipath-platform/resources/library_e2e.yaml`) is
`skip: true`.

To unblock R8, produce a minimal UiPath library `.nupkg` and commit it here as
`e2e-stub-lib.1.0.0.nupkg`. Any tiny library project will do; the test verifies:

- `libraries upload --file <fixture>` succeeds
- `libraries get` returns the uploaded version
- `libraries versions` lists it
- `libraries download` round-trips with byte-equal sha256

The .nupkg is treated as opaque by the test — no specific manifest content is
required beyond being a valid UiPath library package.
