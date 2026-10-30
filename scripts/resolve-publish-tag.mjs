#!/usr/bin/env node

/**
 * Stamp the npmjs publish version and resolve its dist-tag for one package.
 *
 * Every publish.yml job that publishes to npmjs runs this, so all packages of
 * one run carry the same version and follow the same tag rule:
 *
 *   - `preview` (dispatch channel=preview, or a push to `release/*`): stamps
 *     `<base>-preview.<run_number>` (never committed) and syncs the derived
 *     manifests. Only the highest release line owns the bare `preview` tag;
 *     a lower line publishes to `preview-v<M.N>`. `--tag preview` used to be
 *     unconditional, so whichever line published last took it: on
 *     2026-09-06, run 637 (release/v1.201) landed after run 635
 *     (release/v1.202) and pointed `preview` back at the older line. Fails
 *     open: an unset tag or an unreachable registry keeps `preview`.
 *   - `latest` (dispatch channel=latest): the committed version.
 *
 * Usage: node scripts/resolve-publish-tag.mjs <PACKAGE>
 * Env:   EVENT_NAME, PUBLISH_REF, CHANNEL, RUN_NUMBER; writes `tag=<TAG>` to
 *        $GITHUB_OUTPUT (stdout when unset).
 */

import { spawnSync } from "node:child_process";
import { appendFileSync, readFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const NPMJS_REGISTRY = "https://registry.npmjs.org/";
const RELEASE_RE = /^(\d+)\.(\d+)\.(\d+)$/;

/** The npmjs channel a publish.yml event publishes to; throws for any other event. */
export function resolveChannel({ eventName, ref, channel }) {
  if (channel === "preview") return "preview";
  if (eventName === "push" && ref.startsWith("refs/heads/release/")) return "preview";
  if (eventName === "workflow_dispatch" && channel === "latest") return "latest";
  throw new Error(
    `not an npmjs publish: event ${JSON.stringify(eventName)}, ref ${JSON.stringify(ref)}, ` +
      `channel ${JSON.stringify(channel)}`,
  );
}

function parseRelease(version) {
  const match = RELEASE_RE.exec(version);
  return match ? match.slice(1, 4).map(Number) : null;
}

/** Dist-tag for a `<base>-preview.N` publish, given the version `preview` points at now. */
export function previewTag(base, currentPreview) {
  const ours = parseRelease(base);
  if (!ours) throw new Error(`package.json version is not a plain release: ${JSON.stringify(base)}`);
  const current = parseRelease(String(currentPreview ?? "").split("-")[0]);
  if (!current) return "preview";
  const newer = current.findIndex((part, index) => part !== ours[index]);
  return newer >= 0 && current[newer] > ours[newer] ? `preview-v${ours[0]}.${ours[1]}` : "preview";
}

function runOrThrow(run, command, args) {
  const result = run(command, args);
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} failed: ${(result.stderr || result.stdout || "").trim()}`);
  }
  return result.stdout;
}

function defaultRun(command, args) {
  const executable = command === "npm" && process.platform === "win32" ? "npm.cmd" : command;
  return spawnSync(executable, args, { cwd: REPO_ROOT, encoding: "utf8" });
}

export function main(argv = process.argv.slice(2), { env = process.env, run = defaultRun } = {}) {
  try {
    const [packageName] = argv;
    if (!packageName || argv.length !== 1) {
      throw new Error("Usage: node scripts/resolve-publish-tag.mjs <PACKAGE>");
    }
    const channel = resolveChannel({
      eventName: env.EVENT_NAME ?? "",
      ref: env.PUBLISH_REF ?? "",
      channel: env.CHANNEL ?? "",
    });
    const base = JSON.parse(readFileSync(path.join(REPO_ROOT, "package.json"), "utf8")).version;

    let tag = "latest";
    let version = base;
    let note = "";
    if (channel === "preview") {
      if (!/^\d+$/.test(env.RUN_NUMBER ?? "")) throw new Error("RUN_NUMBER must be the workflow run number");
      version = `${base}-preview.${env.RUN_NUMBER}`;
      runOrThrow(run, "npm", ["version", version, "--no-git-tag-version", "--allow-same-version"]);
      runOrThrow(run, process.execPath, [path.join(REPO_ROOT, "scripts", "sync-version.mjs")]);
      const view = run("npm", ["view", `${packageName}@preview`, "version", `--@uipath:registry=${NPMJS_REGISTRY}`]);
      const current = view.status === 0 ? view.stdout.trim() : "";
      tag = previewTag(base, current);
      note = ` (preview is at ${current || "unset"})`;
    }

    if (env.GITHUB_OUTPUT) appendFileSync(env.GITHUB_OUTPUT, `tag=${tag}\n`);
    else console.log(`tag=${tag}`);
    console.error(`Publishing ${packageName}@${version} to dist-tag ${tag}${note}`);
    return 0;
  } catch (error) {
    console.error(`ERROR: ${error.message}`);
    return 1;
  }
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  process.exitCode = main();
}
