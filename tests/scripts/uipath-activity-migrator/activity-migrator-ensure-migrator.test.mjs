import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test, { after } from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const SCRIPT = join(REPO_ROOT, "skills", "uipath-activity-migrator", "scripts", "ensure-migrator.mjs");

// ensure-migrator.mjs is a Windows-only flow that shells out to curl, powershell.exe, tar/unzip and UiPath.Upgrade.exe,
// and asks `uip rpa project migrate version` first.
// To exercise it on any OS without downloading or installing anything, the script runs unmodified under a preload that
// (a) reports platform win32, (b) maps the backslash paths the script builds onto the host file system, and
// (c) replaces child_process.spawnSync with a scripted fake driven by the FAKE_SCENARIO env var. The fake knows no
// reg.exe and no dotnet.exe: the script never inspects a .NET install, and a call to either fails as unexpected.
const PRELOAD = String.raw`
const cp = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const realPlatform = process.platform;
Object.defineProperty(process, 'platform', { value: 'win32' });
// node.exe needs the real SystemRoot to start (Winsock, CSPRNG), so the fake one arrives in its own variable and is
// applied here, before the script reads it.
if (process.env.FAKE_SYSTEMROOT) process.env.SystemRoot = process.env.FAKE_SYSTEMROOT;
const norm = (p) => (typeof p === 'string' && realPlatform !== 'win32' ? p.replace(/\\/g, '/') : p);
for (const name of ['existsSync', 'mkdirSync', 'readFileSync', 'renameSync', 'rmSync', 'statSync', 'writeFileSync']) {
  const orig = fs[name];
  fs[name] = (...a) => {
    const n = name === 'renameSync' ? 2 : 1;
    for (let i = 0; i < n; i++) a[i] = norm(a[i]);
    // FAKE_FAIL_RENAME_FROM fails the rename whose source ends with it, as a folder a program still runs from would.
    if (name === 'renameSync' && process.env.FAKE_FAIL_RENAME_FROM && a[0].endsWith(process.env.FAKE_FAIL_RENAME_FROM)) {
      throw Object.assign(new Error('EPERM: operation not permitted'), { code: 'EPERM' });
    }
    // FAKE_FAIL_RM fails the removal of a path ending with it, as a file another process holds would.
    if (name === 'rmSync' && process.env.FAKE_FAIL_RM && a[0].endsWith(process.env.FAKE_FAIL_RM)) {
      throw Object.assign(new Error('EBUSY: resource busy or locked'), { code: 'EBUSY' });
    }
    return orig.apply(fs, a);
  };
}
const scn = JSON.parse(process.env.FAKE_SCENARIO || '{}');
const calls = [];
const result = (o) => ({ status: 0, stdout: '', stderr: '', ...o });
// What an extractor leaves behind: the exe, Extensions/ and, when the scenario names the .NET the new build targets,
// its runtimeconfig.
const writeLayout = (dir, layout) => {
  dir = norm(dir);
  fs.mkdirSync(dir, { recursive: true });
  if (layout !== 'no-exe') fs.writeFileSync(path.join(dir, 'UiPath.Upgrade.exe'), 'exe');
  if (layout !== 'no-extensions') fs.mkdirSync(path.join(dir, 'Extensions'), { recursive: true });
  if (scn.stagedRuntime) {
    const frameworks = ['Microsoft.NETCore.App', 'Microsoft.WindowsDesktop.App'].map((name) => ({ name, version: scn.stagedRuntime }));
    fs.writeFileSync(path.join(dir, 'UiPath.Upgrade.runtimeconfig.json'), JSON.stringify({ runtimeOptions: { frameworks } }));
  }
};
const arg = (command, re) => (re.exec(command) || [])[1];
cp.spawnSync = (cmd, argv, opts) => {
  const command = String(cmd);
  const text = argv.join(' ');
  if (command.startsWith('uip ')) {
    // One shell command line; record it whole, and whether UIPATH_STUDIO_PID reached it.
    calls.push(command + (opts && opts.env && 'UIPATH_STUDIO_PID' in opts.env ? ' [STUDIO_PID]' : ''));
    if (scn.uip) return result(scn.uip);
    return result({ status: 1, stderr: "'uip' is not recognized as an internal or external command" });
  }
  // Network and archive calls are recorded by what they do; every other call by its arguments.
  const kind = command === 'curl' ? (argv.includes('-o') ? 'download' : 'latest')
    : command === 'powershell.exe' ? ['latest.json', 'DownloadFile', 'Expand-Archive'].find((k) => argv[3].includes(k))
    : '';
  calls.push(command.replace(/^.*[\\/]/, '') + ' ' + (kind || text.slice(0, 60)));
  if (command === 'curl') {
    // Without -o the request reads latest.json, the version the server holds.
    if (!argv.includes('-o')) return result(scn.latest || { status: 22 });
    const zip = argv[argv.indexOf('-o') + 1];
    if (scn.curl && scn.curl.ok) {
      fs.writeFileSync(norm(zip), 'zip');
      return result({});
    }
    if (scn.curl && scn.curl.missing) return { status: null, error: Object.assign(new Error('spawn curl ENOENT'), { code: 'ENOENT' }) };
    return result({ status: 22, stderr: 'curl: (22) first\ncurl: (22) the last line' });
  }
  if (command === 'powershell.exe') {
    const c = argv[3];
    if (c.includes('latest.json')) return result(scn.psLatest || { status: 1 });
    if (c.includes('DownloadFile')) {
      if (scn.psDownload && scn.psDownload.ok) {
        fs.writeFileSync(norm(arg(c, /DownloadFile\('[^']*', '([^']*)'\)/)), 'zip');
        return result({});
      }
      if (scn.psDownload && scn.psDownload.missing) return { status: null, error: Object.assign(new Error('ENOENT'), { code: 'ENOENT' }) };
      return result({ status: 1, stderr: 'proxy said (407)' });
    }
    if (c.includes('Expand-Archive')) {
      if (!scn.expand) return result({ status: 1 });
      writeLayout(arg(c, /-DestinationPath '([^']*)'/), scn.expand);
      return result({});
    }
  }
  if (command === 'unzip') {
    if (!scn.unzip) return result({ status: 9 });
    writeLayout(argv[argv.indexOf('-d') + 1], scn.unzip);
    return result({});
  }
  if (/tar\.exe$/.test(command)) {
    if (!scn.tar) return result({ status: 1 });
    writeLayout(argv[argv.indexOf('-C') + 1], scn.tar);
    return result({});
  }
  if (/UiPath\.Upgrade\.exe$/.test(command)) {
    const envT = opts && opts.env ? opts.env.UIPATH_TELEMETRY_DISABLED : process.env.UIPATH_TELEMETRY_DISABLED;
    if (scn.strictTelemetry && envT !== undefined && !/^(true|false)$/i.test(envT)) return result({ status: 1, stderr: 'FormatException' });
    // A build started from the staging folder is the downloaded one, not yet installed.
    const staged = /\.extract-tmp[\\/]/.test(command);
    return result((staged && scn.stagedVersion) || scn.version || { stdout: 'banner\n25.10.4\n' });
  }
  return result({ status: 1, stderr: 'unexpected command ' + command });
};
require('node:module').syncBuiltinESMExports();
process.on('exit', () => fs.writeFileSync(process.env.FAKE_CALLS, JSON.stringify(calls)));
`;

const base = mkdtempSync(join(tmpdir(), "mig-"));
after(() => rmSync(base, { recursive: true, force: true }));
const preload = join(base, "preload.cjs");
writeFileSync(preload, PRELOAD);

let n = 0;

// Each case gets its own install root.
function setup({ cached = null, stamp = null } = {}) {
  const dir = mkdtempSync(join(base, "case-"));
  const root = join(dir, "root");
  mkdirSync(root, { recursive: true });
  if (cached === "root") writeFileSync(join(root, "UiPath.Upgrade.exe"), "exe");
  if (cached === "current") {
    mkdirSync(join(root, "current"), { recursive: true });
    writeFileSync(join(root, "current", "UiPath.Upgrade.exe"), "exe");
  }
  if (stamp !== null) writeFileSync(join(root, ".last-modified"), stamp);
  return { dir, root, sysRoot: join(dir, "sys") };
}

function run(ctx, scenario, { args = [], env = {}, useEnvDir = true } = {}) {
  const calls = join(ctx.dir, `calls${n++}.json`);
  const childEnv = {
    ...process.env,
    FAKE_SYSTEMROOT: ctx.sysRoot,
    FAKE_SCENARIO: JSON.stringify(scenario),
    FAKE_CALLS: calls,
    UIPATH_ACTIVITY_MIGRATOR_URL: "http://example.invalid/UiPath.Upgrade.Cli.zip",
  };
  // The script reads these only to word a missing-runtime message; a developer's own values must not leak into it.
  for (const key of Object.keys(childEnv)) if (/^DOTNET_ROOT(_|$)/i.test(key)) delete childEnv[key];
  delete childEnv.UIPATH_TELEMETRY_DISABLED;
  delete childEnv.UIPATH_ACTIVITY_MIGRATOR_OFFLINE;
  delete childEnv.UIPATH_ACTIVITY_MIGRATOR_DIR;
  if (useEnvDir) childEnv.UIPATH_ACTIVITY_MIGRATOR_DIR = ctx.root;
  // Windows env names are case-insensitive but object keys are not: drop any differently-cased twin first.
  for (const key of Object.keys(env)) {
    for (const existing of Object.keys(childEnv)) if (existing.toLowerCase() === key.toLowerCase()) delete childEnv[existing];
  }
  Object.assign(childEnv, env);
  const r = spawnSync(process.execPath, ["--require", preload, SCRIPT, ...args], { encoding: "utf8", env: childEnv });
  const lines = r.stdout.trim().split("\n");
  return {
    status: r.status,
    stderr: r.stderr,
    json: JSON.parse(lines[lines.length - 1]),
    calls: existsSync(calls) ? JSON.parse(readFileSync(calls, "utf8")) : [],
  };
}

const fwd = (p) => p.replace(/\\/g, "/");

// The file the .NET SDK writes next to UiPath.Upgrade.exe. A WPF build lists two frameworks; a build with one names
// it under "framework".
function writeRuntimeConfig(dir, version, { single = false } = {}) {
  const core = { name: "Microsoft.NETCore.App", version };
  const runtimeOptions = single
    ? { tfm: "net" + version.slice(0, -2), framework: core }
    : { tfm: "net" + version.slice(0, -2), frameworks: [core, { name: "Microsoft.WindowsDesktop.App", version }] };
  writeFileSync(join(dir, "UiPath.Upgrade.runtimeconfig.json"), JSON.stringify({ runtimeOptions }, null, 2));
}

// Exit codes and text of .NET's launcher, captured from UiPath.Upgrade.exe 25.10.1 started against .NET installs that
// lack its runtime. Only the paths differ.
const FRAMEWORK_MISSING = 0x80008096;
const HOST_MISSING = 0x80008083;
const DOTNET_DIR = "C:\\Program Files\\dotnet\\";
function frameworkMissing(version, found = []) {
  const lines = [
    "You must install or update .NET to run this application.",
    "",
    "App: C:\\tools\\UiPath.Upgrade.exe",
    "Architecture: x64",
    `Framework: 'Microsoft.NETCore.App', version '${version}' (x64)`,
    `.NET location: ${DOTNET_DIR}`,
    "",
    ...(found.length
      ? ["The following frameworks were found:", ...found.map((v) => `  ${v} at [${DOTNET_DIR}shared\\Microsoft.NETCore.App]`)]
      : ["No frameworks were found."]),
    "",
    "Learn more:",
    "https://aka.ms/dotnet/app-launch-failed",
    "",
    "To install missing framework, download:",
    `https://aka.ms/dotnet-core-applaunch?framework=Microsoft.NETCore.App&framework_version=${version}&arch=x64&rid=win-x64&os=win10`,
  ];
  return { status: FRAMEWORK_MISSING, stderr: lines.join("\r\n") + "\r\n" };
}
const NO_DOTNET = {
  status: HOST_MISSING,
  stderr: [
    "You must install .NET to run this application.",
    "",
    "App: C:\\tools\\UiPath.Upgrade.exe",
    "Architecture: x64",
    "App host version: 8.0.30",
    ".NET location: Not found",
    "",
    "Learn more:",
    "https://aka.ms/dotnet/app-launch-failed",
    "",
    "Download the .NET runtime:",
    "https://aka.ms/dotnet-core-applaunch?missing_runtime=true&arch=x64&rid=win-x64&os=win10&apphost_version=8.0.30",
    "Failed to resolve hostfxr.dll [not found]. Error code: 0x80008083",
  ].join("\r\n"),
};
const toolStarts = (r) => r.calls.filter((c) => c.startsWith("UiPath.Upgrade.exe")).length;
const downloads = (r) => r.calls.filter((c) => c === "curl download" || c === "powershell.exe DownloadFile").length;
const lookups = (r) => r.calls.filter((c) => c === "curl latest" || c === "powershell.exe latest.json").length;
// latest.json as UiPath's pipeline writes it: a byte-order mark, then the object.
const serves = (version) => ({ stdout: `﻿{\r\n    "version":  ${JSON.stringify(version)},\r\n    "buildId":  "14276370"\r\n}\r\n` });
// The cached build answers 25.10.4 (the preload's default); the downloaded one answers 26.10.0.
const NEWER = { latest: serves("26.10.0") };
const DOWNLOAD = { curl: { ok: true }, expand: "ok", stagedVersion: { stdout: "26.10.0\n" } };
// The default cache root, used when UIPATH_ACTIVITY_MIGRATOR_DIR is not set, with a build the script installed.
function defaultRoot(ctx) {
  const local = join(ctx.dir, "local");
  const cacheRoot = join(local, "UiPath", "ActivityMigrator");
  mkdirSync(join(cacheRoot, "current"), { recursive: true });
  writeFileSync(join(cacheRoot, "current", "UiPath.Upgrade.exe"), "exe");
  return { cacheRoot, opts: { useEnvDir: false, env: { LOCALAPPDATA: local } } };
}
// A message is checked for the facts it must carry, never for the sentence around them.
function carries(r, ...facts) {
  for (const fact of facts) assert.ok(r.json.message.includes(fact), `"${fact}" is missing from: ${r.json.message}`);
}

test("without the preload the script refuses to run on a non-Windows host", { skip: process.platform === "win32" }, () => {
  const r = spawnSync(process.execPath, [SCRIPT], { encoding: "utf8" });
  assert.equal(r.status, 1);
  const out = JSON.parse(r.stdout.trim());
  assert.equal(out.status, "error");
  assert.equal(out.code, "not-windows");
});

test("a root-level cached tool is verified and reported without any network call", () => {
  const ctx = setup({ cached: "root" });
  const r = run(ctx, {});
  assert.equal(r.status, 0);
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.version, "25.10.4");
  assert.equal(r.json.source, "env");
  assert.equal(fwd(r.json.exe).endsWith("/root/UiPath.Upgrade.exe"), true);
  assert.ok(!r.calls.some((c) => c.startsWith("curl")), "no download for an env-pinned dir");
});

test("a tool that starts is trusted: no .NET install is inspected, whatever runtime the build targets", () => {
  for (const target of ["8.0.0", "10.0.0"]) {
    const ctx = setup({ cached: "root" });
    writeRuntimeConfig(ctx.root, target);
    const r = run(ctx, {});
    assert.equal(r.json.status, "ok", target);
    assert.deepEqual(Object.keys(r.json), ["status", "source", "command", "exe", "version"]);
    assert.deepEqual(r.calls, ["UiPath.Upgrade.exe version"], "starting the tool is the only runtime check");
  }
});

test("a tool under current/ is found", () => {
  const ctx = setup({ cached: "current" });
  const r = run(ctx, {});
  assert.equal(r.json.status, "ok");
  assert.match(fwd(r.json.exe), /\/root\/current\/UiPath\.Upgrade\.exe$/);
});

test("a plain run with nothing cached reports missing with the dir and url, and downloads nothing", () => {
  const ctx = setup();
  const r = run(ctx, { curl: { ok: true }, expand: "ok" });
  assert.equal(r.status, 3);
  assert.equal(r.json.status, "missing");
  assert.match(fwd(r.json.dir), /\/root$/);
  assert.equal(r.json.url, "http://example.invalid/UiPath.Upgrade.Cli.zip");
  assert.deepEqual(r.calls, []);
  assert.ok(!existsSync(join(ctx.root, "current")));
});

test("offline mode with nothing cached is an offline-missing error", () => {
  const ctx = setup();
  const r = run(ctx, {}, { env: { UIPATH_ACTIVITY_MIGRATOR_OFFLINE: "1" } });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "offline-missing");
  assert.match(r.json.message, /Manual placement/);
});

test("offline wins over --install: nothing cached stays an offline-missing error with no network call", () => {
  const ctx = setup();
  const r = run(ctx, { curl: { ok: true }, expand: "ok" }, { args: ["--install"], env: { UIPATH_ACTIVITY_MIGRATOR_OFFLINE: "1" } });
  assert.equal(r.json.code, "offline-missing");
  assert.deepEqual(r.calls, []);
});

test("offline wins over --force: the cached tool is kept and no network call is made", () => {
  const ctx = setup({ cached: "current" });
  writeFileSync(join(ctx.root, "current", "stale.txt"), "old");
  const r = run(ctx, { curl: { ok: true }, expand: "ok" }, { args: ["--force"], env: { UIPATH_ACTIVITY_MIGRATOR_OFFLINE: "1" } });
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.source, "env");
  assert.ok(existsSync(join(ctx.root, "current", "stale.txt")));
  assert.ok(!r.calls.some((c) => c.startsWith("curl") || c.startsWith("powershell.exe")));
});

test("LOCALAPPDATA is required when no install dir is given", () => {
  const ctx = setup();
  const r = run(ctx, {}, { useEnvDir: false, env: { LOCALAPPDATA: "" } });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "verify-failed");
  assert.match(r.json.message, /LOCALAPPDATA is not set/);
});

test("without an install dir the cache lives under LOCALAPPDATA and counts as cached", () => {
  const ctx = setup();
  const local = join(ctx.dir, "local");
  const cacheRoot = join(local, "UiPath", "ActivityMigrator");
  mkdirSync(cacheRoot, { recursive: true });
  writeFileSync(join(cacheRoot, "UiPath.Upgrade.exe"), "exe");
  const r = run(ctx, {}, { useEnvDir: false, env: { LOCALAPPDATA: local } });
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.source, "cached");
});

test("--install downloads with curl, extracts with Expand-Archive and reports downloaded", () => {
  const ctx = setup();
  const r = run(ctx, DOWNLOAD, { args: ["--install"] });
  assert.equal(r.status, 0);
  assert.equal(r.json.source, "downloaded");
  assert.equal(r.json.version, "26.10.0");
  assert.match(fwd(r.json.exe), /\/root\/current\/UiPath\.Upgrade\.exe$/);
  assert.deepEqual(readdirSync(ctx.root), ["current"], "no archive, staging folder or state file left behind");
  assert.ok(existsSync(join(ctx.root, "current", "Extensions")));
});

test("--force re-downloads even when the tool is cached and replaces current/", () => {
  const ctx = setup({ cached: "current", stamp: "a stamp an earlier version of the script wrote" });
  writeFileSync(join(ctx.root, "current", "stale.txt"), "old");
  const r = run(ctx, DOWNLOAD, { args: ["--force"] });
  assert.equal(r.json.source, "downloaded");
  assert.equal(r.json.version, "26.10.0", "the version reported is the new build's");
  assert.equal(lookups(r), 0, "a forced run does not ask the server");
  assert.equal(toolStarts(r), 1, "only the downloaded build is started");
  assert.deepEqual(readdirSync(ctx.root), ["current"], "one build on disk, and the old stamp gone");
  assert.ok(!existsSync(join(ctx.root, "current", "stale.txt")));
});

test("falls back to PowerShell WebClient when curl fails", () => {
  const ctx = setup();
  const r = run(ctx, { ...DOWNLOAD, curl: {}, psDownload: { ok: true } }, { args: ["--install"] });
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.source, "downloaded");
});

test("download failure names both attempts and tells the user how to place the tool manually", () => {
  const ctx = setup();
  const r = run(ctx, { curl: {}, psDownload: {} }, { args: ["--install"] });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "download-failed");
  assert.match(r.json.message, /curl: 22\)? ?the last line|curl: \(22\) the last line/);
  assert.match(r.json.message, /PowerShell WebClient: proxy said \(407\)/);
  assert.match(r.json.message, /Manual placement/);
  assert.ok(!existsSync(join(ctx.root, "UiPath.Upgrade.Cli.download.zip")));
});

test("download failure reports missing curl and missing PowerShell", () => {
  const ctx = setup();
  const r = run(ctx, { curl: { missing: true }, psDownload: { missing: true } }, { args: ["--install"] });
  assert.equal(r.json.code, "download-failed");
  assert.match(r.json.message, /curl: not found/);
  assert.match(r.json.message, /PowerShell WebClient: not found/);
});

test("extraction falls back to unzip when PowerShell and tar cannot extract", () => {
  const ctx = setup();
  const r = run(ctx, { curl: { ok: true }, unzip: "ok" }, { args: ["--install"] });
  assert.equal(r.json.status, "ok");
  assert.ok(r.calls.some((c) => c.startsWith("unzip")));
});

test("extraction falls back to the system tar.exe when it exists", () => {
  const ctx = setup();
  mkdirSync(join(ctx.sysRoot, "System32"), { recursive: true });
  writeFileSync(join(ctx.sysRoot, "System32", "tar.exe"), "");
  const r = run(ctx, { curl: { ok: true }, tar: "ok" }, { args: ["--install"] });
  assert.equal(r.json.status, "ok");
  assert.ok(r.calls.some((c) => c.startsWith("tar.exe")));
  assert.ok(!r.calls.some((c) => c.startsWith("unzip")));
});

test("an archive no tool can extract is an extract-failed error", () => {
  const ctx = setup();
  const r = run(ctx, { curl: { ok: true } }, { args: ["--install"] });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "extract-failed");
  assert.match(r.json.message, /Could not extract/);
  assert.ok(!existsSync(join(ctx.root, ".extract-tmp")));
});

test("an archive missing the exe or Extensions folder is rejected as an unexpected layout", () => {
  for (const layout of ["no-exe", "no-extensions"]) {
    const ctx = setup();
    const r = run(ctx, { curl: { ok: true }, expand: layout }, { args: ["--install"] });
    assert.equal(r.json.code, "extract-failed", layout);
    assert.match(r.json.message, /Archive layout unexpected/);
    assert.deepEqual(readdirSync(ctx.root), [], "nothing installed, and the useless archive is not left behind");
  }
});

// --- The update check: the cached tool's version against the one latest.json names ---

test("a plain run reports a newer served version as update: true and keeps the cached tool", () => {
  const ctx = setup();
  const { cacheRoot, opts } = defaultRoot(ctx);
  const r = run(ctx, { ...NEWER, ...DOWNLOAD }, opts);
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.source, "cached");
  assert.equal(r.json.version, "25.10.4");
  assert.equal(r.json.update, true);
  assert.equal(downloads(r), 0);
  assert.deepEqual(readdirSync(cacheRoot), ["current"], "nothing written");
});

test("--install replaces a cached non-env install when the server holds a newer version, and only then", () => {
  const newer = setup();
  const replaced = run(newer, { ...NEWER, ...DOWNLOAD }, { ...defaultRoot(newer).opts, args: ["--install"] });
  assert.equal(replaced.json.status, "ok");
  assert.equal(replaced.json.source, "updated");
  assert.equal(replaced.json.version, "26.10.0");
  assert.equal(replaced.json.update, undefined);

  const same = setup();
  const kept = run(same, { latest: serves("25.10.4"), ...DOWNLOAD }, { ...defaultRoot(same).opts, args: ["--install"] });
  assert.equal(kept.json.source, "cached");
  assert.equal(downloads(kept), 0);
});

test("no update is reported when the server holds the cached version, an older one, or nothing readable", () => {
  const answers = [serves("25.10.4"), serves("25.9.9"), serves("next"), { stdout: '{ "version": 26 }' }, { stdout: "<html>not found</html>" }, { status: 22 }];
  for (const latest of answers) {
    const ctx = setup();
    const r = run(ctx, { latest }, defaultRoot(ctx).opts);
    assert.equal(r.json.status, "ok", JSON.stringify(latest));
    assert.equal(r.json.update, undefined, JSON.stringify(latest));
  }
});

test("versions compare as versions: by number, a release above its pre-releases, pre-releases in order", () => {
  const cases = [
    ["25.10.4", "25.10.10", true],
    ["26.2.0", "25.12.9", false],
    ["26.10.0-alpha.26345", "26.10.0", true],
    ["26.10.0", "26.10.0-alpha.26347", false],
    ["26.10.0-alpha.26345", "26.10.0-alpha.26347", true],
    ["26.10.0-alpha.26347", "26.10.0-alpha.26345", false],
    ["26.10.0-alpha", "26.10.0-alpha.1", true],
    ["26.10.0-alpha.9", "26.10.0-beta", true],
    ["26.10.0-7", "26.10.0-alpha", true],
  ];
  for (const [cached, served, outdated] of cases) {
    const ctx = setup();
    const r = run(ctx, { version: { stdout: cached + "\n" }, latest: serves(served) }, defaultRoot(ctx).opts);
    assert.equal(r.json.update === true, outdated, `${cached} against ${served}`);
  }
});

test("latest.json is read next to the archive, and through PowerShell when curl cannot reach it", () => {
  const ctx = setup();
  // Whatever precedes the object, such as a byte-order mark decoded as stray characters, is cut away.
  const r = run(ctx, { psLatest: { stdout: '\u00EF\u00BB\u00BF{ "version": "26.10.0" }' } }, defaultRoot(ctx).opts);
  assert.equal(r.json.update, true);
  assert.deepEqual(r.calls, ["UiPath.Upgrade.exe version", "curl latest", "powershell.exe latest.json"]);
});

test("a build placed by hand at the top of the default root is used as is: no update check, and --install downloads nothing", () => {
  // An update installs into current/, which the root build keeps hiding: checked, every install run would download again.
  const ctx = setup();
  const local = join(ctx.dir, "local");
  const cacheRoot = join(local, "UiPath", "ActivityMigrator");
  mkdirSync(cacheRoot, { recursive: true });
  writeFileSync(join(cacheRoot, "UiPath.Upgrade.exe"), "exe");
  const opts = { useEnvDir: false, env: { LOCALAPPDATA: local } };
  for (const args of [[], ["--install"]]) {
    const r = run(ctx, { ...NEWER, ...DOWNLOAD }, { ...opts, args });
    assert.equal(r.json.source, "cached", args.join());
    assert.equal(r.json.exe, join(cacheRoot, "UiPath.Upgrade.exe"), args.join());
    assert.equal(r.json.update, undefined, args.join());
    assert.equal(lookups(r) + downloads(r), 0, args.join());
    assert.deepEqual(readdirSync(cacheRoot), ["UiPath.Upgrade.exe"], args.join());
  }
});

test("an override dir and offline mode never ask the server", () => {
  const override = setup({ cached: "current" });
  const viaDir = run(override, NEWER);
  assert.equal(viaDir.json.source, "env");
  assert.equal(viaDir.json.update, undefined);
  assert.equal(lookups(viaDir), 0);

  const ctx = setup();
  const { opts } = defaultRoot(ctx);
  const offline = run(ctx, NEWER, { ...opts, env: { ...opts.env, UIPATH_ACTIVITY_MIGRATOR_OFFLINE: "1" } });
  assert.equal(offline.json.update, undefined);
  assert.equal(lookups(offline), 0);
});

// --- Replacing a build: the installed one is never lost ---

test("an installed build still in use is not replaced: it stays, and nothing of the download is left behind", () => {
  // Windows refuses to rename a folder a program runs from: the first rename of the swap.
  const ctx = setup({ cached: "current" });
  writeFileSync(join(ctx.root, "current", "keep.txt"), "old");
  const r = run(ctx, DOWNLOAD, { args: ["--force"], env: { FAKE_FAIL_RENAME_FROM: "current" } });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "extract-failed");
  carries(r, join(ctx.root, "current"), "EPERM", "UiPath.Upgrade.exe");
  assert.doesNotMatch(r.json.message, /manually/, "nothing to extract by hand: the installed build works");
  assert.equal(readFileSync(join(ctx.root, "current", "keep.txt"), "utf8"), "old");
  assert.deepEqual(readdirSync(ctx.root), ["current"], "no archive, staging folder or current.old left");
});

test("a swap that fails halfway puts the previous build back", () => {
  const ctx = setup({ cached: "current" });
  writeFileSync(join(ctx.root, "current", "keep.txt"), "old");
  const r = run(ctx, DOWNLOAD, { args: ["--force"], env: { FAKE_FAIL_RENAME_FROM: ".extract-tmp" } });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "extract-failed");
  assert.equal(readFileSync(join(ctx.root, "current", "keep.txt"), "utf8"), "old", "previous build restored");
  assert.deepEqual(readdirSync(ctx.root), ["current"]);
});

test("a first install that cannot be moved into place keeps the archive for manual extraction", () => {
  const ctx = setup();
  const r = run(ctx, DOWNLOAD, { args: ["--install"], env: { FAKE_FAIL_RENAME_FROM: ".extract-tmp" } });
  assert.equal(r.json.code, "extract-failed");
  carries(r, join(ctx.root, "UiPath.Upgrade.Cli.download.zip"), join(ctx.root, "current"));
  assert.deepEqual(readdirSync(ctx.root), ["UiPath.Upgrade.Cli.download.zip"]);
});

test("a staging folder that will not clear stops the run before extraction, with the installed build and the zip intact", () => {
  const ctx = setup({ cached: "current" });
  mkdirSync(join(ctx.root, ".extract-tmp"), { recursive: true });
  writeFileSync(join(ctx.root, ".extract-tmp", "Old.dll"), "stale");
  const r = run(ctx, DOWNLOAD, { args: ["--force"], env: { FAKE_FAIL_RM: ".extract-tmp" } });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "extract-failed");
  carries(r, join(ctx.root, ".extract-tmp"));
  assert.ok(!r.calls.includes("powershell.exe Expand-Archive"), "nothing extracted into the dirty folder");
  assert.ok(existsSync(join(ctx.root, "current", "UiPath.Upgrade.exe")), "installed build untouched");
  assert.ok(existsSync(join(ctx.root, "UiPath.Upgrade.Cli.download.zip")), "zip kept for manual extraction");
});

test("a leftover current.old from an interrupted swap is restored when current/ is gone", () => {
  const ctx = setup();
  mkdirSync(join(ctx.root, "current.old"), { recursive: true });
  writeFileSync(join(ctx.root, "current.old", "UiPath.Upgrade.exe"), "exe");
  const r = run(ctx, {});
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.exe, join(ctx.root, "current", "UiPath.Upgrade.exe"));
  assert.ok(!existsSync(join(ctx.root, "current.old")));
});

test("a leftover current.old that cannot be put back is kept as the only build, then restored by the next run", () => {
  const ctx = setup();
  mkdirSync(join(ctx.root, "current.old"), { recursive: true });
  writeFileSync(join(ctx.root, "current.old", "UiPath.Upgrade.exe"), "exe");
  const r = run(ctx, {}, { env: { FAKE_FAIL_RENAME_FROM: "current.old" } });
  assert.equal(r.status, 3);
  assert.equal(r.json.status, "missing");
  assert.ok(existsSync(join(ctx.root, "current.old", "UiPath.Upgrade.exe")), "the only build is never deleted");
  const next = run(ctx, {});
  assert.equal(next.json.status, "ok");
  assert.equal(next.json.exe, join(ctx.root, "current", "UiPath.Upgrade.exe"));
});

test("a previous build Windows refuses to delete is left for a later run, never a crash", () => {
  const ctx = setup({ cached: "current" });
  const r = run(ctx, DOWNLOAD, { args: ["--force"], env: { FAKE_FAIL_RM: "current.old" } });
  assert.equal(r.json.status, "ok", "the run reports its JSON line although the cleanup failed");
  assert.ok(existsSync(join(ctx.root, "current.old")), "leftover kept");
  const locked = run(ctx, {}, { env: { FAKE_FAIL_RM: "current.old" } });
  assert.equal(locked.json.status, "ok", "still locked at startup: the run goes on");
  const freed = run(ctx, {});
  assert.equal(freed.json.status, "ok");
  assert.ok(!existsSync(join(ctx.root, "current.old")), "removed once the lock is gone");
});

// --- The downloaded build is started before it replaces anything ---

test("an update whose build needs a .NET this machine lacks is not installed: the installed build stays and runs", () => {
  const ctx = setup({ cached: "current" });
  writeFileSync(join(ctx.root, "current", "keep.txt"), "old");
  const r = run(ctx, { ...DOWNLOAD, stagedRuntime: "10.0.0", stagedVersion: frameworkMissing("10.0.0", ["8.0.33"]) }, { args: ["--force"] });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "runtime-missing");
  carries(r, ".NET Desktop Runtime 10 (x64)", "https://dotnet.microsoft.com/download/dotnet/10.0", "8.0.33", join(ctx.root, "current", "UiPath.Upgrade.exe"));
  assert.deepEqual(readdirSync(ctx.root), ["current"], "no staging folder and no archive left");
  assert.equal(readFileSync(join(ctx.root, "current", "keep.txt"), "utf8"), "old", "installed build untouched");
  const next = run(ctx, {});
  assert.equal(next.json.status, "ok");
  assert.equal(next.json.version, "25.10.4");
});

test("an update whose build prints no version is not installed either, and the message sends nobody to --force", () => {
  const ctx = setup({ cached: "current" });
  const r = run(ctx, { ...DOWNLOAD, stagedVersion: { status: 134, stderr: "Unhandled exception." } }, { args: ["--force"] });
  assert.equal(r.json.code, "verify-failed");
  carries(r, "Unhandled exception.", join(ctx.root, "current", "UiPath.Upgrade.exe"));
  assert.doesNotMatch(r.json.message, /--force/, "a second forced run would download the same build again");
  assert.deepEqual(readdirSync(ctx.root), ["current"]);
  assert.equal(run(ctx, {}).json.version, "25.10.4");
});

test("a first install is put in place even when it does not start, and is reported under the path it ends up at", () => {
  const ctx = setup();
  const r = run(ctx, { ...DOWNLOAD, stagedRuntime: "10.0.0", stagedVersion: frameworkMissing("10.0.0") }, { args: ["--install"] });
  assert.equal(r.json.code, "runtime-missing");
  carries(r, join(ctx.root, "current", "UiPath.Upgrade.exe"), ".NET Desktop Runtime 10 (x64)");
  assert.ok(existsSync(join(ctx.root, "current", "UiPath.Upgrade.exe")), "installing the runtime is all that is left to do");
  assert.equal(toolStarts(r), 1);
});

test("an update that starts only under the strict telemetry spelling is installed, and the assignment is reported", () => {
  const ctx = setup({ cached: "current" });
  writeFileSync(join(ctx.root, "current", "stale.txt"), "old");
  const r = run(ctx, { ...DOWNLOAD, strictTelemetry: true }, { args: ["--force"], env: { UIPATH_TELEMETRY_DISABLED: "1" } });
  assert.equal(r.json.code, "telemetry-flag");
  assert.equal(r.json.env, "UIPATH_TELEMETRY_DISABLED=true");
  assert.ok(!existsSync(join(ctx.root, "current", "stale.txt")), "the new build is in place");
});

test("a build whose runtime is missing is told which Desktop Runtime to install, whatever .NET it targets", () => {
  for (const [target, major] of [["8.0.0", "8"], ["10.0.0", "10"], ["12.0.0", "12"]]) {
    const ctx = setup({ cached: "root" });
    writeRuntimeConfig(ctx.root, target);
    const r = run(ctx, { version: frameworkMissing(target, ["9.0.22", "11.0.1"]) });
    assert.equal(r.status, 1, target);
    assert.equal(r.json.code, "runtime-missing", target);
    carries(r, `.NET Desktop Runtime ${major} (x64)`, `https://dotnet.microsoft.com/download/dotnet/${major}.0`, DOTNET_DIR, "9.0.22", "11.0.1");
    assert.doesNotMatch(r.json.message, /aka\.ms/, "the launcher's link installs the base runtime alone");
    assert.deepEqual(r.calls, ["UiPath.Upgrade.exe version"]);
  }
});

test("a runtimeconfig that names one framework is read as well", () => {
  const ctx = setup({ cached: "root" });
  writeRuntimeConfig(ctx.root, "10.0.0", { single: true });
  const r = run(ctx, { version: frameworkMissing("10.0.0") });
  assert.equal(r.json.code, "runtime-missing");
  carries(r, ".NET Desktop Runtime 10 (x64)");
});

test("a machine with no .NET install gets the runtime the build targets and no folder", () => {
  const ctx = setup({ cached: "root" });
  writeRuntimeConfig(ctx.root, "10.0.0");
  const r = run(ctx, { version: NO_DOTNET });
  assert.equal(r.json.code, "runtime-missing");
  carries(r, ".NET Desktop Runtime 10 (x64)", "https://dotnet.microsoft.com/download/dotnet/10.0");
  assert.doesNotMatch(r.json.message, /Not found/, "the launcher's placeholder is not passed on as a folder");
});

test("a set DOTNET_ROOT_X64 is named with its folder, and no install is suggested", () => {
  const ctx = setup({ cached: "root" });
  writeRuntimeConfig(ctx.root, "8.0.0");
  const r = run(ctx, { version: frameworkMissing("8.0.0", ["10.0.0"]) }, { env: { DOTNET_ROOT_X64: ctx.root, DOTNET_ROOT: ctx.dir } });
  assert.equal(r.json.code, "runtime-missing");
  carries(r, ".NET Desktop Runtime 8 (x64)", ctx.root, "DOTNET_ROOT_X64", "10.0.0");
  assert.doesNotMatch(r.json.message, /download/, "an install into the default location would change nothing");
});

test("DOTNET_ROOT is named when DOTNET_ROOT_X64 is not set", () => {
  const ctx = setup({ cached: "root" });
  writeRuntimeConfig(ctx.root, "8.0.0");
  const r = run(ctx, { version: NO_DOTNET }, { env: { DOTNET_ROOT: ctx.dir } });
  assert.equal(r.json.code, "runtime-missing");
  carries(r, ctx.dir, "DOTNET_ROOT");
  assert.doesNotMatch(r.json.message, /DOTNET_ROOT_X64|download/);
});

test("a DOTNET_ROOT variable that names no folder is not blamed: the launcher skips it", () => {
  const ctx = setup({ cached: "root" });
  writeRuntimeConfig(ctx.root, "10.0.0");
  const gone = join(ctx.dir, "gone");
  const version = frameworkMissing("10.0.0", ["8.0.33"]);

  const fallback = run(ctx, { version }, { env: { DOTNET_ROOT_X64: gone, DOTNET_ROOT: gone } });
  assert.equal(fallback.json.code, "runtime-missing");
  carries(fallback, DOTNET_DIR, "https://dotnet.microsoft.com/download/dotnet/10.0");
  assert.doesNotMatch(fallback.json.message, /DOTNET_ROOT/);

  const second = run(ctx, { version }, { env: { DOTNET_ROOT_X64: gone, DOTNET_ROOT: ctx.dir } });
  carries(second, ctx.dir, "DOTNET_ROOT");
  assert.doesNotMatch(second.json.message, /DOTNET_ROOT_X64|download/);
});

test("without a readable runtimeconfig no version is made up: the launcher's own text carries it", () => {
  for (const config of ["not json", "{}", JSON.stringify({ runtimeOptions: { frameworks: [{ name: "Other", version: "1.0.0" }] } })]) {
    const ctx = setup({ cached: "root" });
    writeFileSync(join(ctx.root, "UiPath.Upgrade.runtimeconfig.json"), config);
    const r = run(ctx, { version: frameworkMissing("9.0.0") });
    assert.equal(r.json.code, "runtime-missing", config);
    carries(r, "version '9.0.0'", "https://dotnet.microsoft.com/download/dotnet", DOTNET_DIR);
    assert.doesNotMatch(r.json.message, /Desktop Runtime \d|download\/dotnet\/\d/, config);
  }
  const ctx = setup({ cached: "root" });
  const none = run(ctx, { version: NO_DOTNET });
  assert.equal(none.json.code, "runtime-missing");
  carries(none, "App host version: 8.0.30");
});

test("a missing runtime is reported without the telemetry retry", () => {
  const ctx = setup({ cached: "root" });
  writeRuntimeConfig(ctx.root, "8.0.0");
  const r = run(ctx, { version: frameworkMissing("8.0.0") }, { env: { UIPATH_TELEMETRY_DISABLED: "1" } });
  assert.equal(r.json.code, "runtime-missing");
  assert.equal(toolStarts(r), 1, "a second start cannot find a runtime the first one missed");
});

test("a broken .NET install exits like a missing one and stays a verify failure with the launcher's text", () => {
  const ctx = setup({ cached: "root" });
  writeRuntimeConfig(ctx.root, "8.0.0");
  const stderr = "A fatal error was encountered. The library 'hostpolicy.dll' required to execute the application was not found in 'C:\\x'.";
  const r = run(ctx, { version: { status: HOST_MISSING, stderr } });
  assert.equal(r.json.code, "verify-failed");
  carries(r, stderr);
});

test("launcher text under another exit code is not read as a missing runtime", () => {
  const ctx = setup({ cached: "root" });
  writeRuntimeConfig(ctx.root, "8.0.0");
  const r = run(ctx, { version: { ...frameworkMissing("8.0.0"), status: 1 } });
  assert.equal(r.json.code, "verify-failed");
  carries(r, "You must install or update .NET to run this application.");
});

test("a tool that prints nothing fails verification with its stderr", () => {
  const ctx = setup({ cached: "root" });
  const r = run(ctx, { version: { status: 134, stderr: "Unhandled exception.   System.IO.FileNotFoundException" } });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "verify-failed");
  assert.match(r.json.message, /did not print a version \(Unhandled exception\. System\.IO\.FileNotFoundException\)/);
  assert.match(r.json.message, /rerun with --force/);
});

test("a tool that exits non-zero without output says so", () => {
  const ctx = setup({ cached: "root" });
  const r = run(ctx, { version:{ status: 3 } });
  assert.match(r.json.message, /exit code 3, no output/);
});

test("a bool.Parse crash on UIPATH_TELEMETRY_DISABLED=1 is diagnosed and the strict spelling is named", () => {
  const ctx = setup({ cached: "root" });
  const r = run(ctx, { strictTelemetry:true }, { env: { UIPATH_TELEMETRY_DISABLED: "1" } });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "telemetry-flag");
  assert.equal(r.json.env, "UIPATH_TELEMETRY_DISABLED=true");
  assert.match(r.json.message, /never unset the variable/);
});

test("a telemetry value meaning off is retried as false", () => {
  const ctx = setup({ cached: "root" });
  const r = run(ctx, { strictTelemetry:true }, { env: { UIPATH_TELEMETRY_DISABLED: "off" } });
  assert.equal(r.json.code, "telemetry-flag");
  assert.equal(r.json.env, "UIPATH_TELEMETRY_DISABLED=false");
});

test("a failing tool with a strict telemetry value is a plain verify failure", () => {
  const ctx = setup({ cached: "root" });
  const r = run(ctx, { version:{ status: 1, stderr: "boom" } }, { env: { UIPATH_TELEMETRY_DISABLED: "true" } });
  assert.equal(r.json.code, "verify-failed");
});

// --- uip rpa project migrate (Helm) ----------------------------------------
// The uip path runs only when neither UIPATH_ACTIVITY_MIGRATOR_DIR nor UIPATH_ACTIVITY_MIGRATOR_URL is set.

const UIP_VERSION_CALL = "uip rpa project migrate version";
const uipVersion = (version = "27.0.207-dev") => ({ stdout: `${version}\n` });
const uipFailure = (code, message, instructions = "Fix it like this.", stream = "stderr") => ({
  status: 1,
  [stream]: JSON.stringify({ Result: "Failure", Message: message, Instructions: instructions, Code: code }, null, 2) + "\n",
});
const UNKNOWN_COMMAND = {
  status: 3,
  stdout: JSON.stringify({ Result: "ValidationError", ErrorCode: "invalid_argument", Message: "error: unknown command 'migrate'" }) + "\n",
};
// A Helm released before the verb treats `migrate` as an unknown argument and exits with its own error.
const OLD_HELM = { status: 1, stderr: "Unrecognized command or argument 'migrate'.\n" };

function runUip(ctx, scenario, { args = [], env = {} } = {}) {
  return run(ctx, scenario, { args, useEnvDir: false, env: { UIPATH_ACTIVITY_MIGRATOR_URL: "", LOCALAPPDATA: join(ctx.dir, "local"), ...env } });
}

test("a migrator in uip's Helm is reported as source uip with its command, and nothing else runs", () => {
  const ctx = setup();
  const r = runUip(ctx, { uip: { stdout: "Resolving Helm...\n27.0.207-dev\n" } });
  assert.equal(r.status, 0);
  assert.deepEqual(r.json, { status: "ok", source: "uip", command: "uip rpa project migrate", version: "27.0.207-dev" });
  assert.deepEqual(r.calls, [UIP_VERSION_CALL], "no download and no exe start");
});

test("UIPATH_STUDIO_PID never reaches the uip command", () => {
  const ctx = setup();
  const r = runUip(ctx, { uip: uipVersion() }, { env: { UIPATH_STUDIO_PID: "1234" } });
  assert.equal(r.json.status, "ok");
  assert.equal(r.calls[0], UIP_VERSION_CALL);
});

test("uip's not-windows failure stops the run with its message, wherever uip prints it", () => {
  for (const stream of ["stdout", "stderr"]) {
    const ctx = setup({ cached: "root" });
    const r = runUip(ctx, { uip: uipFailure("not-windows", "The Activity Migrator runs on Windows only.", "Run it on Windows.", stream) });
    assert.equal(r.status, 1, stream);
    assert.equal(r.json.code, "not-windows");
    assert.match(r.json.message, /Windows only\. Run it on Windows\./);
    assert.deepEqual(r.calls, [UIP_VERSION_CALL], "no archive fallback");
  }
});

test("helm-missing on a plain run reports missing with uip's message and downloads nothing", () => {
  const ctx = setup();
  const r = runUip(ctx, {
    uip: uipFailure("helm-missing", "The Activity Migrator ships with Helm, which was not found: no @uipath/studio-helm-win32-x64.", "Reinstall the uip CLI with its optional dependencies, or set HELM_LOCAL_DIR to a Helm tools directory.", "stdout"),
  });
  assert.equal(r.status, 3);
  assert.equal(r.json.status, "missing");
  assert.match(fwd(r.json.dir), /\/local\/UiPath\/ActivityMigrator$/);
  assert.equal(r.json.url, "https://download.uipath.com/upgrade/UiPath.Upgrade.Cli.zip");
  assert.match(r.json.uipMessage, /^uip rpa project migrate version: helm-missing: The Activity Migrator ships with Helm/);
  assert.match(r.json.uipMessage, /HELM_LOCAL_DIR/);
  assert.deepEqual(r.calls, [UIP_VERSION_CALL], "no download without --install");
});

test("helm-missing with --install falls back to the archive download and keeps uip's message", () => {
  const ctx = setup();
  const r = runUip(ctx, { uip: uipFailure("helm-missing", "Helm was not found.", "Reinstall the uip CLI.", "stdout"), curl: { ok: true }, expand: "ok" }, { args: ["--install"] });
  assert.equal(r.status, 0);
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.source, "downloaded");
  assert.equal(r.json.command, r.json.exe);
  assert.match(fwd(r.json.exe), /\/local\/UiPath\/ActivityMigrator\/current\/UiPath\.Upgrade\.exe$/);
  assert.match(r.json.uipMessage, /helm-missing: Helm was not found\. Reinstall the uip CLI\./);
  assert.equal(r.calls[0], UIP_VERSION_CALL);
  assert.ok(r.calls.some((c) => c.startsWith("curl")));
});

test("a uip without project migrate, a Helm without the verb, or no uip fall back to the archive with the reason", () => {
  for (const [uip, reason] of [[UNKNOWN_COMMAND, /unknown command 'migrate'/], [OLD_HELM, /Unrecognized command or argument 'migrate'/], [undefined, /not recognized/]]) {
    const ctx = setup();
    const missing = runUip(ctx, { uip });
    assert.equal(missing.status, 3, String(reason));
    assert.equal(missing.json.status, "missing");
    assert.match(missing.json.uipMessage, reason);
    const installed = runUip(ctx, { uip, curl: { ok: true }, expand: "ok" }, { args: ["--install"] });
    assert.equal(installed.json.source, "downloaded", String(reason));
    assert.match(installed.json.uipMessage, reason);
  }
});

test("a cached archive tool is used after the fallback, with uip's message", () => {
  const ctx = setup();
  const local = join(ctx.dir, "local");
  const cacheRoot = join(local, "UiPath", "ActivityMigrator", "current");
  mkdirSync(cacheRoot, { recursive: true });
  writeFileSync(join(cacheRoot, "UiPath.Upgrade.exe"), "exe");
  const r = runUip(ctx, { uip: uipFailure("helm-missing", "Helm was not found.") });
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.source, "cached");
  assert.match(r.json.uipMessage, /helm-missing/);
  assert.ok(!r.calls.some((c) => c.startsWith("curl") && c.includes("-o")), "no download");
});

test("an archive failure after the fallback still carries uip's message", () => {
  const ctx = setup();
  const r = runUip(ctx, { uip: uipFailure("helm-missing", "Helm was not found."), curl: {}, psDownload: {} }, { args: ["--install"] });
  assert.equal(r.json.code, "download-failed");
  assert.match(r.json.uipMessage, /helm-missing: Helm was not found\./);
});

test("offline mode after the fallback is offline-missing with uip's message", () => {
  const ctx = setup();
  const r = runUip(ctx, { uip: uipFailure("helm-missing", "Helm was not found.") }, { args: ["--install"], env: { UIPATH_ACTIVITY_MIGRATOR_OFFLINE: "1" } });
  assert.equal(r.json.code, "offline-missing");
  assert.match(r.json.uipMessage, /helm-missing/);
  assert.deepEqual(r.calls, [UIP_VERSION_CALL]);
});

test("UIPATH_ACTIVITY_MIGRATOR_OFFLINE=1 still asks uip, which downloads nothing", () => {
  const ctx = setup();
  const r = runUip(ctx, { uip: uipVersion() }, { env: { UIPATH_ACTIVITY_MIGRATOR_OFFLINE: "1" } });
  assert.equal(r.json.source, "uip");
});

test("UIPATH_ACTIVITY_MIGRATOR_URL or UIPATH_ACTIVITY_MIGRATOR_DIR keeps uip out of it", () => {
  const ctx = setup({ cached: "root" });
  const viaDir = run(ctx, { uip: uipVersion() }, { env: { UIPATH_ACTIVITY_MIGRATOR_URL: "" } });
  assert.equal(viaDir.json.source, "env");
  assert.equal(viaDir.json.command, viaDir.json.exe);
  assert.equal(viaDir.json.uipMessage, undefined);
  assert.ok(!viaDir.calls.some((c) => c.startsWith("uip ")));
  const viaUrl = runUip(ctx, { uip: uipVersion(), curl: { ok: true }, expand: "ok" }, { args: ["--install"], env: { UIPATH_ACTIVITY_MIGRATOR_URL: "http://example.invalid/UiPath.Upgrade.Cli.zip" } });
  assert.equal(viaUrl.json.source, "downloaded");
  assert.ok(!viaUrl.calls.some((c) => c.startsWith("uip ")));
});

test("--install and --force do not touch the archive when uip supplies the migrator", () => {
  for (const flag of ["--install", "--force"]) {
    const ctx = setup();
    const r = runUip(ctx, { uip: uipVersion("26.10.3") }, { args: [flag] });
    assert.equal(r.json.source, "uip", flag);
    assert.equal(r.json.version, "26.10.3");
    assert.deepEqual(r.calls, [UIP_VERSION_CALL], flag);
  }
});

test("POSIX-style install dirs from Git Bash are normalised to Windows paths", { skip: process.platform !== "win32" }, () => {
  const ctx = setup({ cached: "root" });
  const posix = ctx.root.replace(/^([A-Za-z]):/, (_, d) => "/" + d.toLowerCase()).replace(/\\/g, "/");
  const r = run(ctx, {}, { env: { UIPATH_ACTIVITY_MIGRATOR_DIR: posix } });
  assert.equal(r.json.status, "ok");
  assert.ok(r.json.exe.includes("\\"));
});
