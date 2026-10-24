import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test, { after } from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SCRIPT = join(REPO_ROOT, "skills", "uipath-activity-migrator", "scripts", "ensure-migrator.mjs");

// ensure-migrator.mjs is a Windows-only flow that shells out to curl, powershell.exe, tar/unzip, reg.exe, dotnet.exe
// and UiPath.Upgrade.exe. To exercise it on any OS without downloading or installing anything, the script runs
// unmodified under a preload that (a) reports platform win32, (b) maps the backslash paths the script builds onto the
// host file system, and (c) replaces child_process.spawnSync with a scripted fake driven by the FAKE_SCENARIO env var.
const PRELOAD = String.raw`
const cp = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const realPlatform = process.platform;
Object.defineProperty(process, 'platform', { value: 'win32' });
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
  if (/reg\.exe$/.test(command)) return result(scn.reg || { status: 1 });
  if (/dotnet\.exe$/.test(command)) return result(scn.runtimes || { stdout: '' });
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

const DOTNET_OK = { stdout: "Microsoft.NETCore.App 8.0.1 [x]\nMicrosoft.WindowsDesktop.App 8.0.7 [C:\\x]\nMicrosoft.WindowsDesktop.App 6.0.1 [y]\n" };
let n = 0;

// Each case gets its own install root and a fake DOTNET_ROOT_X64 holding a dotnet.exe marker file.
function setup({ cached = null, stamp = null, dotnet = true } = {}) {
  const dir = mkdtempSync(join(base, "case-"));
  const root = join(dir, "root");
  mkdirSync(root, { recursive: true });
  if (cached === "root") writeFileSync(join(root, "UiPath.Upgrade.exe"), "exe");
  if (cached === "current") {
    mkdirSync(join(root, "current"), { recursive: true });
    writeFileSync(join(root, "current", "UiPath.Upgrade.exe"), "exe");
  }
  if (stamp !== null) writeFileSync(join(root, ".last-modified"), stamp);
  const dotnetRoot = join(dir, "dotnet");
  mkdirSync(dotnetRoot, { recursive: true });
  if (dotnet) writeFileSync(join(dotnetRoot, "dotnet.exe"), "");
  return { dir, root, dotnetRoot, sysRoot: join(dir, "sys") };
}

function run(ctx, scenario, { args = [], env = {}, useEnvDir = true } = {}) {
  const calls = join(ctx.dir, `calls${n++}.json`);
  const childEnv = {
    ...process.env,
    SystemRoot: ctx.sysRoot,
    DOTNET_ROOT_X64: ctx.dotnetRoot,
    FAKE_SCENARIO: JSON.stringify(scenario),
    FAKE_CALLS: calls,
    UIPATH_ACTIVITY_MIGRATOR_URL: "http://example.invalid/UiPath.Upgrade.Cli.zip",
  };
  delete childEnv.DOTNET_ROOT;
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

test("without the preload the script refuses to run on a non-Windows host", { skip: process.platform === "win32" }, () => {
  const r = spawnSync(process.execPath, [SCRIPT], { encoding: "utf8" });
  assert.equal(r.status, 1);
  const out = JSON.parse(r.stdout.trim());
  assert.equal(out.status, "error");
  assert.equal(out.code, "not-windows");
});

test("a root-level cached tool is verified and reported without any network call", () => {
  const ctx = setup({ cached: "root" });
  const r = run(ctx, { runtimes: DOTNET_OK });
  assert.equal(r.status, 0);
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.version, "25.10.4");
  assert.equal(r.json.runtime, "8.0.7");
  assert.equal(r.json.source, "env");
  assert.equal(fwd(r.json.exe).endsWith("/root/UiPath.Upgrade.exe"), true);
  assert.ok(!r.calls.some((c) => c.startsWith("curl")), "no download for an env-pinned dir");
});

test("a tool under current/ is found", () => {
  const ctx = setup({ cached: "current" });
  const r = run(ctx, { runtimes: DOTNET_OK });
  assert.equal(r.json.status, "ok");
  assert.match(fwd(r.json.exe), /\/root\/current\/UiPath\.Upgrade\.exe$/);
});

test("--check-only with nothing cached exits 3 with status missing", () => {
  const ctx = setup();
  const r = run(ctx, {}, { args: ["--check-only"] });
  assert.equal(r.status, 3);
  assert.equal(r.json.status, "missing");
  assert.match(fwd(r.json.dir), /\/root$/);
  assert.deepEqual(r.calls, []);
});

test("offline mode with nothing cached is an offline-missing error", () => {
  const ctx = setup();
  const r = run(ctx, {}, { env: { UIPATH_ACTIVITY_MIGRATOR_OFFLINE: "1" } });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "offline-missing");
  assert.match(r.json.message, /Manual placement/);
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
  const r = run(ctx, { head: { status: 1 }, psHead: { status: 1 }, runtimes: DOTNET_OK }, { useEnvDir: false, env: { LOCALAPPDATA: local } });
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.source, "cached");
});

test("downloads with curl, extracts with Expand-Archive, stamps Last-Modified and reports downloaded", () => {
  const ctx = setup();
  const r = run(ctx, {
    curl: { ok: true, headers: "HTTP/1.1 301\r\nLast-Modified: old\r\n\r\nHTTP/1.1 200\r\nLast-Modified: Tue, 01 Oct 2025 10:00:00 GMT\r\n" },
    expand: "ok",
    runtimes: DOTNET_OK,
  });
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
  const r = run(ctx, { curl: { ok: true }, expand: "ok", runtimes: DOTNET_OK }, { args: ["--force"] });
  assert.equal(r.json.source, "downloaded");
  assert.ok(!existsSync(join(ctx.root, "current", "stale.txt")));
  assert.equal(existsSync(join(ctx.root, ".last-modified")), false, "no stamp without a Last-Modified header");
});

test("falls back to PowerShell WebClient when curl fails and records its Last-Modified", () => {
  const ctx = setup();
  const r = run(ctx, { curl: {}, psDownload: { ok: true, stdout: " Wed, 02 Oct 2025 GMT " }, expand: "ok", runtimes: DOTNET_OK });
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.source, "downloaded");
  assert.equal(readFileSync(join(ctx.root, ".last-modified"), "utf8"), "Wed, 02 Oct 2025 GMT");
});

test("download failure names both attempts and tells the user how to place the tool manually", () => {
  const ctx = setup();
  const r = run(ctx, { curl: {}, psDownload: {} });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "download-failed");
  assert.match(r.json.message, /curl: 22\)? ?the last line|curl: \(22\) the last line/);
  assert.match(r.json.message, /PowerShell WebClient: proxy said \(407\)/);
  assert.match(r.json.message, /Manual placement/);
  assert.ok(!existsSync(join(ctx.root, "UiPath.Upgrade.Cli.download.zip")));
});

test("download failure reports missing curl and missing PowerShell", () => {
  const ctx = setup();
  const r = run(ctx, { curl: { missing: true }, psDownload: { missing: true } });
  assert.equal(r.json.code, "download-failed");
  assert.match(r.json.message, /curl: not found/);
  assert.match(r.json.message, /PowerShell WebClient: not found/);
});

test("extraction falls back to unzip when PowerShell and tar cannot extract", () => {
  const ctx = setup();
  const r = run(ctx, { curl: { ok: true }, unzip: "ok", runtimes: DOTNET_OK });
  assert.equal(r.json.status, "ok");
  assert.ok(r.calls.some((c) => c.startsWith("unzip")));
});

test("extraction falls back to the system tar.exe when it exists", () => {
  const ctx = setup();
  mkdirSync(join(ctx.sysRoot, "System32"), { recursive: true });
  writeFileSync(join(ctx.sysRoot, "System32", "tar.exe"), "");
  const r = run(ctx, { curl: { ok: true }, tar: "ok", runtimes: DOTNET_OK });
  assert.equal(r.json.status, "ok");
  assert.ok(r.calls.some((c) => c.startsWith("tar.exe")));
  assert.ok(!r.calls.some((c) => c.startsWith("unzip")));
});

test("an archive no tool can extract is an extract-failed error", () => {
  const ctx = setup();
  const r = run(ctx, { curl: { ok: true } });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "extract-failed");
  assert.match(r.json.message, /Could not extract/);
  assert.ok(!existsSync(join(ctx.root, ".extract-tmp")));
});

test("an archive missing the exe or Extensions folder is rejected as an unexpected layout", () => {
  for (const layout of ["no-exe", "no-extensions"]) {
    const ctx = setup();
    const r = run(ctx, { curl: { ok: true }, expand: layout });
    assert.equal(r.json.code, "extract-failed", layout);
    assert.match(r.json.message, /Archive layout unexpected/);
    assert.ok(!existsSync(join(ctx.root, "current")));
  }
});

test("a cached non-env install is updated when the remote Last-Modified differs from the stamp", () => {
  const ctx = setup();
  const local = join(ctx.dir, "local");
  const cacheRoot = join(local, "UiPath", "ActivityMigrator");
  mkdirSync(cacheRoot, { recursive: true });
  writeFileSync(join(cacheRoot, "UiPath.Upgrade.exe"), "exe");
  writeFileSync(join(cacheRoot, ".last-modified"), "\uFEFFold stamp\r\n");
  const r = run(
    ctx,
    { head: { stdout: "HTTP/1.1 200\r\nLast-Modified: new stamp\r\n" }, curl: { ok: true, headers: "Last-Modified: new stamp\r\n" }, expand: "ok", runtimes: DOTNET_OK },
    { useEnvDir: false, env: { LOCALAPPDATA: local } },
  );
  assert.equal(r.json.status, "ok");
  assert.equal(r.json.source, "updated");
  assert.equal(readFileSync(join(cacheRoot, ".last-modified"), "utf8"), "new stamp");
});

test("an unchanged remote Last-Modified (BOM in the stamp ignored) keeps the cached tool", () => {
  const ctx = setup();
  const local = join(ctx.dir, "local");
  const cacheRoot = join(local, "UiPath", "ActivityMigrator");
  mkdirSync(cacheRoot, { recursive: true });
  writeFileSync(join(cacheRoot, "UiPath.Upgrade.exe"), "exe");
  writeFileSync(join(cacheRoot, ".last-modified"), "\uFEFFsame\r\n");
  const r = run(ctx, { head: { stdout: "Last-Modified: same\n" }, runtimes: DOTNET_OK }, { useEnvDir: false, env: { LOCALAPPDATA: local } });
  assert.equal(r.json.source, "cached");
  assert.ok(!r.calls.some((c) => c.startsWith("curl") && c.includes("-o")));
});

test("the HEAD request falls back to PowerShell and a missing stamp is written from it", () => {
  const ctx = setup();
  const local = join(ctx.dir, "local");
  const cacheRoot = join(local, "UiPath", "ActivityMigrator");
  mkdirSync(cacheRoot, { recursive: true });
  writeFileSync(join(cacheRoot, "UiPath.Upgrade.exe"), "exe");
  const r = run(ctx, { head: { status: 1 }, psHead: { stdout: " ps stamp " }, runtimes: DOTNET_OK }, { useEnvDir: false, env: { LOCALAPPDATA: local } });
  assert.equal(r.json.source, "cached");
  assert.equal(readFileSync(join(cacheRoot, ".last-modified"), "utf8"), "ps stamp");
});

test("a missing .NET Desktop Runtime 8 is reported with the install hint", () => {
  const ctx = setup({ cached: "root" });
  const r = run(ctx, { runtimes: { stdout: "Microsoft.WindowsDesktop.App 6.0.1 [x]\nMicrosoft.NETCore.App 8.0.1 [y]\n" } });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "runtime-missing");
  assert.match(r.json.message, /Microsoft\.WindowsDesktop\.App 8\.x not found/);
  assert.match(r.json.message, /while DOTNET_ROOT_X64 is set/);
});

test("without a dotnet.exe at all the runtime is reported missing", () => {
  const ctx = setup({ cached: "root", dotnet: false });
  const r = run(ctx, {});
  assert.equal(r.json.code, "runtime-missing");
});

test("DOTNET_ROOT is honoured when DOTNET_ROOT_X64 is not set", () => {
  const ctx = setup({ cached: "root" });
  const r = run(ctx, { runtimes: { stdout: "none\n" } }, { env: { DOTNET_ROOT: ctx.dotnetRoot, DOTNET_ROOT_X64: "" } });
  assert.equal(r.json.code, "runtime-missing");
  assert.match(r.json.message, /while DOTNET_ROOT is set/);
});

test("with no DOTNET_ROOT the registered install location is used, then Program Files", () => {
  const ctx = setup({ cached: "root" });
  const registered = join(ctx.dir, "registered");
  mkdirSync(registered, { recursive: true });
  writeFileSync(join(registered, "dotnet.exe"), "");
  const reg = { stdout: `    InstallLocation    REG_SZ    ${registered}\r\n` };
  const ok = run(ctx, { reg, runtimes: DOTNET_OK }, { env: { DOTNET_ROOT_X64: "" } });
  assert.equal(ok.json.status, "ok");
  assert.ok(ok.calls.some((c) => c.startsWith("reg.exe")));

  // Windows hands children its own ProgramFiles regardless of the env passed, so only a non-Windows host can
  // prove the Program Files fallback finds no dotnet.exe.
  if (process.platform !== "win32") {
    const missing = run(ctx, { runtimes: DOTNET_OK }, { env: { DOTNET_ROOT_X64: "" } });
    assert.equal(missing.json.code, "runtime-missing");
    assert.match(missing.json.message, /dotnet\.microsoft\.com\/download/);
  }
});

test("a tool that prints nothing fails verification with its stderr", () => {
  const ctx = setup({ cached: "root" });
  const r = run(ctx, { runtimes: DOTNET_OK, version: { status: 134, stderr: "You must install .NET   to run this application" } });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "verify-failed");
  assert.match(r.json.message, /did not print a version \(You must install \.NET to run this application\)/);
  assert.match(r.json.message, /rerun with --force/);
});

test("a tool that exits non-zero without output says so", () => {
  const ctx = setup({ cached: "root" });
  const r = run(ctx, { runtimes: DOTNET_OK, version: { status: 3 } });
  assert.match(r.json.message, /exit code 3, no output/);
});

test("a bool.Parse crash on UIPATH_TELEMETRY_DISABLED=1 is diagnosed and the strict spelling is named", () => {
  const ctx = setup({ cached: "root" });
  const r = run(ctx, { runtimes: DOTNET_OK, strictTelemetry: true }, { env: { UIPATH_TELEMETRY_DISABLED: "1" } });
  assert.equal(r.status, 1);
  assert.equal(r.json.code, "telemetry-flag");
  assert.equal(r.json.env, "UIPATH_TELEMETRY_DISABLED=true");
  assert.match(r.json.message, /never unset the variable/);
});

test("a telemetry value meaning off is retried as false", () => {
  const ctx = setup({ cached: "root" });
  const r = run(ctx, { runtimes: DOTNET_OK, strictTelemetry: true }, { env: { UIPATH_TELEMETRY_DISABLED: "off" } });
  assert.equal(r.json.code, "telemetry-flag");
  assert.equal(r.json.env, "UIPATH_TELEMETRY_DISABLED=false");
});

test("a failing tool with a strict telemetry value is a plain verify failure", () => {
  const ctx = setup({ cached: "root" });
  const r = run(ctx, { runtimes: DOTNET_OK, version: { status: 1, stderr: "boom" } }, { env: { UIPATH_TELEMETRY_DISABLED: "true" } });
  assert.equal(r.json.code, "verify-failed");
});

test("POSIX-style install dirs from Git Bash are normalised to Windows paths", { skip: process.platform !== "win32" }, () => {
  const ctx = setup({ cached: "root" });
  const posix = ctx.root.replace(/^([A-Za-z]):/, (_, d) => "/" + d.toLowerCase()).replace(/\\/g, "/");
  const r = run(ctx, { runtimes: DOTNET_OK }, { env: { UIPATH_ACTIVITY_MIGRATOR_DIR: posix } });
  assert.equal(r.json.status, "ok");
  assert.ok(r.json.exe.includes("\\"));
});
