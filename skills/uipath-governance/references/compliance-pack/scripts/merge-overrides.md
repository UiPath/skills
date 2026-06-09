# merge-overrides

Deep-merges compliance pack overrides onto a base formData object (template defaults for new policies, or existing deployed policy data for subset updates). Output is ready to pass directly to `uip gov aops-policy create|update --input`.

**Merge rules:**
- Objects → recursive key-by-key merge
- Arrays → wholesale replace (override wins; `[]` is a deliberate clear)
- Scalars → replace
- Explicit `null` → clear that leaf
- Paths the override doesn't touch → kept from base

**Write to disk before running:**
```bash
node "$SESSION_TEMP/merge-overrides.mjs" \
  --base      "$SESSION_TEMP/products/<product>/form-data.json" \
  --overrides "$SESSION_TEMP/overrides/<product>.json" \
  --out       "$SESSION_TEMP/merged/<product>.json" \
  --summary
```

`--summary` prints the list of overridden paths — useful for confirming which compliance pack settings were applied.

**Exit codes:** `0` = merged file written · `2` = missing or malformed inputs

## Script

```js
#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const args = {};
for (let i = 2; i < process.argv.length; i++) {
    const a = process.argv[i];
    if (a === "--summary") { args.summary = true; continue; }
    if (a.startsWith("--")) args[a.slice(2)] = process.argv[++i];
}
const basePath = args.base ?? args.defaults;
for (const [k, v] of Object.entries({ base: basePath, overrides: args.overrides, out: args.out })) {
    if (!v) {
        console.error(`error: --${k === "base" ? "base (or --defaults)" : k} is required`);
        process.exit(2);
    }
}

function readJson(p) {
    try { return JSON.parse(fs.readFileSync(p, "utf8")); }
    catch (e) { console.error(`error: ${p}: ${e.message}`); process.exit(2); }
}

const base = readJson(basePath);
const overrides = readJson(args.overrides);

if (base === null || typeof base !== "object" || Array.isArray(base)) {
    console.error(`error: --base must be an object (the bare formData, not wrapped in { data: ... })`);
    process.exit(2);
}
if (overrides === null || typeof overrides !== "object" || Array.isArray(overrides)) {
    console.error(`error: --overrides must be an object (the bare formData, not wrapped in { data: ... })`);
    process.exit(2);
}

const touched = [];

function isPlainObject(v) {
    return v !== null && typeof v === "object" && !Array.isArray(v);
}

function merge(dst, src, trail) {
    for (const key of Object.keys(src)) {
        const overrideVal = src[key];
        const next = trail ? `${trail}.${key}` : key;
        if (overrideVal === null) {
            dst[key] = null;
            touched.push({ path: next, op: "clear" });
            continue;
        }
        if (isPlainObject(overrideVal)) {
            if (!isPlainObject(dst[key])) dst[key] = {};
            merge(dst[key], overrideVal, next);
            continue;
        }
        if (Array.isArray(overrideVal)) {
            dst[key] = overrideVal.slice();
            touched.push({ path: next, op: "replace-array", size: overrideVal.length });
            continue;
        }
        dst[key] = overrideVal;
        touched.push({ path: next, op: "replace-scalar" });
    }
    return dst;
}

const merged = JSON.parse(JSON.stringify(base));
merge(merged, overrides, "");

fs.mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
fs.writeFileSync(args.out, JSON.stringify(merged, null, 2));
process.stdout.write(`MERGED: ${path.resolve(args.out)}\n`);

if (args.summary) {
    process.stdout.write(`Overridden paths: ${touched.length}\n`);
    const grouped = touched.slice(0, 20);
    for (const t of grouped) {
        process.stdout.write(`  ${t.op.padEnd(16)} ${t.path}${t.size != null ? ` (array[${t.size}])` : ""}\n`);
    }
    if (touched.length > 20) process.stdout.write(`  … and ${touched.length - 20} more\n`);
}
```
