#!/usr/bin/env node
// Keep tool plugins on the installed CLI's release line.
//
// The CLI runs a tool only when the tool's `major.minor` matches its own
// (UiPath/cli packages/cli/src/services/tool-manager.ts, `cliVersionPrefix`;
// the prefix rule is `versionLinePrefix` in services/versionPin.ts). A dist-tag
// such as `@dev` is a per-package pointer, so `@uipath/cli@dev` and
// `@uipath/maestro-tool@dev` can sit on different lines. On 2026-10-05 they
// did (1.204.0-dev.9000 vs 1.205.0-dev.9021), and every `uip maestro` and
// `uip solution` call in the image failed with `not_found` / RetryWillNotFix.
//
// Usage:
//   node tool-line.mjs line <cli-version>
//       Print the `major.minor.` prefix, e.g. `1.204.`.
//   node tool-line.mjs pick <package> <line-prefix> <tag> [<registry>]
//       Print the highest published version of <package> on <line-prefix>
//       from the same train as <tag>: for `latest`, stable versions only; for
//       any other tag (dev, preview, ...), prereleases whose first identifier
//       is <tag>. <registry> overrides the `@uipath` scope registry for the
//       lookup. Exit 3 when the package has no such version.
//   node tool-line.mjs check <line-prefix>  < uip-tools-list.json
//       Read `uip tools list --output json` on stdin. Exit 1 and name every
//       installed tool that is off <line-prefix>.

import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";

export function linePrefix(version) {
    const [major, minor] = String(version).trim().split(".");
    if (!/^\d+$/.test(major ?? "") || !/^\d+$/.test(minor ?? "")) {
        throw new Error(`not a version: '${version}'`);
    }
    return `${major}.${minor}.`;
}

function parse(version) {
    const match = /^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+.*)?$/.exec(
        version,
    );
    if (!match) return null;
    return {
        core: [Number(match[1]), Number(match[2]), Number(match[3])],
        pre: match[4] ? match[4].split(".") : [],
    };
}

// semver 2.0 precedence.
function compare(a, b) {
    for (let i = 0; i < 3; i++) {
        if (a.core[i] !== b.core[i]) return a.core[i] - b.core[i];
    }
    if (!a.pre.length || !b.pre.length) return b.pre.length - a.pre.length;
    for (let i = 0; i < Math.max(a.pre.length, b.pre.length); i++) {
        const x = a.pre[i];
        const y = b.pre[i];
        if (x === undefined) return -1;
        if (y === undefined) return 1;
        const xn = /^\d+$/.test(x);
        const yn = /^\d+$/.test(y);
        if (xn && yn) {
            if (Number(x) !== Number(y)) return Number(x) - Number(y);
        } else if (xn !== yn) {
            return xn ? -1 : 1;
        } else if (x !== y) {
            return x < y ? -1 : 1;
        }
    }
    return 0;
}

export function pickVersion(versions, prefix, tag) {
    let best = null;
    for (const version of versions) {
        if (!version.startsWith(prefix)) continue;
        const parsed = parse(version);
        if (!parsed) continue;
        const onTrain =
            tag === "latest" ? parsed.pre.length === 0 : parsed.pre[0] === tag;
        if (!onTrain) continue;
        if (!best || compare(parsed, best.parsed) > 0) {
            best = { version, parsed };
        }
    }
    return best?.version ?? null;
}

export function offLineTools(toolList, prefix) {
    const tools = Array.isArray(toolList?.Data) ? toolList.Data : [];
    return tools
        .filter((tool) => !String(tool.Version ?? "").startsWith(prefix))
        .map((tool) => `${tool.Name}@${tool.Version}`);
}

function main(argv) {
    const [mode, ...args] = argv;
    if (mode === "line" && args.length === 1) {
        console.log(linePrefix(args[0]));
        return 0;
    }
    if (mode === "pick" && (args.length === 3 || args.length === 4)) {
        const [pkg, prefix, tag, registry] = args;
        const npmArgs = ["view", pkg, "versions", "--json"];
        if (registry) npmArgs.push(`--@uipath:registry=${registry}`);
        const raw = execFileSync("npm", npmArgs, {
            encoding: "utf8",
            stdio: ["ignore", "pipe", "inherit"],
        });
        const parsed = JSON.parse(raw);
        const versions = Array.isArray(parsed) ? parsed : [parsed];
        const version = pickVersion(versions, prefix, tag);
        if (!version) {
            console.error(`${pkg}: no ${tag} build on the ${prefix}x line`);
            return 3;
        }
        console.log(version);
        return 0;
    }
    if (mode === "check" && args.length === 1) {
        const off = offLineTools(JSON.parse(readFileSync(0, "utf8")), args[0]);
        if (off.length) {
            console.error(
                `Error: ${off.length} tool(s) off the CLI's ${args[0]}x line: ${off.join(", ")}`,
            );
            return 1;
        }
        console.error(`All installed tools are on the CLI's ${args[0]}x line`);
        return 0;
    }
    console.error(
        "usage: tool-line.mjs line <version> | pick <pkg> <prefix> <tag> [<registry>] | check <prefix>",
    );
    return 2;
}

if (import.meta.url === `file://${process.argv[1]}`) {
    process.exit(main(process.argv.slice(2)));
}
