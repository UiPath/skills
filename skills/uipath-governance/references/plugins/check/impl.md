# Check · Compliance Posture Against a Pack

Read-only audit of a tenant's live state against a `.uipolicy` compliance pack. Outputs a JSON report, an HTML report, and a terminal summary. Optionally offers a remediation handoff to APPLY mode.

## When this plugin is invoked

Orchestrator detects CHECK mode from phrases like:
- "check compliance", "audit against the pack", "is my tenant compliant"
- "check posture against ISO 27001", "drift check"
- "compare my tenant state to the compliance pack"

## Runtime output discipline

These rules govern what the **user** sees, not internal tool output:

1. **Quiet by default.** Do not narrate "Step 0 preflight…", "Now unzipping…", or similar. Step headings in this document are for you, not the user.
2. **No intermediate echoes.** Do not print manifest contents, clause listings, per-policy metadata, or CLI responses. The walker prints the final summary.
3. **One user-visible block at the end.** The walker's stdout (terminal summary + report paths) is the entire user-facing output. Plus any pack-selection prompt (Step 1), confirmation gate (Step 4), and remediation prompt (Step 9).
4. **Consolidate shell work.** Combine preflight, pack selection, unzip, and structural validation into one Bash call per phase.
5. **Errors halt with context.** If a step fails, surface the exact failure and stop.

## Shared primitives used

- [../../auth-context.md](../../auth-context.md) — read `UIPATH_TENANT_ID` / `UIPATH_TENANT_NAME`
- [../../cli-cheatsheet.md](../../cli-cheatsheet.md) — `deployed-policy get` command reference
- [../../property-labels.md](../../property-labels.md) — runtime label lookup for drift-detail descriptions

## Input contract

```jsonc
{
  "mode": "check",
  "pack":   "<packId-or-packName>",   // optional; if absent or ambiguous, prompt from catalog
  "scope":  "all" | "mandatory" | "specific" | "nl",  // default "all" unless prompt signals
  "scopeDetail":  null,               // list of clause IDs or NL phrase per scope-selection.md
  "tenantIdentifier": "<from ~/.uipath/.auth>"
}
```

## Recipe

### Step 0 — Preflight (one shell call)

```bash
set -eu
uip login status --output json | node -e "
const r=JSON.parse(require('fs').readFileSync(0,'utf8'));
process.exit(r.Data?.Status === 'Logged in' ? 0 : 1);
" || { echo "NOT_LOGGED_IN" >&2; exit 1; }
AUTH="$HOME/.uipath/.auth"
UIPATH_TENANT_ID=$(grep '^UIPATH_TENANT_ID=' "$AUTH" | cut -d= -f2-)
UIPATH_TENANT_NAME=$(grep '^UIPATH_TENANT_NAME=' "$AUTH" | cut -d= -f2-)
```

If `NOT_LOGGED_IN` → halt, ask user to run `uip login`.

### Step 1 — Resolve the pack from the local catalog

The skill ships a catalog at `assets/packs/*.uipolicy`. Build the catalog from filesystem + each manifest; match against the user's prompt; prompt if ambiguous.

```bash
# SKILL_DIR = absolute path to the uipath-governance skill (normalize for Node)
SKILL_DIR=$(cd "<absolute-path-to-uipath-governance>" && (pwd -W 2>/dev/null || pwd))
PACK_DIR="$SKILL_DIR/assets/packs"

# Build catalog via in-place unzip-to-stdout + node (one line per pack, TAB-separated)
CATALOG=$(for f in "$PACK_DIR"/*.uipolicy; do
  unzip -p "$f" manifest.json 2>/dev/null | node -e "
const m = JSON.parse(require('fs').readFileSync(0, 'utf8'));
console.log([m.packId, m.packName, m.version, process.argv[1]].join('\t'));
" "$f"
done)
```

**Present the catalog to the user:**

```
Available compliance packs in the local catalog:
  [1] ISO/IEC 42001:2023 — AI Trust Layer Controls (v1.0.0)
  [2] SOC 2 Type II — AI Agent Governance (v1.0.0)
Which standard would you like to check posture against?
```

If the user's prompt already names a standard:
- Exact match on `packId` or `packName` substring → confirm and proceed.
- Multiple matches (e.g., two versions) → list them, ask which.
- No match → list available and ask.

**Match the user's prompt:**
- Prompt explicitly names a `packId` ("iso-42001-2023-aitl") → use that entry.
- Prompt names a standard by display name ("ISO 42001", "SOC 2") → case-insensitive `packName` substring match. If exactly one match → confirm. If multiple (e.g., multiple versions) → list and ask.
- Prompt doesn't name a standard → list the catalog and ask which.
- No catalog entry matches → list available standards and halt.

**Confirmation line before proceeding:**
```
Check posture against: ISO/IEC 42001:2023 — AI Trust Layer Controls (v1.0.0)
Pack: assets/packs/iso-42001-aitl-v1.0.0.uipolicy
Tenant: DefaultTenant
Proceed? (y/n)
```

### Step 2 — Unzip + validate structure (one shell call)

Place the run under the OS temp directory — this is scratch work, not user data. Resolve the temp root via Node so the path is already Windows-native (forward slashes after normalization) and Node-readable on every platform.

```bash
TS=$(date -u +%Y%m%dT%H%M%SZ)
# Resolve the OS temp dir and normalize to forward-slash form so Node (native
# Windows binary) can read it. cygpath -m converts C:\… → C:/… on Git Bash;
# the fallback runs on macOS/Linux where os.tmpdir() is already POSIX.
TMP_ROOT=$(cygpath -m "$(node -p 'require("os").tmpdir()')" 2>/dev/null || node -p 'require("os").tmpdir()')
RUNDIR="$TMP_ROOT/uipath-governance/check-$TS"
mkdir -p "$RUNDIR"

# Reuse an existing extraction when possible — session-cache hashes the archive
# by path+size+mtime, so edits to the pack file auto-invalidate.
EXTRACT_LINE=$(node "$SKILL_DIR/assets/scripts/session-cache.mjs" fetch pack-extract "$PACK_FILE")
EXTRACTED_DIR="${EXTRACT_LINE#*extracted=}"
# Point $RUNDIR/extracted at the cached extraction (symlink on macOS/Linux,
# directory junction or copy on Windows). Avoids duplicating the tree.
ln -sfn "$EXTRACTED_DIR" "$RUNDIR/extracted" 2>/dev/null || cp -r "$EXTRACTED_DIR" "$RUNDIR/extracted"

test -f "$RUNDIR/extracted/manifest.json"   || { echo "missing manifest.json" >&2; exit 1; }
test -f "$RUNDIR/extracted/clause-map.json" || { echo "missing clause-map.json" >&2; exit 1; }
test -d "$RUNDIR/extracted/policies"         || { echo "missing policies/ dir" >&2; exit 1; }
```

`$RUNDIR` resolves to `C:/Users/.../AppData/Local/Temp/uipath-governance/check-<ts>` on Windows, `/tmp/uipath-governance/check-<ts>` on macOS/Linux — Node-readable and bash-usable everywhere. The OS cleans its temp dir on its own schedule; no manual cleanup required. The final JSON + HTML reports are written to the user-chosen `--out-dir` (default: current working directory), not under `$RUNDIR` — so they survive temp-dir wipes.

### Step 3 — Determine scope

Reuse [../../plugins/compliance/scope-selection.md](../compliance/scope-selection.md). Default: all clauses. Narrow only on explicit prompt signals (obligation level, specific clause IDs, NL phrase).

### Step 4 — Pre-flight preview + approval

Print the effective plan in one block:
```
Pack: iso-42001-2023-aitl v1.0.0
Scope: all (21 clauses)
Applicable tenant-scope policy files:  3
Skipped (group/user scope or access):  2
Tenant: DefaultTenant
Continue? (y/n)
```

Require `y`.

### Step 5 — Fetch effective policies (parallel, deduplicated, NEVER cached)

> ⚠ `deployed-policy get` is NEVER cached on disk — see [../../compliance-impact.md Step 2](../../compliance-impact.md#step-2--hydrate-the-before-cache-parallel-never-cached). Tenant state can change under admin activity at any time. Always fetch live every run.

Collect unique `(licenseType, productIdentifier)` tuples across all **tenant-scope product** policy files in the pack, then fan out all calls concurrently via `parallel-cli.mjs`:

```bash
CACHE="$RUNDIR/cli-cache.json"
BATCH="$RUNDIR/batch.json"
RESULTS="$RUNDIR/results.json"

# Build a jobs batch — one entry per unique (license, product) tuple.
node -e "
const fs=require('fs'), path=require('path');
const mf=JSON.parse(fs.readFileSync('$RUNDIR/extracted/manifest.json','utf8'));
const pairs=new Map();
for (const p of mf.policies) {
  const pf=JSON.parse(fs.readFileSync(path.join('$RUNDIR/extracted', p.file),'utf8'));
  const level=p.deploymentLevel || pf.deploymentLevel || 'tenant';
  if (level !== 'tenant' || pf.policyKind === 'access') continue;
  const key = pf.policy.licenseTypeIdentifier + '|' + pf.policy.productIdentifier;
  pairs.set(key, { lt: pf.policy.licenseTypeIdentifier, prod: pf.policy.productIdentifier });
}
const batch = [...pairs.entries()].map(([key, {lt, prod}]) => ({
  id: key,
  args: ['gov','aops-policy','deployed-policy','get', lt, prod, process.argv[1]],
  out: path.join('$RUNDIR', 'resp-' + lt + '-' + prod + '.json')
}));
fs.writeFileSync('$BATCH', JSON.stringify(batch, null, 2));
" "$UIPATH_TENANT_ID"

# Fire the batch. Default concurrency 8 — tune with --concurrency if needed.
node "$SKILL_DIR/assets/scripts/parallel-cli.mjs" \
  --batch   "$BATCH" \
  --results "$RESULTS" \
  --concurrency 8

# Merge successful responses into cli-cache.json, applying the cross-product guard:
# if Data.productIdentifier != the product we asked for, drop the entry so the walker
# reports cache-miss instead of producing phantom drift.
node -e "
const fs=require('fs');
const results=JSON.parse(fs.readFileSync('$RESULTS','utf8'));
const out={};
for (const [key, r] of Object.entries(results)) {
  if (!r.ok || !r.out) continue;
  const resp = JSON.parse(fs.readFileSync(r.out,'utf8'));
  if (resp?.Result !== 'Success') continue;
  const data = resp.Data ?? null;
  const [, expected] = key.split('|');
  const live = data?.productIdentifier ?? data?.product?.identifier ?? data?.product ?? null;
  if (live && live !== expected) continue;
  out[key] = data;
}
fs.writeFileSync('$CACHE', JSON.stringify(out, null, 2));
"
```

**Why response-to-file, not argv:** on Windows, passing a 25KB+ JSON response as a shell-escaped argument to `node -e` exceeds the argv length limit (`Argument list too long`). `parallel-cli.mjs` writes each response to `out` so the merge step reads files, never argv.

**About the CLI mode:** `deployed-policy get <license> <product> <tenant>` with no extra flags resolves the **caller's own effective policy** (full user → group → tenant → global walk). This skill intentionally uses only this mode — the authenticated admin typically has no user-level overrides, so the caller's view matches tenant-level semantics. The `--tenant-only` / `--user-id` modes require an S2S token and are out of scope.

### Step 6 — Fetch property labels (cached, 30 min TTL)

For each unique product present in the cache, fetch its locale-resolved label bundle. Templates are stable within a session — the session-cache returns the same file on every subsequent run within the TTL, so this step drops to near-zero cost on repeat invocations.

```bash
LABEL_CACHE="$RUNDIR/label-cache.json"
echo '{}' > "$LABEL_CACHE"
PRODUCTS=$(node -e "
const c=JSON.parse(require('fs').readFileSync('$CACHE','utf8'));
console.log([...new Set(Object.keys(c).map(k => k.split('|')[1]))].join('\n'));
")
for product in $PRODUCTS; do
  LOCALE_FILE="$RUNDIR/locale-$product.json"
  # session-cache returns a cached template-locale file if fresh, else refreshes via `uip`.
  if node "$SKILL_DIR/assets/scripts/session-cache.mjs" fetch template-locale "$product" --out "$LOCALE_FILE" > /dev/null 2>&1; then
    node -e "
const fs=require('fs');
try {
  const res=JSON.parse(fs.readFileSync('$LOCALE_FILE','utf8'));
  const flat={};
  const data = res.defaultData?.data || {};
  for (const [k, v] of Object.entries(data)) {
    if (v && typeof v === 'object' && ('label' in v || 'description' in v)) {
      flat[k] = v.description || v.label;
    }
  }
  const cache=JSON.parse(fs.readFileSync('$LABEL_CACHE','utf8'));
  cache['$product'] = flat;
  fs.writeFileSync('$LABEL_CACHE', JSON.stringify(cache, null, 2));
} catch(e) { /* skip — renderer falls back to raw paths */ }
"
  fi
done
```

This builds a `{ product → { propertyPath → description } }` map for the HTML renderer. If any fetch fails, the renderer falls back to the raw property path — no blocker.

### Step 7 — Walk + write JSON + print terminal summary

Normalize the output directory to a Node-readable absolute path:

```bash
OUT_DIR=.
mkdir -p "$OUT_DIR"
OUT_ABS=$(cd "$OUT_DIR" && (pwd -W 2>/dev/null || pwd))

node "$SKILL_DIR/assets/scripts/check-walk.mjs" \
  --pack-dir    "$RUNDIR/extracted" \
  --cli-cache   "$CACHE" \
  --tenant-id   "$UIPATH_TENANT_ID" \
  --tenant-name "$UIPATH_TENANT_NAME" \
  --pack-source "assets/packs/$(basename "$PACK_FILE")" \
  --out-dir     "$OUT_ABS"
```

The walker's stdout **is** the user-visible block for the check. Do not echo any prior Bash output; do not reformat. The walker also writes `./compliance-report-<packId>-<ts>.json`.

### Step 8 — Render HTML

```bash
JSON_POSIX=$(ls -t "$OUT_DIR"/compliance-report-*.json | head -1)
JSON_ABS=$(cd "$(dirname "$JSON_POSIX")" && (pwd -W 2>/dev/null || pwd))/$(basename "$JSON_POSIX")

node "$SKILL_DIR/assets/scripts/render-report.mjs" \
  --json        "$JSON_ABS" \
  --template    "$SKILL_DIR/assets/templates/compliance-report.html" \
  --label-cache "$LABEL_CACHE" \
  --open
```

The renderer writes `<JSON_BASENAME>.html` next to the JSON and — with `--open` — launches the default browser (uses `cmd /c start` on Windows, `open` on macOS, `xdg-open` on Linux). Both stdout lines (`HTML: <path>` and `Opened in browser.`) are appended to the user summary. Drop `--open` only if the user explicitly asked for a headless run.

Each drift block in the HTML now groups properties **per contributing policy**, with a header showing the product, the effective policy name deployed on the tenant (or "global default" if none), the deployment scope (`TENANT` / `GROUP` / `USER`), and the pack file path. The main clauses table also shows attribution chips under each clause name (`AITrustLayer · <b>iso-42001-ai-trust-layer</b> · TENANT`) so the user can see which policy is being evaluated for each clause without scrolling to drift details.

### Step 9 — Drift handoff (prompt only if drifted)

If the JSON report's `overall` field is `Non-Compliant` or `Partially Compliant`:

```
Some clauses have drifted. Would you like me to re-apply the
pack using APPLY mode?
```

If yes: dispatch to the APPLY mode with the same pack file (same `$PACK_FILE`). The user can narrow scope to only drifted clauses via follow-up prompt.

If everything is compliant: no prompt. The terminal summary + report paths are the only output.

## Critical rules (CHECK mode)

1. **Read-only.** Never call `create`, `update`, `delete`, `assign`, `configure`. Only `list`, `get`, `deployed-policy get`, `template get`, `login status`.
2. **One walker call per run.** Do not iterate the walk inline — it's deterministic and testable.
3. **Cache key is `{licenseType}|{productIdentifier}`.** Deduplicate before fetching.
4. **Non-tenant scopes skip, they don't fail.** `deploymentLevel` of `group` / `user` → record as `skipped / <level>-scope-check-not-supported`. The walker handles this.
5. **Drift is a finding, not a failure.** Walker exits 0 whether drift is present or not.
6. **Always write both reports.** JSON (machine) + HTML (auditor). Terminal summary is the user-visible block.
7. **Never commit the reports.** They contain tenant identifiers and live policy values.
8. **Never mutate on drift.** Hand off to APPLY; CHECK is an observer.

## Error map

| Situation | Action |
|---|---|
| Not logged in | Halt at Step 0. |
| Malformed pack (missing manifest / clause-map / policies/) | Halt at Step 2 with the path. |
| No catalog entry matches the prompt | List available standards, ask user to pick, or halt. |
| `deployed-policy get` 4xx | Halt at Step 5. Surface stderr. Check license / product / tenant identifiers. |
| Cache miss in walker | Walker exits 3. Means Step 5 missed a pair — regenerate. |
| Unresolved placeholders in HTML | Renderer exits 3. Template is out of date vs. schema. |
