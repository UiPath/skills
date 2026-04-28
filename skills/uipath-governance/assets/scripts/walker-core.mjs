/**
 * Shared pack-walker core. Pure function: given an extracted pack directory
 * and a CLI cache (live or simulated), return per-clause compliance status.
 *
 * No filesystem writes, no process.exit. Consumed by check-walk.mjs (single
 * pack, writes report) and impact.mjs (before/after diff across packs).
 */

import fs from "node:fs";
import path from "node:path";

export function readJson(p) {
    return JSON.parse(fs.readFileSync(p, "utf8"));
}

export function getNested(obj, dotted) {
    if (obj == null) return undefined;
    let cur = obj;
    for (const seg of dotted.split(".")) {
        if (cur && typeof cur === "object" && seg in cur) cur = cur[seg];
        else return undefined;
    }
    return cur;
}

export function deepEqual(a, b) {
    if (a === b) return true;
    if (a == null || b == null) return a === b;
    if (
        Array.isArray(a) &&
        Array.isArray(b) &&
        a.length > 0 &&
        typeof a[0] === "object" &&
        a[0] !== null &&
        "identifier" in a[0]
    ) {
        const ai = new Map(a.filter((x) => x && typeof x === "object").map((x) => [x.identifier, x]));
        const bi = new Map(b.filter((x) => x && typeof x === "object").map((x) => [x.identifier, x]));
        if (ai.size !== bi.size) return false;
        for (const [k, v] of ai) {
            if (!bi.has(k)) return false;
            if (!deepEqual(v, bi.get(k))) return false;
        }
        return true;
    }
    if (Array.isArray(a) !== Array.isArray(b)) return false;
    if (Array.isArray(a)) {
        if (a.length !== b.length) return false;
        return a.every((v, i) => deepEqual(v, b[i]));
    }
    if (typeof a === "object" && typeof b === "object") {
        const ak = Object.keys(a);
        if (ak.length !== Object.keys(b).length) return false;
        return ak.every((k) => deepEqual(a[k], b[k]));
    }
    return false;
}

/**
 * Preload a pack's manifest, clause-map, and every referenced policy file.
 * Returns a value that can be passed as `pack` to multiple `walkPack` calls
 * — e.g., Impact's before/after walks share one preload, halving fs+parse
 * work.
 *
 * @param {string} packDir  Extracted pack directory
 * @returns {object} { packDir, manifest, clauseMap, manifestByFile, policies }
 */
export function preloadPack(packDir) {
    const manifest = readJson(path.join(packDir, "manifest.json"));
    const clauseMap = readJson(path.join(packDir, "clause-map.json"));
    const manifestByFile = new Map(manifest.policies.map((p) => [p.file, p]));
    const policies = new Map();
    for (const entry of manifest.policies) {
        try { policies.set(entry.file, readJson(path.join(packDir, entry.file))); }
        catch (e) { /* leave missing — walker surfaces it per clause */ }
    }
    return { packDir, manifest, clauseMap, manifestByFile, policies };
}

/**
 * Walk a single pack against a CLI cache.
 *
 * @param {object} input
 * @param {string} [input.packDir]    Extracted pack directory (ignored if `pack` provided)
 * @param {object} [input.pack]       Pre-loaded pack from `preloadPack()` — preferred when
 *                                    walking the same pack multiple times.
 * @param {object} input.cliCache     { "<license>|<product>": { data, "policy-name", deployment } }
 * @param {boolean} [input.strict]    If true, cache miss throws; if false, clause is skipped
 * @returns {object}  { manifest, clauseMap, clauses, summary, skippedPolicies, productsTouched }
 */
export function walkPack({ packDir, pack, cliCache, strict = true }) {
    const preloaded = pack ?? preloadPack(packDir);
    const { manifest, clauseMap, manifestByFile, policies } = preloaded;

    const loadPolicy = (rel) => {
        if (policies.has(rel)) return policies.get(rel);
        // Fallback: lazy-read if somehow not preloaded
        const loaded = readJson(path.join(preloaded.packDir, rel));
        policies.set(rel, loaded);
        return loaded;
    };

    const resolveLevel = (rel, p) => manifestByFile.get(rel)?.deploymentLevel ?? p.deploymentLevel ?? "tenant";

    const clauses = [];
    const skippedPoliciesSet = new Map();
    const productsTouched = new Set();

    for (const clause of clauseMap.clauses) {
        const result = {
            clauseId: clause.id,
            name: clause.name ?? "",
            category: clause.category ?? null,
            obligationLevel:
                clause.obligationLevel ??
                (clause.mandatory === true
                    ? "Mandatory"
                    : clause.mandatory === false
                    ? "Optional"
                    : "Mandatory"),
            status: "unknown",
            contributions: [],
        };

        for (const contrib of clause.contributions ?? []) {
            const rel = contrib.uipolicyFile;
            const policy = loadPolicy(rel);
            const kind = policy.policyKind ?? "product";
            const productId = policy.policy?.productIdentifier;
            const accessType = policy.accessPolicy?.accessPolicyType;

            if (kind === "access") {
                result.contributions.push({
                    policyFile: rel,
                    product: accessType,
                    status: "skipped",
                    reason: "access-policies-not-yet-supported",
                    properties: [],
                });
                skippedPoliciesSet.set(rel, { product: accessType ?? "access", reason: "access-policies-not-yet-supported" });
                continue;
            }

            const level = resolveLevel(rel, policy);
            if (level !== "tenant") {
                result.contributions.push({
                    policyFile: rel,
                    product: productId,
                    status: "skipped",
                    reason: `${level}-scope-check-not-supported`,
                    properties: [],
                });
                skippedPoliciesSet.set(rel, { product: productId, reason: `${level}-scope-check-not-supported` });
                continue;
            }

            if (productId) productsTouched.add(productId);

            const licenseType = policy.policy.licenseTypeIdentifier;
            const key = `${licenseType}|${productId}`;
            if (!(key in cliCache)) {
                if (strict) throw new Error(`cache miss for ${key}`);
                result.contributions.push({
                    policyFile: rel,
                    product: productId,
                    status: "skipped",
                    reason: "cache-miss",
                    properties: [],
                });
                skippedPoliciesSet.set(rel, { product: productId, reason: "cache-miss" });
                continue;
            }
            const live = cliCache[key];

            // Guard: deployed-policy get sometimes returns a cross-product fallback
            // (e.g., NoLicense|StudioWeb may resolve to an AITrustLayer policy when no
            // StudioWeb-specific policy is deployed). Comparing AITL-shaped data against
            // a StudioWeb pack produces phantom drift. Skip these entries explicitly.
            const liveProduct =
                live?.productIdentifier ?? live?.product?.identifier ?? live?.product ?? null;
            if (liveProduct && liveProduct !== productId) {
                result.contributions.push({
                    policyFile: rel,
                    product: productId,
                    status: "skipped",
                    reason: `cross-product-fallback (expected ${productId}, CLI returned ${liveProduct})`,
                    properties: [],
                });
                skippedPoliciesSet.set(rel, {
                    product: productId,
                    reason: `cross-product-fallback (got ${liveProduct})`,
                });
                continue;
            }

            const liveData = live?.data ?? null;

            const properties = [];
            const expectedFd = policy.formData ?? {};
            for (const p of contrib.properties ?? []) {
                const expected = getNested(expectedFd, p);
                const actual = getNested(liveData, p);
                properties.push({
                    path: p,
                    expected: expected ?? null,
                    actual: actual ?? null,
                    match: deepEqual(expected, actual),
                });
            }

            result.contributions.push({
                policyFile: rel,
                product: productId,
                status: "checked",
                effectivePolicyName: live?.["policy-name"] ?? null,
                effectiveDeployment: live?.deployment ?? null,
                properties,
            });
        }

        const checked = result.contributions.filter((c) => c.status === "checked");
        if (checked.some((c) => c.properties.some((p) => !p.match))) result.status = "drifted";
        else if (checked.length > 0) result.status = "compliant";
        else result.status = "skipped";

        clauses.push(result);
    }

    const summary = {
        totalClauses: clauses.length,
        compliant: clauses.filter((c) => c.status === "compliant").length,
        drifted: clauses.filter((c) => c.status === "drifted").length,
        skipped: clauses.filter((c) => c.status === "skipped").length,
    };

    const skippedPolicies = [...skippedPoliciesSet.entries()].map(([file, meta]) => ({
        file,
        product: meta.product,
        reason: meta.reason,
    }));

    return { manifest, clauseMap, clauses, summary, skippedPolicies, productsTouched: [...productsTouched] };
}
