# Compliance Impact — preview posture delta before applying a change

Shared primitive for **Advise** and **Diagnose**. Given a proposed policy change (create or update), compute how it shifts compliance against every pack in `assets/packs/` that touches the target product, and surface the delta at the approval gate.

## When to invoke

| Mode | When |
|---|---|
| **Diagnose** | After Step 5 (diff preview), BEFORE Step 6 (apply) — blocks approval with regressions. |
| **Advise** | Right before the user approves CREATE or UPDATE — included in the plan presentation. |
| **Apply** | NOT called — Apply is pack-driven, so the pack itself is the ground truth. |

## Contract

**Input** — the caller must provide:

1. **Before cache** — live tenant state keyed `{licenseType}|{productIdentifier}`. Same shape the check walker consumes. Build via `uip gov aops-policy deployed-policy get <lt> <product> <tenantId> --output json` for each `(lt, product)` touched by any pack.
2. **After cache** — the same map, but with the target entry's `data` swapped for the proposed `formData`. For an update: read current policy, apply the proposed changes, write back as `{ data, "policy-name", deployment }`. For a create on a slot that had no prior custom policy: synthesize an `{ data: <proposed>, deployment: { type: "TENANT", ... } }` entry.
3. **Target product** — the `productIdentifier` being changed. Only packs that reference this product are walked; others are reported as `unaffected`.

**Output** — one JSON blob and a terminal summary:

```
Compliance impact of change to AITrustLayer:
  SOC 2 Type 2 (v1.0.3)           8/17 → 10/17  (+2)
     ✓ improves:   CC6.1 — Logical access — AI model controls
     ✓ improves:   CC7.2 — Monitoring — prompt injection detection
  ISO 42001 (v1.0.0)              7/21 → 7/21  (±0) unchanged
  ISO 27001 (v2.0.1)              5/14 → 4/14  (-1) ⚠ 1 regression
     ✗ regression: A.5.23 — Information security for cloud services [Mandatory]

⚠ 1 MANDATORY-clause regression(s). Default: do not apply.
```

## Orchestrator recipe

### Step 1 — Extract all local packs (cached across sessions)

Use the session-cache helper — it hashes each `.uipolicy` by path+size+mtime and reuses extractions within a 1h TTL. No more re-unzipping the same 5 packs every time Claude re-enters Advise or Diagnose in the same session.

```bash
# One fetch per pack; each prints "extracted=<dir>" to stdout (hit or miss).
SKILL_PACKS_DIR="<skill-root>/assets/packs"
declare -A EXTRACTED
for pack in "$SKILL_PACKS_DIR"/*.uipolicy; do
  line=$(node "$SKILL_DIR/assets/scripts/session-cache.mjs" fetch pack-extract "$pack")
  # line looks like: cache-hit: extracted=<dir>   or   cache-miss (extracted): extracted=<dir>
  dir="${line#*extracted=}"
  EXTRACTED["$(basename "$pack" .uipolicy)"]="$dir"
done

# Build a single directory Impact can walk — symlink (or copy) each extraction
# under one root so impact.mjs discovers all packs via its --packs-root flag.
TMP_ROOT=$(cygpath -m "$(node -p 'require("os").tmpdir()')" 2>/dev/null || node -p 'require("os").tmpdir()')
PACKS_ROOT="$TMP_ROOT/uipath-governance/impact-$(date -u +%Y%m%dT%H%M%SZ)/packs"
mkdir -p "$PACKS_ROOT"
for name in "${!EXTRACTED[@]}"; do
  ln -sfn "${EXTRACTED[$name]}" "$PACKS_ROOT/$name" 2>/dev/null || cp -r "${EXTRACTED[$name]}" "$PACKS_ROOT/$name"
done
```

First session: each extraction runs `unzip` once and writes a sentinel. Subsequent runs within the TTL skip `unzip` entirely and return the cached path. Edit or replace a pack file and the cache invalidates automatically (size or mtime changes).

### Step 1b — Validate every `deployed-policy get` response before caching

⚠ `uip gov aops-policy deployed-policy get <licenseType> <productName> <tenantId>` can return a **cross-product fallback** — e.g., asking for `NoLicense StudioWeb <tenant>` may resolve to an AITrustLayer policy when no StudioWeb-specific policy is deployed (effective-policy walker returns the nearest ancestor). Caching this verbatim produces phantom drift when the pack's StudioWeb-shaped expected values get compared to AITL-shaped live data.

Before inserting the response into the cache, check that `Data.productIdentifier` (or `Data.product?.identifier` / `Data.product` depending on shape) **equals** the `productName` you queried with. If it differs:
- Record the cache entry as `null` (explicit "no deployed policy of the requested product"), OR
- Omit the key entirely so the walker's strict=false path reports it as `cache-miss` / `cross-product-fallback`.

The walker (`walker-core.mjs`) also guards against this at evaluation time — but the cache-side check is faster and makes the fallback visible in the hydration log. Both layers are worth keeping.

### Step 2 — Hydrate the BEFORE cache (parallel, NEVER cached)

> ⚠ `deployed-policy get` responses are **never** cached on disk. Tenant state can change under admin activity — a stale cache would produce wrong Impact deltas and ruin the skill's compliance claims. Always call live.

Walk every `(licenseType, productIdentifier)` pair mentioned by any extracted pack's manifest. Use `parallel-cli.mjs` to issue all calls concurrently (capped at 8 for CLI politeness):

```bash
RUNDIR="$PACKS_ROOT/.."
BATCH="$RUNDIR/batch-before.json"
RESULTS="$RUNDIR/results-before.json"

# Build the batch — one job per (lt, product) pair; each writes its response to its own file.
# The pair list is derived by scanning every pack's manifest.policies[].
node -e '
  const fs = require("fs"), path = require("path");
  const pairs = new Map();
  for (const d of fs.readdirSync(process.argv[1])) {
    const m = JSON.parse(fs.readFileSync(path.join(process.argv[1], d, "manifest.json"), "utf8"));
    for (const p of m.policies ?? []) {
      try {
        const pol = JSON.parse(fs.readFileSync(path.join(process.argv[1], d, p.file), "utf8"));
        const lt = pol.policy?.licenseTypeIdentifier, prod = pol.policy?.productIdentifier;
        if (lt && prod) pairs.set(`${lt}|${prod}`, { lt, prod });
      } catch {}
    }
  }
  const tenant = process.argv[2];
  const outDir = process.argv[3];
  const batch = [...pairs.values()].map(({lt, prod}) => ({
    id: `${lt}|${prod}`,
    args: ["gov", "aops-policy", "deployed-policy", "get", lt, prod, tenant],
    out: path.join(outDir, `resp-${lt}-${prod}.json`)
  }));
  fs.writeFileSync(process.argv[4], JSON.stringify(batch, null, 2));
' "$PACKS_ROOT" "$UIPATH_TENANT_ID" "$RUNDIR" "$BATCH"

node "$SKILL_DIR/assets/scripts/parallel-cli.mjs" \
  --batch       "$BATCH" \
  --results     "$RESULTS" \
  --concurrency 8

# Merge each response file's Data subtree into cache-before.json under the pair key.
# Also apply the cross-product guard (Step 1b): if Data.productIdentifier doesn't match
# the product we queried with, drop the entry rather than letting phantom drift leak in.
node -e '
  const fs = require("fs"), path = require("path");
  const results = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
  const out = {};
  for (const [key, r] of Object.entries(results)) {
    if (!r.ok || !r.out) continue;
    const resp = JSON.parse(fs.readFileSync(r.out, "utf8"));
    if (resp?.Result !== "Success") continue;
    const data = resp.Data ?? null;
    const [, expectedProduct] = key.split("|");
    const liveProduct = data?.productIdentifier ?? data?.product?.identifier ?? data?.product ?? null;
    if (liveProduct && liveProduct !== expectedProduct) continue;  // cross-product fallback — skip
    out[key] = data;
  }
  fs.writeFileSync(process.argv[2], JSON.stringify(out, null, 2));
' "$RESULTS" "$RUNDIR/cache-before.json"
CACHE_BEFORE="$RUNDIR/cache-before.json"
```

`parallel-cli.mjs` reports `X/Y ok, Z failed, <wall>s wall`. Typical numbers: 10 pairs at concurrency 8 ≈ 1.5–3s vs. 6–10s serial. If a pair fails (permission, timeout), that entry drops from the cache and the walker records it as `cache-miss` — it does not abort the run.

### Step 3 — Build the AFTER cache

The after cache is the before cache with exactly one entry replaced:

```bash
CACHE_AFTER="$EXTRACTED_ROOT/../cache-after.json"
node -e '
  const fs = require("fs");
  const before = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
  const after = structuredClone(before);
  const key = process.argv[2];                       // "<lt>|<product>"
  const proposed = JSON.parse(fs.readFileSync(process.argv[3], "utf8")); // the proposed formData
  after[key] = {
    ...(after[key] ?? { deployment: { type: "TENANT" } }),
    data: proposed,
  };
  fs.writeFileSync(process.argv[4], JSON.stringify(after, null, 2));
' "$CACHE_BEFORE" "<lt>|<product>" "$PROPOSED_FORMDATA_JSON" "$CACHE_AFTER"
```

### Step 4 — Run the impact script

```bash
node <skill-root>/assets/scripts/impact.mjs \
  --packs-root       "$EXTRACTED_ROOT" \
  --cli-cache-before "$CACHE_BEFORE" \
  --cli-cache-after  "$CACHE_AFTER" \
  --target-product   "<productIdentifier>" \
  --json-out         "$EXTRACTED_ROOT/../impact.json"
```

The script walks affected packs in parallel (before + after concurrently per pack, all packs concurrently). Runtime is dominated by JSON parsing — typically < 500 ms for 3–5 packs.

### Step 5 — Surface at the approval gate

Paste the terminal summary directly into the approval prompt. Apply this decision rule:

| Situation | Default prompt |
|---|---|
| `totals.mandatoryRegressions > 0` | Default to `n`. Require the user to type `yes` explicitly, calling out the regressed clause by id. |
| `totals.totalRegressions > 0` (non-mandatory only) | Surface the regression. Normal `y / partial / n` prompt; user decides. |
| Only improvements | Surface as a positive signal. Normal prompt. |
| No change | Mention it briefly and continue. |
| All packs `unaffected` | Skip the section; note "no packs touch this product". |

## Performance notes

- **Why parallel packs**: a user may have 3–10 packs locally; serial would take 5–10× longer. Each pack walk is ~50–200 ms of JSON work; `Promise.all` across packs runs them concurrently on Node's event loop.
- **Why parallel unzip**: 5 packs × 50 ms sequential is 250 ms of wall clock; parallel drops it to ~60 ms. Noticeable because extraction happens every session.
- **Why before+after concurrent**: two independent pure walks over the same pack, zero contention.
- **Cache miss handling**: the impact walker runs in `strict: false` mode — unknown `(lt, product)` pairs in the after cache are reported as skipped rather than aborting. Important because the user may be changing a product the pack references but the tenant has never deployed.

## Files

- `assets/scripts/walker-core.mjs` — shared pure-function walker (consumed by both check and impact)
- `assets/scripts/impact.mjs` — the before/after orchestrator
- `assets/scripts/check-walk.mjs` — single-pack check wrapper (see check/impl.md)

## Out of scope

- **Access policies** — same limitation as Check. Packs referencing access-level policies report those contributions as `skipped` in both walks, so they don't show up as regressions.
- **Group/user deployment** — the simulated cache only replaces the tenant-level entry. If the proposed change is at group/user scope, this primitive currently reports unaffected. (A future iteration can resolve effective policy per scope.)
- **Cross-product blast radius** — if a proposed AITrustLayer change incidentally affects a Robot clause via some shared property, the walker will catch it as long as the pack declares the dependency. It won't infer dependencies the pack doesn't state.
