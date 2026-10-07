import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
    chmodSync,
    copyFileSync,
    mkdtempSync,
    rmSync,
    symlinkSync,
    writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { after, describe, test } from "node:test";
import { fileURLToPath } from "node:url";

import {
    linePrefix,
    lookupFailure,
    offLineTools,
    pickVersion,
    trainOf,
} from "./tool-line.mjs";

const script = join(dirname(fileURLToPath(import.meta.url)), "tool-line.mjs");
const scratch = mkdtempSync(join(tmpdir(), "tool-line test "));
after(() => rmSync(scratch, { recursive: true, force: true }));

// Runs tool-line.mjs as the Dockerfile does. `npmOut` / `npmErr` / `npmRc`
// stand in for `npm view` through a fake `npm` first on PATH.
function run(args, { input, entry = script, npmOut = "", npmErr = "", npmRc = 0 } = {}) {
    const bin = mkdtempSync(join(scratch, "bin-"));
    writeFileSync(join(bin, "out"), npmOut);
    writeFileSync(join(bin, "err"), npmErr);
    writeFileSync(
        join(bin, "npm"),
        `#!/bin/sh\ncat "${bin}/out"\ncat "${bin}/err" >&2\nexit ${npmRc}\n`,
    );
    chmodSync(join(bin, "npm"), 0o755);
    return spawnSync(process.execPath, [entry, ...args], {
        encoding: "utf8",
        input,
        env: { ...process.env, PATH: `${bin}:${process.env.PATH}` },
    });
}

// The feed on 2026-10-05: cli@dev on 1.204, maestro-tool@dev already on 1.205.
const SPLIT_FEED = [
    "1.203.0",
    "1.203.0-dev.8800",
    "1.204.0-preview.212",
    "1.204.0-dev.8990",
    "1.204.0-dev.9000",
    "1.205.0-dev.9021",
];

describe("linePrefix / trainOf", () => {
    test("reduce a CLI version to its line and train", () => {
        assert.equal(linePrefix("1.204.0-dev.9000"), "1.204.");
        assert.equal(trainOf("1.204.0-dev.9000"), "dev");
        assert.equal(trainOf("1.204.0-preview.219"), "preview");
        assert.equal(trainOf("1.202.1"), "latest");
    });

    test("GitHub Packages cli@latest is a dev build, so its train is dev", () => {
        assert.equal(trainOf("1.205.0-dev.9071"), "dev");
    });

    test("reject a non-version", () => {
        assert.throws(() => linePrefix(""), /not a version/);
        assert.throws(() => trainOf("latest"), /not a version/);
    });
});

describe("pickVersion", () => {
    test("the 2026-10-05 version set picks the CLI's line, not the dist-tag's", () => {
        assert.deepEqual(pickVersion(SPLIT_FEED, "1.204.", "dev"), {
            version: "1.204.0-dev.9000",
            lagging: null,
        });
    });

    test("a date-stamped build beats a run-numbered one (semver numeric order)", () => {
        const versions = ["1.204.0-dev.9000", "1.204.0-dev.20260930.8"];
        assert.equal(
            pickVersion(versions, "1.204.", "dev").version,
            "1.204.0-dev.20260930.8",
        );
    });

    test("latest takes stable builds only", () => {
        const versions = ["1.202.0", "1.202.1", "1.202.2-preview.5", "1.202.3-dev.1"];
        assert.equal(pickVersion(versions, "1.202.", "latest").version, "1.202.1");
    });

    test("a train with builds only on an older line reports the lag", () => {
        // cli@dev reached 1.206 before maestro-tool did.
        assert.deepEqual(pickVersion(SPLIT_FEED, "1.206.", "dev"), {
            version: null,
            lagging: "1.205.0-dev.9021",
        });
    });

    test("no build on the line or below returns null with no lag", () => {
        // A tool first published after the CLI's line, or never on this train.
        assert.deepEqual(pickVersion(["1.205.0-dev.1"], "1.204.", "dev"), {
            version: null,
            lagging: null,
        });
        assert.deepEqual(
            pickVersion(["1.203.0-preview.203"], "1.202.", "latest"),
            { version: null, lagging: null },
        );
    });
});

describe("offLineTools", () => {
    const tool = (Name, Version) => ({ Name, Version, Status: "ok" });

    test("the skewed list returns the two off-line tools", () => {
        const list = {
            Data: [
                tool("agent-tool", "1.204.0-dev.9000"),
                tool("maestro-tool", "1.205.0-dev.9021"),
                tool("solution-tool", "1.205.0-dev.9021"),
            ],
        };
        assert.deepEqual(offLineTools(list, "1.204.", 3), [
            "maestro-tool@1.205.0-dev.9021",
            "solution-tool@1.205.0-dev.9021",
        ]);
    });

    test("an unreadable or empty list throws instead of passing", () => {
        for (const list of [{}, { Data: null }, { Data: {} }, { Data: [] }, null]) {
            assert.throws(() => offLineTools(list, "1.204."), /no tools/);
        }
    });

    test("a list that does not hold every installed tool throws", () => {
        const list = { Data: [tool("agent-tool", "1.204.0-dev.9000")] };
        assert.throws(() => offLineTools(list, "1.204.", 2), /shows 1 tools, but 2/);
    });
});

describe("lookupFailure", () => {
    test("E404 means not published only on an explicit registry", () => {
        const npm = "https://registry.npmjs.org";
        assert.equal(lookupFailure("npm error code E404\nnpm error 404 Not Found", npm), "missing");
        assert.equal(lookupFailure("npm error code E404\nnpm error 404 Not Found"), "error");
        assert.equal(lookupFailure("npm error code E401\nnpm error 401 Unauthorized", npm), "error");
        assert.equal(lookupFailure("npm error code ECONNRESET"), "error");
    });
});

describe("command line", () => {
    test("runs from a path with spaces and through a symlink", () => {
        const spaced = join(scratch, "dir with spaces", "tool-line.mjs");
        spawnSync("mkdir", ["-p", dirname(spaced)]);
        copyFileSync(script, spaced);
        const link = join(scratch, "linked-tool-line.mjs");
        symlinkSync(script, link);
        for (const entry of [spaced, link]) {
            const result = run(["line", "1.204.0-dev.9000"], { entry });
            assert.equal(result.status, 0, result.stderr);
            assert.equal(result.stdout, "1.204.\n");
        }
    });

    test("pick exit codes: 0 version, 3 nothing to install, 4 lagging, 5 lookup error", () => {
        const feed = JSON.stringify(SPLIT_FEED);
        let result = run(["pick", "@uipath/maestro-tool", "1.204.", "dev"], { npmOut: feed });
        assert.equal(result.status, 0, result.stderr);
        assert.equal(result.stdout, "1.204.0-dev.9000\n");

        result = run(["pick", "@uipath/maestro-tool", "1.206.", "dev"], { npmOut: feed });
        assert.equal(result.status, 4);
        assert.match(result.stderr, /1\.205\.0-dev\.9021, none on the CLI's 1\.206\.x line/);

        result = run(["pick", "@uipath/new-tool", "1.204.", "dev"], {
            npmOut: JSON.stringify(["1.205.0-dev.1"]),
        });
        assert.equal(result.status, 3);

        result = run(
            ["pick", "@uipath/rules-tool", "1.202.", "latest", "https://registry.npmjs.org"],
            { npmErr: "npm error code E404\n", npmRc: 1 },
        );
        assert.equal(result.status, 3);
        assert.match(result.stderr, /not published/);

        // GitHub Packages answers 404 to a token that cannot read the package.
        result = run(["pick", "@uipath/maestro-tool", "1.204.", "dev"], {
            npmErr: "npm error code E404\n",
            npmRc: 1,
        });
        assert.equal(result.status, 5);
        assert.match(result.stderr, /registry lookup failed/);

        result = run(["pick", "@uipath/maestro-tool", "1.204.", "dev"], {
            npmErr: "npm error code E401\n",
            npmRc: 1,
        });
        assert.equal(result.status, 5);
        assert.match(result.stderr, /registry lookup failed/);
    });

    test("check fails on an empty list, a count mismatch, and an off-line tool", () => {
        const list = (versions) =>
            JSON.stringify({
                Data: versions.map((Version, i) => ({ Name: `t${i}`, Version })),
            });
        assert.equal(run(["check", "1.204.", "1"], { input: list(["1.204.0-dev.9000"]) }).status, 0);
        assert.equal(run(["check", "1.204.", "1"], { input: "{}" }).status, 1);
        assert.equal(run(["check", "1.204.", "2"], { input: list(["1.204.0-dev.9000"]) }).status, 1);
        assert.equal(run(["check", "1.204.", "1"], { input: list(["1.205.0-dev.9021"]) }).status, 1);
        assert.equal(run(["check", "1.204."], { input: list(["1.204.0-dev.9000"]) }).status, 2);
    });
});
