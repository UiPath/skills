// Contract guard for hooks/flow-diff-hook.mjs: runs the hook as a subprocess against a temp
// HOME, a 0600 lockfile in $HOME/.uipath/ide and a local socket server, and asserts what the
// UiPath VS Code extension would receive. POSIX-only (CI runs it on ubuntu).

import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { attestationHash, editedContent, isRelevantCommand, isWithin } from "../../hooks/flow-diff-hook.mjs";

const REPO_ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const HOOK = path.join(REPO_ROOT, "hooks", "flow-diff-hook.mjs");
const POSIX = { skip: process.platform === "win32" && "POSIX-only (CI runs it on ubuntu)" };
const sha256 = (text) => crypto.createHash("sha256").update(text, "utf8").digest("hex");
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const hex = (bytes) => crypto.randomBytes(bytes).toString("hex");

// ---- fixture: temp HOME, workspace, lockfiles and socket servers ----

/** A server on a short socket path (macOS caps socket paths at ~104 bytes); records every line. */
async function startServer() {
  const dir = process.platform === "darwin" ? "/tmp" : os.tmpdir();
  const socket = path.join(dir, `uipath-flow-hook-${hex(8)}.sock`);
  const messages = [];
  const server = net.createServer((connection) => {
    let buffer = "";
    connection.on("data", (chunk) => {
      buffer += chunk;
      const newline = buffer.indexOf("\n");
      if (newline !== -1) {
        messages.push(JSON.parse(buffer.slice(0, newline)));
        connection.end("{}\n");
      }
    });
    connection.on("error", () => undefined);
  });
  await new Promise((resolve) => server.listen(socket, resolve));
  return { socket, messages, close: () => new Promise((resolve) => server.close(resolve)) };
}

async function setup(t, { windows = 1 } = {}) {
  const home = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "flow-diff-hook-")));
  const lockDir = path.join(home, ".uipath", "ide");
  fs.mkdirSync(lockDir, { recursive: true, mode: 0o700 });
  const list = [];
  for (let index = 0; index < windows; index += 1) {
    const workspace = path.join(home, `ws${index}`);
    fs.mkdirSync(workspace);
    const server = await startServer();
    const token = hex(32);
    const lockFile = path.join(lockDir, `${process.pid}-${hex(4)}.lock`);
    const lock = { v: 2, socket: server.socket, token, pid: process.pid, workspaceFolders: [workspace], extensions: [".flow"] };
    fs.writeFileSync(lockFile, JSON.stringify(lock), { mode: 0o600 });
    list.push({ workspace, server, messages: server.messages, token, lockFile, lock });
  }
  t.after(async () => {
    await Promise.all(list.map(({ server }) => server.close()));
    fs.rmSync(home, { recursive: true, force: true });
  });
  return { home, lockDir, sessionsDir: path.join(lockDir, "sessions"), windows: list, ...list[0] };
}

/** Runs the hook; asserts the contract every run must keep: exit 0 and nothing on stdout. */
function runHook(home, stdin, { env = {}, args = [] } = {}) {
  return new Promise((resolve, reject) => {
    const childEnv = { ...process.env, HOME: home, USERPROFILE: home, ...env };
    delete childEnv.UIPATH_FLOW_HOOK_LOCK;
    if (!("UIPATH_FLOW_DIFF_DISABLED" in env)) {
      delete childEnv.UIPATH_FLOW_DIFF_DISABLED;
    }
    const child = spawn(process.execPath, [HOOK, ...args], { env: childEnv });
    let stdout = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.on("error", reject);
    child.on("close", (code) => {
      try {
        assert.equal(code, 0, "hook must always exit 0");
        assert.equal(stdout, "", "hook must print nothing");
        resolve();
      } catch (error) {
        reject(error);
      }
    });
    child.stdin.on("error", () => undefined);
    child.stdin.end(typeof stdin === "string" ? stdin : JSON.stringify(stdin));
  });
}

const SESSION = "b3c1e0f2-1a2b-4c5d-8e9f-001122334455";
const event = (name, extra = {}) => ({ hook_event_name: name, session_id: SESSION, cwd: "/", ...extra });
const write = (file, content) => event("PostToolUse", { tool_name: "Write", tool_input: { file_path: file, content } });
const bash = (command) => event("PostToolUse", { tool_name: "Bash", tool_input: { command } });

function sessionEntries(sessionsDir) {
  if (!fs.existsSync(sessionsDir)) {
    return [];
  }
  return fs.readdirSync(sessionsDir).flatMap((dir) => fs.readdirSync(path.join(sessionsDir, dir)).filter((name) => name !== "since"));
}

// ---- golden vectors: must match the extension's attestationHash byte for byte ----

// Inputs are the ones UiPath/flow-workbench pins in
// packages/vsix/src/extension/services/localAgentProtocol.unit.test.ts (HASH, HOOK_WRITE.hashes,
// and the BOM/CRLF case). That suite asserts equalities only, so the hex digests below were
// computed independently with `shasum -a 256` over the normalized bytes.
test("attestationHash matches the extension's golden vectors", () => {
  assert.equal(attestationHash('{"nodes":[]}'), "acf2fa576acb702442f9d0101673354c398db67315c066ca48be8db8e0d2c75b");
  assert.equal(attestationHash('{"nodes":[{"id":"n1"}]}'), "97885295d481ac380df3d4354e5a74ffc908a5d6859497e817e1817a1e4e056a");
  assert.equal(attestationHash('{"nodes":[]}\n'), "ac08ce34ba4f8123618661bef2425f7028ffb9ac740578a3ee88684d2523fee8");
  assert.equal(attestationHash('﻿{"nodes":[]}\r\n'), "ac08ce34ba4f8123618661bef2425f7028ffb9ac740578a3ee88684d2523fee8");
  // Only a leading BOM is dropped, and a lone CR is kept.
  assert.notEqual(attestationHash('{"nodes":[]}\r'), attestationHash('{"nodes":[]}\n'));
});

// ---- pure helpers ----

test("isWithin keeps a subfolder whose name starts with '..'", POSIX, () => {
  assert.equal(isWithin("/ws", "/ws/..drafts/a.flow"), true);
  assert.equal(isWithin("/ws", "/ws/a.flow"), true);
  assert.equal(isWithin("/ws", "/ws"), true);
  assert.equal(isWithin("/ws", "/ws/../a.flow"), false);
  assert.equal(isWithin("/ws", "/other/a.flow"), false);
  assert.equal(isWithin("/ws", "/"), false);
});

test("isRelevantCommand passes uip maestro and reviewed file types only", () => {
  assert.equal(isRelevantCommand("( cd Sol/Main && uip maestro flow compile .flow-sdk/Main.flow.ts -o Main.flow )"), true);
  assert.equal(isRelevantCommand("uip maestro case sdd convert sdd.md --out caseplan.case"), true);
  assert.equal(isRelevantCommand("uip maestro bpmn format p.bpmn"), true);
  assert.equal(isRelevantCommand("node .flow-sdk/Main.pipeline.mjs"), true);
  assert.equal(isRelevantCommand("ls -la"), false);
  assert.equal(isRelevantCommand("uip login status"), false);
  assert.equal(isRelevantCommand(undefined), false);
});

test("editedContent rebuilds the post-edit file from the PostToolUse payload", () => {
  const edit = (response) => ({ tool_name: "Edit", tool_response: response });
  assert.equal(editedContent(edit({ originalFile: "a b a", oldString: "a", newString: "x", replaceAll: false })), "x b a");
  assert.equal(editedContent(edit({ originalFile: "a b a", oldString: "a", newString: "x", replaceAll: true })), "x b x");
  assert.equal(editedContent(edit({ originalFile: "a $& b", oldString: "b", newString: "$&", replaceAll: false })), "a $& $&");
  assert.equal(editedContent(edit({ oldString: "a", newString: "x" })), undefined);
  assert.equal(editedContent(edit({ originalFile: "abc", oldString: "zzz", newString: "x" })), undefined);
  const multi = {
    tool_name: "MultiEdit",
    tool_input: { edits: [{ old_string: "one", new_string: "two" }, { old_string: "two", new_string: "three", replace_all: true }] },
    tool_response: { originalFile: "one two" },
  };
  assert.equal(editedContent(multi), "three three");
});

// ---- black-box contract ----

test("Write on a .flow sends one write with the token and the hash of the tool's content", POSIX, async (t) => {
  const { home, workspace, messages, token } = await setup(t);
  const file = path.join(workspace, "x.flow");
  // The disk differs (e.g. a user save landed meanwhile): only the tool's content is attested.
  fs.writeFileSync(file, '{"nodes":["user"]}');
  await runHook(home, write(file, '{"nodes":[]}'));
  assert.deepEqual(messages, [
    { v: 2, agent: "claude", sessionId: SESSION, pid: process.pid, event: "write", file, hashes: [sha256('{"nodes":[]}')], token },
  ]);
});

test("Edit attests the content rebuilt from tool_response, and falls back to the disk without it", POSIX, async (t) => {
  const { home, workspace, messages } = await setup(t);
  const file = path.join(workspace, "x.flow");
  fs.writeFileSync(file, "on disk");
  const edit = (response) => event("PostToolUse", { tool_name: "Edit", tool_input: { file_path: file }, tool_response: response });
  await runHook(home, edit({ originalFile: '{"a":1}', oldString: "1", newString: "2", replaceAll: false }));
  await runHook(home, edit(undefined));
  assert.deepEqual(
    messages.map((message) => message.hashes),
    [[sha256('{"a":2}')], [sha256("on disk")]]
  );
});

test("a non-reviewed path sends nothing and creates no sessions dir", POSIX, async (t) => {
  const { home, workspace, messages, sessionsDir } = await setup(t);
  await runHook(home, write(path.join(workspace, "x.json"), "{}"));
  assert.deepEqual(messages, []);
  assert.equal(fs.existsSync(sessionsDir), false);
});

test("a .flow outside every workspace sends nothing", POSIX, async (t) => {
  const { home, messages } = await setup(t);
  await runHook(home, write(path.join(home, "elsewhere.flow"), "{}"));
  assert.deepEqual(messages, []);
});

for (const [name, mutate] of [
  ["a 0644 lockfile", ({ lockFile }) => fs.chmodSync(lockFile, 0o644)],
  ["a dead pid", ({ lockFile, lock }) => rewriteLock(lockFile, { ...lock, pid: spawnSync(process.execPath, ["-e", ""]).pid })],
  ["a wrong protocol version", ({ lockFile, lock }) => rewriteLock(lockFile, { ...lock, v: 3 })],
  ["a socket path that is a symlink", ({ lockFile, lock, home }) => {
    const link = path.join(path.dirname(lock.socket), `uipath-flow-hook-${hex(8)}.sock`);
    fs.symlinkSync(lock.socket, link);
    rewriteLock(lockFile, { ...lock, socket: link });
    return () => fs.rmSync(link, { force: true });
  }],
]) {
  test(`${name} is ignored`, POSIX, async (t) => {
    const fixture = await setup(t);
    const cleanup = mutate(fixture);
    if (typeof cleanup === "function") {
      t.after(cleanup);
    }
    await runHook(fixture.home, write(path.join(fixture.workspace, "x.flow"), "{}"));
    assert.deepEqual(fixture.messages, []);
  });
}

function rewriteLock(lockFile, lock) {
  fs.writeFileSync(lockFile, JSON.stringify(lock), { mode: 0o600 });
}

test("PermissionRequest then Stop sends turn.end and clears the marker", POSIX, async (t) => {
  const { home, workspace, messages, sessionsDir } = await setup(t);
  const file = path.join(workspace, "x.flow");
  await runHook(home, event("PermissionRequest", { tool_name: "Write", tool_input: { file_path: file, content: "{}" } }));
  assert.deepEqual(messages, []);
  assert.equal(sessionEntries(sessionsDir).length, 1);
  await runHook(home, event("Stop"));
  assert.deepEqual(messages.map((message) => message.event), ["turn.end"]);
  assert.deepEqual(sessionEntries(sessionsDir), []);
});

test("UserPromptSubmit with no marker sends nothing", POSIX, async (t) => {
  const { home, messages } = await setup(t);
  await runHook(home, event("UserPromptSubmit", { prompt: "hi" }));
  await runHook(home, event("Stop"));
  assert.deepEqual(messages, []);
});

test("UserPromptSubmit ends a turn that never got its Stop", POSIX, async (t) => {
  const { home, workspace, messages, sessionsDir } = await setup(t);
  await runHook(home, write(path.join(workspace, "x.flow"), "{}"));
  await runHook(home, event("UserPromptSubmit", { prompt: "next" }));
  assert.deepEqual(messages.map((message) => message.event).at(-1), "turn.end");
  assert.deepEqual(sessionEntries(sessionsDir), []);
});

test("a uip maestro command that changes a .flow sends a write for it", POSIX, async (t) => {
  const { home, workspace, messages } = await setup(t);
  const file = path.join(workspace, "Main", "Main.flow");
  const untouched = path.join(workspace, "Other.flow");
  fs.mkdirSync(path.dirname(file));
  fs.writeFileSync(file, "before");
  fs.writeFileSync(untouched, "untouched");
  await runHook(home, event("UserPromptSubmit", { prompt: "edit it" }));
  await sleep(20);
  fs.writeFileSync(file, '{"nodes":[]}');
  await runHook(home, bash("( cd Sol/Main && uip maestro flow compile .flow-sdk/Main.flow.ts -o Main.flow )"));
  assert.deepEqual(
    messages.map(({ event: name, file: written, hashes }) => ({ name, written, hashes })),
    [{ name: "write", written: file, hashes: [sha256('{"nodes":[]}')] }]
  );
  // The checkpoint moved: the next command reports only what changed after this one.
  await runHook(home, bash("uip maestro flow validate Main.flow"));
  assert.equal(messages.length, 1);
  // A command that exits non-zero (PostToolUseFailure) may still have written.
  await sleep(20);
  fs.writeFileSync(file, '{"nodes":[1]}');
  await runHook(home, { ...bash("uip maestro flow format Main.flow"), hook_event_name: "PostToolUseFailure", error: "Exit code 1" });
  assert.deepEqual(messages.at(-1).hashes, [sha256('{"nodes":[1]}')]);
});

test("an unrelated Bash command touches nothing and sends nothing", POSIX, async (t) => {
  const { home, workspace, messages, sessionsDir } = await setup(t);
  fs.writeFileSync(path.join(workspace, "x.flow"), "{}");
  await runHook(home, bash("ls -la && git status"));
  assert.deepEqual(messages, []);
  assert.equal(fs.existsSync(sessionsDir), false);
});

test("Stop re-attests a file that changed after its first report", POSIX, async (t) => {
  const { home, workspace, messages } = await setup(t);
  const file = path.join(workspace, "x.flow");
  fs.writeFileSync(file, "A");
  await runHook(home, write(file, "A"));
  fs.writeFileSync(file, "A, formatted");
  await runHook(home, event("Stop"));
  assert.deepEqual(
    messages.map(({ event: name, hashes }) => ({ name, hashes })),
    [
      { name: "write", hashes: [sha256("A")] },
      { name: "write", hashes: [sha256("A, formatted")] },
      { name: "turn.end", hashes: undefined },
    ]
  );
});

test("UIPATH_FLOW_DIFF_DISABLED or a missing ~/.uipath/ide turns the hook off", POSIX, async (t) => {
  const { home, workspace, messages, lockDir } = await setup(t);
  const payload = write(path.join(workspace, "x.flow"), "{}");
  await runHook(home, payload, { env: { UIPATH_FLOW_DIFF_DISABLED: "1" } });
  await runHook(home, payload, { env: { UIPATH_FLOW_DIFF_DISABLED: "true" } });
  assert.deepEqual(messages, []);
  fs.rmSync(lockDir, { recursive: true });
  await runHook(home, payload);
  assert.deepEqual(messages, []);
  assert.equal(fs.existsSync(lockDir), false);
});

test("exit 0 and empty stdout on malformed input, an unknown event, or stray arguments", POSIX, async (t) => {
  const { home, workspace, messages } = await setup(t);
  await runHook(home, "not json");
  await runHook(home, "");
  await runHook(home, "null");
  await runHook(home, event("SessionStart"));
  await runHook(home, { hook_event_name: "Stop" });
  await runHook(home, write(path.join(workspace, "x.flow"), "{}"), { args: ["--agent", "gemini"] });
  assert.equal(messages.length, 1, "stray arguments are ignored; the payload still reports");
});

// ---- concurrency: parallel hook processes must not lose a window's turn.end ----

test("parallel writes across two windows each get exactly one turn.end", POSIX, async (t) => {
  const { home, windows, sessionsDir } = await setup(t, { windows: 2 });
  for (let iteration = 0; iteration < 20; iteration += 1) {
    const sessionId = `session-${iteration}`;
    const at = (name, extra) => ({ ...event(name, extra), session_id: sessionId });
    for (const window of windows) {
      window.messages.length = 0;
    }
    const runs = [];
    for (let index = 0; index < 8; index += 1) {
      const { workspace } = windows[index % 2];
      const file = path.join(workspace, `f${index}.flow`);
      runs.push(
        index === 7
          ? runHook(home, at("PermissionRequest", { tool_name: "Write", tool_input: { file_path: file } }))
          : runHook(home, at("PostToolUse", { tool_name: "Write", tool_input: { file_path: file, content: `${iteration}:${index}` } }))
      );
    }
    await Promise.all(runs);
    await runHook(home, at("Stop"));
    for (const [index, window] of windows.entries()) {
      const events = window.messages.map((message) => message.event);
      assert.equal(events.filter((name) => name === "turn.end").length, 1, `iteration ${iteration}, window ${index}`);
      assert.equal(events.at(-1), "turn.end");
    }
    assert.deepEqual(sessionEntries(sessionsDir), [], `iteration ${iteration} left a marker`);
  }
});
