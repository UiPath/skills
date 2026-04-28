# scaffold

## Purpose
Bootstrap the Vite+React+TypeScript+shadcn/ui+Tailwind project on first Build run. Produce a complete, buildable project tree in a user-chosen directory.

> **Implementation note:** the entire pipeline below is encapsulated in `assets/scripts/scaffold-project.sh`. The Build subagent invokes it as a single `Bash` call rather than executing each step via individual tool calls — saves ~60-90 seconds of LLM round-trip latency. The doc below describes the contract; the script is the implementation. See [../plugins/build/impl.md § Subagent throughput discipline](../plugins/build/impl.md) for the broader batching strategy.

## Inputs
- Target directory (default: `./<state.app.name>/`).
- Resolved state.json (for substitutions in templates).

## Outputs
Rendered project tree per spec §9.

## Rules
1. **`<target>` is always `<cwd>/.uipath-dashboards/<app.name>/`.** Never scaffold into the user's cwd directly. The workspace dir `<cwd>/.uipath-dashboards/` is created if it doesn't exist; multiple dashboards share the same workspace.
2. **Idempotent.** If `<target>/package.json` already exists, this primitive MUST delegate to [incremental-editor.md](incremental-editor.md) instead of re-scaffolding. Empty target dirs are FINE — only `package.json` blocks; if you see one without state.json, the project is in a half-built state and the user should clear it manually.
3. **Name collisions get numeric suffixes.** Per [intent-capture.md](intent-capture.md) rule 6, an existing project at `<cwd>/.uipath-dashboards/<name>/` either becomes the incremental target (if user wants update) or the new scaffold gets `-1`, `-2`, etc.
4. **Order matters.** Templates → `npm install` → `shadcn init` → `shadcn add` → restore `index.css`/`tailwind.config.ts`. Don't run `shadcn` before `npm install`.
5. **Non-interactive shadcn.** Use `npx shadcn@latest init --yes --defaults` and `npx shadcn@latest add --yes <components>` so nothing blocks on user prompts.
6. **Pin shadcn major version in `package.json`** — non-interactive flag behavior can drift across minors.
7. **Never commit `node_modules/` or `dist/`** — gitignore handles this at scaffold time.
8. **Per-project state lives at `<target>/.dashboard/state.json`.** NOT `<target>/.uipath-dashboards/state.json` — that path would collide with the OUTER workspace dir. State dir was renamed to `.dashboard/` precisely to avoid this confusion. See [state-file.md](state-file.md).

## Pipeline

### 1. Render templates
For each file under `assets/templates/scaffold/`:
- Strip `.template` suffix.
- Substitute `{{name}}`, `{{orgName}}`, `{{tenantName}}`, `{{env}}`, `{{baseUrl}}`, `{{routingName}}` from state.json.
- Write to `<target>/<relative-path>`.

**Required files in this step include `src/vite-env.d.ts`** — without it, every reference to `import.meta.env.VITE_UIPATH_*` (in `auth-strategy.ts`) fails type-check with `Property 'env' does not exist on type 'ImportMeta'`. Standard Vite practice; the template is in `assets/templates/scaffold/src/vite-env.d.ts.template`.

### 2. Install deps
```bash
cd <target>
npm install
```
Verify `node_modules/` exists and `@uipath/uipath-typescript` (the SDK) is present. Poppins font is loaded via `<link>` in `index.html` from Google Fonts — no third-party design-system stylesheet at runtime, so no `node_modules` check beyond the SDK is required.

### 3. Initialize shadcn
**First, remove the pre-rendered `components.json`** — `shadcn init` prompts "overwrite? y/N" if it exists, despite `--yes` (the `--yes` flag does NOT suppress that specific prompt; known shadcn CLI gotcha — agents hang silently waiting for input).

```bash
rm -f <target>/components.json
npx shadcn@latest init --yes --defaults
```

**`shadcn init` overwrites these files:**
- `src/index.css` → restored in Step 6 (our UiPath-flavored HSL palette + Apollo font import).
- `src/lib/utils.ts` → shadcn regenerates with only `cn()`. Dashboard primitives live in `src/lib/queries/_shared.ts` instead.
- `tailwind.config.ts` → restored in Step 6 (our chart color slots + content paths).
- `components.json` → written fresh by shadcn.

### 4. Add shadcn components
```bash
npx shadcn@latest add --yes card button badge table chart separator skeleton
```

**Note:** `tooltip` is NOT in this list. Recent shadcn versions ship Tooltip as `@base-ui/react` rather than `@radix-ui/react-tooltip`, with breaking API changes. Our `InfoTooltip` chrome component uses a CSS-only Tailwind hover/focus pattern to sidestep this churn.

### 5. Append `.gitignore`
```
.env.local
.env.production
.uipath-dashboards/
.uipath/
dist/
node_modules/
```

### 6. Restore `src/index.css` and `tailwind.config.ts` (CRITICAL — runs AFTER `shadcn init`+`add`)
Re-render these two templates from `assets/templates/scaffold/`, OVERWRITING whatever shadcn wrote:
- `src/index.css` — re-establishes the UiPath-flavored HSL palette (`--primary: 14 96% 53%` for orange `#FA4616`), the chart-1..5 brand-aligned tokens, the dark-mode block (matches both `.dark` and `body.dark` selectors), and the Poppins-first `body` font-family. Poppins itself is loaded by `<link>` tags in `index.html` from Google Fonts — no CSS-side font import.
- `tailwind.config.ts` — re-establishes our `extend.colors.chart` slots, `darkMode: 'class'`, content paths, and `tailwindcss-animate` plugin.

Without this step, shadcn's grayscale `oklch` defaults take over and dashboards lose UiPath branding entirely.

**Verify:** `grep -q "14 96% 53%" <target>/src/index.css` should succeed after this step (the UiPath orange HSL value).

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
1. `<target>/src/index.css` contains `--chart-1: 14 96% 53%` (UiPath orange) and does NOT contain `oklch(` (shadcn's defaults weren't restored).
2. `<target>/index.html` contains `fonts.googleapis.com/css2?family=Poppins` (font preconnect/link present).
3. `<target>/src/components/ui/chart.tsx` exists (shadcn add succeeded).
4. `<target>/node_modules/tailwindcss/package.json` `version` field starts with `3.` (v3, not v4).

If ANY check fails → halt with the exact failed check reported to the user. Do NOT launch `npm run dev` with a broken CSS pipeline — the dashboard will render unstyled (no Apollo tokens, grayscale charts), which is a worse user experience than a loud failure.

## Error paths
| Condition | Action |
|---|---|
| Target dir exists with non-empty non-scaffold contents | Ask: "overwrite / pick new name / cancel". |
| `npm install` fails | Surface stderr. Common causes: Node version, registry unreachable. |
| `shadcn init` fails | Halt with stderr; link shadcn docs. Don't silent-skip. |
| `shadcn add` fails for a component | Halt; an incomplete UI kit is a worse state than no UI kit. |
| Template substitution leaves `{{placeholder}}` unresolved | Halt; surface the template path + missing var. |
| Step 9 sanity check fails | Halt; surface the failed check. Do NOT proceed to dev-server. |
