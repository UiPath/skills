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

Fire all of these simultaneously in **a single response**. Use multiple tool calls in the same message — do not wait for one to complete before starting another.

> **Path note:** All file paths below are relative to `SKILL_BASE_DIR` — the directory where `SKILL.md` lives (shown as "Base directory for this skill:" in your activation message). They are **not** relative to this file's location (`references/dashboards/`).
>
> Verify: this file's own path is `$SKILL_BASE_DIR/references/dashboards/CAPABILITY.md`

**4 file reads (all in one message — parallel):**

| File | Purpose |
|------|---------|
| `references/dashboards/plugins/build/impl.md` *(from skill root)* | Build instructions, preflight, plan format, intent.json schema |
| `references/dashboards/primitives/tier-resolution.md` *(from skill root)* | Metric classification, hard-refuse list, SDK service reference, SDK usage patterns |
| `references/dashboards/aesthetic/layout-patterns.md` *(from skill root)* | Layout rules |
| `assets/scripts/capability-registry.json` *(from skill root)* | Metric catalog |

> `tier-resolution.md` contains the SDK service class reference table (import subpaths + response field names). **Do not** fetch the live SDK docs URL — it takes 60–90 seconds and the information is already in `tier-resolution.md`. For T2/T3-SDK field verification, Phase 3.5 reads local `.d.ts` files instead.

**2 commands (same message, parallel with reads):**

```bash
uip login status --output json
```

```bash
node -e "
const fs = require('fs')
fs.existsSync('.dashboard/state.json') ? process.exit(0) : process.exit(1)
" && echo INCREMENTAL || echo FRESH
```

**Pre-warm (same message — MUST use `run_in_background: true` on the Bash tool call):**

Derive `<PROJECT_DIR>` from the user's request first, then include this Bash call in the same message as the reads and commands above:

```bash
node "<SKILL_BASE_DIR>/assets/scripts/build-dashboard.mjs" --prewarm "<PROJECT_DIR>"
```

⚠️ **Set `run_in_background: true` on this specific Bash tool call.** This is a parameter on the tool call itself, not a shell flag. Without it the call blocks and the plan is delayed by 60–90 seconds of npm ci. The build script emits `PREWARM_DONE` when complete — do not wait for it.

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

- **Never** fetch `https://uipath.github.io/uipath-typescript/llms-full-content.txt` — it takes 60–90s; SDK service reference is already in `tier-resolution.md`
- **Never** use the Agent tool for SDK documentation — use Read on local files only
- **Never** read `build-dashboard.mjs` — fully documented in impl.md
- **Never** run `ls`, `find`, or directory exploration
- **Never** read `sdk-capabilities.md` — tier-resolution.md + capability-registry.json are sufficient
- **Never** read files one at a time
- **Never** show tool call output to the user between their request and the plan
- **Never** wait for pre-warm before showing the plan — it must use run_in_background: true
- **Never** auto-deploy
- **Never** commit generated dashboard files
