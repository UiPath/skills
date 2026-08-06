# Releasing the skills packages

The complete default tree is published as **`@uipath/skills`**, versioned in lockstep with **`@uipath/cli`** so a given CLI release always resolves to a compatible skills package. Every directory under `skill-flavors/` also builds a marker-free package at the same version. Flavor publication is deliberately separate from the established default-package release path.

## Version model

`package.json` `version` is the **single source of truth** for every generated npm package. `scripts/sync-version.mjs` derives these manifests from it (do not edit by hand):

| File | Field | Purpose |
|------|-------|---------|
| `version-manifest.json` | `skillsVersion`, `targetCli` | CLI↔skills pairing record |
| `.claude-plugin/plugin.json` | `version` | Claude Code plugin version — always equals `package.json`'s base `M.N.P` (pre-release suffix stripped) — the canonical plugin version |
| `.claude-plugin/marketplace.json` | `plugins[0].version` | Always equals `plugin.json` `version` |
| `.codex-plugin/plugin.json` | `version` | Codex plugin version — always equals `plugin.json` `version` |

### One version line

All channels carry `package.json`'s version; the pre-release channels (`dev`, `preview`) add a stamp that is never committed:

| Package or manifest | Channel | Registry | Version | Cadence |
|---------------------|---------|----------|---------|---------|
| `@uipath/skills` | `latest` | npmjs | `M.N.<release>` | per stable release — what the CLI pins |
| `@uipath/skills` | `preview` | npmjs | `M.N.<release>-preview.<run>` | per push to `release/v*`, or preview dispatch |
| `@uipath/skills` | `dev` | GitHub Packages | `M.N.<release>-dev.<run>` | per push to `main`, or dev dispatch |
| `@uipath/skills-studioweb` | `preview` | GitHub Packages | `M.N.<release>-preview.<run>` | per push to `release/v*`, or preview dispatch |
| `@uipath/skills-studioweb` | `dev` | GitHub Packages | `M.N.<release>-dev.<run>` | per push to `main`, or dev dispatch |
| plugin manifests (`.claude-plugin/plugin.json`, `marketplace.json`, `.codex-plugin/plugin.json`) | — | — | `M.N.<release>` (base version, no pre-release suffix) | per `package.json` bump — drives Claude Code / Codex plugin auto-update |

`sync-version.mjs` enforces the line: the plugin version always equals `package.json`'s base `M.N.P` — there is **no independent plugin patch counter**. It **refuses to downgrade** (plugin auto-update never goes backwards, so a reverted `package.json` would freeze users), and it strips pre-release suffixes so the `dev`/`preview` stamps from `publish.yml` never land in the plugin manifests. The marketplace and Codex versions must always equal the plugin version exactly. `--check` fails on any violation, so a hand-bumped plugin manifest cannot drift the line. To bump the plugin version, bump `package.json` and run the sync — that is the only lever.

Run after any version change:

```bash
npm run version:sync      # rewrite derived manifests from package.json
npm run version:check     # CI guard — non-zero exit if drifted
```

### Why lockstep with the CLI

The version line mirrors the CLI's `MAJOR.MINOR` (e.g. CLI `1.197.x` → skills `1.197.x`). `version-manifest.json.targetCli` records the matching line as `^MAJOR.MINOR.0`. The CLI pins this line, so it never pulls a skills package from a different minor.

> **The CLI resolves `@uipath/skills` from npm, matched to its own minor line.** `uip skills install` lists the published versions and picks the one matching the CLI's `MAJOR.MINOR` (`packages/cli/src/commands/skills/contentStore.ts` → `fetchMatchingSkillsPackageInfo` / `pickMatchingSkillsVersion`, registry `registry.npmjs.org`), then fetches that tarball into the content store. So a given CLI release always resolves a compatible skills package and the loop this section describes is closed — for the `uip skills install` **content** path. The Claude Code / Codex plugin marketplace is a **separate** channel (a git ref, not the npm package); its manifests carry the package version, so bumping `package.json` (plus `version:sync`) is what drives plugin auto-update.

### Flavor package convention

There is no package registry file. The source directory is the package identity:

| Source | npm package |
|--------|-------------|
| canonical `skills/` | `@uipath/skills` |
| `skill-flavors/studioweb/` | `@uipath/skills-studioweb` |
| `skill-flavors/<flavor>/` | `@uipath/skills-<flavor>` |

`npm run skills:pack` discovers every flavor, builds complete files first, stages the packages under `build/packages/`, and creates verified tarballs under `build/npm/`. The default package preserves the existing hooks, commands, plugin metadata, and assets, but its `skills/` directory comes from the marker-free `build/skills/default` tree. Every custom package contains the complete canonical skill catalog with its sparse flavor replacements applied, plus minimal package/legal metadata.

The established repository-root commands remain supported. Normal `npm pack` builds exactly one marker-free `@uipath/skills` default tarball, and normal `npm publish` publishes that default package using the caller's registry, tag, access, and provenance flags. A `prepack`/`postpack` transaction temporarily activates the composed default tree and restores the exact canonical `skills/` source afterward. If npm fails or is interrupted between those steps and `build/.root-pack-transaction` remains, confirm the original npm process has ended, run `npm run skills:recover`, and retry. Recovery restores canonical sources; unexpected overlay edits are preserved under `build/.root-pack-recovery-*` and make recovery exit nonzero for explicit review. Do not use `--ignore-scripts` for source-repository packaging because that npm option deliberately bypasses composition. The default jobs in `publish.yml` retain these root `npm publish` commands and never run the all-flavor package loop.

All generated packages use the root `package.json` version. Adding a valid `skill-flavors/<new-flavor>/` directory with at least one sparse override therefore makes `@uipath/skills-<new-flavor>` buildable without changing composer code, npm scripts, or validation CI. It does **not** publish the new package automatically. Each published flavor needs an explicit isolated release path so its registry and channel policy can be reviewed independently.

Studio Web is the first isolated flavor publisher. `publish.yml` calls `.github/workflows/publish-studioweb.yml` in the same workflow run so both paths derive the same stamped version from `github.run_number`. The called workflow builds all packages but selects exactly one tarball whose manifest has both `name: @uipath/skills-studioweb` and `uipathSkillsFlavor: studioweb`, scans that exact archive for flavor markers, and publishes only the selected path. Studio Web goes only to GitHub Packages: `dev` from `main` and `preview` from `release/v*`; it is never published to npmjs or `latest`.

## Publishing tracks (`.github/workflows/publish.yml`)

Registry follows channel — you pick a channel, not a registry.

| Package | Trigger | Channel | Registry | dist-tag | Version | Provenance |
|---------|---------|---------|----------|----------|---------|------------|
| default | push to `main` (normally a merge) | `dev` | GitHub Packages | `dev` | `<base>-dev.<run_number>` | no¹ |
| default | push to `release/v*` (normally a merge) | `preview` | npmjs | `preview` | `<base>-preview.<run_number>` | yes |
| default | `workflow_dispatch` (channel: `dev`) | `dev` | GitHub Packages | `dev` | `<base>-dev.<run_number>` | no¹ |
| default | `workflow_dispatch` (channel: `preview`) | `preview` | npmjs | `preview` | `<base>-preview.<run_number>` | yes |
| default | `workflow_dispatch` (channel: `latest`) | `latest` | npmjs | `latest` | `package.json` version | yes |
| Studio Web | push to `main` or dispatch `dev` | `dev` | GitHub Packages | `dev` | `<base>-dev.<run_number>` | no¹ |
| Studio Web | push to `release/v*` or dispatch `preview` | `preview` | GitHub Packages | `preview` | `<base>-preview.<run_number>` | no¹ |

¹ GitHub Packages does not support npm provenance attestations; only the npmjs channels are signed.

**Two default-package channels publish automatically** (mirroring `UiPath/cli`): every push to `main` (normally a merge) publishes a default `dev` build to GitHub Packages, and every push to a `release/v*` branch publishes a default `preview` build to npmjs. The same run invokes the isolated Studio Web publisher for its GitHub Packages `dev` or `preview` counterpart. `latest` (stable) is published **only** for the default package by an explicit `channel=latest` dispatch — there is no `release:` trigger, so creating a GitHub Release does not publish anything. `npm install @uipath/skills` (no tag, from npmjs) always resolves the last stable release. The `preview`/`dev` version suffix (`<base>-preview.<run_number>` / `<base>-dev.<run_number>`) matches the CLI's stamping scheme exactly.

### Cutting a preview

**Every push to a `release/v*` branch auto-publishes a preview** (normally after a merge; see the tracks table) — this is the normal path, mirroring `UiPath/cli`. To cut one ad hoc from any ref, dispatch with channel `preview`:

```bash
gh workflow run publish.yml --ref release/v<minor> -f channel=preview
```

Either way the default job stamps `<base>-preview.<run_number>` (never committed), runs `sync-version.mjs`, and publishes to the npmjs `preview` dist-tag with `--provenance` via the same OIDC job as `latest`. The isolated Studio Web job derives the identical version and publishes it to the GitHub Packages `preview` tag without provenance. Consume the default with `npm install @uipath/skills@preview`. Each run gets a unique version from `run_number`; the tags advance to the newest one in their respective registries.

### The `dev` channel (GitHub Packages)

Every push to `main` (normally a merge) publishes both `@uipath/skills@<base>-dev.<run_number>` and `@uipath/skills-studioweb@<base>-dev.<run_number>` to **GitHub Packages** under the `dev` dist-tag. The default package uses the established root publish job; Studio Web uses its isolated called workflow. Both use the built-in `GITHUB_TOKEN` (`packages: write`) and carry no provenance because GitHub Packages does not support it. Consume the default from GitHub Packages with `npm install @uipath/skills@dev`. Publishes are serialized by a `concurrency` group so back-to-back pushes do not race on the `dev` tag. Re-run a publish manually with `gh workflow run publish.yml --ref main -f channel=dev`.

### Registry routing

Both released packages are under the **`@uipath` scope**, so the publish target is set via the **scoped registry** (`@uipath:registry=<url>`) — not a `--registry` flag (which only sets the *unscoped* default and is ignored for scoped packages). There is **no committed `.npmrc` and no `publishConfig.registry`**: a static scoped-registry line would override the per-job target.

| Job | registry | Auth |
|-----|----------|------|
| `publish-dev` | GitHub Packages (`npm.pkg.github.com`) | built-in `GITHUB_TOKEN` |
| `publish-npmjs` | npmjs (`registry.npmjs.org`) | **OIDC trusted publishing** (no token) + signed `--provenance` |
| `publish-studioweb.yml` / `publish` | GitHub Packages (`npm.pkg.github.com`) only | built-in `GITHUB_TOKEN` |

## Promoting a line to stable (manual)

Stable (`latest`) is **not** published automatically — the sprint cut publishes only prerelease `dev` and `preview` builds (below). When a release line has been validated via its preview builds, promote it to stable manually:

1. Dispatch the stable publish on the release branch (or its tag):
   ```bash
   gh workflow run publish.yml --ref release/v<minor> -f channel=latest
   ```
   This publishes the exact committed `package.json` version to npm `latest` via OIDC + `--provenance`.
2. (Optional) Create a GitHub Release tagged `v<version>` as a durable changelog record. This is **just a record** — there is no `release:` trigger, so it does **not** publish anything to npm; the dispatch in step 1 is what publishes.

> **Lockstep note.** The CLI resolves `@uipath/skills` from npm `latest` for its own minor line. Because stable is now manual, **promote the matching skills line to stable before the CLI cuts that minor**, or the CLI will resolve the previous skills minor.

### Automated sprint cut (`sprint-release-cut.yml`)

`main` carries the line **currently in development** (`M.N.0`). The cut runs **Sunday 06:00 UTC**, gated to the **14-day cadence** anchored at `2026-06-14` — the same cadence as `UiPath/cli`, 6 hours earlier. It never reads the CLI version (skills lead, never follow), so no cross-repo secret is required. On a release Sunday it:

1. cuts `release/v<M.N>` from `main` at the version **already in `main`** (`M.N.0`) — the release branch matches main; it is **not** bumped (no off-by-one);
2. publishes a **dev build and a preview**, and waits for both workflow runs — dispatches `publish.yml` twice on the release branch. `channel=dev` publishes default and Studio Web `M.N.0-dev.<run>` packages to GitHub Packages. `channel=preview` publishes the default `M.N.0-preview.<run>` package to npmjs with provenance and the Studio Web package at the identical version to GitHub Packages without provenance. Both dispatches are explicit because the bot's own branch push can't trigger `publish.yml` (`GITHUB_TOKEN` recursion guard). A failed publish keeps the cut run red and is recorded in the bump PR warning. **Stable is not published here** — promote it manually (above);
3. **opens a PR** bumping `main` to the **next** line (`M.(N+1).0`) whenever the release branch was cut successfully, even if publication failed. A publish failure adds an explicit warning so a maintainer can verify or retry it before approving the bump; merging the PR advances `main` while `release/v<M.N>` stabilizes.

Off-cadence or ad-hoc cut: dispatch manually with `minor_override` (e.g. `1.198`) to cut exactly that line, or `dry_run` to print the plan without pushing, publishing, or opening a PR.

> **Line alignment is manual.** The cut does **not** compare itself to the CLI: it publishes a preview, and the preview line legitimately runs 1–2 minors ahead of the CLI's published stable during the RC window (stable is promoted by hand). Alignment between the skills and CLI minor lines is therefore a manual decision made at **stable-promotion** time, not at cut time. If a line ever needs to be cut out of the normal sequence, `minor_override=<M.N>` cuts exactly that line.

> **Idempotent resume.** The line to cut is read from `main`'s `package.json`; `main` advances only when the bump PR (step 3) is merged, so once merged the next sprint's `main` line is a fresh line. If a run fails after cutting the branch, the next run finds `release/v<M.N>` already at `M.N.0` and **resumes** (re-publishes, re-opens the bump PR) — no new line is cut. (If the branch exists at a *different* version, the cut stops loudly with `already exists at version <X> (expected <Y>)` for manual resolution.) **Merge the bump PR before the next cut** — until it merges, `main` stays on the old line and the cut keeps re-targeting it.

> **Repo setup:** branch protection must allow the Actions identity (`github-actions[bot]`) to push `release/v*` branches. `main` is intentionally **not** pushable by the bot — the cut opens a PR for it (below).

> **Automating the bump (optional).** `main` is protected (PR + 1 approval + smoke-test checks) on a public repo, so the cut opens a bump PR that a maintainer merges — no bypass credential is introduced. A PR opened by the built-in `GITHUB_TOKEN` does **not** trigger the required check workflows, so a maintainer may need to reopen/re-run them before merge. To make the bump fully hands-off, create a scoped **GitHub App**, add it to the `main` ruleset bypass, and have step 3 mint a short-lived token (`actions/create-github-app-token`) to open the PR (its checks run) and `gh pr merge --auto` it — App tokens are short-lived and repo-scoped, unlike a personal PAT. This is the only safe route to full automation; do **not** store a long-lived PAT for it.

## Required setup

- [x] **npmjs Trusted Publishing for the default package** — configure a GitHub Actions trusted publisher on `@uipath/skills` (npmjs → package → Settings → Trusted Publisher): repository `UiPath/skills`, workflow `publish.yml`. No `NPM_TOKEN` secret is used — the default `publish-npmjs` job authenticates via OIDC (`id-token: write`). Do **not** set `NODE_AUTH_TOKEN`; a token makes npm bypass OIDC and (with 2FA) fail `EOTP`.
- [x] **Studio Web registry isolation** — `@uipath/skills-studioweb` is released only through `publish-studioweb.yml` to GitHub Packages with `GITHUB_TOKEN`. It requires no npmjs package, trusted publisher, OIDC permission, or provenance configuration.
- [x] Package name/scope confirmed: **`@uipath/skills`** (published).
- [x] **Version source confirmed** — `package.json` and `version-manifest.json` are authoritative for the current CLI minor line; do not copy a volatile version number into this checklist. The ongoing CLI↔skills lockstep is automated by `sprint-release-cut.yml` (Sunday 06:00 UTC, 6 h before the CLI's own cut, on the same 14-day cadence anchored at `2026-06-14`).

> The `dev` channel also needs no secret — `publish-dev` uses the built-in `GITHUB_TOKEN` with `packages: write`.
