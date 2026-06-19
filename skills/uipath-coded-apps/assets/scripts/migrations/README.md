# Intent-schema migrations

Empty by design. When `intent.json`'s `schemaVersion` is bumped, add one file here:

`intent-v<N>-to-v<N+1>.mjs` exporting `export function migrate(intent) { /* return upgraded intent */ }`

`runIntentMigrations` (in `build-dashboard.mjs`) applies them in sequence from the
artifact's `schemaVersion` up to `INTENT_SCHEMA_VERSION`. Pure functions, no I/O.
