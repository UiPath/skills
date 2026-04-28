# sdk-introspection

## Purpose
**The SDK is the source of truth for what's queryable. The skill's job is to read it, not mirror it.**

The flow: introspect the installed `@uipath/uipath-typescript` package's TypeScript declarations, produce a manifest of every service / class / method / signature, and reason over THAT — not over hand-maintained catalogs. New SDK releases (a `Spans` service, a new tracing API) become available for dashboard generation immediately, without skill changes.

There are TWO introspection passes per Build session:

1. **Preflight introspection** — runs at the START of the Plan phase, BEFORE any project directory exists. Installs the SDK into a workspace-scoped cache and produces a manifest the plan reasons against. Resolves the chicken-and-egg problem where the plan needs to know what's queryable but no `node_modules` exists yet.

2. **Per-project introspection** — runs after the project's `npm install` completes during scaffold. Confirms the project's installed SDK matches what the plan was built against; re-introspects only on version drift.

## Preflight cache layout

```
<cwd>/.uipath-dashboards/.cache/sdk/
├── package.json          # { dependencies: { "@uipath/uipath-typescript": "<version>" } }
├── node_modules/         # populated by the preflight `npm install`
│   └── @uipath/uipath-typescript/
└── sdk-manifest.json     # produced by introspect-sdk.mjs --out <here>
```

The cache is workspace-scoped (sibling to project directories under `.uipath-dashboards/`) so multiple dashboards in the same workspace share it. The first Build pays ~20 seconds for `npm install`; subsequent Builds reuse the cache and pay ~0 seconds.

## Pipeline

### 1. Preflight install (Plan phase, before scaffolding)

```bash
CACHE_DIR="<cwd>/.uipath-dashboards/.cache/sdk"
mkdir -p "$CACHE_DIR"

# Write a minimal package.json if absent
if [[ ! -f "$CACHE_DIR/package.json" ]]; then
  cat > "$CACHE_DIR/package.json" <<EOF
{
  "name": "uipath-dashboards-sdk-cache",
  "private": true,
  "dependencies": {
    "@uipath/uipath-typescript": "latest",
    "typescript": "^5.6.2"
  }
}
EOF
fi

# Install (no-op if node_modules is already populated and SDK is current).
# Use --silent to keep the subagent's output clean.
(cd "$CACHE_DIR" && npm install --silent)
```

The cached `package.json` declares `"@uipath/uipath-typescript": "latest"` so the cache always reflects what the user *would* get from a fresh install. To pin a specific version, edit the cache's package.json before re-running.

### 2. Run introspection against the cache

```bash
node "$SKILL_DIR/assets/scripts/introspect-sdk.mjs" \
  --root="$CACHE_DIR" \
  --out="$CACHE_DIR/sdk-manifest.json"
```

`--root` tells the script to look for `node_modules/@uipath/uipath-typescript` under the cache dir (instead of cwd). `--out` writes the manifest directly into the cache (instead of the default `<root>/.dashboard/sdk-manifest.json`).

The manifest is the input to the plan. The plan agent reads it and reasons about which services match the user's prompt.

### 3. Pin the SDK version in the project's `package.json`

After preflight, read the resolved version from the cache. **Use `node`, not `jq`** — `jq` is not on PATH for end-customer environments:
```bash
PINNED_VERSION=$(P="$CACHE_DIR/node_modules/@uipath/uipath-typescript/package.json" node -e "
  process.stdout.write(JSON.parse(require('fs').readFileSync(process.env.P,'utf8')).version || '');
")
```

When the project is scaffolded, substitute this exact version into `package.json.template`'s `@uipath/uipath-typescript` entry (replace the default `^1.2.1`). This guarantees the project ships with the same SDK the plan was built against.

### 4. Per-project re-introspection (post-scaffold, version-drift only)

After the project's `npm install` succeeds:
```bash
PROJECT_VERSION=$(P="<project>/node_modules/@uipath/uipath-typescript/package.json" node -e "
  process.stdout.write(JSON.parse(require('fs').readFileSync(process.env.P,'utf8')).version || '');
")
CACHE_VERSION=$(P="$CACHE_DIR/sdk-manifest.json" node -e "
  process.stdout.write(JSON.parse(require('fs').readFileSync(process.env.P,'utf8')).sdkVersion || '');
")

if [[ "$PROJECT_VERSION" != "$CACHE_VERSION" ]]; then
  # Version drift — re-introspect against the project's own copy
  cd <project>
  node "$SKILL_DIR/assets/scripts/introspect-sdk.mjs"
  # writes <project>/.dashboard/sdk-manifest.json
else
  # Versions match — copy the cached manifest into the project to avoid re-introspecting
  cp "$CACHE_DIR/sdk-manifest.json" "<project>/.dashboard/sdk-manifest.json"
fi
```

In the common path (no drift), the project inherits the preflight manifest with no extra TypeScript-compiler work.

## Inputs / outputs summary

| Phase | Input | Output |
|---|---|---|
| Preflight install | (none) — bootstraps from scratch | `<cwd>/.uipath-dashboards/.cache/sdk/node_modules/` |
| Preflight introspect | `<cache>/node_modules/@uipath/uipath-typescript/` | `<cache>/sdk-manifest.json` |
| Plan phase | `<cache>/sdk-manifest.json` | Approved plan |
| Project scaffold | `package.json` with pinned SDK version | Project tree at `<cwd>/.uipath-dashboards/<name>/` |
| Per-project re-introspect (drift only) | `<project>/node_modules/@uipath/uipath-typescript/` | `<project>/.dashboard/sdk-manifest.json` |

## Manifest shape (unchanged)

```json
{
  "sdkVersion": "1.3.2",
  "generatedAt": "2026-04-27T...",
  "services": [
    {
      "subpath": "jobs",
      "dtsPath": "node_modules/@uipath/uipath-typescript/dist/jobs/index.d.ts",
      "exports": {
        "classes":    [{ "name": "Jobs", "aliasOf": "JobService" }],
        "interfaces": [{ "name": "JobGetResponse" }],
        "types":      [{ "name": "JobState" }]
      },
      "methods": [
        { "class": "Jobs", "name": "getAll", "params": "options?: JobGetAllOptions", "returnType": "Promise<...>" }
      ]
    }
  ]
}
```

## Rules

1. **Preflight runs in the Plan phase, BEFORE any directory creation in `<cwd>/.uipath-dashboards/<name>/`.** Plan reasoning is downstream of preflight.
2. **The cache is workspace-scoped, not project-scoped.** Multiple dashboards under the same `<cwd>/.uipath-dashboards/` reuse one cache.
3. **Pin the SDK version** the cache resolved into the scaffolded project's `package.json`. Don't let the project fetch `latest` independently — that introduces drift.
4. **Re-introspect on drift.** If the project's installed SDK differs from the cached manifest's `sdkVersion`, re-run introspection against the project's `node_modules`. Otherwise copy the manifest forward.
5. **Manifest is illustrative; deep types come from the .d.ts.** When the agent decides which service owns a metric, the next step is to OPEN `dtsPath` for that service and read the actual interface bodies. The manifest is the index; the .d.ts is the body.
6. **`intent-map.md` and `service-semantics.md` are OPINION layered on top of the manifest, not a substitute.** When the manifest reveals a service that isn't in our catalogs, use it via the four-axis decomposition in `metric-derivation.md`.
7. **Search the manifest semantically, not lexically.** When a user asks for "agent traces", look at every service's class/method/type names for matches like `trace`, `span`, `execution`, `tool`, `step` — not only services literally named `Traces`.

## Searching the manifest by intent

| User says | Search the manifest for keywords |
|---|---|
| "agent traces" / "execution spans" / "tool calls" | `trace`, `span`, `execution`, `tool`, `step` in class/method/type names |
| "conversation feedback" / "user satisfaction" | `feedback`, `rating`, `satisfaction`, `exchange` |
| "pipeline stages" / "case flow" | `stage`, `flow`, `pipeline`, `caseInstance` |
| "model usage" / "token consumption" | `model`, `token`, `usage`, `consumption` |
| "error rate" | `error`, `fault`, `state`, `incident` |

The keywords are illustrative — actual reasoning is "what concept in the user's intent matches what classes/methods/types?". Multiple candidates is fine; pick the best fit (often the one with `getAll` and a filter signature).

## When to halt vs synthesize

**Synthesize when:**
- The introspection reveals a service whose method signatures match the metric.
- Cross-cutting gotchas don't block (scope present, method paginates predictably, etc.).

**Halt when:**
- No service in the manifest covers the user's intent.
- Service exists but the auth scope isn't available; surface the missing scope clearly.
- Method exists but its time-axis or aggregation needs aren't satisfiable from the SDK alone.

## Anti-patterns

- **Building the plan from `intent-map.md` because the cache hasn't been populated.** That's exactly the chicken-and-egg the preflight cache solves. Always run preflight first.
- **Using `latest` in the project's `package.json` directly.** The plan agreed to a specific version's surface area; the project must ship that version.
- **Skipping introspection because the metric "looks like Jobs".** Always introspect — what looks like a Jobs question may be better answered by a service with richer per-execution detail.
- **Falling back to Jobs as a default.** Jobs is one service among many. Four-axis decomposition + manifest + service-semantics together pick the right one.
- **Silently working around a missing service.** If the user wants a metric the SDK can't surface, halt and say so.
