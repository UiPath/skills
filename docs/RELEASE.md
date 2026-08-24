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
| `.cursor-plugin/plugin.json` | `version` | Cursor plugin version — always equals `plugin.json` `version` |

### One version line

All channels carry `package.json`'s version; the pre-release channels (`dev`, `preview`) add a stamp that is never committed:

| Package or manifest | Channel | Registry | Version | Cadence |
|---------------------|---------|----------|---------|---------|
| `@uipath/skills` | `latest` | npmjs | `M.N.<release>` | per stable release — what the CLI pins |
| `@uipath/skills` | `preview` | npmjs | `M.N.<release>-preview.<run>` | per push to `release/v*`, or preview dispatch |
| `@uipath/skills` | `dev` | GitHub Packages | `M.N.<release>-dev.<run>` | per push to `main`, or dev dispatch |
| `@uipath/skills-studioweb` | `preview` | GitHub Packages | `M.N.<release>-preview.<run>` | per push to `release/v*`, or preview dispatch |
| `@uipath/skills-studioweb` | `dev` | GitHub Packages | `M.N.<release>-dev.<run>` | per push to `main`, or dev dispatch |
| plugin manifests (`.claude-plugin/plugin.json`, `marketplace.json`, `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json`) | — | — | `M.N.<release>` (base version, no pre-release suffix) | per `package.json` bump — drives Claude Code / Codex / Cursor plugin auto-update |

`sync-version.mjs` enforces the line: the plugin version always equals `package.json`'s base `M.N.P` — there is **no independent plugin patch counter**. It **refuses to downgrade** (plugin auto-update never goes backwards, so a reverted `package.json` would freeze users), and it strips pre-release suffixes so the `dev`/`preview` stamps from `publish.yml` never land in the plugin manifests. The marketplace, Codex, and Cursor versions must always equal the plugin version exactly. `--check` fails on any violation, so a hand-bumped plugin manifest cannot drift the line. To bump the plugin version, bump `package.json` and run the sync — that is the only lever.

Run after any version change:

```bash
npm run version:sync      # rewrite derived manifests from package.json
npm run version:check     # CI guard — non-zero exit if drifted
node scripts/sync-version.mjs --list-paths   # the file set this script owns
```

`--list-paths` prints `package.json` plus every derived manifest, one
repo-relative path per line. `sprint-release-cut.yml` stages exactly that set
when it commits a bump, so adding a channel to `PATHS` is picked up by release
automation with no second edit — a hardcoded `git add` list is what dropped
`.cursor-plugin/plugin.json` from the 1.201 cut.

`version:check` runs in two places. `validate-version-sync.yml` runs it on every
pull request, so drift fails pre-merge. The `guard` job in `publish.yml` runs it
again on merge; because every publish job declares `needs: [guard]`, a single
stale manifest blocks `dev`, `preview`, and every flavor package at once — with
no failure louder than nothing shipping. **A PR that adds a new derived manifest
to `PATHS` in `sync-version.mjs` must run `npm run version:sync` as its last
step before merge**, or it lands the stale value together with the check that
rejects it. Staging in release automation needs no matching edit — it reads
`--list-paths`.

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

`npm run skills:pack` discovers every flavor, builds complete files first, stages the packages under `build/packages/`, and creates verified tarballs under `build/npm/`. The default package preserves the existing hooks, commands, plugin metadata, and assets, but its `skills/` directory comes from the marker-free `build/skills/default` tree. Every custom package contains the complete canonical skill catalog with its sparse flavor replacements applied, plus minimal package/legal metadata. Custom manifests omit `package.json.repository` and pin both the default and `@uipath` scoped registry to `https://npm.pkg.github.com/`; the scoped pin prevents an ambient `@uipath` npmjs setting from redirecting an ordinary publish. The default manifest and root publishing behavior remain unchanged.

The established repository-root commands remain supported. Normal `npm pack` builds exactly one marker-free `@uipath/skills` default tarball, and normal `npm publish` publishes that default package using the caller's registry, tag, access, and provenance flags. A `prepack`/`postpack` transaction temporarily activates the composed default tree and restores the exact canonical `skills/` source afterward. If npm fails or is interrupted between those steps and `build/.root-pack-transaction` remains, confirm the original npm process has ended, run `npm run skills:recover`, and retry. Recovery restores canonical sources; unexpected overlay edits are preserved under `build/.root-pack-recovery-*` and make recovery exit nonzero for explicit review. Do not use `--ignore-scripts` for source-repository packaging because that npm option deliberately bypasses composition. The default jobs in `publish.yml` retain these root `npm publish` commands and never run the all-flavor package loop.

All generated packages use the root `package.json` version. Adding a valid `skill-flavors/<new-flavor>/` directory with at least one sparse override therefore makes `@uipath/skills-<new-flavor>` buildable without changing composer code, npm scripts, or validation CI. It does **not** publish the new package automatically. Each published flavor needs an explicit caller and reviewed registry/channel policy; GitHub Packages `dev`/`preview` callers reuse the generic flavor publisher.

Studio Web is the first explicit caller of the generic flavor publisher. `publish.yml` calls `.github/workflows/publish-skill-flavor.yml` with `flavor: studioweb` in the same workflow run so both paths derive the same stamped version from `github.run_number`. The reusable workflow accepts only a flavor and channel, validates the flavor, derives `@uipath/skills-<flavor>` through the composer package-name contract, builds all packages, and selects exactly one tarball with the expected name, flavor, and version. It scans that exact archive for flavor markers and publishes only the selected path. The reusable workflow is GitHub Packages-only and accepts only `dev` or `preview`; Studio Web is never published to npmjs or `latest`. Its only job is skipped unless the repository variable `ENABLE_SKILL_FLAVOR_PUBLISH` equals exactly `true`; this leaves every default-package job unchanged.

### One-time Internal package bootstrap

Registry routing does not set GitHub package visibility. Keep `ENABLE_SKILL_FLAVOR_PUBLISH` absent or false until an organization owner or package administrator completes this sequence for every flavor with an explicit publish caller:

1. Build the hardened artifacts with `npm run skills:pack`. Confirm the selected custom tarball pins both `publishConfig.registry` and `publishConfig["@uipath:registry"]` to GitHub Packages and has no `repository` field.
2. Authenticate locally with a classic GitHub PAT that has `read:packages` and `write:packages` (and UiPath SSO authorization when required):
   ```bash
   npm login --scope=@uipath --auth-type=legacy --registry=https://npm.pkg.github.com
   ```
3. Create the package with one explicitly routed bootstrap publication. Use the exact filename printed by `skills:pack`, never a wildcard:
   ```bash
   npm publish ./build/npm/uipath-skills-studioweb-<version>.tgz \
     --registry=https://npm.pkg.github.com \
     --tag bootstrap \
     --access restricted
   ```
4. In the UiPath organization package settings, change `@uipath/skills-studioweb` to **Internal** and add `UiPath/skills` under **Manage Actions access** with **Write** access. Confirm that access is not inherited from the public source repository; if the package is linked and the inheritance control is present, disable inheritance or unlink the repository.
5. Only after verifying those settings, set the repository Actions variable `ENABLE_SKILL_FLAVOR_PUBLISH=true`. Normal `dev` and `preview` flavor jobs may then run with `GITHUB_TOKEN`. Log out of the local registry session when finished.

The variable is a global, operator-controlled fail-closed switch for custom flavor publication; it does not query or enforce live GitHub visibility. Before merging a caller for another new flavor, unset or set it to false, bootstrap every newly called package as Internal, and then re-enable it. Never use the existing automatic action for first creation from this public repository, and never set a custom flavor package to Public.

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

**Two default-package channels publish automatically** (mirroring `UiPath/cli`): every push to `main` (normally a merge) publishes a default `dev` build to GitHub Packages, and every push to a `release/v*` branch publishes a default `preview` build to npmjs. When the custom-package gate is enabled after bootstrap, the same run invokes the isolated Studio Web publisher for its GitHub Packages `dev` or `preview` counterpart. `latest` (stable) is published **only** for the default package by an explicit `channel=latest` dispatch — there is no `release:` trigger, so creating a GitHub Release does not publish anything. `npm install @uipath/skills` (no tag, from npmjs) always resolves the last stable release. The `preview`/`dev` version suffix (`<base>-preview.<run_number>` / `<base>-dev.<run_number>`) matches the CLI's stamping scheme exactly.

### Cutting a preview

**Every push to a `release/v*` branch auto-publishes a preview** (normally after a merge; see the tracks table) — this is the normal path, mirroring `UiPath/cli`. To cut one ad hoc from any ref, dispatch with channel `preview`:

```bash
gh workflow run publish.yml --ref release/v<minor> -f channel=preview
```

Either way the default job stamps `<base>-preview.<run_number>` (never committed), runs `sync-version.mjs`, and publishes to the npmjs `preview` dist-tag with `--provenance` via the same OIDC job as `latest`. When the custom-package gate is enabled, the isolated Studio Web job derives the identical version and publishes it to the GitHub Packages `preview` tag without provenance. Consume the default with `npm install @uipath/skills@preview`. Each run gets a unique version from `run_number`; the tags advance to the newest one in their respective registries.

### The `dev` channel (GitHub Packages)

Every push to `main` (normally a merge) publishes `@uipath/skills@<base>-dev.<run_number>` to **GitHub Packages** under the `dev` dist-tag. After the custom-package gate is enabled, it also publishes `@uipath/skills-studioweb@<base>-dev.<run_number>` through the isolated called workflow. Both paths use the built-in `GITHUB_TOKEN` (`packages: write`) and carry no provenance because GitHub Packages does not support it. Consume the default from GitHub Packages with `npm install @uipath/skills@dev`. Publishes are serialized by effective channel: a `main` push and manual `dev` dispatch share `publish-dev`, a `release/v*` push and manual `preview` dispatch share `publish-preview`, and manual `latest` uses `publish-latest`. Equivalent automatic and manual runs therefore cannot race on the same dist-tag. Start a new publish with `gh workflow run publish.yml --ref main -f channel=dev` after enabling the gate.

### Registry routing

Both released packages are under the **`@uipath` scope**. There is no committed root `.npmrc`: the established default jobs continue to configure their scoped registry dynamically so `dev` can target GitHub Packages while `preview` and `latest` target npmjs. Generated custom manifests instead pin both `publishConfig.registry` and `publishConfig["@uipath:registry"]` to `https://npm.pkg.github.com/` and omit `package.json.repository`. The flavor workflow adds defense in depth by configuring and validating the same scoped registry, passing the GitHub registry explicitly, and publishing only the selected tarball. It deliberately omits `--access` after bootstrap so later versions preserve the administrator-configured Internal visibility. Explicit command-line overrides can still supersede package defaults, which is why the workflow preflight remains mandatory.

| Job | registry | Auth |
|-----|----------|------|
| `publish-dev` | GitHub Packages (`npm.pkg.github.com`) | built-in `GITHUB_TOKEN` |
| `publish-npmjs` | npmjs (`registry.npmjs.org`) | **OIDC trusted publishing** (no token) + signed `--provenance` |
| `publish-skill-flavor.yml` / `publish` | GitHub Packages (`npm.pkg.github.com`) only | built-in `GITHUB_TOKEN` |

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
2. publishes a **dev build and a preview**, and waits for both workflow runs — dispatches `publish.yml` twice on the release branch. `channel=dev` publishes the default `M.N.0-dev.<run>` package to GitHub Packages. `channel=preview` publishes the default `M.N.0-preview.<run>` package to npmjs with provenance. When the custom-package gate is enabled, those runs also publish the Studio Web package at the matching version to GitHub Packages without provenance. Both dispatches are explicit because the bot's own branch push can't trigger `publish.yml` (`GITHUB_TOKEN` recursion guard). A failed publish keeps the cut run red and is recorded in the bump PR warning. **Stable is not published here** — promote it manually (above);
3. **opens a PR** bumping `main` to the **next** line (`M.(N+1).0`) whenever the release branch was cut successfully, even if publication failed. A publish failure adds an explicit warning so a maintainer can verify or retry it before approving the bump; merging the PR advances `main` while `release/v<M.N>` stabilizes.

Off-cadence or ad-hoc cut: dispatch manually with `minor_override` (e.g. `1.198`) to cut exactly that line, or `dry_run` to print the plan without pushing, publishing, or opening a PR.

> **Line alignment is manual.** The cut does **not** compare itself to the CLI: it publishes a preview, and the preview line legitimately runs 1–2 minors ahead of the CLI's published stable during the RC window (stable is promoted by hand). Alignment between the skills and CLI minor lines is therefore a manual decision made at **stable-promotion** time, not at cut time. If a line ever needs to be cut out of the normal sequence, `minor_override=<M.N>` cuts exactly that line.

> **Idempotent resume.** The line to cut is read from `main`'s `package.json`; `main` advances only when the bump PR (step 3) is merged, so once merged the next sprint's `main` line is a fresh line. If a run fails after cutting the branch, the next run finds `release/v<M.N>` already at `M.N.0` and **resumes** (re-publishes, re-opens the bump PR) — no new line is cut. (If the branch exists at a *different* version, the cut stops loudly with `already exists at version <X> (expected <Y>)` for manual resolution.) **Merge the bump PR before the next cut** — until it merges, `main` stays on the old line and the cut keeps re-targeting it.

> **Repo setup:** branch protection must allow the Actions identity (`github-actions[bot]`) to push `release/v*` branches. `main` is intentionally **not** pushable by the bot — the cut opens a PR for it (below).

> **Automating the bump (optional).** `main` is protected (PR + 1 approval + smoke-test checks) on a public repo, so the cut opens a bump PR that a maintainer merges — no bypass credential is introduced. A PR opened by the built-in `GITHUB_TOKEN` does **not** trigger the required check workflows, so a maintainer may need to reopen/re-run them before merge. To make the bump fully hands-off, create a scoped **GitHub App**, add it to the `main` ruleset bypass, and have step 3 mint a short-lived token (`actions/create-github-app-token`) to open the PR (its checks run) and `gh pr merge --auto` it — App tokens are short-lived and repo-scoped, unlike a personal PAT. This is the only safe route to full automation; do **not** store a long-lived PAT for it.

## Required setup

- [x] **npmjs Trusted Publishing for the default package** — configure a GitHub Actions trusted publisher on `@uipath/skills` (npmjs → package → Settings → Trusted Publisher): repository `UiPath/skills`, workflow `publish.yml`. No `NPM_TOKEN` secret is used — the default `publish-npmjs` job authenticates via OIDC (`id-token: write`). Do **not** set `NODE_AUTH_TOKEN`; a token makes npm bypass OIDC and (with 2FA) fail `EOTP`.
- [x] **Studio Web registry isolation in code** — the explicit Studio Web jobs call `publish-skill-flavor.yml` with `flavor: studioweb`; generated custom manifests and the reusable workflow target only GitHub Packages. It requires no npmjs package, trusted publisher, OIDC permission, or provenance configuration.
- [ ] **Studio Web Internal package bootstrap** — manually create `@uipath/skills-studioweb`, set it to Internal, confirm it does not inherit access from the public source repository, grant `UiPath/skills` Actions write access, and only then set `ENABLE_SKILL_FLAVOR_PUBLISH=true` as described above.
- [x] Package name/scope confirmed: **`@uipath/skills`** (published).
- [x] **Version source confirmed** — `package.json` and `version-manifest.json` are authoritative for the current CLI minor line; do not copy a volatile version number into this checklist. The ongoing CLI↔skills lockstep is automated by `sprint-release-cut.yml` (Sunday 06:00 UTC, 6 h before the CLI's own cut, on the same 14-day cadence anchored at `2026-06-14`).

> The `dev` channel also needs no secret — `publish-dev` uses the built-in `GITHUB_TOKEN` with `packages: write`.
