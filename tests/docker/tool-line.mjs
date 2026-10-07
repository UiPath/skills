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
//   node tool-line.mjs train <cli-version>
//       Print the train of an installed CLI version: its first prerelease
//       identifier (`1.205.0-dev.9071` -> `dev`), or `latest` for a stable
//       version. The tag name in CLI_VERSION is not the train: GitHub Packages
//       `cli@latest` is a dev build.
//   node tool-line.mjs pick <package> <line-prefix> <train> [<registry>]
//       Print the highest published version of <package> on <line-prefix>
//       from <train>: for `latest`, stable versions only; for any other train
//       (dev, preview, ...), prereleases whose first identifier is <train>.
//       <registry> overrides the `@uipath` scope registry for the lookup.
//       Exit codes:
//         0  printed the version.
//         3  nothing to install: the package is not on <registry> (E404,
//            only when <registry> is given), or the train has no build on
//            this line or an older one (the tool is newer than the CLI).
//            Safe to skip.
//         4  the train has builds on an older line but none on this one: the
//            tool lags the CLI (a line bump in progress). Fail the build.
//         5  the registry lookup failed (network, auth), including an E404
//            from the default (GitHub Packages) registry: a token that cannot
//            read a package also gets a 404 there. Fail the build.
//   node tool-line.mjs check <line-prefix> <expected-count>  < tools-list.json
//       Read `uip tools list --output json` on stdin. Exit 1 when the list is
//       unreadable or empty, when it does not hold <expected-count> tools, or
//       when any tool is off <line-prefix>.

import { spawnSync } from "node:child_process";
import { readFileSync, realpathSync } from "node:fs";
import { pathToFileURL } from "node:url";

export function linePrefix(version) {
    const [major, minor] = String(version).trim().split(".");
    if (!/^\d+$/.test(major ?? "") || !/^\d+$/.test(minor ?? "")) {
        throw new Error(`not a version: '${version}'`);
    }
    return `${major}.${minor}.`;
}

export function trainOf(version) {
    const parsed = parse(String(version).trim());
    if (!parsed) throw new Error(`not a version: '${version}'`);
    return parsed.pre.length ? parsed.pre[0] : "latest";
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

// Returns { version } for the highest build of `train` on `prefix`, or
// { version: null, lagging } where `lagging` is the highest build of `train`
// on an older line (null when there is none).
export function pickVersion(versions, prefix, train) {
    const line = parse(`${prefix}0`).core;
    let best = null;
    let lagging = null;
    for (const version of versions) {
        const parsed = parse(version);
        if (!parsed) continue;
        const onTrain =
            train === "latest"
                ? parsed.pre.length === 0
                : parsed.pre[0] === train;
        if (!onTrain) continue;
        if (version.startsWith(prefix)) {
            if (!best || compare(parsed, best.parsed) > 0) {
                best = { version, parsed };
            }
        } else if (
            parsed.core[0] < line[0] ||
            (parsed.core[0] === line[0] && parsed.core[1] < line[1])
        ) {
            if (!lagging || compare(parsed, lagging.parsed) > 0) {
                lagging = { version, parsed };
            }
        }
    }
    return {
        version: best?.version ?? null,
        lagging: best ? null : (lagging?.version ?? null),
    };
}

// Throws when the list cannot prove anything: a missing, non-array or empty
// `Data`, or a tool count other than `expected`.
export function offLineTools(toolList, prefix, expected) {
    const tools = toolList?.Data;
    if (!Array.isArray(tools) || tools.length === 0) {
        throw new Error("`uip tools list` returned no tools in `Data`");
    }
    if (expected !== undefined && tools.length !== expected) {
        throw new Error(
            `\`uip tools list\` shows ${tools.length} tools, but ${expected} were installed`,
        );
    }
    return tools
        .filter((tool) => !String(tool.Version ?? "").startsWith(prefix))
        .map((tool) => `${tool.Name}@${tool.Version}`);
}

// `npm view` stderr -> "missing" or "error". An E404 means "missing" only on
// an explicit <registry> (public npm). On the default GitHub Packages feed a
// token without read access to a package also gets a 404, so it is an error.
export function lookupFailure(stderr, registry) {
    return registry && /\bE404\b/.test(String(stderr)) ? "missing" : "error";
}

function main(argv) {
    const [mode, ...args] = argv;
    if (mode === "line" && args.length === 1) {
        console.log(linePrefix(args[0]));
        return 0;
    }
    if (mode === "train" && args.length === 1) {
        console.log(trainOf(args[0]));
        return 0;
    }
    if (mode === "pick" && (args.length === 3 || args.length === 4)) {
        const [pkg, prefix, train, registry] = args;
        const npmArgs = ["view", pkg, "versions", "--json"];
        if (registry) npmArgs.push(`--@uipath:registry=${registry}`);
        const result = spawnSync("npm", npmArgs, {
            encoding: "utf8",
            stdio: ["ignore", "pipe", "pipe"],
        });
        if (result.status !== 0) {
            if (lookupFailure(result.stderr, registry) === "missing") {
                console.error(`${pkg}: not published on this registry`);
                return 3;
            }
            process.stderr.write(result.stderr ?? "");
            console.error(
                `${pkg}: registry lookup failed (${result.error?.message ?? `npm exit ${result.status}`})`,
            );
            return 5;
        }
        const parsed = JSON.parse(result.stdout);
        const versions = Array.isArray(parsed) ? parsed : [parsed];
        const { version, lagging } = pickVersion(versions, prefix, train);
        if (version) {
            console.log(version);
            return 0;
        }
        if (lagging) {
            console.error(
                `${pkg}: newest ${train} build is ${lagging}, none on the CLI's ${prefix}x line yet`,
            );
            return 4;
        }
        console.error(`${pkg}: no ${train} build on the ${prefix}x line or older`);
        return 3;
    }
    if (mode === "check" && args.length === 2) {
        const expected = Number(args[1]);
        if (!Number.isInteger(expected) || expected < 1) {
            throw new Error(`not a tool count: '${args[1]}'`);
        }
        const off = offLineTools(
            JSON.parse(readFileSync(0, "utf8")),
            args[0],
            expected,
        );
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
        "usage: tool-line.mjs line <version> | train <version> | pick <pkg> <prefix> <train> [<registry>] | check <prefix> <count>",
    );
    return 2;
}

// Node resolves the entry script's symlinks before setting import.meta.url, so
// compare against the real path's file URL (also right for spaces and Windows
// drive paths).
if (
    process.argv[1] &&
    import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href
) {
    process.exit(main(process.argv.slice(2)));
}
