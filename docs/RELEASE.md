# Releasing the skills package

The whole skills repo is published as an npm package, **`@uipath/skills`**, versioned in lockstep with **`@uipath/cli`** so a given CLI release always resolves to a compatible skills package.

## Version model

`package.json` `version` is the **single source of truth** for the npm package. `scripts/sync-version.mjs` derives these manifests from it (do not edit by hand):

| File | Field | Purpose |
|------|-------|---------|
| `version-manifest.json` | `skillsVersion`, `targetCli` | CLI↔skills pairing record |
| `.claude-plugin/plugin.json` | `version` | Claude Code plugin version — always equals `package.json`'s base `M.N.P` (pre-release suffix stripped) — the canonical plugin version |
| `.claude-plugin/marketplace.json` | `plugins[0].version` | Always equals `plugin.json` `version` |
| `.codex-plugin/plugin.json` | `version` | Codex plugin version — always equals `plugin.json` `version` |

### One version line

All channels carry `package.json`'s version; only the alpha track adds a pre-release stamp:

| Channel | Version | Cadence |
|---------|---------|---------|
| npm `latest` | `M.N.<release>` | per stable release — what the CLI pins |
| npm `alpha` | `M.N.<release>-alpha.<date>.<run>` | per alpha dispatch (stamp never committed) |
| plugin manifests (`.claude-plugin/plugin.json`, `marketplace.json`, `.codex-plugin/plugin.json`) | `M.N.<release>` (base version, no pre-release suffix) | per `package.json` bump — drives Claude Code / Codex plugin auto-update |

`sync-version.mjs` enforces the line: the plugin version always equals `package.json`'s base `M.N.P` — there is **no independent plugin patch counter**. It **refuses to downgrade** (plugin auto-update never goes backwards, so a reverted `package.json` would freeze users), and it strips pre-release suffixes so the alpha stamp from `publish.yml` never lands in the plugin manifests. The marketplace and Codex versions must always equal the plugin version exactly. `--check` fails on any violation, so a hand-bumped plugin manifest cannot drift the line. To bump the plugin version, bump `package.json` and run the sync — that is the only lever.

Run after any version change:

```bash
npm run version:sync      # rewrite derived manifests from package.json
npm run version:check     # CI guard — non-zero exit if drifted
```

### Why lockstep with the CLI

The version line mirrors the CLI's `MAJOR.MINOR` (e.g. CLI `1.197.x` → skills `1.197.x`). `version-manifest.json.targetCli` records the matching line as `^MAJOR.MINOR.0`. The CLI pins this line, so it never pulls a skills package from a different minor.

> **The CLI resolves `@uipath/skills` from npm, matched to its own minor line.** `uip skills install` lists the published versions and picks the one matching the CLI's `MAJOR.MINOR` (`packages/cli/src/commands/skills/contentStore.ts` → `fetchMatchingSkillsPackageInfo` / `pickMatchingSkillsVersion`, registry `registry.npmjs.org`), then fetches that tarball into the content store. So a given CLI release always resolves a compatible skills package and the loop this section describes is closed — for the `uip skills install` **content** path. The Claude Code / Codex plugin marketplace is a **separate** channel (a git ref, not the npm package); its manifests carry the package version, so bumping `package.json` (plus `version:sync`) is what drives plugin auto-update.

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

## Cutting a stable release

1. Bump `package.json` to the target version (match the CLI minor line), run `npm run version:sync`, merge.
2. Create a GitHub Release tagged `v<version>` → `publish.yml` publishes to npmjs.

### Automated sprint cut (`sprint-release-cut.yml`)

Steps 1–2 are automated per sprint by `sprint-release-cut.yml`. It runs **Sunday 06:00 UTC**, gated to the **14-day cadence** anchored at `2026-06-14` — the same cadence as `UiPath/cli`, but **6 hours earlier** so the skills package lands before the CLI release. It is **self-driven**: the target line is the current skills minor **+ 1**; it never reads the CLI version (skills lead, never follow), so no cross-repo secret is required. On a release Sunday it:

1. cuts `release/v<minor>` from `main` at `M.N.0` (`sync-version.mjs` resets plugin/marketplace/Codex to `M.N.0` too);
2. publishes `@uipath/skills@M.N.0` to npm `latest` — creates the GitHub Release `v<minor>.0` as the durable record, then **dispatches `publish.yml` on the tag** (`gh workflow run publish.yml --ref v<minor>.0 -f target=npmjs`). A release created with the default `GITHUB_TOKEN` does not trigger other workflows, so `release: published` would never start `publish.yml`; the explicit `workflow_dispatch` (which `GITHUB_TOKEN` *can* trigger) is what publishes. Guarded on `npm view` so a re-run doesn't re-dispatch an already-published version;
3. opens the matching version-bump PR against `main`.

Off-cadence or ad-hoc cut: dispatch manually with `minor_override` (e.g. `1.198`) to skip the gate and the auto-increment, or `dry_run` to print the plan without pushing.

> **Drift realignment.** The skills and CLI lines stay paired only because both cut on the same 14-day anchor; nothing reads the other side. If either repo skips a cut or cuts off-cadence, the minors drift permanently. The cut emits a **non-blocking warning** when its target isn't exactly one minor ahead of the CLI's latest npm release (`npm view @uipath/cli`) — the signal that the lines have drifted. **`minor_override` is the realignment lever:** dispatch the cut with `minor_override=<correct M.N>` to skip the gate and the auto-increment and cut exactly that line back into alignment.

> **Operational dependency — merge the bump PR before the next cut.** The target line is `current + 1` read from `main`'s `package.json`. If the bump PR from step 3 is not merged before the next release Sunday, `main` is still on the old line, so the cut re-targets the line it already created: it finds `release/v<minor>` already at `M.N.0` and **resumes idempotently** (skips the publish since npm already has the version, leaves the existing PR open) — no new line is cut. Safe, but a forgotten bump PR silently **stalls the cadence**. Merge sprint-cut bump PRs promptly. (If the branch exists at a *different* version, the cut stops loudly with `already exists at version <X> (expected <Y>)` for manual resolution.)

> **Repo setup:** branch protection must allow the Actions identity to push `release/v*` branches.

## Required setup

- [x] **npmjs Trusted Publishing** — configure a GitHub Actions trusted publisher on the `@uipath/skills` package (npmjs → package → Settings → Trusted Publisher): repository `UiPath/skills`, workflow `publish.yml`. No `NPM_TOKEN` secret is used — the `publish-release` job authenticates via OIDC (`id-token: write`). Do **not** set `NODE_AUTH_TOKEN`; a token makes npm bypass OIDC and (with 2FA) fail `EOTP`.
- [x] Package name/scope confirmed: **`@uipath/skills`** (published).
- [x] Seed version confirmed: **`1.197.0`** (current CLI minor line). The ongoing CLI↔skills lockstep is automated by `sprint-release-cut.yml` (Sunday 06:00 UTC, 6 h before the CLI's own cut, on the same 14-day cadence anchored at `2026-06-14`).

> The alpha track also needs no secret — `publish-alpha` uses the built-in `GITHUB_TOKEN` with `packages: write`.
