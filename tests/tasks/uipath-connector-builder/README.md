# uipath-connector-builder task tests

Task-tier coverage for the `uipath-connector-builder` skill (`uip is connectors builder`).

These tasks exercise the **offline authoring flow** only, which is hermetic and
needs no tenant or login:

```
init (offline via --organization) → auth set → activity create (+ fields) → validate
```

They assert on the real generated artifacts under
`periodic-design-<org>-<slug>/app/element/` (`element.json`,
`standard-resources/*.json`), not on agent self-reports, and check the specific
builder verbs ran — so a task can't pass just because `validate` was invoked.

| Task | Tier | Covers |
|------|------|--------|
| `init-validate` | smoke | scaffold a connector shell + validate; element key is derived |
| `oauth2-activity` | e2e | init → OAuth2 auth → CRUD activity with a typed field schema → validate |

`import` / `publish` / `download` need `uip login` and a tenant, so they're out of
scope here — those belong in a live e2e run, not the hermetic task suite.
