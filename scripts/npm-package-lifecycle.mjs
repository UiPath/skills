#!/usr/bin/env node

import { existsSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const composerPath = path.join(repoRoot, "scripts", "compose-skill-flavor.mjs");
const action = process.argv[2] ?? process.env.npm_lifecycle_event;
const actions = new Set(["prepare", "restore", "recover"]);

async function main() {
  if (!actions.has(action)) {
    throw new Error(`expected lifecycle action prepare, restore, or recover; got ${JSON.stringify(action)}`);
  }

  if (!existsSync(composerPath)) {
    const sourceIndicators = [
      path.join(repoRoot, ".git"),
      path.join(repoRoot, "skill-flavors"),
      path.join(repoRoot, "build", ".root-pack-transaction"),
    ].filter((candidate) => existsSync(candidate));
    if (sourceIndicators.length) {
      throw new Error(
        `skill package source was detected, but the flavor composer is missing: ${composerPath}`,
      );
    }
    return;
  }

  const composer = await import(pathToFileURL(composerPath).href);
  if (action === "prepare") {
    composer.prepareRootDefaultPackage(repoRoot);
    return;
  }

  composer.restoreRootDefaultPackage(repoRoot);
}

try {
  await main();
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exitCode = 1;
}
