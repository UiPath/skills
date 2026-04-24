# scaffold

## Purpose
Bootstrap the Vite+React+TypeScript+shadcn/ui+Tailwind project on first Build run. Produce a complete, buildable project tree in a user-chosen directory.

## Inputs
- Target directory (default: `./<state.app.name>/`).
- Resolved state.json (for substitutions in templates).

## Outputs
Rendered project tree per spec §9.

## Rules
1. **Idempotent.** If `<target>/package.json` already exists, this primitive MUST delegate to [incremental-editor.md](incremental-editor.md) instead of re-scaffolding.
2. **Order matters.** Templates → `npm install` → `shadcn init` → `shadcn add` → `.gitignore`. Don't run `shadcn` before `npm install`.
3. **Non-interactive.** Use `npx shadcn@latest init --defaults` and `npx shadcn@latest add --yes <components>` so nothing blocks on user prompts.
4. **Pin shadcn major version in `package.json`** — non-interactive flag behavior can drift across minors.
5. **Never commit `node_modules/` or `dist/`** — gitignore handles this at scaffold time.

## Pipeline

### 1. Render templates
For each file under `assets/templates/scaffold/`:
- Strip `.template` suffix.
- Substitute `{{name}}`, `{{orgName}}`, `{{tenantName}}`, `{{env}}`, `{{baseUrl}}`, `{{routingName}}` from state.json.
- Write to `<target>/<relative-path>`.

### 2. Install deps
```bash
cd <target>
npm install
```
Verify `node_modules/` exists + `@uipath/uipath-typescript` is present.

### 3. Initialize shadcn
**First, remove our pre-rendered `components.json`** — otherwise `shadcn init` sees it and prompts "overwrite? y/N" despite `--yes` (the `--yes` flag does NOT suppress that specific prompt; known shadcn CLI gotcha — agents hang silently waiting for input).

```bash
rm -f <target>/components.json
npx shadcn@latest init --yes --defaults
```

We keep `components.json.template` in the skill for reference only (so contributors can see what we'd configure if we had a choice) — but it's DELETED from the target before `shadcn init` runs so the CLI generates a fresh one matching its current expectations.

**IMPORTANT — `shadcn init` overwrites these files:**
- `src/index.css` → restored in Step 6 (our HSL-space chart tokens; shadcn's grayscale oklch defaults make every chart render black).
- `src/lib/utils.ts` → shadcn regenerates with only `cn()`. We don't fight this. Dashboard primitives (`zeroFill`, `groupBy`, `fetchAllJobs`, `FAULT_STATES`, `formatJobError`, `isoHoursAgo`, `hourBucket`, `percentile`, `delta`, `jobsService`, `agentNameOf`, `jobDurationMs`, `meanOfNumbers`) live in **`src/lib/queries/_shared.ts`** instead — rendered as part of Step 1 via `_shared.ts.template`.
- `components.json` → written fresh.

### 4. Add shadcn components
```bash
npx shadcn@latest add --yes card badge table chart separator skeleton
```

**Note:** `tooltip` is NOT in this list. Recent shadcn versions ship Tooltip as `@base-ui/react` rather than `@radix-ui/react-tooltip`, with breaking API changes (`delayDuration` → `delay`, `asChild` removed). Our `InfoTooltip` chrome component uses a CSS-only tooltip (title attribute + Tailwind hover-peer) to sidestep this churn. If you genuinely need the shadcn Tooltip primitive, `shadcn add tooltip` works but pin shadcn to a Radix-era version or rewrite `InfoTooltip` to the base-ui API.

These are the IN list from [../aesthetic/design-system.md](../aesthetic/design-system.md). Don't add more up front — users can `shadcn add` later if they need.

### 5. Write .gitignore
Append (don't overwrite — scaffold template ships a base):
```
.env.local
.env.production
.uipath-dashboards/
.uipath/
dist/
node_modules/
```

### 6. Restore our `src/index.css` (CRITICAL — runs AFTER shadcn init+add)
Re-render `assets/templates/scaffold/src/index.css.template` → `<target>/src/index.css`, OVERWRITING whatever shadcn wrote. This re-establishes:
- `@tailwind base/components/utilities` (no dead `@import` lines)
- HSL-space CSS vars (`--chart-1: 221 83% 53%` etc.) that match the Tailwind config's `hsl(var(--X))` wrap
- Vibrant chart colors (not the shadcn v4 grayscale defaults)
- Dark-mode overrides

Without this step, every widget's `fill="var(--color-invocations)"` resolves to `hsl(oklch(...))` which is invalid CSS → bars render black, Cards have no borders, `bg-background` / `bg-card` don't apply, dashboard looks entirely unstyled.

**Verify:** `grep -q "221 83% 53%" <target>/src/index.css` should succeed after this step.

### 7. Pin Tailwind v3 (prevent v4 upgrade)
Ensure `<target>/package.json` has `"tailwindcss": "^3.4.13"` in `devDependencies`. If `shadcn init` or `shadcn add` bumped to v4, downgrade:
```bash
npm install --save-dev tailwindcss@^3.4.13
```

Rationale: our `tailwind.config.ts.template` uses v3 syntax (`content: [...]`, `plugins: [require('tailwindcss-animate')]`). Upgrading to v4 requires a different config format; we stay on v3 until the whole toolchain catches up.

### 8. Idempotence check
If called on an existing dir: detect by `<target>/package.json` existence. Delegate to [incremental-editor.md](incremental-editor.md); do NOT re-run steps 1-7.

### 9. End-to-end sanity check (BEFORE handing to dev-server)
After all steps, verify:
1. `<target>/src/index.css` contains `--chart-1: 221 83% 53%` (our HSL, not shadcn's oklch).
2. `<target>/src/index.css` does NOT contain `@import "shadcn/tailwind.css"` or `oklch(` — those are leftover shadcn v4 artifacts that indicate Step 6 didn't run.
3. `<target>/src/components/ui/chart.tsx` exists (shadcn add succeeded).
4. `<target>/node_modules/tailwindcss/package.json` `version` field starts with `3.` (v3, not v4).

If ANY check fails → halt with the exact failed check reported to the user. Do NOT launch `npm run dev` with a broken CSS pipeline — the dashboard will render as unstyled HTML (grayscale bars, no cards, no grid), which is a worse user experience than a loud failure.

## Error paths
| Condition | Action |
|---|---|
| Target dir exists with non-empty non-scaffold contents | Ask: "overwrite / pick new name / cancel". |
| `npm install` fails | Surface stderr. Common causes: Node version, `GH_NPM_REGISTRY_TOKEN` env var shadowing `.npmrc`, registry unreachable. |
| `shadcn init` fails | Halt with stderr; link shadcn docs. Don't silent-skip. |
| `shadcn add` fails for a component | Halt; an incomplete UI kit is a worse state than no UI kit. |
| Template substitution leaves `{{placeholder}}` unresolved | Halt; surface the template path + missing var. |
| Step 9 sanity check fails | Halt; surface the failed check. Do NOT proceed to dev-server. |
