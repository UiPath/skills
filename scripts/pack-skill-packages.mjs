#!/usr/bin/env node

/**
 * Build all standard skill flavor packages and augment the Cowork flavor with
 * upload-ready Microsoft 365 artifacts. The generic composer remains unaware
 * of host transports; this repository-level pack entry point supplies the
 * Cowork transport extension before any tarball is created or installed.
 */

import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { pathToFileURL } from "node:url";
import {
  buildAllSkillTrees,
  packAllVariants,
  readTarballEntries,
  REPO_ROOT,
  treeFileBytes,
} from "./compose-skill-flavor.mjs";

const COWORK_FLAVOR = "cowork";
const COWORK_DIRECTORY = "cowork";
const COWORK_REPORT = "report.json";
const COWORK_GENERATOR = "scripts/export-cowork.py";
const COWORK_FORMAT_VERSION = 1;

function readJson(filePath, label) {
  try {
    return JSON.parse(readFileSync(filePath, "utf8"));
  } catch (error) {
    throw new Error(`${label} is invalid JSON: ${filePath}: ${error.message}`);
  }
}

function mapsOfBuffersEqual(left, right) {
  if (left.size !== right.size) return false;
  for (const [key, value] of left) {
    if (!right.get(key)?.equals(value)) return false;
  }
  return true;
}

export function validateCoworkReport(report, expectedVersion) {
  if (
    !report ||
    typeof report !== "object" ||
    Array.isArray(report) ||
    report.format_version !== COWORK_FORMAT_VERSION ||
    report.generator !== COWORK_GENERATOR ||
    report.source_package_version !== expectedVersion ||
    !Array.isArray(report.skills) ||
    !Array.isArray(report.plugin_packages) ||
    report.skills.length === 0 ||
    report.plugin_packages.length === 0 ||
    report.skill_count !== report.skills.length ||
    report.plugin_package_count !== report.plugin_packages.length
  ) {
    throw new Error(`Cowork report does not match package version ${expectedVersion}`);
  }

  const artifacts = new Set([COWORK_REPORT]);
  const skillNames = new Set();
  for (const skill of report.skills) {
    if (
      typeof skill?.name !== "string" ||
      !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(skill.name) ||
      skillNames.has(skill.name) ||
      skill.archive !== `skills/${skill.name}.skill`
    ) {
      throw new Error("Cowork report contains an invalid skill archive path");
    }
    skillNames.add(skill.name);
    artifacts.add(skill.archive);
  }

  const coveredSkills = new Set();
  for (const [index, plugin] of report.plugin_packages.entries()) {
    const expectedArchive =
      report.plugin_packages.length === 1
        ? "plugins/uipath-skills-cowork.zip"
        : `plugins/uipath-skills-cowork-${String(index + 1).padStart(2, "0")}.zip`;
    if (
      plugin?.archive !== expectedArchive ||
      !Array.isArray(plugin.skills) ||
      plugin.skills.length === 0 ||
      plugin.skills.length > 20
    ) {
      throw new Error("Cowork report contains an invalid plugin archive path");
    }
    for (const skillName of plugin.skills) {
      if (!skillNames.has(skillName) || coveredSkills.has(skillName)) {
        throw new Error("Cowork report plugin shards do not cover each skill exactly once");
      }
      coveredSkills.add(skillName);
    }
    artifacts.add(plugin.archive);
  }
  if (artifacts.size !== 1 + report.skills.length + report.plugin_packages.length) {
    throw new Error("Cowork report contains duplicate artifact paths");
  }
  if (coveredSkills.size !== skillNames.size) {
    throw new Error("Cowork report plugin shards do not cover each skill exactly once");
  }
  return artifacts;
}

export function runCoworkExporter({ repoRoot, skillsDir, outputDir, force = false }) {
  const python =
    process.env.UIP_COWORK_PYTHON || (process.platform === "win32" ? "python" : "python3");
  const args = [
    path.join(repoRoot, "scripts", "export-cowork.py"),
    "--repo-root",
    repoRoot,
    "--skills-root",
    skillsDir,
    "--output",
    outputDir,
  ];
  if (force) args.push("--force");
  const result = spawnSync(python, args, {
    cwd: repoRoot,
    encoding: "utf8",
    env: { ...process.env, PYTHONUTF8: "1" },
  });
  if (result.error?.code === "ENOENT") {
    throw new Error(`Python is required to build the Cowork skill flavor (${python} was not found)`);
  }
  if (result.error) throw result.error;
  if (result.status !== 0) {
    const detail =
      (result.stderr || "").trim() ||
      (result.stdout || "").trim() ||
      (result.signal ? `terminated by ${result.signal}` : `exit status ${result.status}`);
    throw new Error(`Cowork exporter failed: ${detail}`);
  }
  return (result.stdout || "").trim();
}

export function augmentCoworkPackage(item) {
  if (item.variant !== COWORK_FLAVOR) return;
  const outputDir = path.join(item.packageDir, COWORK_DIRECTORY);
  runCoworkExporter({
    repoRoot: item.repoRoot,
    skillsDir: item.skillsDir,
    outputDir,
  });

  const report = readJson(path.join(outputDir, COWORK_REPORT), "Cowork report");
  validateCoworkReport(report, item.version);

  const manifestPath = path.join(item.packageDir, "package.json");
  const manifest = readJson(manifestPath, "Cowork package manifest");
  if (
    manifest.name !== item.packageName ||
    manifest.version !== item.version ||
    manifest.uipathSkillsFlavor !== COWORK_FLAVOR ||
    !Array.isArray(manifest.files)
  ) {
    throw new Error(`Cowork package manifest is incomplete: ${manifestPath}`);
  }
  if (!manifest.files.includes(COWORK_DIRECTORY)) manifest.files.push(COWORK_DIRECTORY);
  manifest.description =
    "UiPath agent skills and upload-ready packages composed for Microsoft 365 Copilot Cowork.";
  manifest.uipathCoworkFormatVersion = COWORK_FORMAT_VERSION;
  writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");

  const readmePath = path.join(item.packageDir, "README.md");
  const readme = readFileSync(readmePath, "utf8");
  writeFileSync(
    readmePath,
    `${readme.trimEnd()}\n\n` +
      "Upload-ready Cowork artifacts are under `cowork/`: individual `.skill` files in " +
      "`cowork/skills/`, Microsoft 365 plugin ZIPs in `cowork/plugins/`, and the exact " +
      "artifact contract in `cowork/report.json`.\n",
    "utf8",
  );
}

export function verifyCoworkPackage(item) {
  if (item.variant !== COWORK_FLAVOR) return;
  const entries = readTarballEntries(item.tarball);
  const manifestBytes = entries.get("package/package.json");
  const reportBytes = entries.get(`package/${COWORK_DIRECTORY}/${COWORK_REPORT}`);
  if (!manifestBytes || !reportBytes) {
    throw new Error(`Cowork tarball is missing its manifest or report: ${item.tarball}`);
  }
  const manifest = JSON.parse(manifestBytes.toString("utf8"));
  if (
    manifest.uipathSkillsFlavor !== COWORK_FLAVOR ||
    manifest.uipathCoworkFormatVersion !== COWORK_FORMAT_VERSION ||
    !Array.isArray(manifest.files) ||
    !manifest.files.includes(COWORK_DIRECTORY)
  ) {
    throw new Error(`Cowork tarball manifest is incomplete: ${item.tarball}`);
  }
  const report = JSON.parse(reportBytes.toString("utf8"));
  const expected = validateCoworkReport(report, item.version);
  const actual = new Map(
    [...entries]
      .filter(([name]) => name.startsWith(`package/${COWORK_DIRECTORY}/`))
      .map(([name, data]) => [name.slice(`package/${COWORK_DIRECTORY}/`.length), data]),
  );
  const staged = treeFileBytes(path.join(item.packageDir, COWORK_DIRECTORY));
  if (!mapsOfBuffersEqual(actual, staged)) {
    throw new Error(`Cowork tarball artifact tree differs from staged package: ${item.tarball}`);
  }
  if (actual.size !== expected.size || [...actual.keys()].some((name) => !expected.has(name))) {
    throw new Error(`Cowork tarball artifact tree differs from report.json: ${item.tarball}`);
  }
}

export function packRepository(repoRoot = REPO_ROOT) {
  return packAllVariants(repoRoot, {
    augmentStagedPackage: augmentCoworkPackage,
    verifyPackedPackage: verifyCoworkPackage,
  });
}

export function buildCoworkExport(repoRoot = REPO_ROOT) {
  repoRoot = path.resolve(repoRoot);
  const { variants, outputRoot } = buildAllSkillTrees(repoRoot);
  if (!variants.some(({ name }) => name === COWORK_FLAVOR)) {
    throw new Error(`The ${COWORK_FLAVOR} skill flavor is not defined`);
  }
  const skillsDir = path.join(outputRoot, COWORK_FLAVOR);
  const outputDir = path.join(repoRoot, "build", COWORK_DIRECTORY);
  const message = runCoworkExporter({ repoRoot, skillsDir, outputDir, force: true });
  const version = readJson(path.join(repoRoot, "package.json"), "root package manifest").version;
  const report = readJson(path.join(outputDir, COWORK_REPORT), "Cowork report");
  validateCoworkReport(report, version);
  return { message, outputDir, report };
}

export function main(argv = process.argv.slice(2)) {
  const command = argv[0] || "pack";
  if (command === "pack") {
    const packages = packRepository(REPO_ROOT);
    console.log(`Built and verified ${packages.length} npm packages:`);
    for (const item of packages) {
      console.log(`  ${item.packageName}@${item.version} [${item.variant}] -> ${item.tarball}`);
    }
    return;
  }
  if (command === "cowork-export") {
    const result = buildCoworkExport(REPO_ROOT);
    console.log(result.message || `Built Cowork export at ${result.outputDir}`);
    return;
  }
  throw new Error(`Unsupported package build command: ${command}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try {
    main();
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
