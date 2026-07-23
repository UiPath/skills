# Connector Debugging Guide

Workflow: `inspect` → understand → identify the misconfiguration → fix with a single
addressed write → re-`validate`. Tooling: `inspect` (read-only rollup), `state query
<POINTER>` (surgical read), `state patch <POINTER>` (REPLACES the whole node — to edit one
field, query the entry and patch the complete object back), `validate` (full check set,
exits non-zero on failure). All run under `uip is connectors builder`.

## Investigation steps
1. `inspect` — auth types, config, resources (with SR files + hooks), global hooks, events, metadata.
2. `state query` the relevant slice:
   - Auth → `element.json/authentication`, `element.json/configuration`, then `.../configuration/{key}`
   - Resource → `element.json/resources`, then `.../resources/{METHOD}/{url-encoded-path}` + `standard-resources/{name}`
   - Hook → `hooks/{file}.js` + `element.json/resources/{M}/{P}/hooks`
   - Event → `element.json/configuration/event.poller.configuration` + `standard-resources/{name}/metadata/events`
3. Cross-reference: resources[] ↔ SR files (paths match), hook `ref`s ↔ `hooks/` files,
   configuration[] ↔ auth-type requirements, element-metadata flags ↔ capabilities.
4. `validate` for automated pass/fail (use this to gate, not `inspect`).

## Connection issues
- **OAuth redirect loop / error**: wrong `oauth.authorization.url` (often the token URL by
  mistake), missing scopes, hardcoded `oauth.callback.url` (periodic sets it), `typeOauth`
  false when it should be true.
- **Token exchange fails**: wrong `oauth.token.url`; vendor expects/rejects
  `oauth.basic.header`; creds in wrong place (body vs header).
- **Works then fails after expiry**: `oauth.token.refresh_url` unset (NOTE underscore — the all-dots key is dead), refresh interval too
  long, or wrong param mapping in `oauthOnTokenRefresh`.
- **API key unauthorized**: wrong header name, missing prefix (`Bearer `/`Token `), or key
  sent as query when the vendor wants a header. Re-run `auth set --auth-type customApiKey`.

## Resource (activity) issues
- **Empty results**: wrong `vendorPath`, wrong response `root-key`, postRequest hook filters
  wrongly, or broken pagination.
- **404**: `vendorPath` typo/version, path-param mismatch, wrong/missing `base.url`,
  deprecated endpoint.
- **Create/Update sends wrong data**: request body wrapped in the wrong key, preRequest hook
  mangles the body, IS↔vendor field-name mismatch.
- **Fields don't show in Studio**: missing `--request-curated`/`--response-curated` on the
  `activity field create` call, or the field is `--hidden`.
- **Object shows in Studio but has NO methods under it**: the SR method's path points at the
  VENDOR path, not the IS slug `/<object>`, so periodic can't link it; `validate` flags "SR
  linkage broken". Fix: set the SR method's `reference` (or `path`) to the IS slug `/<object>`
  so it matches the element.json resource path. See [standard-resources.md](standard-resources.md).
- **Methods aren't curated activities**: a method created with `--no-curate` has no `curated`
  block — re-run `activity create` (curates by default) or `activity method curate`.
- **by-id confusion**: GETBYID/PATCH/DELETE auto-add the `/{primaryKey}` path param; only
  model GETBYID for TRUE by-id endpoints, not search.

## Hook issues
- **done() not called**: an exception or a branch skips `done()`.
- **Hook not applied**: not registered in element.json (run without `--no-auto-register`),
  `ref`/filename mismatch (case-sensitive), wrong `type` or resource/method.
- **Global hook over-applies**: re-create it scoped to the resource instead of `--global`.
- **Hook throws / 500 from a hook**: a real JS error, or a `require()` of a module Denali doesn't provide (it supports `axios`/`crypto`/`url`/`querystring`/`lodash`/`moment`). Modern JS (`?.`, `??`, `async`/`await`) is fine. See [hooks.md](hooks.md).

## Event / pagination issues
- **Events not working**: `hasEvents` unset, missing event config keys, malformed
  `event.poller.configuration` JSON. Re-run `trigger create` to re-seed the bundle.
- **Polling returns everything**: missing date filter in the URL, wrong `--updated-date-field`,
  or date-format mismatch. See [events.md](events.md).
- **Only first page**: wrong `--pagination-type`, missing `--next-page-key`/`--root-key`, or
  missing nextPage handling in a preRequest hook.

## Publish / import issues (tenant lifecycle — under `uip is connectors`, NOT builder)
`import` → `publish` order and the `publish`/`--wait`/`publish-status` mechanics live in
SKILL.md; the symptoms below are debug-only:
- **Local edits not reflected after publish**: `publish` promotes what was already imported —
  it does NOT push local file changes. Re-`import` first, then `publish`.
- **"version must be higher"**: re-publishing needs a HIGHER version than the last published
  one. Bump `element-metadata.json:latestVersion` (or pass `--version 1.0.1`). A brand-new
  connector publishes with NO `--version` (`init` seeds `latestVersion = "1.0.0"`).
- **Published but not visible**: Studio Web shows a fresh publish ~5–10 min after `SUCCESS`.
- **Live smoke test**: `uip is connectors probe --connection-id <id>` proxies each on-disk SR
  through a real connection (GET-only; `--include-mutations` to add POST/PUT/PATCH/DELETE).
  Catches `metadata.method.<VERB>.path` typos that static `validate` cannot.
- **Auth**: `import` / `download` / `publish` / `publish-status` / `probe` all require `uip login`.

## See also
- [hooks.md](hooks.md), [events.md](events.md), [configuration.md](configuration.md),
  [standard-resources.md](standard-resources.md), [system-resources.md](system-resources.md)
