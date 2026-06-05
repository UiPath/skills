# Releasing the skills package

The whole skills repo is published as an npm package, **`@uipath/skills`**, versioned in lockstep with **`@uipath/cli`** so a given CLI release always resolves to a compatible skills package.

## Version model

`package.json` `version` is the **single source of truth** for the npm package. `scripts/sync-version.mjs` derives this manifest from it (do not edit by hand):

| File | Field | Purpose |
|------|-------|---------|
| `version-manifest.json` | `skillsVersion`, `targetCli` | CLI↔skills pairing record |

> **Not yet unified:** `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` stay on their own version track (bumped daily by `daily-version-bump.yml`) until the alignment task lands. Unifying them under this scheme is tracked separately — see the linked Jira task in PR #1283.

Run after any version change:

```bash
npm run version:sync      # rewrite derived manifests from package.json
npm run version:check     # CI guard — non-zero exit if drifted
```

### Why lockstep with the CLI

The version line mirrors the CLI's `MAJOR.MINOR` (e.g. CLI `1.196.x` → skills `1.196.x`). `version-manifest.json.targetCli` records the matching line as `^MAJOR.MINOR.0`. The CLI pins this line, so it never pulls a skills package from a different minor.

> **Today the CLI clones `main` directly** (`packages/cli/src/commands/skills/contentStore.ts` → `REPO_URL` / `ZIP_URL`). That is the mismatch source: any CLI version gets whatever is on `main` at install time. Switching that consumption path to install the pinned `@uipath/skills` version is the **CLI-side change** that closes the loop — tracked as a decision below, not yet done.

## Publishing tracks (`.github/workflows/publish.yml`)

| Trigger | Registry | dist-tag | Version |
|---------|----------|----------|---------|
| Push to `main` | GitHub Packages | `alpha` | `<base>-alpha.<YYYYMMDD>.<run_number>` |
| GitHub Release published | npmjs | `latest` | `package.json` version |
| `workflow_dispatch` | either (input) | matching | as above |

`npm install @uipath/skills` (no tag) always resolves to the last stable npmjs release — alphas live only under the `alpha` tag on GitHub Packages. This mirrors `@uipath/cli`'s `ci.yml` (alpha on merge) + `publish-npm.yml` (stable on release).

## Cutting a stable release

1. Bump `package.json` to the target version (match the CLI minor line), run `npm run version:sync`, merge.
2. Create a GitHub Release tagged `v<version>` → `publish.yml` publishes to npmjs.

## Required secrets / setup (TODO before first publish)

- [ ] **`NPM_TOKEN`** — npmjs automation token with publish rights to the `@uipath` scope (for stable releases).
- [ ] **`GH_WRITE_TOKEN`** — token with `packages: write` for GitHub Packages alpha publishing (the CLI repo already uses a secret of this name).
- [ ] Confirm the npm package name/scope: **`@uipath/skills`** (assumed).
- [ ] Seed version: currently **`1.196.0`** to match the CLI's current line — adjust if a different starting point is wanted.
