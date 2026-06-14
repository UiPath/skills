# synthesize-formdata

Extracts compliance pack catalog contributions for a given product + clause subset and writes them as a flat formData overrides object.

**Write to disk before running:**
```bash
# Unix
cat > "$SESSION_TEMP/synthesize-formdata.mjs" << 'SCRIPT'
# Windows PS
Set-Content "$tmpDir\synthesize-formdata.mjs" -Value @'
```

Paste the script block below, then:
```bash
node "$SESSION_TEMP/synthesize-formdata.mjs" \
  --catalog    "$SESSION_TEMP/catalog.json" \
  --product    "<productIdentifier>" \
  --clause-ids "<clauseId1,clauseId2,...>" \
  --out        "$SESSION_TEMP/overrides/<product>.json"
```

**Exit codes:** `0` = written · `2` = bad args · `3` = no contributions for product+clauses (skip this product, continue)

**Warnings on stdout:** lines starting with `⚠` indicate controls whose values are org-specific (`notEmpty`) or are access-policy checks (`exists`) — collect those values from the user before proceeding.

## Script

```js
#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const args = {};
for (let i = 2; i < process.argv.length; i++) {
    if (process.argv[i].startsWith("--")) args[process.argv[i].slice(2)] = process.argv[++i];
}
for (const r of ["catalog", "product", "clause-ids", "out"]) {
    if (!args[r]) { console.error(`error: --${r} is required`); process.exit(2); }
}

function readJson(p) {
    try { return JSON.parse(fs.readFileSync(p, "utf8")); }
    catch (e) { console.error(`error reading ${p}: ${e.message}`); process.exit(2); }
}

function setNested(obj, dotted, value) {
    const segs = dotted.split(".");
    let cur = obj;
    for (let i = 0; i < segs.length - 1; i++) {
        if (cur[segs[i]] == null || typeof cur[segs[i]] !== "object") cur[segs[i]] = {};
        cur = cur[segs[i]];
    }
    cur[segs.at(-1)] = value;
}

const raw = readJson(args["catalog"]);
// Normalize: CLI output is PascalCase; accept both PascalCase and camelCase.
const data = raw?.PackId || raw?.packId ? raw : (raw?.Data ?? raw);
function pick(obj, ...keys) { for (const k of keys) if (obj[k] !== undefined) return obj[k]; }
const catalog = {
    clauses: (pick(data, "Clauses", "clauses") ?? []).map(c => ({
        clauseId: pick(c, "ClauseId", "clauseId"),
        editorialPolicies: (pick(c, "EditorialPolicies", "editorialPolicies") ?? []).map(ep => ({
            productIdentifier: pick(ep, "ProductIdentifier", "productIdentifier"),
            contributions: (pick(ep, "Contributions", "contributions") ?? []).map(cn => {
                const req = pick(cn, "Required", "required") ?? {};
                return {
                    key: pick(cn, "Key", "key"),
                    required: {
                        eq:       pick(req, "Eq",       "eq"),
                        gte:      pick(req, "Gte",      "gte"),
                        lte:      pick(req, "Lte",      "lte"),
                        contains: pick(req, "Contains", "contains"),
                        notEmpty: pick(req, "NotEmpty", "notEmpty"),
                        exists:   pick(req, "Exists",   "exists"),
                    },
                };
            }),
        })),
    })),
};
const targetProduct = args["product"];
const targetClauseIds = new Set(args["clause-ids"].split(",").map(s => s.trim()).filter(Boolean));

const formData = {};
const warnings = [];
let count = 0;

for (const clause of catalog.clauses) {
    if (!targetClauseIds.has(clause.clauseId)) continue;
    for (const ep of clause.editorialPolicies) {
        if (ep.productIdentifier !== targetProduct) continue;
        for (const { key, required } of ep.contributions) {
            if (!required) continue;
            if (required.eq !== undefined)             { setNested(formData, key, required.eq);        count++; }
            else if (required.gte !== undefined)       { setNested(formData, key, required.gte);       count++; }
            else if (required.lte !== undefined)       { setNested(formData, key, required.lte);       count++; }
            else if (Array.isArray(required.contains)) { setNested(formData, key, required.contains);  count++; }
            else if (required.notEmpty === true)       warnings.push(`"${key}": notEmpty — value is org-specific; configure manually`);
            else if (required.exists === true)         warnings.push(`"${key}": exists — access policy check, not a formData key`);
            else warnings.push(`"${key}": unknown operator ${JSON.stringify(required)}`);
        }
    }
}

if (count === 0) {
    console.error(`error: no contributions for product "${targetProduct}" in clauses [${[...targetClauseIds].join(", ")}]`);
    process.exit(3);
}

warnings.forEach(w => console.warn(`  ⚠ ${w}`));
fs.mkdirSync(path.dirname(path.resolve(args["out"])), { recursive: true });
fs.writeFileSync(args["out"], JSON.stringify(formData, null, 2));
process.stdout.write(`SYNTHESIZED: ${path.resolve(args["out"])} (${count} contributions)\n`);
```
