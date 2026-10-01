// Stopgap for CLI_SOURCE=archive (see tests/docker/Dockerfile).
//
// install.js installs the UiPath/cli air-gapped archive with
// `npm install -g --offline`, which fails (ENOTCACHED) when the install needs a
// package the archive does not carry. Build 10's archive (export-airgapped run
// 36882965827) lacks the runtime dependencies the CLI ships unbundled
// (typescript, @earendil-works/pi-coding-agent and its closure, fflate), the
// external @uipath/integration-service-design-time, and required peers such as
// @uipath/flow-converter. Remove once UiPath/cli's build-airgap-archive.mjs
// packs the full runtime closure.
//
//   warm  <dir>  run the archive's own install.js ONLINE into a throwaway
//                prefix, so npm's cache holds exactly the closure the real
//                offline install will resolve; then the image runs install.js
//                unchanged.
//   audit <dir>  after the real install: every installed copy of a package the
//                archive contains, nested copies included, must be the
//                archive's version. A registry copy of a stack package would
//                mean the run no longer tests the stack, so it fails the build.
"use strict";
const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const [mode, dir] = process.argv.slice(2);

function archiveVersions() {
    const versions = new Map();
    for (const f of fs.readdirSync(dir).filter((n) => n.endsWith(".tgz"))) {
        try {
            const m = JSON.parse(
                execFileSync("tar", ["-xzOf", path.join(dir, f), "package/package.json"], { encoding: "utf8" }),
            );
            versions.set(m.name, m.version);
        } catch {
            // native/vendored tarballs without a package/package.json
        }
    }
    return versions;
}

if (mode === "warm") {
    const source = fs.readFileSync(path.join(dir, "install.js"), "utf8");
    // Online, and without lifecycle scripts: priming needs the cache, not
    // built natives (kerberos runs node-gyp); the real install still runs them.
    const online = source.replace(/"--offline",\s*/, '"--ignore-scripts", ');
    if (online === source) throw new Error("install.js no longer passes \"--offline\"; revisit this stopgap");
    const copy = path.join(dir, "install-online.js");
    fs.writeFileSync(copy, online);
    const scratch = fs.mkdtempSync(path.join(os.tmpdir(), "warm-"));
    try {
        execFileSync("node", [copy, scratch], { stdio: "inherit" });
    } finally {
        fs.rmSync(scratch, { recursive: true, force: true });
        fs.rmSync(copy, { force: true });
    }
    console.log("warm-unbundled-deps: npm cache primed with the archive's install closure");
} else if (mode === "audit") {
    const versions = archiveVersions();
    const root = execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim();
    const foreign = [];
    const seen = new Set();
    const walk = (d, depth) => {
        if (depth > 12 || !fs.existsSync(d)) return;
        for (const e of fs.readdirSync(d, { withFileTypes: true })) {
            if (!e.isDirectory()) continue;
            const p = path.join(d, e.name);
            if (e.name.startsWith("@")) { walk(p, depth); continue; }
            const pj = path.join(p, "package.json");
            if (fs.existsSync(pj)) {
                const { name, version } = JSON.parse(fs.readFileSync(pj, "utf8"));
                if (versions.get(name) === version) seen.add(name);
                if (versions.has(name) && versions.get(name) !== version) foreign.push(`${name}@${version} at ${p} (archive has ${versions.get(name)})`);
            }
            walk(path.join(p, "node_modules"), depth + 1);
        }
    };
    walk(root, 0);
    // An empty install would otherwise pass. install.js installs the CLI, every
    // tool and skills by name (manifest.json); each must be at the global root
    // at the archive's version. The archive's other tarballs are libraries it
    // carries for dependency resolution, installed only where something needs them.
    const manifest = JSON.parse(fs.readFileSync(path.join(dir, "manifest.json"), "utf8"));
    const named = [manifest.cli, ...(manifest.tools || []).map((t) => ({ name: t.package, version: t.version }))];
    if (manifest.skills) named.push(manifest.skills);
    const absent = named.filter(({ name, version }) => {
        const pj = path.join(root, name, "package.json");
        return !fs.existsSync(pj) || JSON.parse(fs.readFileSync(pj, "utf8")).version !== version;
    });
    if (absent.length) {
        console.error(`audit: ${absent.length} of the ${named.length} packages install.js installs are missing or at another version:\n  ${absent.map((p) => `${p.name}@${p.version}`).join("\n  ")}`);
        process.exit(1);
    }
    if (foreign.length) {
        console.error(`audit: ${foreign.length} installed copies of stack packages are not the archive's:\n  ${foreign.join("\n  ")}`);
        process.exit(1);
    }
    console.log(`audit: ${named.length} named packages (cli, ${named.length - 2} tools, skills) at the archive's versions; every installed copy of the archive's ${versions.size} packages matches; archive built from UiPath/cli ${manifest.generatedFromGitSha}`);
} else {
    throw new Error("usage: warm-unbundled-deps.js warm|audit <archive-dir>");
}
