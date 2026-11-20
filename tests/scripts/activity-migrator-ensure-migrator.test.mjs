import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test, { after } from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SCRIPT = join(REPO_ROOT, "skills", "uipath-activity-migrator", "scripts", "ensure-migrator.mjs");

// ensure-migrator.mjs is a Windows-only flow that shells out to curl, powershell.exe, tar/unzip and UiPath.Upgrade.exe.
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
    return orig.apply(fs, a);
  };
}
const scn = JSON.parse(process.env.FAKE_SCENARIO || '{}');
const calls = [];
const result = (o) => ({ status: 0, stdout: '', stderr: '', ...o });
const writeLayout = (dir, layout) => {
  dir = norm(dir);
  fs.mkdirSync(dir, { recursive: true });
  if (layout !== 'no-exe') fs.writeFileSync(path.join(dir, 'UiPath.Upgrade.exe'), 'exe');
  if (layout !== 'no-extensions') fs.mkdirSync(path.join(dir, 'Extensions'), { recursive: true });
};
const arg = (command, re) => (re.exec(command) || [])[1];
cp.spawnSync = (cmd, argv, opts) => {
  const command = String(cmd);
  const text = argv.join(' ');
  calls.push(command.replace(/^.*[\\/]/, '') + ' ' + text.slice(0, 60));
  if (command === 'curl') {
    if (argv.includes('-sSIL')) return result(scn.head || { status: 1 });
    const zip = argv[argv.indexOf('-o') + 1];
    if (scn.curl && scn.curl.ok) {
      fs.writeFileSync(norm(zip), 'zip');
      fs.writeFileSync(norm(argv[argv.indexOf('-D') + 1]), scn.curl.headers || '');
      return result({});
    }
    if (scn.curl && scn.curl.missing) return { status: null, error: Object.assign(new Error('spawn curl ENOENT'), { code: 'ENOENT' }) };
    return result({ status: 22, stderr: 'curl: (22) first\ncurl: (22) the last line' });
  }
  if (command === 'powershell.exe') {
    const c = argv[3];
    if (c.includes("Method = 'HEAD'")) return result(scn.psHead || { status: 1 });
    if (c.includes('DownloadFile')) {
      if (scn.psDownload && scn.psDownload.ok) {
        fs.writeFileSync(norm(arg(c, /DownloadFile\('[^']*', '([^']*)'\)/)), 'zip');
        return result({ stdout: scn.psDownload.stdout || '' });
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
    return result(scn.version || { stdout: 'banner\n25.10.4\n' });
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
    assert.deepEqual(Object.keys(r.json), ["status", "exe", "version", "source"]);
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
  const r = run(ctx, { head: { status: 1 }, psHead: { status: 1 } }, { useEnvDir: false, env: { LOCALAPPDATA: local } });
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.source, "cached");
});

test("--install downloads with curl, extracts with Expand-Archive, stamps Last-Modified and reports downloaded", () => {
  const ctx = setup();
  const r = run(
    ctx,
    {
      curl: { ok: true, headers: "HTTP/1.1 301\r\nLast-Modified: old\r\n\r\nHTTP/1.1 200\r\nLast-Modified: Tue, 01 Oct 2025 10:00:00 GMT\r\n" },
      expand: "ok",
    },
    { args: ["--install"] },
  );
  assert.equal(r.status, 0);
  assert.equal(r.json.source, "downloaded");
  assert.match(fwd(r.json.exe), /\/root\/current\/UiPath\.Upgrade\.exe$/);
  assert.equal(readFileSync(join(ctx.root, ".last-modified"), "utf8"), "Tue, 01 Oct 2025 10:00:00 GMT");
  assert.ok(existsSync(join(ctx.root, "current", "Extensions")));
  assert.ok(!existsSync(join(ctx.root, "UiPath.Upgrade.Cli.download.zip")), "temporary archive removed");
  assert.ok(!existsSync(join(ctx.root, ".extract-tmp")), "staging folder renamed away");
});

test("--force re-downloads even when the tool is cached and replaces current/", () => {
  const ctx = setup({ cached: "current" });
  writeFileSync(join(ctx.root, "current", "stale.txt"), "old");
  const r = run(ctx, { curl: { ok: true }, expand: "ok" }, { args: ["--force"] });
  assert.equal(r.json.source, "downloaded");
  assert.ok(!existsSync(join(ctx.root, "current", "stale.txt")));
  assert.equal(existsSync(join(ctx.root, ".last-modified")), false, "no stamp without a Last-Modified header");
});

test("falls back to PowerShell WebClient when curl fails and records its Last-Modified", () => {
  const ctx = setup();
  const r = run(ctx, { curl: {}, psDownload: { ok: true, stdout: " Wed, 02 Oct 2025 GMT " }, expand: "ok" }, { args: ["--install"] });
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.source, "downloaded");
  assert.equal(readFileSync(join(ctx.root, ".last-modified"), "utf8"), "Wed, 02 Oct 2025 GMT");
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
    assert.ok(!existsSync(join(ctx.root, "current")));
  }
});

const CHANGED_REMOTE = { head: { stdout: "HTTP/1.1 200\r\nLast-Modified: new stamp\r\n" }, curl: { ok: true, headers: "Last-Modified: new stamp\r\n" }, expand: "ok" };

function cachedUnderLocalAppData(ctx, stamp) {
  const local = join(ctx.dir, "local");
  const cacheRoot = join(local, "UiPath", "ActivityMigrator");
  mkdirSync(cacheRoot, { recursive: true });
  writeFileSync(join(cacheRoot, "UiPath.Upgrade.exe"), "exe");
  if (stamp !== undefined) writeFileSync(join(cacheRoot, ".last-modified"), stamp);
  return { local, cacheRoot };
}

test("a plain run reports a changed remote Last-Modified as update: true and keeps the cached tool", () => {
  const ctx = setup();
  const { local, cacheRoot } = cachedUnderLocalAppData(ctx, "\uFEFFold stamp\r\n");
  const r = run(ctx, CHANGED_REMOTE, { useEnvDir: false, env: { LOCALAPPDATA: local } });
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.source, "cached");
  assert.equal(r.json.update, true);
  assert.equal(readFileSync(join(cacheRoot, ".last-modified"), "utf8"), "\uFEFFold stamp\r\n", "stamp untouched so the next install run still sees the change");
  assert.ok(!r.calls.some((c) => c.startsWith("curl") && c.includes("-o")), "no download");
  assert.ok(!existsSync(join(cacheRoot, "current")));
});

test("--install replaces a cached non-env install when the remote Last-Modified differs from the stamp", () => {
  const ctx = setup();
  const { local, cacheRoot } = cachedUnderLocalAppData(ctx, "\uFEFFold stamp\r\n");
  const r = run(ctx, CHANGED_REMOTE, { args: ["--install"], useEnvDir: false, env: { LOCALAPPDATA: local } });
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.source, "updated");
  assert.equal(r.json.update, undefined);
  assert.equal(readFileSync(join(cacheRoot, ".last-modified"), "utf8"), "new stamp");
});

test("an unchanged remote Last-Modified (BOM in the stamp ignored) keeps the cached tool without an update flag", () => {
  const ctx = setup();
  const { local } = cachedUnderLocalAppData(ctx, "\uFEFFsame\r\n");
  const r = run(ctx, { head: { stdout: "Last-Modified: same\n" } }, { useEnvDir: false, env: { LOCALAPPDATA: local } });
  assert.equal(r.json.source, "cached");
  assert.equal(r.json.update, undefined);
  assert.ok(!r.calls.some((c) => c.startsWith("curl") && c.includes("-o")));
});

test("the HEAD request falls back to PowerShell and a missing stamp is written from it", () => {
  const ctx = setup();
  const { local, cacheRoot } = cachedUnderLocalAppData(ctx);
  const r = run(ctx, { head: { status: 1 }, psHead: { stdout: " ps stamp " } }, { useEnvDir: false, env: { LOCALAPPDATA: local } });
  assert.equal(r.json.source, "cached");
  assert.equal(readFileSync(join(cacheRoot, ".last-modified"), "utf8"), "ps stamp");
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

test("POSIX-style install dirs from Git Bash are normalised to Windows paths", { skip: process.platform !== "win32" }, () => {
  const ctx = setup({ cached: "root" });
  const posix = ctx.root.replace(/^([A-Za-z]):/, (_, d) => "/" + d.toLowerCase()).replace(/\\/g, "/");
  const r = run(ctx, {}, { env: { UIPATH_ACTIVITY_MIGRATOR_DIR: posix } });
  assert.equal(r.json.status, "ok");
  assert.ok(r.json.exe.includes("\\"));
});
