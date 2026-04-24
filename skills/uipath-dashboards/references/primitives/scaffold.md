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
```bash
npx shadcn@latest init --defaults
```
Uses `components.json.template` we've already rendered — `--defaults` accepts all defaults.

**IMPORTANT:** `shadcn init` **overwrites `src/index.css`** with the current shadcn defaults (as of shadcn v5 / Tailwind v4 these are `oklch(L 0 0)` grayscale values, with dead `@import` lines to `tw-animate-css`, `shadcn/tailwind.css`, `@fontsource-variable/geist`). Do NOT accept that file as-is — Step 6 below restores our HSL-space vars that match the Tailwind config's `hsl(var(--X))` wrap.

### 4. Add shadcn components
```bash
npx shadcn@latest add --yes card badge table chart tooltip separator skeleton
```
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
