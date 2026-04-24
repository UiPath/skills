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
Uses `components.json.template` we've already rendered — `--defaults` accepts all defaults (style: default, baseColor: slate, cssVariables: true, rsc: false).

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

### 6. Idempotence check
If called on an existing dir: detect by `<target>/package.json` existence. Delegate to [incremental-editor.md](incremental-editor.md); do NOT re-run steps 1-4.

## Error paths
| Condition | Action |
|---|---|
| Target dir exists with non-empty non-scaffold contents | Ask: "overwrite / pick new name / cancel". |
| `npm install` fails | Surface stderr. Common causes: Node version, `GH_NPM_REGISTRY_TOKEN` env var shadowing `.npmrc`, registry unreachable. |
| `shadcn init` fails | Halt with stderr; link shadcn docs. Don't silent-skip. |
| `shadcn add` fails for a component | Halt; an incomplete UI kit is a worse state than no UI kit. |
| Template substitution leaves `{{placeholder}}` unresolved | Halt; surface the template path + missing var. |
