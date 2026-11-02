#!/usr/bin/env node

/**
 * Runs the repo's Python and Node test suites with coverage and writes the two
 * reports sonar-project.properties points SonarCloud at:
 *
 *   coverage/coverage.xml   Python — coverage.py (Cobertura XML), scope in .coveragerc
 *   coverage/lcov.info      JavaScript — V8 coverage reported by c8
 *
 * Python suites mirror .github/workflows/test-helpers.yml: every `pytest <target>`
 * there runs here as its own invocation, because the suites ship sibling
 * `_shared` packages that cannot be collected in one session. Its individual
 * tests/scripts files are replaced by the whole tests/scripts directory.
 * Node suites are `npm run skills:test` plus the coded-apps dashboard tests.
 *
 * NODE_V8_COVERAGE stays set for the Python suites too, so the node hooks those
 * tests spawn are measured; COVERAGE_FILE / COVERAGE_RCFILE / COVERAGE_ROOT are
 * absolute so Python children started from a temp cwd still measure the repo's
 * sources and report into coverage/.
 *
 * A failing suite does not stop the run: both reports are always written, and
 * the exit code is 1 if any suite failed.
 *
 * Usage:
 *   node scripts/run-coverage.mjs
 *
 * Requires `coverage`, `pytest` and `pyyaml` in the interpreter named by
 * $PYTHON (default: python3, or python on Windows). That interpreter must also
 * be first on PATH — tests spawn bare `python3`, and only an interpreter with
 * coverage installed measures those child processes.
 */

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const OUT = join(ROOT, "coverage");
const V8_DIR = join(OUT, "v8");
const WIN = process.platform === "win32";
const PYTHON = process.env.PYTHON ?? (WIN ? "python" : "python3");
const C8 = "c8@10.1.3";
const DASHBOARD_TESTS = "skills/uipath-coded-apps/assets/scripts/dashboards/tests";

const testEnv = {
  ...process.env,
  PYTHONUTF8: "1",
  COVERAGE_RCFILE: join(ROOT, ".coveragerc"),
  COVERAGE_FILE: join(OUT, ".coverage"),
  COVERAGE_ROOT: ROOT,
  NODE_V8_COVERAGE: V8_DIR,
};
const reportEnv = { ...process.env };
delete reportEnv.NODE_V8_COVERAGE;

const failed = [];

function run(label, cmd, args, env) {
  console.log(`\n▶ ${label}`);
  // npm/npx are .cmd shims on Windows and need a shell; nothing else does.
  const shell = WIN && (cmd === "npm" || cmd === "npx");
  const result = spawnSync(cmd, args, { cwd: ROOT, env, stdio: "inherit", shell });
  if (result.error) console.error(`✗ ${label}: ${result.error.message}`);
  const ok = result.status === 0;
  if (!ok) failed.push(label);
  return ok;
}

function pytestTargets() {
  const workflow = readFileSync(join(ROOT, ".github/workflows/test-helpers.yml"), "utf8");
  const targets = new Set(["tests/scripts"]);
  // `run: pytest …` (with or without a leading `- `), or a `pytest …` line inside a `run: |` block.
  for (const [, args] of workflow.matchAll(/^\s*(?:-\s+)?(?:run:\s*)?pytest\s+(.+)$/gm)) {
    for (const arg of args.trim().split(/\s+/)) {
      if (!arg.startsWith("-") && arg !== "\\" && !arg.startsWith("tests/scripts/")) targets.add(arg);
    }
  }
  if (targets.size < 2) {
    throw new Error("found no `pytest <target>` lines in test-helpers.yml — has the job shape changed?");
  }
  return [...targets];
}

// coverage.py lists each `source` dir from .coveragerc under <sources>, but after
// `combine` the filenames are repo-relative (scripts/x.py). Sonar joins every
// filename to every <source> and drops a file that resolves under none, so the
// report would carry no Python coverage. Point <sources> at the repo root and make
// every filename repo-relative.
function rootCoberturaSources(xmlPath) {
  const xml = readFileSync(xmlPath, "utf8");
  const sources = [...xml.matchAll(/<source>([^<]*)<\/source>/g)].map(([, dir]) => dir).filter(Boolean);
  const unresolved = [];
  const rewritten = xml
    .replace(/filename="([^"]+)"/g, (match, file) => {
      if (existsSync(join(ROOT, file))) return match;
      const dir = sources.find((source) => existsSync(join(source, file)));
      if (!dir) {
        unresolved.push(file);
        return match;
      }
      return `filename="${relative(ROOT, join(dir, file)).split(sep).join("/")}"`;
    })
    .replace(/<sources>[\s\S]*?<\/sources>/, `<sources>\n\t\t<source>${ROOT.split(sep).join("/")}</source>\n\t</sources>`);
  writeFileSync(xmlPath, rewritten);
  if (unresolved.length) {
    console.error(`✗ coverage.xml: ${unresolved.length} file(s) not under the repo root: ${unresolved.join(", ")}`);
    failed.push("coverage.xml paths");
  }
}

rmSync(OUT, { recursive: true, force: true });
mkdirSync(V8_DIR, { recursive: true });

for (const target of pytestTargets()) {
  run(`pytest ${target}`, PYTHON, ["-m", "coverage", "run", "-m", "pytest", target, "-q", "-p", "no:cacheprovider"], testEnv);
}

// No `-s`: npm exports it as npm_config_loglevel=silent, which mutes the
// `npm publish --dry-run` notices compose-skill-flavor.test.mjs asserts on.
run("npm run skills:test", "npm", ["run", "skills:test"], testEnv);
const dashboardTests = readdirSync(join(ROOT, DASHBOARD_TESTS))
  .filter((name) => name.endsWith(".test.mjs"))
  .map((name) => `${DASHBOARD_TESTS}/${name}`);
run("node --test (coded-apps dashboards)", process.execPath, ["--test", ...dashboardTests], testEnv);

// Reports: failures here mean a report is missing, which Sonar would read as 0%.
run("coverage combine", PYTHON, ["-m", "coverage", "combine", "--quiet"], testEnv);
if (run("coverage xml", PYTHON, ["-m", "coverage", "xml", "--quiet", "-o", join(OUT, "coverage.xml")], testEnv)) {
  rootCoberturaSources(join(OUT, "coverage.xml"));
}
run("coverage report", PYTHON, ["-m", "coverage", "report", "--sort=cover"], testEnv);
run(`${C8} report`, "npx", [
  "--yes", C8, "report",
  "--temp-directory", V8_DIR,
  "--reports-dir", OUT,
  "--reporter=lcovonly", "--reporter=text",
  "--all", "--src", ".",
  "--extension", ".mjs", "--extension", ".js", "--extension", ".cjs",
  "--include", "scripts/**", "--include", "hooks/**",
  "--include", ".github/workflows/scripts/**", "--include", "skills/**",
  // --exclude replaces c8's defaults, so node_modules must be listed again.
  "--exclude", "**/node_modules/**",
  "--exclude", "**/tests/**", "--exclude", "**/*.test.mjs",
  "--exclude", "skills/uipath-maestro-flow/examples/**",
], reportEnv);

if (failed.length) {
  console.error(`\n✗ ${failed.length} step(s) failed:\n  - ${failed.join("\n  - ")}`);
  process.exit(1);
}
console.log("\n✓ all suites passed; reports in coverage/");
