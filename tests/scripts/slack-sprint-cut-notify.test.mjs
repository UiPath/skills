import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SCRIPT = join(HERE, "..", "..", ".github", "workflows", "scripts", "slack-sprint-cut-notify.mjs");
const PRELOAD = pathToFileURL(join(HERE, "support", "redirect-preload.mjs")).href;

const BASE_ENV = {
  SLACK_BOT_TOKEN: "xoxb-secret",
  CHANNEL_ID: "C123",
  CUT_LINE: "1.199",
  NEXT_LINE: "1.200",
  REPO_URL: "https://github.com/UiPath/skills",
  RUN_ID: "555",
  CUT_OUTCOME: "success",
  PUBLISH_OUTCOME: "success",
  BUMP_OUTCOME: "success",
  BUMP_URL: "https://github.com/UiPath/skills/pull/9",
};

/** Runs the script against a local Slack and returns what it posted. */
async function notify(env, reply) {
  const posts = [];
  const server = createServer((req, res) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => {
      posts.push({
        url: req.url,
        auth: req.headers.authorization,
        body: JSON.parse(Buffer.concat(chunks).toString("utf8")),
      });
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify(reply ?? { ok: true, ts: "1700.1" }));
    });
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const childEnv = {
      PATH: process.env.PATH,
      SystemRoot: process.env.SystemRoot,
      REDIRECT_FETCH_ORIGIN: `http://127.0.0.1:${server.address().port}`,
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
    return { status, stdout, stderr, posts };
  } finally {
    server.close();
  }
}

const lines = (post) => post.body.text.split("\n");

test("everything succeeded: ticks every line, links the exact preview version and the bump PR", async () => {
  const { status, stdout, posts } = await notify({ ...BASE_ENV, PREVIEW_VERSION: "1.199.0-preview.77" });
  assert.equal(status, 0);
  assert.equal(stdout, "Posted sprint-cut announcement to C123 (ts=1700.1).\n");
  assert.equal(posts.length, 1);
  assert.equal(posts[0].url, "/api/chat.postMessage");
  assert.equal(posts[0].auth, "Bearer xoxb-secret");
  assert.equal(posts[0].body.channel, "C123");
  const [head, branch, preview, bump] = lines(posts[0]);
  assert.equal(head, ":checkbox_ticked: *Sprint release cut — `1.199`*");
  assert.equal(
    branch,
    ":checkbox_ticked: Release branch `release/v1.199` cut from `main` (version `1.199.0`, <https://github.com/UiPath/skills/tree/release/v1.199|view branch>)",
  );
  assert.match(preview, /^:checkbox_ticked: Default preview published to npmjs — `@uipath\/skills@1\.199\.0-preview\.77`/);
  assert.ok(preview.includes("<https://www.npmjs.com/package/@uipath/skills/v/1.199.0-preview.77|view on npmjs>"));
  assert.equal(
    bump,
    ":checkbox_ticked: Version-bump PR opened: `main` → `1.200.0` (<https://github.com/UiPath/skills/pull/9|PR>)",
  );
});

test("without the exact preview version the message links the versions tab", async () => {
  const { posts } = await notify(BASE_ENV);
  const preview = lines(posts[0])[2];
  assert.ok(preview.includes("`@uipath/skills@1.199.0-preview`"));
  assert.ok(preview.includes("<https://www.npmjs.com/package/@uipath/skills?activeTab=versions|view on npmjs>"));
});

test("a failed cut warns, skips publishing and says main stays on the cut version", async () => {
  const { posts } = await notify({
    ...BASE_ENV,
    CUT_OUTCOME: "failure",
    PUBLISH_OUTCOME: "skipped",
    BUMP_OUTCOME: "skipped",
    BUMP_URL: "",
  });
  const [head, branch, preview, bump] = lines(posts[0]);
  assert.ok(head.startsWith(":warning: *Sprint release cut"));
  assert.equal(
    branch,
    ":warning: Release branch `release/v1.199` cut from `main` FAILED (<https://github.com/UiPath/skills/actions/runs/555|see logs>)",
  );
  assert.equal(preview, ":warning: Dev/preview package publishing skipped");
  assert.equal(bump, ":warning: Version-bump PR not opened — `main` stays on `1.199.0`");
});

test("cut ok but publish failed: warns with the run link; a bump PR is flagged for verification", async () => {
  const { posts } = await notify({ ...BASE_ENV, PUBLISH_OUTCOME: "failure" });
  const [head, , preview, bump] = lines(posts[0]);
  assert.ok(head.startsWith(":warning:"));
  assert.match(
    preview,
    /^:warning: A dev\/preview publish FAILED .*<https:\/\/github\.com\/UiPath\/skills\/actions\/runs\/555\|see logs>/,
  );
  assert.match(
    bump,
    /^:checkbox_ticked: Version-bump PR opened anyway: `main` → `1\.200\.0` .*:warning: verify the failed publish before merging$/,
  );
});

test("bump succeeded without a PR url: main was already on the next version", async () => {
  const { posts } = await notify({ ...BASE_ENV, BUMP_URL: "" });
  assert.equal(lines(posts[0])[3], ":checkbox_ticked: `main` already on `1.200.0` — no bump PR needed");
});

test("without REPO_URL and RUN_ID the links fall back to the default repository", async () => {
  const env = { ...BASE_ENV, CUT_OUTCOME: "failure" };
  delete env.REPO_URL;
  delete env.RUN_ID;
  const { posts } = await notify(env);
  assert.ok(lines(posts[0])[1].includes("(<https://github.com/UiPath/skills|see logs>)"));
});

test("a missing required variable fails before any post", async () => {
  const env = { ...BASE_ENV };
  delete env.NEXT_LINE;
  const { status, stderr, posts } = await notify(env);
  assert.notEqual(status, 0);
  assert.match(stderr, /Missing NEXT_LINE environment variable\./);
  assert.equal(posts.length, 0);
});

test("a Slack rejection fails the step with Slack's error", async () => {
  const { status, stderr } = await notify(BASE_ENV, { ok: false, error: "invalid_auth" });
  assert.notEqual(status, 0);
  assert.match(stderr, /Slack post failed: invalid_auth/);
});
