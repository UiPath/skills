# Releasing the skills package

The whole skills repo is published as an npm package, **`@uipath/skills`**, versioned in lockstep with **`@uipath/cli`** so a given CLI release always resolves to a compatible skills package.

## Version model

`package.json` `version` is the **single source of truth** for the npm package. `scripts/sync-version.mjs` derives these manifests from it (do not edit by hand):

| File | Field | Purpose |
|------|-------|---------|
| `version-manifest.json` | `skillsVersion`, `targetCli` | CLI↔skills pairing record |
| `.claude-plugin/plugin.json` | `version` | Claude Code plugin version (shared `major.minor`, independent patch) — the canonical plugin version |
| `.claude-plugin/marketplace.json` | `plugins[0].version` | Always equals `plugin.json` `version` |
| `.codex-plugin/plugin.json` | `version` | Codex plugin version — always equals `plugin.json` `version` |

### One `major.minor`, three patch counters

All channels share `major.minor` (the CLI-compatibility signal); the **patch diverges deliberately per channel**:

| Channel | Version | Patch cadence |
|---------|---------|---------------|
| npm `latest` | `M.N.<release>` | per stable release — what the CLI pins |
| npm `alpha` | `M.N.<release>-alpha.<date>.<run>` | per alpha dispatch |
| plugin manifests (`.claude-plugin/plugin.json`, `marketplace.json`, `.codex-plugin/plugin.json`) | `M.N.<daily-counter>` | daily (`daily-version-bump.yml`) — drives Claude Code / Codex plugin auto-update |

`sync-version.mjs` enforces the shared line: if the plugin `major.minor` differs from `package.json`, it resets the plugin version to `M.N.0` (and **refuses to downgrade** if `package.json`'s minor is below the plugin's); if they match, `--bump-patch` advances the daily counter, otherwise the patch is left untouched. The marketplace and Codex versions must always equal the plugin version exactly. `--check` fails on any violation, so a hand-bumped plugin manifest cannot drift the line. The bump rule lives only in `sync-version.mjs` (`daily-version-bump.yml` calls `--bump-patch` rather than reimplementing it).

Run after any version change:

```bash
npm run version:sync      # rewrite derived manifests from package.json
npm run version:check     # CI guard — non-zero exit if drifted
```

### Why lockstep with the CLI

The version line mirrors the CLI's `MAJOR.MINOR` (e.g. CLI `1.197.x` → skills `1.197.x`). `version-manifest.json.targetCli` records the matching line as `^MAJOR.MINOR.0`. The CLI pins this line, so it never pulls a skills package from a different minor.

> **The CLI resolves `@uipath/skills` from npm, matched to its own minor line.** `uip skills install` lists the published versions and picks the one matching the CLI's `MAJOR.MINOR` (`packages/cli/src/commands/skills/contentStore.ts` → `fetchMatchingSkillsPackageInfo` / `pickMatchingSkillsVersion`, registry `registry.npmjs.org`), then fetches that tarball into the content store. So a given CLI release always resolves a compatible skills package and the loop this section describes is closed — for the `uip skills install` **content** path. The Claude Code / Codex plugin marketplace is a **separate** channel (a git ref, not the npm package) and is what the daily plugin-version bump serves.

## Publishing tracks (`.github/workflows/publish.yml`)

| Trigger | Registry | dist-tag | Version |
|---------|----------|----------|---------|
| `workflow_dispatch` (target: `github-alpha`) | GitHub Packages | `alpha` | `<base>-alpha.<YYYYMMDD>.<run_number>` |
| GitHub Release published | npmjs | `latest` | `package.json` version |
| `workflow_dispatch` (target: `npmjs`) | npmjs | `latest` | `package.json` version |

Both tracks are **manually triggered** — there is no auto-publish on push to `main`. Alpha is dispatched on demand; stable runs when a GitHub Release is published. `npm install @uipath/skills` (no tag) always resolves to the last stable npmjs release — alphas live only under the `alpha` tag on GitHub Packages.

### Registry routing

`@uipath/skills` is a **scoped** package, so the publish target is set via the **scoped registry** (`@uipath:registry=<url>`) — not a `--registry` flag (which only sets the *unscoped* default and is ignored for scoped packages). There is **no committed `.npmrc` and no `publishConfig.registry`**: a static scoped-registry line would override the per-job target (and break `npm install` for anyone cloning this public repo).

| Job | registry | Auth |
|-----|----------|------|
| `publish-alpha` | GitHub Packages (`npm.pkg.github.com`) | built-in `GITHUB_TOKEN` |
| `publish-release` | npmjs (`registry.npmjs.org`) | **OIDC trusted publishing** (no token) + signed `--provenance` |

## Marketplace channel (`release/latest`)

The Claude Code marketplace tracks the **latest release branch**, not `main`. Release branches are named per sprint (`release/v1.195` → `release/v1.196`), and a marketplace `ref` is a fixed string — so the marketplace points permanently at the stable ref **`release/latest`**, which always equals the HEAD of the newest `release/v<minor>` branch.

Who moves what:

| Ref | Moved by | How |
|-----|----------|-----|
| `release/v<minor>` | `daily-version-bump.yml` | daily plugin-version bump commit (skipped when nothing landed since the last bump) |
| `release/latest` | `daily-version-bump.yml` | fast-forward to the same commit |
| `release/latest` | sprint release cut (Sunday automation) | **forced ref update** to the new `release/v<minor>` (the new branch does not contain the old line's daily-bump commits; `release/latest` is a pointer, never a base for work) |

`main` gets **no daily plugin bumps** — its plugin version is pinned at `M.N.0` per sprint. Plugin auto-update fires off the `version` field on the tracked ref, so daily bumps land only on the release line. Plugin version monotonicity holds across the sprint handoff (`1.197.0 > 1.196.k`).

Manual marketplace add (when not using `uip skills install`) must pin the ref:

```text
/plugin marketplace add UiPath/skills@release/latest
```

> **Warning:** installs added as bare `UiPath/skills` track `main` and will never see a version bump again — they silently freeze. Re-add with `@release/latest`.

### One-time setup for a new line (or first rollout)

```bash
git push origin main:refs/heads/release/v<minor>
git push origin main:refs/heads/release/latest
```

Branch-protection requirements (repo settings): `release/v*` and `release/latest` must allow direct push by the Actions identity, and `release/latest` must additionally allow **force push** (for the sprint handoff).

## Cutting a stable release

1. Bump `package.json` to the target version (match the CLI minor line), run `npm run version:sync`, merge.
2. Create a GitHub Release tagged `v<version>` → `publish.yml` publishes to npmjs.

## Required setup

- [x] **npmjs Trusted Publishing** — configure a GitHub Actions trusted publisher on the `@uipath/skills` package (npmjs → package → Settings → Trusted Publisher): repository `UiPath/skills`, workflow `publish.yml`. No `NPM_TOKEN` secret is used — the `publish-release` job authenticates via OIDC (`id-token: write`). Do **not** set `NODE_AUTH_TOKEN`; a token makes npm bypass OIDC and (with 2FA) fail `EOTP`.
- [x] Package name/scope confirmed: **`@uipath/skills`** (published).
- [x] Seed version confirmed: **`1.197.0`** (current CLI minor line). Automating the ongoing CLI↔skills lockstep is tracked in PILOT-5518.

> The alpha track also needs no secret — `publish-alpha` uses the built-in `GITHUB_TOKEN` with `packages: write`.
