# Incremental Editor

Handles ADD / REMOVE / CHANGE / REBUILD / UPGRADE / EJECT requests on existing dashboards.

## Trigger

Detects `.dashboard/state.json` at session start or after `BUILD_RESULT`. State schema: [state-file.md](state-file.md).

> **Regime gate (check first).** Read `state.regime`. If it is `"ejected"`, the structured edit-script is **disabled** — it emits `EJECTED_PROJECT` and exits non-zero rather than regenerate over hand work. Edit the project's `src/` directly per the request, then `npm run build`. Only `compiler-managed` (or absent/legacy) dashboards use the ops below. See [customization.md](customization.md#regimes-compiler-managed-vs-ejected).

> **Precondition:** the project must still contain the extracted starter kit, including `_gen/widgets/` (the widget generator templates the build reads). It's there from the initial build; if the project dir was wiped, the build fails loud with the extract command — re-extract the kit (or run a fresh build) before editing. See `plugins/build/impl.md § The starter-kit archive`.

## edit-intent.json schema

Write `edit-intent.json` **inside the project directory** (the dir that holds `.dashboard/state.json`). **Multiple changes = ONE `ops` batch — never run the script once per change.** The whole batch is validated up front (nothing is written if any op would fail), applied in order, and Dashboard.tsx/index.ts + tsc run once at the end.

> **Path safety — never reconstruct the project's absolute path.** Reuse the directory the build already created (where `.dashboard/state.json` lives) and work with **relative** paths: `cd` into the project, set `"projectDir": "."`, and pass a relative `edit-intent.json` to the script. Do NOT retype or rebuild a `/tmp/…` sandbox path — the sandbox hash can differ by a single character (e.g. `_` vs `-`), and a mistyped absolute path silently writes the edit to a sibling directory the build never created, so the change appears to succeed but lands nowhere the project (or the graders) can see it.

`edit-intent.json` carries **metadata only** — no `fnBody` fields. Data-fetch code ships as `metrics/<name>.ts` modules sibling to `edit-intent.json`.

```json
{
  "projectDir": ".",
  "ops": [
    { "op": "CHANGE", "target": "MemoryCallsTrend", "delta": { "displayAs": "bar-chart" } },
    { "op": "REMOVE", "target": "AgentConsumption" },
    { "op": "ADD", "metric": { "name": "agent-health", "tier": "T1", "title": "Agent Health" } }
  ]
}
```

Op shapes:
- **ADD** — `metric` is a full intent.json metric entry (metadata only, no `fnBody`). Also write `metrics/<name>.ts` module alongside `edit-intent.json` — the build copies it in.
- **REMOVE** — `target` is the widget component name from state.json. Also delete the corresponding `metrics/<name>.ts` module.
- **CHANGE** — `delta` merges over the widget's persisted `intentMetric`. Metadata-only changes (e.g. `displayAs`, `title`) leave the existing module in place. Changing query logic requires shipping a new `metrics/<name>.ts` module alongside the op.
- **REBUILD** — no fields; regenerates every widget from persisted `intentMetric` + the on-disk `metrics/*.ts` modules (e.g. after template updates). No module changes needed unless also updating queries. **Stop the dev server before REBUILD on Windows** — a running Vite holds every widget file open, so the rewrite hits `EPERM`/`EBUSY`. The build retries the rename and falls back to an in-place overwrite, but to avoid the race entirely, stop the dev server first and prefer scoped `CHANGE` ops for single-widget edits.
- **UPGRADE** — `{ "projectDir": "...", "op": "UPGRADE" }` (no target/metric; run it as a lone op, never batched). Refreshes the disposable scaffold framework to the current version, migrates `intent.json`, regenerates all widgets/views from persisted metadata + on-disk modules, re-validates (Stage A + full tsc), and re-stamps `state.versions`. Preserves `intent.json`, `src/metrics/*.ts`, and `uipath.json` (the SDK config incl. deploy `clientId`). See "Offer-on-detect upgrade" below.
- **EJECT** — `{ "projectDir": "...", "op": "EJECT" }` (lone op, never batched). Flips `state.regime` to `"ejected"` and emits `EJECTED` — no files regenerated. One-way: after this the edit-script refuses (`EJECTED_PROJECT`) and you edit `src/` directly + `npm run build`. Use when a request exceeds the declarative surface. See [customization.md](customization.md#regimes-compiler-managed-vs-ejected).

A single-op shorthand (`{ "op": "ADD", "projectDir": "...", "metric": ... }`) is also accepted.

## Run command

Run from **inside the project directory** (the one holding `.dashboard/state.json` — reference it relatively, e.g. `cd <ROUTING_NAME>`, never a retyped `/tmp/…` path), with `edit-intent.json` written there and `"projectDir": "."`:

```bash
cd "<PROJECT_DIR>" && node "${SKILL_BASE_DIR}/assets/scripts/dashboards/build-dashboard.mjs" edit-intent.json
```

The script resolves both `projectDir` (`.`) and the relative `edit-intent.json` against this directory, so there is no absolute sandbox path to mistype. (`${SKILL_BASE_DIR}` is the skill's own install dir — unrelated to the project — and is safe to use as-is.)

## CHANGE semantics

Each widget's full intent metric (title, display hints) is persisted in `state.json` at build time. CHANGE merges your `delta` over it, so a delta only needs the fields that change. The data-fetch code lives in the on-disk `src/metrics/<name>.ts` module.

1. **Changing the time window requires a new module.** The module imports time constants by name (e.g. `THIRTY_DAYS_AGO`) from `@/lib/time` — a `timeRange` delta alone updates the subtitle but not the query window. Ship an updated `metrics/<name>.ts` using the matching constant (`SEVEN_DAYS_AGO` for 7d, etc.) alongside the delta.
2. Changing `displayAs` between chart ↔ table/kpi is supported — the build regenerates or removes the detail view accordingly.
3. **Legacy dashboards** (built before intent persistence) have no stored `intentMetric` — the build fails with a clear message; include the full metric (title, display hints) in `delta` and ship a fresh module, or re-run a fresh build.

## Stage A type-check

Before applying any op, the build type-checks all affected `metrics/*.ts` modules in isolation (Stage A).
- `METRICS_PASS` — silent; batch proceeds.
- `METRICS_RETRY:{ files: [...], errors: [...] }` — fix the named `src/metrics/<name>.ts` files and re-run. Max 2 attempts; if still failing, drop the metric.

## Events to watch

- `HAND_EDIT_DETECTED:{"widget":"X"}` — file was hand-edited; the whole batch is rejected before any write. Ask the user (see [customization.md](customization.md)).
- `METRICS_PASS` — silent; proceed
- `METRICS_RETRY:{"files":[...],"errors":[...]}` — fix named module files and re-run
- `TSC_PASS` — edit validated clean
- `TSC_FAIL:{"errors":"..."}` — surface to user
- `INCREMENTAL_READY:{"count":N,"ops":[{"op":"ADD","widget":"X"},…]}` — done; the running dev server hot-reloads automatically. If no dev-server background job is running, start one per `plugins/build/impl.md` Phase 4 Step 3 (the script never starts servers).
- `UPGRADE_AVAILABLE:{"from":"1.0.0","to":"1.1.0"}` — the shipped scaffold is newer than this dashboard's. Offer to upgrade (below) — never auto-upgrade.
- `UPGRADE_DONE:{"to":"1.1.0","widgets":[...]}` — upgrade complete; the dev server hot-reloads.
- `EJECTED:{"projectDir":"..."}` — eject succeeded; dashboard is now full-source/agent-edited. Stop using the edit-script; edit `src/` + `npm run build`.
- `EJECTED_PROJECT:{"projectDir":"..."}` — you ran the edit-script on an already-ejected project; it refused. Edit source directly instead.

## Offer-on-detect upgrade

Any build or edit against an existing project emits `UPGRADE_AVAILABLE:{from,to}` when its stamped `scaffold` version differs from the one now shipped. Tell the user a newer dashboard scaffold is available and offer to upgrade — same plan→confirm ethos, **never automatic**. On confirm, run a lone `UPGRADE` op. It preserves their metrics (`intent.json` + `src/metrics`) and regenerates the app framework against the current scaffold.

## Rules

0. **Customized project?** If the user hand-edited files (or asks for look-and-feel changes), read [customization.md](customization.md) BEFORE running any edit-intent — the build regenerates `Dashboard.tsx` + `widgets/index.ts` on every op and would wipe their changes.
1. Only regenerate affected widget files — never the full scaffold.
1b. **Batch every multi-widget request into one `ops` array** ("convert everything to charts" = one run with N CHANGE ops, not N runs). One layout regen, one tsc.
2. Routing name never changes on edit.
3. After REMOVE or CHANGE: always regenerate Dashboard.tsx and widgets/index.ts (the build does this automatically).
4. Chart widgets get their detail view regenerated on ADD/CHANGE/REBUILD automatically — never hand-create views.
5. Do not touch `uipath.json` unless user explicitly requests a config change.
6. **Never reconstruct the project's absolute path.** Run the edit from inside the project (`cd <ROUTING_NAME>`, `"projectDir": "."`, relative `edit-intent.json`). A retyped `/tmp/…` sandbox path — off by even one character (`_`↔`-`) — writes the edit to a sibling directory, so it silently no-ops. See § edit-intent.json schema (Path safety).
