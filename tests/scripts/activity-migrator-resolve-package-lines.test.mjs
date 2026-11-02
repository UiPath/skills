import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SCRIPT = join(REPO_ROOT, "skills", "uipath-activity-migrator", "scripts", "resolve-package-lines.mjs");

const VERSIONS = [
  "24.10.1", "24.10.5", "24.10.5-preview", "25.4.2", "25.10.0", "25.10.3", "25.10.11", "26.2.0", "not-a-version",
];

// Serves `/<lowercased id>/index.json` the way a NuGet v3 flat container does.
async function withFeed(handler, fn) {
  const requested = [];
  const server = createServer((req, res) => {
    requested.push(req.url);
    handler(req, res);
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    return await fn(`http://127.0.0.1:${server.address().port}/flat2/`, requested);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
}

const jsonFeed = (versions) => (req, res) => {
  res.setHeader("content-type", "application/json");
  res.end(JSON.stringify({ versions }));
};

// Async spawn: the fake feed lives in this process, so a sync spawn would deadlock it.
function run(args, feedUrl) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [SCRIPT, ...args], {
      env: { ...process.env, UIPATH_ACTIVITY_MIGRATOR_FEED_URL: feedUrl },
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => (stdout += d));
    child.stderr.on("data", (d) => (stderr += d));
    child.on("close", (status) => resolve({ status, stdout, stderr }));
  });
}

test("returns the two newest LTS lines, newest recommended, ignoring STS and prereleases", async () => {
  await withFeed(jsonFeed(VERSIONS), async (feed, requested) => {
    const r = await run(["--package", "UiPath.UIAutomation.Activities"], feed);
    assert.equal(r.status, 0);
    const out = JSON.parse(r.stdout);
    assert.deepEqual(out.lines, [
      { line: "25.10", version: "25.10.11" },
      { line: "24.10", version: "24.10.5" },
    ]);
    assert.equal(out.recommended, "25.10");
    assert.equal(out.reason, "newest release line");
    assert.equal(out.package, "UiPath.UIAutomation.Activities");
    assert.equal(requested[0], "/flat2/uipath.uiautomation.activities/index.json");
    assert.ok(out.feed.endsWith("/flat2/uipath.uiautomation.activities/index.json"));
  });
});

test("--all-lines keeps STS lines and --lines limits the count", async () => {
  await withFeed(jsonFeed(VERSIONS), async (feed) => {
    const all = JSON.parse((await run(["--package", "P", "--all-lines", "--lines", "10"], feed)).stdout);
    assert.deepEqual(all.lines.map((l) => l.line), ["26.2", "25.10", "25.4", "24.10"]);
    const one = JSON.parse((await run(["--package", "P", "--all-lines", "--lines", "1"], feed)).stdout);
    assert.deepEqual(one.lines, [{ line: "26.2", version: "26.2.0" }]);
    assert.equal(one.recommended, "26.2");
  });
});

test("--min drops lines whose highest patch is below it", async () => {
  await withFeed(jsonFeed(VERSIONS), async (feed) => {
    const out = JSON.parse((await run(["--package", "P", "--min", "25.10.0"], feed)).stdout);
    assert.deepEqual(out.lines, [{ line: "25.10", version: "25.10.11" }]);
  });
});

test("reports no candidate lines when nothing qualifies", async () => {
  await withFeed(jsonFeed(["25.4.0"]), async (feed) => {
    const r = await run(["--package", "P"], feed);
    assert.equal(r.status, 0);
    const out = JSON.parse(r.stdout);
    assert.deepEqual(out.lines, []);
    assert.equal(out.recommended, null);
    assert.equal(out.reason, "no candidate lines");
  });
});

test("tolerates a feed document without a versions array", async () => {
  await withFeed((req, res) => res.end("{}"), async (feed) => {
    const out = JSON.parse((await run(["--package", "P"], feed)).stdout);
    assert.equal(out.recommended, null);
  });
});

test("exits 1 with an error object when the feed answers with an HTTP error", async () => {
  await withFeed(
    (req, res) => {
      res.statusCode = 404;
      res.end("nope");
    },
    async (feed) => {
      const r = await run(["--package", "Unknown.Package"], feed);
      assert.equal(r.status, 1);
      const out = JSON.parse(r.stdout);
      assert.match(out.error, /feed unreachable or package unknown/);
      assert.match(out.error, /HTTP 404/);
    },
  );
});

test("exits 1 when the feed is unreachable", async () => {
  const r = await run(["--package", "P"], "http://127.0.0.1:1/flat2");
  assert.equal(r.status, 1);
  assert.match(JSON.parse(r.stdout).error, /feed unreachable/);
});

test("exits 2 with usage when --package is missing", async () => {
  const r = await run([], "http://127.0.0.1:1/flat2");
  assert.equal(r.status, 2);
  assert.match(r.stderr, /usage: node resolve-package-lines\.mjs --package/);
  assert.equal(r.stdout, "");
});
