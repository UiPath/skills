#!/usr/bin/env node

/**
 * Swap this checkout's canonical `skills/` for one flavor's built tree, so an
 * eval reads exactly the files that flavor's package ships.
 *
 * CI only: it replaces `skills/` in place and does not restore it, so it
 * refuses to run unless CI=true (GitHub Actions sets it; an Azure Pipelines
 * step must set it explicitly). The canonical tree is parked at
 * `build/skills/.canonical` for inspection. `default` changes nothing, so a
 * pipeline can pass its flavor parameter through unconditionally.
 *
 * Usage: node scripts/activate-skill-flavor.mjs <FLAVOR>
 */

import { renameSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { pathToFileURL } from "node:url";

import {
  DEFAULT_VARIANT,
  FLAVORS_DIRNAME,
  FlavorCompositionError,
  REPO_ROOT,
  buildAllSkillTrees,
  discoverFlavorRoots,
} from "./compose-skill-flavor.mjs";

export function activateSkillFlavor(repoRoot, flavor) {
  if (flavor === DEFAULT_VARIANT) return null;
  if (!discoverFlavorRoots(repoRoot).some((root) => path.basename(root) === flavor)) {
    throw new Error(`not a skill flavor under ${FLAVORS_DIRNAME}/: ${JSON.stringify(flavor)}`);
  }
  const { variants, outputRoot } = buildAllSkillTrees(repoRoot);
  const { plan } = variants.find(({ name }) => name === flavor);

  const skills = path.join(repoRoot, "skills");
  const parked = path.join(outputRoot, ".canonical");
  renameSync(skills, parked);
  try {
    renameSync(path.join(outputRoot, flavor), skills);
  } catch (error) {
    renameSync(parked, skills);
    throw error;
  }
  return { skillCount: plan.skills.length, fileCount: plan.files.length };
}

export function main(argv = process.argv.slice(2), { env = process.env, repoRoot = REPO_ROOT } = {}) {
  try {
    if (argv.length !== 1 || !argv[0]) throw new Error("Usage: node scripts/activate-skill-flavor.mjs <FLAVOR>");
    if (env.CI !== "true") throw new Error("refusing to replace skills/ outside CI; set CI=true in the pipeline step");
    const [flavor] = argv;
    const activated = activateSkillFlavor(repoRoot, flavor);
    console.log(
      activated
        ? `Activated ${flavor}: skills/ now holds its ${activated.fileCount} built files for ${activated.skillCount} skills.`
        : "Flavor default: skills/ keeps the canonical tree.",
    );
    return 0;
  } catch (error) {
    const findings = error instanceof FlavorCompositionError ? error.findings : [error.message];
    for (const finding of findings) console.error(`ERROR: ${finding}`);
    return 1;
  }
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  process.exitCode = main();
}
