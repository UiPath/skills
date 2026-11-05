import assert from "node:assert/strict";
import { createServer } from "node:http";
import test from "node:test";

import { postMessage, requireEnv } from "../../.github/workflows/scripts/slack.mjs";

/** Serves one canned Slack reply, records the request, and routes fetch() to it. */
async function withSlack(reply, body) {
  const seen = [];
  const server = createServer((req, res) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => {
      seen.push({ method: req.method, url: req.url, headers: req.headers, body: Buffer.concat(chunks).toString("utf8") });
      res.writeHead(reply.status, { "Content-Type": "application/json" });
      res.end(JSON.stringify(reply.json));
    });
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const realFetch = globalThis.fetch;
  const origin = `http://127.0.0.1:${server.address().port}`;
  globalThis.fetch = (url, init) => realFetch(`${origin}${new URL(url).pathname}`, init);
  try {
    return await body(seen);
  } finally {
    globalThis.fetch = realFetch;
    server.close();
  }
}

test("postMessage posts JSON with the bot token, disables unfurling and returns Slack's payload", async () => {
  await withSlack({ status: 200, json: { ok: true, ts: "1.23", channel: "C1" } }, async (seen) => {
    const data = await postMessage("xoxb-secret", { channel: "C1", text: "hi", thread_ts: "9.9" });
    assert.deepEqual(data, { ok: true, ts: "1.23", channel: "C1" });
    assert.equal(seen.length, 1);
    assert.equal(seen[0].method, "POST");
    assert.equal(seen[0].url, "/api/chat.postMessage");
    assert.equal(seen[0].headers.authorization, "Bearer xoxb-secret");
    assert.equal(seen[0].headers["content-type"], "application/json; charset=utf-8");
    assert.deepEqual(JSON.parse(seen[0].body), { unfurl_links: false, channel: "C1", text: "hi", thread_ts: "9.9" });
  });
});

test("a caller can override unfurl_links", async () => {
  await withSlack({ status: 200, json: { ok: true } }, async (seen) => {
    await postMessage("t", { channel: "C", unfurl_links: true });
    assert.equal(JSON.parse(seen[0].body).unfurl_links, true);
  });
});

test("HTTP 200 with ok:false is a failure carrying Slack's error code", async () => {
  await withSlack({ status: 200, json: { ok: false, error: "channel_not_found" } }, async () => {
    await assert.rejects(postMessage("t", { channel: "C" }), /Slack post failed: channel_not_found$/);
  });
});

test("a non-2xx reply without an error code falls back to the HTTP status", async () => {
  await withSlack({ status: 503, json: { ok: true } }, async () => {
    await assert.rejects(postMessage("t", { channel: "C" }), /Slack post failed: 503 /);
  });
});

test("requireEnv returns the value and names the missing variable otherwise", () => {
  process.env.SLACK_TEST_PRESENT = "value";
  delete process.env.SLACK_TEST_ABSENT;
  try {
    assert.equal(requireEnv("SLACK_TEST_PRESENT"), "value");
    assert.throws(() => requireEnv("SLACK_TEST_ABSENT"), /Missing SLACK_TEST_ABSENT environment variable\./);
    process.env.SLACK_TEST_PRESENT = "";
    assert.throws(() => requireEnv("SLACK_TEST_PRESENT"), /Missing SLACK_TEST_PRESENT/);
  } finally {
    delete process.env.SLACK_TEST_PRESENT;
  }
});
