#!/usr/bin/env node
/**
 * Vendor the browser bundle's command surface from a UiPath/cli checkout into
 * assets/uip-browser-commands-snapshot.json, in the shape
 * assets/uip-catalog-snapshot.json uses (`generated_at`, a version stamp,
 * `verbs`).
 *
 * Two inputs from the CLI repo:
 *   - packages/cli-browser/browser-commands.snapshot.json — every command the
 *     stable bundle registers, per tool package.
 *   - packages/<tool>/browser.json `unavailable` — commands the bundle
 *     registers as present but refusing (cli#5399). They are in the snapshot,
 *     so they are written out separately, as full paths, for the check to
 *     subtract.
 *
 * The file is rewritten only when `verbs` or `unavailable` changed, so an
 * unchanged surface leaves no diff and the refresh opens no PR.
 *
 * Usage:
 *   node scripts/build-uip-browser-catalog.mjs --cli-root ../cli [--output PATH]
 */
import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const DEFAULT_OUTPUT = join(REPO_ROOT, "assets", "uip-browser-commands-snapshot.json");

const readJson = (file) => JSON.parse(readFileSync(file, "utf8"));

/**
 * Build `{ verbs, unavailable }` from the snapshot and the tools' browser.json
 * files. `browserJsons` maps a package name to its parsed browser.json.
 * Pure — no I/O — so it is unit-testable without a CLI checkout.
 */
export function browserSurface(snapshot, browserJsons) {
  const stable = snapshot.stable ?? {};
  const verbs = [...new Set(Object.values(stable).flat())].sort();
  const unavailable = {};
  for (const [pkg, manifest] of Object.entries(browserJsons)) {
    const declared = Object.entries(manifest.unavailable ?? {});
    if (declared.length === 0) continue;
    // An `unavailable` key is the path under the tool; the snapshot paths
    // carry the tool's command prefix as their first word.
    const prefix = stable[pkg]?.[0]?.split(" ")[0];
    if (!prefix) throw new Error(`${pkg} declares unavailable commands but the snapshot lists none for it`);
    for (const [path, reason] of declared) {
      const full = `${prefix} ${path}`;
      if (!stable[pkg].includes(full)) {
        throw new Error(`${pkg} declares '${full}' unavailable but the snapshot does not register it`);
      }
      unavailable[full] = reason;
    }
  }
  return {
    verbs,
    unavailable: Object.fromEntries(Object.entries(unavailable).sort(([a], [b]) => a.localeCompare(b))),
  };
}

function readBrowserJsons(cliRoot) {
  const packages = join(cliRoot, "packages");
  const out = {};
  for (const dir of readdirSync(packages)) {
    const browserJson = join(packages, dir, "browser.json");
    if (!existsSync(browserJson)) continue;
    out[readJson(join(packages, dir, "package.json")).name] = readJson(browserJson);
  }
  return out;
}

function main(argv) {
  const arg = (name) => {
    const at = argv.indexOf(name);
    return at === -1 ? undefined : argv[at + 1];
  };
  const cliRoot = arg("--cli-root");
  if (!cliRoot) {
    process.stderr.write("usage: build-uip-browser-catalog.mjs --cli-root <cli checkout> [--output PATH]\n");
    process.exit(2);
  }
  const output = resolve(arg("--output") ?? DEFAULT_OUTPUT);
  const snapshot = readJson(join(cliRoot, "packages", "cli-browser", "browser-commands.snapshot.json"));
  const surface = browserSurface(snapshot, readBrowserJsons(cliRoot));
  if (surface.verbs.length === 0) throw new Error("the browser snapshot lists no commands");

  const previous = existsSync(output) ? readJson(output) : undefined;
  if (
    previous &&
    JSON.stringify(previous.verbs) === JSON.stringify(surface.verbs) &&
    JSON.stringify(previous.unavailable) === JSON.stringify(surface.unavailable)
  ) {
    process.stdout.write(`Browser surface unchanged (${surface.verbs.length} commands).\n`);
    return;
  }

  const cliCommit = execFileSync("git", ["-C", cliRoot, "rev-parse", "HEAD"], { encoding: "utf8" }).trim();
  const data = {
    generated_at: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
    cli_commit: cliCommit,
    verbs: surface.verbs,
    unavailable: surface.unavailable,
  };
  writeFileSync(output, `${JSON.stringify(data, null, 2)}\n`);
  process.stdout.write(
    `Wrote ${output}: ${data.verbs.length} commands, ${Object.keys(data.unavailable).length} unavailable.\n`,
  );
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2));
}
