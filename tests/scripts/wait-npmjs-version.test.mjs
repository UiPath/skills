import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SCRIPT = join(HERE, "..", "..", ".github", "workflows", "scripts", "wait-npmjs-version.mjs");
const PRELOAD = pathToFileURL(join(HERE, "support", "redirect-preload.mjs")).href;

/**
 * `replies` is consumed one entry per registry poll (the last repeats):
 * a packument object, a number (HTTP status), or "drop" (connection reset).
 * The preload fast-forwards the script's 15-minute deadline and poll sleeps.
 */
async function wait(replies, env) {
  const polls = [];
  const server = createServer((req, res) => {
    polls.push(req.url);
    const reply = replies[Math.min(polls.length - 1, replies.length - 1)];
    if (reply === "drop") return req.socket.destroy();
    if (typeof reply === "number") {
      res.writeHead(reply);
      return res.end("nope");
    }
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(reply));
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const childEnv = {
      PATH: process.env.PATH,
      SystemRoot: process.env.SystemRoot,
      REDIRECT_FETCH_ORIGIN: `http://127.0.0.1:${server.address().port}`,
      REDIRECT_FAST_TIME: "1",
      ...env,
    };
    if (process.env.NODE_V8_COVERAGE) childEnv.NODE_V8_COVERAGE = process.env.NODE_V8_COVERAGE;
    const child = spawn(process.execPath, ["--import", PRELOAD, SCRIPT], {
      env: childEnv,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (c) => (stdout += c));
    child.stderr.on("data", (c) => (stderr += c));
    const status = await new Promise((resolve) => child.on("close", resolve));
    return { status, stdout, stderr, polls };
  } finally {
    server.close();
  }
}

test("exits 0 as soon as the packument lists the version, polling the cache-busted packument URL", async () => {
  const { status, stdout, polls } = await wait([{ versions: { "1.2.3": {} } }], { VERSION: "1.2.3" });
  assert.equal(status, 0);
  assert.equal(stdout, "npmjs serves @uipath/skills@1.2.3.\n");
  assert.equal(polls.length, 1);
  assert.match(polls[0], /^\/@uipath%2Fskills\?t=\d+$/);
});

test("keeps polling while the version is missing, errors, or the connection fails, then succeeds", async () => {
  const { status, stdout, polls } = await wait(
    [{ versions: { "1.2.2": {} } }, {}, 500, "drop", { versions: { "1.2.3": {} } }],
    { VERSION: "1.2.3" },
  );
  assert.equal(status, 0);
  assert.equal(polls.length, 5);
  assert.match(stdout, /registry poll failed, retrying: /);
  assert.match(stdout, /npmjs serves @uipath\/skills@1\.2\.3\./);
});

test("fails with a GitHub error annotation when the version never appears before the deadline", async () => {
  const { status, stderr, polls } = await wait([{ versions: {} }], { VERSION: "9.9.9" });
  assert.equal(status, 1);
  assert.equal(stderr, "::error::npmjs is not serving @uipath/skills@9.9.9 after 15 minutes.\n");
  assert.ok(polls.length > 1, "polled more than once before giving up");
});

test("refuses to run without VERSION", async () => {
  const { status, stderr, polls } = await wait([{}], {});
  assert.notEqual(status, 0);
  assert.match(stderr, /Missing VERSION environment variable\./);
  assert.equal(polls.length, 0);
});
