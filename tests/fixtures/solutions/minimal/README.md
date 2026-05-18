# Minimal solution fixture — for E2E platform tests (S1, S2, S3)

**Status:** scaffold only — `e2e-minimal.uipx` declares an empty `Projects` array,
which `uip solution pack` rejects (`Solution definition empty or not found`).

To make S1/S2/S3 runnable, add at least one project inside this directory and
register it in `e2e-minimal.uipx`'s `Projects` array. Smallest workable shape:

```bash
cd tests/fixtures/solutions/minimal
uip rpa init MinimalProject   # or equivalent for whatever skill ships an "init"
uip solution project add MinimalProject e2e-minimal.uipx
uip solution pack . /tmp/check.zip   # confirm pack now succeeds
```

Once `uip solution pack` succeeds against this directory, S1/S2/S3 can drop
their `skip: true` and run end-to-end.

The `SolutionId` in `e2e-minimal.uipx` is the all-zeros placeholder — Studio Web
rewrites it on first publish. Do not bake a real ID into the committed file.
