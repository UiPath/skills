# Dashboard Capability

Build or edit a React dashboard powered by Insights RTM and the UiPath TypeScript SDK.

---

## The 3-turn contract

From the user's perspective, building a dashboard looks like this:

1. **They send their request**
2. **They see a polished plan** — no tool calls visible between request and plan
3. **They confirm** — a single bash call runs, progress ticks appear, browser opens

Every internal mechanic (reads, pre-warm, login, intent.json) happens invisibly. The user sees only: plan → confirm → live dashboard.

---

## Turn 2 — Everything in ONE parallel message (this turn)

Fire all of these simultaneously. This is the only turn before the plan.

**Reads (all parallel):**

| File | Purpose |
|------|---------|
| `plugins/build/impl.md` | Full build instructions |
| `primitives/tier-resolution.md` | Metric classification + hard-refuse list |
| `primitives/auth-context.md` | Login + credential extraction |
| `primitives/sdk-field-reference.md` | SDK response shapes + import paths |
| `primitives/build-plan.md` | intent.json schema |
| `aesthetic/layout-patterns.md` | Layout rules |
| `assets/scripts/capability-registry.json` | Metric catalog |

**Commands (in the same message):**

```bash
uip login status --output json
```

```bash
node -e "
const fs = require('fs')
fs.existsSync('.dashboard/state.json') ? process.exit(0) : process.exit(1)
" && echo INCREMENTAL || echo FRESH
```

**Pre-warm — fire in background, do NOT wait:**

Derive the routing name from the user's request (e.g. `agent-health-x7k2`), then fire npm ci immediately:

```bash
# run_in_background: true — do not wait for this
mkdir -p ~/dashboards/<ROUTING_NAME> && npm --prefix ~/dashboards/<ROUTING_NAME> ci --prefer-offline 2>&1
```

Set `run_in_background: true` on this Bash call. Continue to the plan output immediately — do not wait for npm ci.

---

## Turn 2 output — Show the plan (pure text, zero tool calls)

After all reads complete and pre-warm is fired, output the plan directly as text. No more tool calls until the user confirms.

See `plugins/build/impl.md` for the plan format and subsequent phases.

---

## Routing

- `INCREMENTAL` → read `primitives/incremental-editor.md`, then follow it
- `FRESH` → follow `plugins/build/impl.md`

---

## Hard stops

- **Never** read `build-dashboard.mjs` — fully documented in impl.md
- **Never** run `ls`, `find`, or directory exploration
- **Never** read `sdk-capabilities.md` — tier-resolution.md + capability-registry.json are sufficient
- **Never** read files one at a time
- **Never** show tool call output to the user between their request and the plan
- **Never** wait for pre-warm before showing the plan — fire it in background and move on
- **Never** auto-deploy
- **Never** commit generated dashboard files
