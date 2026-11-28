import assert from "node:assert/strict";
import { execFile, spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { mkdirSync, mkdtempSync, rmSync, symlinkSync, utimesSync, writeFileSync } from "node:fs";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

import { discoverWindows, preview } from "../../skills/uipath-coded-apps/scripts/uipath-apps-preview.mjs";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SCRIPT = join(REPO_ROOT, "skills", "uipath-coded-apps", "scripts", "uipath-apps-preview.mjs");

// A pid that is certainly not running: a child that has already exited.
const DEAD_PID = spawnSync(process.execPath, ["-e", ""]).pid;

function scratch(t) {
  const root = mkdtempSync(join(tmpdir(), "uipath-apps-preview-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const lockDir = join(root, "ide");
  mkdirSync(lockDir);
  const dir = (...parts) => {
    const path = join(root, ...parts);
    mkdirSync(path, { recursive: true });
    return path;
  };
  return { root, lockDir, dir };
}

/**
 * One editor window: a listener on its own socket that records each request and answers `reply` (null: never
 * answers; `newline: false` ends the connection after the reply without a newline), and its lockfile in `lockDir`.
 * With `listening: false` only the lockfile exists, so the connection never opens. Socket paths are length-limited,
 * so they sit directly in the temp dir.
 */
async function fakeWindow(
  t,
  lockDir,
  { folders, reply = '{"ok":true,"status":"opening"}', newline = true, listening = true, lock = {}, mtime } = {},
) {
  const id = randomBytes(8).toString("hex");
  const socket =
    process.platform === "win32"
      ? `\\\\.\\pipe\\uipath-agent-hook-${id}`
      : join(tmpdir(), `uipath-agent-hook-${id}.sock`);
  const requests = [];
  if (listening) {
    const server = createServer((conn) => {
      let text = "";
      conn.on("error", () => undefined);
      conn.on("data", (chunk) => {
        text += chunk;
        if (!text.includes("\n")) return;
        requests.push(JSON.parse(text.slice(0, text.indexOf("\n"))));
        if (reply !== null) conn.end(newline ? `${reply}\n` : reply);
      });
    });
    await new Promise((done) => server.listen(socket, done));
    t.after(() => new Promise((done) => server.close(done)));
  }

  const token = randomBytes(32).toString("hex");
  const file = join(lockDir, `appshift-${process.pid}-${id.slice(0, 8)}.lock`);
  const contents = {
    v: 2,
    socket,
    token,
    pid: process.pid,
    workspaceFolders: folders,
    extensions: [".ts"],
    requests: ["preview"],
    ...lock,
  };
  writeFileSync(file, JSON.stringify(contents));
  if (mtime) utimesSync(file, mtime, mtime);
  return { requests, token };
}

test("a window whose folder holds the app gets one preview request carrying its token", async (t) => {
  const { lockDir, dir } = scratch(t);
  const ws = dir("ws");
  const app = dir("ws", "my-app");
  const window = await fakeWindow(t, lockDir, { folders: [ws] });

  assert.equal(await preview(app, { dir: lockDir }), "OPENING");
  assert.equal(window.requests.length, 1);
  const [request] = window.requests;
  assert.deepEqual(
    { ...request, sessionId: undefined },
    { v: 2, agent: "uipath-coded-apps", sessionId: undefined, pid: process.pid, event: "preview", app, token: window.token },
  );
  assert.match(request.sessionId, /^[A-Za-z0-9._:-]{1,128}$/);
});

test("each reply maps to its verdict, and anything else is NOT_AVAILABLE", async (t) => {
  const cases = [
    ['{"ok":true,"status":"opening"}', "OPENING"],
    ['{"ok":true,"status":"shown"}', "SHOWN"],
    ['{"ok":false,"reason":"no_app"}', "REFUSED no_app"],
    ['{"ok":false,"reason":"busy"}', "REFUSED busy"],
    ['{"ok":false,"reason":"not_signed_in"}', "REFUSED not_signed_in"],
    ["{}", "NOT_AVAILABLE"], // a window from before the preview request
    ['{"ok":true,"status":"later"}', "NOT_AVAILABLE"],
    ['{"ok":false,"reason":"two words"}', "NOT_AVAILABLE"],
    ["not json", "NOT_AVAILABLE"],
  ];
  for (const [reply, expected] of cases) {
    const { lockDir, dir } = scratch(t);
    await fakeWindow(t, lockDir, { folders: [dir("ws")], reply });
    assert.equal(await preview(dir("ws", "app"), { dir: lockDir }), expected, reply);
  }
});

test("an app outside every window's folders is NOT_AVAILABLE and nothing is sent", async (t) => {
  const { lockDir, dir } = scratch(t);
  const window = await fakeWindow(t, lockDir, { folders: [dir("ws")] });

  assert.equal(await preview(dir("elsewhere", "app"), { dir: lockDir }), "NOT_AVAILABLE");
  assert.equal(await preview(dir("ws-sibling", "app"), { dir: lockDir }), "NOT_AVAILABLE");
  assert.equal(window.requests.length, 0);
});

test("no lock folder at all is NOT_AVAILABLE", async (t) => {
  const { root, dir } = scratch(t);
  assert.equal(await preview(dir("ws", "app"), { dir: join(root, "missing") }), "NOT_AVAILABLE");
});

test("a lockfile whose pid is gone is skipped", async (t) => {
  const { lockDir, dir } = scratch(t);
  const window = await fakeWindow(t, lockDir, { folders: [dir("ws")], lock: { pid: DEAD_PID } });

  assert.equal(await preview(dir("ws", "app"), { dir: lockDir }), "NOT_AVAILABLE");
  assert.equal(window.requests.length, 0);
});

test("a lockfile that does not list the preview request is skipped", async (t) => {
  const { lockDir, dir } = scratch(t);
  const older = await fakeWindow(t, lockDir, { folders: [dir("ws")], lock: { requests: undefined } });
  const other = await fakeWindow(t, lockDir, { folders: [dir("ws")], lock: { requests: ["something-else"] } });

  assert.equal(await preview(dir("ws", "app"), { dir: lockDir }), "NOT_AVAILABLE");
  assert.equal(older.requests.length + other.requests.length, 0);
});

test("a lockfile that is not a v2 agent-hook lockfile is not a window", async (t) => {
  const { lockDir, dir } = scratch(t);
  const ws = dir("ws");
  for (const lock of [
    { v: 1 },
    { socket: join(tmpdir(), "uipath-flow-hook-0000.sock") },
    { token: "not-hex" },
    { workspaceFolders: [ws, 7] },
    { pid: 0 },
  ]) {
    await fakeWindow(t, lockDir, { folders: [ws], lock });
  }
  writeFileSync(join(lockDir, "appshift-1-broken.lock"), "{");
  writeFileSync(join(lockDir, "appshift-2-big.lock"), " ".repeat(64 * 1024 + 1));

  assert.deepEqual(discoverWindows(lockDir), []);
});

test("the deepest folder that holds the app wins over a shallower one", async (t) => {
  const { lockDir, dir } = scratch(t);
  const outer = await fakeWindow(t, lockDir, { folders: [dir("ws")], mtime: new Date() });
  const inner = await fakeWindow(t, lockDir, {
    folders: [dir("ws", "solution")],
    reply: '{"ok":true,"status":"shown"}',
    mtime: new Date(Date.now() - 60_000),
  });

  assert.equal(await preview(dir("ws", "solution", "app", "source"), { dir: lockDir }), "SHOWN");
  assert.equal(outer.requests.length, 0);
  assert.equal(inner.requests.length, 1);
});

test("between windows on the same folder, the newest lockfile wins", async (t) => {
  const { lockDir, dir } = scratch(t);
  const ws = dir("ws");
  const older = await fakeWindow(t, lockDir, { folders: [ws], mtime: new Date(Date.now() - 60_000) });
  const newer = await fakeWindow(t, lockDir, { folders: [ws], reply: '{"ok":true,"status":"shown"}', mtime: new Date() });

  assert.equal(await preview(dir("ws", "app"), { dir: lockDir }), "SHOWN");
  assert.equal(older.requests.length, 0);
  assert.equal(newer.requests.length, 1);
});

test("a window whose connection never opens is passed over for the next window that holds the app", async (t) => {
  const { lockDir, dir } = scratch(t);
  await fakeWindow(t, lockDir, { folders: [dir("ws", "solution")], listening: false });
  const working = await fakeWindow(t, lockDir, { folders: [dir("ws")], reply: '{"ok":true,"status":"shown"}' });

  assert.equal(await preview(dir("ws", "solution", "app"), { dir: lockDir }), "SHOWN");
  assert.equal(working.requests.length, 1);
});

test("a window that answers no_app is passed over for the next window that holds the app", async (t) => {
  const { lockDir, dir } = scratch(t);
  const ws = dir("ws");
  const first = await fakeWindow(t, lockDir, { folders: [ws], reply: '{"ok":false,"reason":"no_app"}', mtime: new Date() });
  const second = await fakeWindow(t, lockDir, { folders: [ws], mtime: new Date(Date.now() - 60_000) });

  assert.equal(await preview(dir("ws", "app"), { dir: lockDir }), "OPENING");
  assert.equal(first.requests.length, 1);
  assert.equal(second.requests.length, 1);
});

test("once a window has the request, only a no_app answer passes it to the next window", async (t) => {
  const cases = [
    ['{"ok":true,"status":"opening"}', "OPENING"],
    ['{"ok":true,"status":"shown"}', "SHOWN"],
    ['{"ok":false,"reason":"busy"}', "REFUSED busy"],
    ['{"ok":false,"reason":"not_signed_in"}', "REFUSED not_signed_in"],
    [null, "NOT_AVAILABLE"], // the request went out and no reply came
  ];
  for (const [reply, expected] of cases) {
    const { lockDir, dir } = scratch(t);
    const ws = dir("ws");
    const first = await fakeWindow(t, lockDir, { folders: [ws], reply, mtime: new Date() });
    const second = await fakeWindow(t, lockDir, { folders: [ws], mtime: new Date(Date.now() - 60_000) });

    assert.equal(await preview(dir("ws", "app"), { dir: lockDir, timeoutMs: 200 }), expected, String(reply));
    assert.equal(first.requests.length, 1, String(reply));
    assert.equal(second.requests.length, 0, String(reply));
  }
});

test("a reply that ends the connection without a newline is still read", async (t) => {
  const { lockDir, dir } = scratch(t);
  await fakeWindow(t, lockDir, { folders: [dir("ws")], reply: '{"ok":true,"status":"shown"}', newline: false });

  assert.equal(await preview(dir("ws", "app"), { dir: lockDir }), "SHOWN");
});

// pid 1 belongs to root, so signalling it from an unprivileged test fails with EPERM.
test(
  "a lockfile whose pid cannot be signalled from here is kept, and the connect decides",
  { skip: process.platform === "win32" && "pid 1 is not a process on Windows" },
  async (t) => {
    const { lockDir, dir } = scratch(t);
    const window = await fakeWindow(t, lockDir, { folders: [dir("ws")], lock: { pid: 1 } });

    assert.equal(await preview(dir("ws", "app"), { dir: lockDir }), "OPENING");
    assert.equal(window.requests.length, 1);
  },
);

test("the app is spelled from the folder exactly as the lockfile writes it", async (t) => {
  const { root, lockDir, dir } = scratch(t);
  dir("real", "app", "source");
  const link = join(root, "link");
  symlinkSync(join(root, "real"), link, process.platform === "win32" ? "junction" : "dir");
  const window = await fakeWindow(t, lockDir, { folders: [link] });

  assert.equal(await preview(join(root, "real", "app", "source"), { dir: lockDir }), "OPENING");
  assert.equal(window.requests[0].app, join(link, "app", "source"));
});

test("a window that never replies is NOT_AVAILABLE once the timeout passes", async (t) => {
  const { lockDir, dir } = scratch(t);
  const window = await fakeWindow(t, lockDir, { folders: [dir("ws")], reply: null });

  const started = Date.now();
  assert.equal(await preview(dir("ws", "app"), { dir: lockDir, timeoutMs: 200 }), "NOT_AVAILABLE");
  assert.ok(Date.now() - started < 2000);
  assert.equal(window.requests.length, 1);
});

test("the CLI prints one verdict line from the home lock folder and never the token", async (t) => {
  const { root, dir } = scratch(t);
  const lockDir = dir(".uipath", "ide");
  const window = await fakeWindow(t, lockDir, { folders: [dir("ws")] });
  // The child resolves its home from these, so the real ~/.uipath/ide is never read.
  const env = { ...process.env, HOME: root, USERPROFILE: root };

  dir("ws", "app");

  // A relative app folder resolves against the working directory.
  const { stdout, stderr } = await promisify(execFile)(process.execPath, [SCRIPT, "app"], { cwd: dir("ws"), env });
  assert.equal(stdout, "OPENING\n");
  assert.equal(stderr, "");
  assert.equal(window.requests[0].app, join(dir("ws"), "app"));
  assert.ok(!stdout.includes(window.token));
});

test("the CLI exits 2 with usage on more than one argument", () => {
  const result = spawnSync(process.execPath, [SCRIPT, "a", "b"], { encoding: "utf8" });
  assert.equal(result.status, 2);
  assert.equal(result.stdout, "");
  assert.match(result.stderr, /^usage: /);
});
