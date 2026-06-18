# Externalize the Dashboard Starter Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Steps use `- [ ]` tracking.

**Goal:** The skill should contain NO custom zip/unzip code and NO scaffold source — only the packaged starter-kit `.zip` it consumes. The scaffold + widget templates + packer move to `C:\Work\apps-dev-tools` as the maintained source; the agent extracts the zip with OS-native tools at build time.

**Decisions (from owner):** keep the `.zip` artifact; the agent extracts it (OS-native, documented commands); full move across both repos.

## Target architecture

**`apps-dev-tools/uipath-dashboard-starter-kit/`** (source of truth)
- `scaffold/` — the React app (moved from skill `assets/templates/dashboard/scaffold/`)
- `widgets/` — `*.tsx`/`*.tsx.template` generator templates (moved from skill `assets/templates/dashboard/widgets/`)
- `lib/zip.mjs`, `pack.mjs` (was `pack-scaffold.mjs`) — the deterministic packer (moved from skill). Dev repo may keep custom zip; the SKILL must not.
- `publish.mjs` — pack → copy `.zip` into the skill `assets/fixtures/` + stamp version
- `package.json` — `build`/`test` (compile the scaffold standalone), `pack`, `publish`
- `starter-kit.json` — `{ version }`, bundled into the zip so the skill can stamp `state.json`

**skill `uipath-coded-apps`** (consumer)
- KEEP: `assets/scripts/build-dashboard.mjs`, `references/`, `assets/fixtures/governance-dashboard-starter-kit.zip`
- DELETE: `assets/scripts/lib/zip.mjs`, `assets/scripts/pack-scaffold.mjs`, `assets/fixtures/*.manifest.json`, `assets/templates/dashboard/**`
- zip now bundles: scaffold app files (at root) + `_gen/widgets/` (templates) + `_gen/starter-kit.json`

## Build contract (agent-driven extraction)

1. Agent extracts the zip into the project dir, OS-native:
   - Windows: `Expand-Archive -LiteralPath "<zip>" -DestinationPath "<proj>" -Force`
   - macOS: `unzip -o "<zip>" -d "<proj>"` (alt `ditto -x -k`)
   - Linux: `unzip -o "<zip>" -d "<proj>"` (fallback `python3 -m zipfile -e "<zip>" "<proj>"`)
2. `build-dashboard.mjs`:
   - No extraction. Verifies `<proj>/package.json` AND `<proj>/_gen/widgets/` exist; else `fail()` with the exact OS command + zip path.
   - `WIDGETS_DIR` → `<proj>/_gen/widgets`; reads templates from there.
   - `SCAFFOLD_VERSION` ← `<proj>/_gen/starter-kit.json`.
   - After generating widgets, `rm -rf <proj>/_gen` so templates never ship (also not under `src`, so tsc ignores it regardless).
   - Prewarm (`npm ci`) unchanged except it assumes an already-extracted dir.

## Tasks

- [ ] **1. apps-dev-tools scaffold-kit dir:** create `uipath-dashboard-starter-kit/`; copy skill `scaffold/`→`scaffold/`, `widgets/`→`widgets/`; move `zip.mjs`→`lib/zip.mjs`, `pack-scaffold.mjs`→`pack.mjs` (retarget to emit `_gen/widgets` + `_gen/starter-kit.json` alongside scaffold root); add `package.json`, `publish.mjs`, `starter-kit.json`.
- [ ] **2. Pack + publish:** `pack.mjs` zips scaffold-at-root + `_gen/{widgets,starter-kit.json}`; `publish.mjs` copies the zip into the skill fixtures dir. Run it to regenerate the skill's zip in the new layout.
- [ ] **3. Skill gut:** delete `lib/zip.mjs`, `pack-scaffold.mjs`, `*.manifest.json`, `assets/templates/dashboard/**`.
- [ ] **4. build-dashboard rewire:** drop `unzipTo`/`extractFixture`/manifest; add `assertScaffoldExtracted()` (fail-loud + OS commands); `WIDGETS_DIR`→`_gen/widgets`; version from `_gen/starter-kit.json`; cleanup `_gen` post-gen; `runUpgrade`/`--prewarm` assume extracted.
- [ ] **5. impl.md:** add the "Extract the starter kit" step (OS commands) to the build-subagent + prewarm instructions; update references mentioning the scaffold/zip/templates paths.
- [ ] **6. Tests:** remove drift-guard/contentHash tests; point any template-reading tests at the new location or stub; keep widget-gen + resolution coverage. `node --test` green.
- [ ] **7. Verify end-to-end:** extract the published zip into a temp project (simulating the agent), run `build-dashboard.mjs` → METRICS_PASS + TSC_PASS; confirm `_gen` cleaned and no `.template` files in the app.

## Notes / risks
- Cross-platform: extraction now depends on OS tools (owner-accepted). Mitigation: build fails loud with copy-paste commands; `python3 -m zipfile` documented as the universal fallback.
- The scaffold's own toolchain (vite/tsc) lives in apps-dev-tools; the skill no longer compiles the scaffold standalone — the integration check is the real build (Task 7).
- CRLF/drift machinery is gone from the skill (the artifact is opaque-by-design now); any "is the published zip in sync" check lives in apps-dev-tools.
