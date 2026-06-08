# Dashboard Capability

Build or edit a React dashboard powered by Insights RTM and the UiPath TypeScript SDK.

---

## Step 1 — Read everything in ONE parallel message block

Fire all of these simultaneously before any other work:

| File | Purpose |
|------|---------|
| `plugins/build/impl.md` | Full build instructions |
| `primitives/tier-resolution.md` | Metric classification + hard-refuse list |
| `primitives/auth-context.md` | Login + credential extraction |
| `primitives/build-plan.md` | intent.json schema |
| `aesthetic/layout-patterns.md` | Layout rules |
| `assets/scripts/capability-registry.json` | Metric catalog (machine-readable T1/T2 entries) |

In the same message, also run:

```bash
uip login status --output json
```

```bash
node -e "
const fs = require('fs')
fs.existsSync('.dashboard/state.json') ? process.exit(0) : process.exit(1)
" && echo INCREMENTAL || echo FRESH
```

---

## Step 2 — Route based on result

- `INCREMENTAL` → read `primitives/incremental-editor.md`, then follow it
- `FRESH` → follow `plugins/build/impl.md` (already loaded above)

---

## Hard stops — never do these

- **Do not** read `build-dashboard.mjs` — the build protocol is fully documented in impl.md
- **Do not** run `ls`, `find`, or directory exploration — all paths are given explicitly
- **Do not** read `sdk-capabilities.md` — `primitives/tier-resolution.md` and `capability-registry.json` are sufficient
- **Do not** read one file at a time — always batch all reads in a single message
- **Do not** auto-deploy — deploy requires explicit user confirmation
- **Do not** commit generated dashboard files
