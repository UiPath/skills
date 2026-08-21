#!/usr/bin/env node

/**
 * Compose complete skill trees and npm packages from sparse flavor blocks.
 *
 * A custom flavor is a direct directory under `skill-flavors/`. It inherits
 * every canonical skill and must contain at least one Markdown override whose
 * path mirrors `skills/<skill>/<file>.md`. Override files contain only complete
 * marker blocks; no allowlist or flavor manifest is used.
 *
 * The no-argument `validate`, `build`, and `pack` commands discover every
 * flavor by convention. Legacy explicit-flavor validate/build invocations are
 * retained for focused debugging. Generated files are marker-free and are
 * swapped into `build/` only after the complete operation succeeds.
 */

import {
  copyFileSync,
  chmodSync,
  existsSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  renameSync,
  rmSync,
  statSync,
  utimesSync,
  writeFileSync,
} from "node:fs";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { gunzipSync } from "node:zlib";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";
import { TextDecoder } from "node:util";

export const REPO_ROOT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);
export const FLAVORS_DIRNAME = "skill-flavors";
export const DEFAULT_VARIANT = "default";
export const PACKAGE_NAME_MAX_LENGTH = 214;
export const ROOT_PACK_TRANSACTION_DIRNAME = ".root-pack-transaction";
export const CUSTOM_PACKAGE_PUBLISH_CONFIG = Object.freeze({
  registry: "https://npm.pkg.github.com/",
  "@uipath:registry": "https://npm.pkg.github.com/",
});

const MARKER_SHAPE_RE = /skill-flavor[ \t]*:/;
const SKILL_NAME_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const MARKER_LINE_RE =
  /^<!--skill-flavor:([a-z0-9]+(?:-[a-z0-9]+)*):(start|end)-->(?:\r\n|\n|\r)?$/;
const UTF8_DECODER = new TextDecoder("utf-8", { fatal: true });
const REMOVE_OPTIONS = { recursive: true, force: true, maxRetries: 3, retryDelay: 100 };
const ROOT_PACK_STATE_SCHEMA = 1;

export class FlavorCompositionError extends Error {
  constructor(findings) {
    super(findings.join("\n"));
    this.name = "FlavorCompositionError";
    this.findings = [...findings];
  }
}

export function containsFlavorMarker(value) {
  const text = Buffer.isBuffer(value) ? value.toString("latin1") : String(value);
  return MARKER_SHAPE_RE.test(text);
}

function quote(value) {
  return JSON.stringify(String(value));
}

function posixRelative(from, to) {
  return path.relative(from, to).split(path.sep).join("/");
}

function splitPosix(value) {
  return value.split("/").filter((part) => part.length > 0);
}

function splitLinesKeepEnds(text) {
  const lines = [];
  let cursor = 0;
  while (cursor < text.length) {
    const start = cursor;
    while (cursor < text.length && text[cursor] !== "\r" && text[cursor] !== "\n") {
      cursor += 1;
    }
    if (cursor < text.length) {
      if (text[cursor] === "\r" && text[cursor + 1] === "\n") {
        cursor += 2;
      } else {
        cursor += 1;
      }
    }
    lines.push(text.slice(start, cursor));
  }
  return lines;
}

function readUtf8(filePath, findings, kind) {
  try {
    return UTF8_DECODER.decode(readFileSync(filePath));
  } catch (error) {
    if (error?.code === "ERR_ENCODING_INVALID_ENCODED_DATA" || error instanceof TypeError) {
      findings.push(`${filePath}: ${kind} must be UTF-8`);
    } else {
      findings.push(`${filePath}: could not read ${kind}: ${error.message}`);
    }
    return null;
  }
}

function safeLstat(filePath) {
  try {
    return lstatSync(filePath);
  } catch (error) {
    if (error?.code === "ENOENT") return null;
    throw error;
  }
}

function compareCodepoints(left, right) {
  if (left < right) return -1;
  if (left > right) return 1;
  return 0;
}

function sortedEntries(directory) {
  return readdirSync(directory, { withFileTypes: true }).sort((left, right) =>
    compareCodepoints(left.name, right.name),
  );
}

function walkTree(root) {
  const entries = [];
  const visit = (directory) => {
    for (const entry of sortedEntries(directory)) {
      const entryPath = path.join(directory, entry.name);
      const stats = lstatSync(entryPath);
      entries.push({ path: entryPath, stats });
      if (stats.isDirectory() && !stats.isSymbolicLink()) visit(entryPath);
    }
  };
  visit(root);
  return entries;
}

export function parseMarkerBlocks(filePath, text, findings = []) {
  const blocks = [];
  const seen = new Set();
  let openedName = null;
  let openedStart = 0;
  let openedLine = 0;
  let offset = 0;

  splitLinesKeepEnds(text).forEach((line, index) => {
    const lineNumber = index + 1;
    const lineStart = offset;
    offset += line.length;
    if (!containsFlavorMarker(line)) return;

    const match = MARKER_LINE_RE.exec(line);
    if (!match) {
      findings.push(
        `${filePath}:${lineNumber}: malformed flavor marker; markers must start at column 1, ` +
          `occupy a line, contain no whitespace, and use ` +
          `'<!--skill-flavor:<name>:start|end-->'`,
      );
      return;
    }

    const [, name, boundary] = match;
    if (boundary === "start") {
      if (openedName !== null) {
        findings.push(
          `${filePath}:${lineNumber}: nested flavor marker ${quote(name)} inside ` +
            `${quote(openedName)} opened on line ${openedLine}`,
        );
        return;
      }
      if (seen.has(name)) {
        findings.push(`${filePath}:${lineNumber}: duplicate flavor block ${quote(name)}`);
        return;
      }
      openedName = name;
      openedStart = lineStart;
      openedLine = lineNumber;
      return;
    }

    if (openedName === null) {
      findings.push(
        `${filePath}:${lineNumber}: flavor marker ${quote(name)} ends without a start`,
      );
      return;
    }
    if (name !== openedName) {
      findings.push(
        `${filePath}:${lineNumber}: flavor marker ${quote(name)} does not match ` +
          `${quote(openedName)} opened on line ${openedLine}`,
      );
      openedName = null;
      return;
    }

    blocks.push({
      name,
      start: openedStart,
      end: offset,
      text: text.slice(openedStart, offset),
    });
    seen.add(name);
    openedName = null;
  });

  if (openedName !== null) {
    findings.push(
      `${filePath}:${openedLine}: flavor block ${quote(openedName)} has no end marker`,
    );
  }
  return blocks;
}

function validateOverrideHasOnlyBlocks(filePath, text, blocks, findings) {
  if (blocks.length === 0) {
    findings.push(`${filePath}: override must contain at least one complete flavor block`);
    return;
  }
  let cursor = 0;
  for (const block of blocks) {
    if (text.slice(cursor, block.start).trim()) {
      findings.push(`${filePath}: override contains stray unmarked content`);
      return;
    }
    cursor = block.end;
  }
  if (text.slice(cursor).trim()) {
    findings.push(`${filePath}: override contains stray unmarked content`);
  }
}

export function composeText(canonicalText, canonicalBlocks, overrideBlocks) {
  const replacements = new Map(overrideBlocks.map((block) => [block.name, block.text]));
  const pieces = [];
  let cursor = 0;
  for (const block of canonicalBlocks) {
    pieces.push(canonicalText.slice(cursor, block.start));
    pieces.push(replacements.get(block.name) ?? block.text);
    cursor = block.end;
  }
  pieces.push(canonicalText.slice(cursor));
  return pieces.join("");
}

export function stripMarkerBoundaries(text) {
  return splitLinesKeepEnds(text)
    .map((line) => (MARKER_LINE_RE.test(line) ? "" : line))
    .join("");
}

function discoverCanonicalSkills(repoRoot, findings) {
  const skillsRoot = path.join(repoRoot, "skills");
  const rootStats = safeLstat(skillsRoot);
  if (!rootStats) return [];
  if (rootStats.isSymbolicLink()) {
    findings.push(`${skillsRoot}: canonical skills root cannot be a symlink`);
    return [];
  }
  if (!rootStats.isDirectory()) return [];

  const skills = [];
  for (const entry of sortedEntries(skillsRoot)) {
    const skillRoot = path.join(skillsRoot, entry.name);
    const stats = lstatSync(skillRoot);
    if (stats.isSymbolicLink()) {
      findings.push(`${skillRoot}: canonical skill trees cannot contain symlinks`);
      continue;
    }
    if (!stats.isDirectory()) continue;
    const entrypoint = path.join(skillRoot, "SKILL.md");
    const entrypointStats = safeLstat(entrypoint);
    if (entrypointStats?.isSymbolicLink()) {
      findings.push(`${entrypoint}: canonical skill trees cannot contain symlinks`);
      continue;
    }
    if (entrypointStats?.isFile()) skills.push(entry.name);
  }
  return skills;
}

function collectCanonicalFiles(repoRoot, skills, findings) {
  const canonicalFiles = new Map();
  const canonicalText = new Map();
  const canonicalBlocks = new Map();

  for (const skill of skills) {
    const skillRoot = path.join(repoRoot, "skills", skill);
    for (const entry of walkTree(skillRoot)) {
      if (entry.stats.isSymbolicLink()) {
        findings.push(`${entry.path}: canonical skill trees cannot contain symlinks`);
        continue;
      }
      if (!entry.stats.isFile()) continue;
      const relative = posixRelative(repoRoot, entry.path);
      canonicalFiles.set(relative, entry.path);
      if (path.extname(entry.path).toLowerCase() !== ".md") continue;
      const text = readUtf8(entry.path, findings, "canonical Markdown");
      if (text === null) continue;
      canonicalText.set(relative, text);
      canonicalBlocks.set(relative, parseMarkerBlocks(entry.path, text, findings));
    }
  }
  return { canonicalFiles, canonicalText, canonicalBlocks };
}

function plannedFiles(canonicalFiles, canonicalText, replacements = new Map()) {
  const files = [];
  for (const relative of [...canonicalFiles.keys()].sort()) {
    const sourcePath = canonicalFiles.get(relative);
    let composedBytes = null;
    const text = replacements.has(relative)
      ? replacements.get(relative)
      : canonicalText.get(relative);
    if (text !== undefined) {
      const finalBytes = Buffer.from(stripMarkerBoundaries(text), "utf8");
      const sourceBytes = readFileSync(sourcePath);
      if (!finalBytes.equals(sourceBytes)) composedBytes = finalBytes;
    }
    const relativePath = relative.startsWith("skills/")
      ? relative.slice("skills/".length)
      : relative;
    files.push({ relativePath, sourcePath, composedBytes });
  }
  return files;
}

export function createDefaultPlan(repoRoot = REPO_ROOT) {
  repoRoot = path.resolve(repoRoot);
  const findings = [];
  const skills = discoverCanonicalSkills(repoRoot, findings);
  if (skills.length === 0) findings.push(`${path.join(repoRoot, "skills")}: no canonical skills found`);
  const { canonicalFiles, canonicalText } = collectCanonicalFiles(
    repoRoot,
    skills,
    findings,
  );
  if (findings.length) throw new FlavorCompositionError(findings);
  return {
    flavorRoot: null,
    skills,
    files: plannedFiles(canonicalFiles, canonicalText),
    overriddenFiles: [],
    replacementCount: 0,
  };
}

function validateFlavorName(flavorRoot, findings) {
  const name = path.basename(flavorRoot);
  if (!SKILL_NAME_RE.test(name)) {
    findings.push(
      `${flavorRoot}: invalid flavor name ${quote(name)}; use a lowercase kebab-case directory name`,
    );
  } else if (name === DEFAULT_VARIANT) {
    findings.push(`${flavorRoot}: ${quote(DEFAULT_VARIANT)} is reserved for the canonical package`);
  }
}

export function createCompositionPlan(repoRoot = REPO_ROOT, flavorRoot) {
  repoRoot = path.resolve(repoRoot);
  if (!flavorRoot) throw new TypeError("flavorRoot is required");
  flavorRoot = path.resolve(flavorRoot);
  const findings = [];
  const flavorStats = safeLstat(flavorRoot);
  if (!flavorStats) {
    throw new FlavorCompositionError([`flavor directory does not exist: ${flavorRoot}`]);
  }
  if (flavorStats.isSymbolicLink()) {
    throw new FlavorCompositionError([`${flavorRoot}: flavor directory cannot be a symlink`]);
  }
  if (!flavorStats.isDirectory()) {
    throw new FlavorCompositionError([`flavor directory does not exist: ${flavorRoot}`]);
  }
  validateFlavorName(flavorRoot, findings);

  const skills = discoverCanonicalSkills(repoRoot, findings);
  if (skills.length === 0) findings.push(`${path.join(repoRoot, "skills")}: no canonical skills found`);
  const { canonicalFiles, canonicalText, canonicalBlocks } = collectCanonicalFiles(
    repoRoot,
    skills,
    findings,
  );

  const replacements = new Map();
  let replacementCount = 0;
  let overrideFileCount = 0;
  for (const entry of walkTree(flavorRoot)) {
    if (entry.stats.isDirectory()) continue;
    if (entry.stats.isSymbolicLink()) {
      findings.push(`${entry.path}: flavor directories cannot contain symlinks`);
      continue;
    }
    if (!entry.stats.isFile()) {
      findings.push(`${entry.path}: flavor directories may contain only directories and Markdown files`);
      continue;
    }

    const relative = posixRelative(flavorRoot, entry.path);
    const parts = splitPosix(relative);
    if (parts.length < 2) {
      findings.push(`${entry.path}: override path must mirror <skill>/<file>.md`);
      continue;
    }
    if (path.extname(entry.path).toLowerCase() !== ".md") {
      findings.push(`${entry.path}: only Markdown files may contain flavor blocks`);
      continue;
    }
    overrideFileCount += 1;

    const skill = parts[0];
    if (!skills.includes(skill)) {
      findings.push(`${entry.path}: override belongs to unknown canonical skill ${quote(skill)}`);
      continue;
    }
    const logical = `skills/${relative}`;
    if (!canonicalFiles.has(logical)) {
      findings.push(`${entry.path}: canonical target does not exist: ${logical}`);
      continue;
    }

    const overrideText = readUtf8(entry.path, findings, "flavor override");
    if (overrideText === null) continue;
    const parsedOverride = parseMarkerBlocks(entry.path, overrideText, findings);
    validateOverrideHasOnlyBlocks(entry.path, overrideText, parsedOverride, findings);

    const available = new Set((canonicalBlocks.get(logical) ?? []).map((block) => block.name));
    for (const block of parsedOverride) {
      if (!available.has(block.name)) {
        findings.push(
          `${entry.path}: flavor block ${quote(block.name)} has no matching canonical marker in ${logical}`,
        );
      }
    }

    if (parsedOverride.length && parsedOverride.every((block) => available.has(block.name))) {
      const sourceText = canonicalText.get(logical);
      if (sourceText !== undefined) {
        replacements.set(
          logical,
          composeText(sourceText, canonicalBlocks.get(logical), parsedOverride),
        );
        replacementCount += parsedOverride.length;
      }
    }
  }

  if (overrideFileCount === 0) {
    findings.push(`${flavorRoot}: flavor must contain at least one Markdown override file`);
  }
  if (findings.length) throw new FlavorCompositionError([...new Set(findings)]);

  return {
    flavorRoot,
    skills,
    files: plannedFiles(canonicalFiles, canonicalText, replacements),
    overriddenFiles: [...replacements.keys()]
      .sort()
      .map((relative) => relative.slice("skills/".length)),
    replacementCount,
  };
}

export function discoverFlavorRoots(repoRoot = REPO_ROOT) {
  repoRoot = path.resolve(repoRoot);
  const flavorsRoot = path.join(repoRoot, FLAVORS_DIRNAME);
  const rootStats = safeLstat(flavorsRoot);
  if (!rootStats) return [];
  if (rootStats.isSymbolicLink()) {
    throw new FlavorCompositionError([`${flavorsRoot}: flavor root cannot be a symlink`]);
  }
  if (!rootStats.isDirectory()) {
    throw new FlavorCompositionError([`${flavorsRoot}: flavor root is not a directory`]);
  }

  const findings = [];
  const roots = [];
  for (const entry of sortedEntries(flavorsRoot)) {
    const entryPath = path.join(flavorsRoot, entry.name);
    const stats = lstatSync(entryPath);
    if (stats.isSymbolicLink()) {
      findings.push(`${entryPath}: flavor entries cannot be symlinks`);
      continue;
    }
    if (!stats.isDirectory()) continue;
    validateFlavorName(entryPath, findings);
    roots.push(entryPath);
  }
  if (findings.length) throw new FlavorCompositionError(findings);
  return roots;
}

export function createAllVariants(repoRoot = REPO_ROOT) {
  repoRoot = path.resolve(repoRoot);
  const findings = [];
  const variants = [];
  try {
    variants.push({ name: DEFAULT_VARIANT, plan: createDefaultPlan(repoRoot) });
  } catch (error) {
    if (error instanceof FlavorCompositionError) findings.push(...error.findings);
    else throw error;
  }

  let roots = [];
  try {
    roots = discoverFlavorRoots(repoRoot);
  } catch (error) {
    if (error instanceof FlavorCompositionError) findings.push(...error.findings);
    else throw error;
  }
  for (const flavorRoot of roots) {
    try {
      variants.push({ name: path.basename(flavorRoot), plan: createCompositionPlan(repoRoot, flavorRoot) });
    } catch (error) {
      if (error instanceof FlavorCompositionError) findings.push(...error.findings);
      else throw error;
    }
  }
  if (findings.length) throw new FlavorCompositionError([...new Set(findings)]);
  return variants;
}

function validateOutputDirectory(outputDir) {
  outputDir = path.resolve(outputDir);
  const stats = safeLstat(outputDir);
  if (stats?.isSymbolicLink()) throw new Error(`composition output cannot be a symlink: ${outputDir}`);
  if (stats && !stats.isDirectory()) throw new Error(`composition output is not a directory: ${outputDir}`);
  if (stats && readdirSync(outputDir).length > 0) {
    throw new Error(`composition output must be empty: ${outputDir}`);
  }
  return outputDir;
}

function copyFilePreservingTimes(source, destination) {
  copyFileSync(source, destination);
  const stats = statSync(source);
  chmodSync(destination, stats.mode);
  utimesSync(destination, stats.atime, stats.mtime);
}

export function materializeComposition(plan, outputDir) {
  outputDir = validateOutputDirectory(outputDir);
  for (const item of plan.files) {
    const destination = path.join(outputDir, ...splitPosix(item.relativePath));
    mkdirSync(path.dirname(destination), { recursive: true });
    if (item.composedBytes === null) copyFilePreservingTimes(item.sourcePath, destination);
    else {
      writeFileSync(destination, item.composedBytes);
      chmodSync(destination, statSync(item.sourcePath).mode);
    }
  }
}

function prepareBuildRoot(repoRoot) {
  const buildRoot = path.join(path.resolve(repoRoot), "build");
  const stats = safeLstat(buildRoot);
  if (stats?.isSymbolicLink()) throw new Error(`generated build root cannot be a symlink: ${buildRoot}`);
  if (stats && !stats.isDirectory()) throw new Error(`generated build root is not a directory: ${buildRoot}`);
  mkdirSync(buildRoot, { recursive: true });
  return buildRoot;
}

function materializeVariants(variants, outputRoot) {
  mkdirSync(outputRoot, { recursive: false });
  for (const variant of variants) {
    materializeComposition(variant.plan, path.join(outputRoot, variant.name));
  }
}

function markerFindings(root, label) {
  const findings = [];
  for (const entry of walkTree(root)) {
    if (entry.stats.isSymbolicLink()) {
      findings.push(`${entry.path}: ${label} cannot contain symlinks`);
      continue;
    }
    if (entry.stats.isFile() && containsFlavorMarker(readFileSync(entry.path))) {
      findings.push(`${entry.path}: flavor marker leaked into ${label}`);
    }
  }
  return findings;
}

function removeGeneratedPath(target) {
  const stats = safeLstat(target);
  if (!stats) return;
  if (stats.isSymbolicLink()) throw new Error(`refusing to remove generated symlink: ${target}`);
  rmSync(target, { recursive: true, force: false, maxRetries: 3, retryDelay: 100 });
}

function replaceGeneratedDirectories(replacements) {
  if (!replacements.length) return;
  const parents = new Set(replacements.map(([, target]) => path.resolve(path.dirname(target))));
  if (parents.size !== 1) throw new Error("generated outputs must share one build directory");
  const parent = [...parents][0];
  const targets = new Set();
  for (const [source, targetInput] of replacements) {
    const sourceStats = safeLstat(source);
    if (!sourceStats?.isDirectory() || sourceStats.isSymbolicLink()) {
      throw new Error(`generated source is not a real directory: ${source}`);
    }
    const target = path.resolve(targetInput);
    if (targets.has(target)) throw new Error(`duplicate generated output target: ${target}`);
    targets.add(target);
    const targetStats = safeLstat(target);
    if (targetStats?.isSymbolicLink()) throw new Error(`generated output cannot replace a symlink: ${target}`);
    if (targetStats && !targetStats.isDirectory()) throw new Error(`generated output is not a directory: ${target}`);
  }

  const backupRoot = mkdtempSync(path.join(parent, ".skill-flavor-backup-"));
  const backedUp = [];
  const installed = [];
  try {
    for (const [, targetInput] of replacements) {
      const target = path.resolve(targetInput);
      if (!existsSync(target)) continue;
      const backup = path.join(backupRoot, path.basename(target));
      renameSync(target, backup);
      backedUp.push([target, backup]);
    }
    for (const [source, targetInput] of replacements) {
      const target = path.resolve(targetInput);
      renameSync(source, target);
      installed.push(target);
    }
  } catch (error) {
    for (const target of installed.reverse()) removeGeneratedPath(target);
    for (const [target, backup] of backedUp.reverse()) {
      if (existsSync(backup)) renameSync(backup, target);
    }
    throw error;
  } finally {
    rmSync(backupRoot, REMOVE_OPTIONS);
  }
}

export function buildAllSkillTrees(repoRoot = REPO_ROOT) {
  repoRoot = path.resolve(repoRoot);
  const variants = createAllVariants(repoRoot);
  const buildRoot = prepareBuildRoot(repoRoot);
  const temporaryRoot = mkdtempSync(path.join(buildRoot, ".skill-flavor-build-"));
  const temporarySkills = path.join(temporaryRoot, "skills");
  try {
    materializeVariants(variants, temporarySkills);
    const findings = markerFindings(temporarySkills, "built skill tree");
    if (findings.length) throw new FlavorCompositionError(findings);
    const finalSkills = path.join(buildRoot, "skills");
    replaceGeneratedDirectories([[temporarySkills, finalSkills]]);
    return { variants, outputRoot: finalSkills };
  } finally {
    rmSync(temporaryRoot, REMOVE_OPTIONS);
  }
}

function loadPackageManifest(repoRoot) {
  const manifestPath = path.join(repoRoot, "package.json");
  let manifest;
  try {
    manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  } catch (error) {
    if (error?.code === "ENOENT") throw new Error(`npm package manifest is missing: ${manifestPath}`);
    throw new Error(`npm package manifest is invalid JSON: ${manifestPath}: ${error.message}`);
  }
  if (!manifest || typeof manifest !== "object" || Array.isArray(manifest)) {
    throw new Error(`npm package manifest must be an object: ${manifestPath}`);
  }
  for (const key of ["name", "version"]) {
    if (typeof manifest[key] !== "string" || !manifest[key]) {
      throw new Error(`npm package manifest requires a non-empty ${quote(key)}: ${manifestPath}`);
    }
  }
  if (!Array.isArray(manifest.files) || !manifest.files.every((entry) => typeof entry === "string" && entry)) {
    throw new Error(`npm package manifest requires a string 'files' list: ${manifestPath}`);
  }
  return manifest;
}

export function packageName(baseName, variant) {
  if (variant === DEFAULT_VARIANT) return baseName;
  let result;
  if (baseName.startsWith("@")) {
    const separator = baseName.indexOf("/");
    if (separator < 0) throw new Error(`invalid scoped npm package name: ${quote(baseName)}`);
    result = `${baseName.slice(0, separator)}/${baseName.slice(separator + 1)}-${variant}`;
  } else {
    result = `${baseName}-${variant}`;
  }
  if (result.length > PACKAGE_NAME_MAX_LENGTH) {
    throw new Error(`derived npm package name is too long (${result.length} characters): ${result}`);
  }
  return result;
}

function checkedPayloadPath(repoRoot, entry) {
  const parts = entry.split("/");
  if (
    path.posix.isAbsolute(entry) ||
    parts.includes("..") ||
    /[*?\[\]\\]/.test(entry)
  ) {
    throw new Error(`unsupported npm package 'files' entry: ${quote(entry)}`);
  }
  return { source: path.join(repoRoot, ...parts), relative: parts };
}

function assertTreeHasNoSymlinks(root, label) {
  const stats = safeLstat(root);
  if (stats?.isSymbolicLink()) throw new Error(`${label} cannot be a symlink: ${root}`);
  if (stats?.isDirectory()) {
    for (const entry of walkTree(root)) {
      if (entry.stats.isSymbolicLink()) throw new Error(`${label} cannot contain symlinks: ${entry.path}`);
    }
  }
}

function copyPayload(source, destination, label) {
  assertTreeHasNoSymlinks(source, label);
  const stats = safeLstat(source);
  if (!stats) throw new Error(`${label} is neither a file nor directory: ${source}`);
  if (stats.isFile()) {
    mkdirSync(path.dirname(destination), { recursive: true });
    copyFilePreservingTimes(source, destination);
    return;
  }
  if (!stats.isDirectory()) throw new Error(`${label} is neither a file nor directory: ${source}`);
  mkdirSync(destination, { recursive: false });
  chmodSync(destination, stats.mode);
  for (const entry of walkTree(source)) {
    const relative = path.relative(source, entry.path);
    const target = path.join(destination, relative);
    if (entry.stats.isDirectory()) {
      mkdirSync(target, { recursive: true });
      chmodSync(target, entry.stats.mode);
    }
    else if (entry.stats.isFile()) {
      mkdirSync(path.dirname(target), { recursive: true });
      copyFilePreservingTimes(entry.path, target);
    }
  }
}

function generatedPackageManifest(sourceManifest, variant, customFiles) {
  const manifest = JSON.parse(JSON.stringify(sourceManifest));
  manifest.name = packageName(sourceManifest.name, variant);
  manifest.uipathSkillsFlavor = variant;
  if (variant !== DEFAULT_VARIANT) {
    delete manifest.scripts;
    delete manifest.repository;
    manifest.publishConfig = { ...CUSTOM_PACKAGE_PUBLISH_CONFIG };
    manifest.description = `UiPath agent skills composed for the ${variant} host environment.`;
    const keywords = Array.isArray(sourceManifest.keywords)
      ? sourceManifest.keywords.filter((item) => typeof item === "string")
      : [];
    for (const keyword of ["skill-flavor", variant]) {
      if (!keywords.includes(keyword)) keywords.push(keyword);
    }
    manifest.keywords = keywords;
    manifest.files = customFiles;
  }
  return manifest;
}

function customPackageReadme(name, variant) {
  return (
    `# ${name}\n\n` +
    `This package is the generated **${variant}** flavor of ` +
    `[UiPath skills](https://github.com/UiPath/skills).\n\n` +
    `It contains the complete, marker-free canonical skill catalog with the sparse ` +
    `\`${variant}\` overrides applied. Consumers should copy the files under ` +
    "`skills/` directly; no runtime composition is required.\n\n" +
    "This package is generated from the canonical repository. Do not edit its contents directly.\n"
  );
}

function stagePackages(repoRoot, variants, skillTreesRoot, packagesRoot) {
  const sourceManifest = loadPackageManifest(repoRoot);
  const baseName = sourceManifest.name;
  const version = sourceManifest.version;
  for (const variant of variants) packageName(baseName, variant.name);
  const checkedPayload = sourceManifest.files.map((entry) => ({
    entry,
    ...checkedPayloadPath(repoRoot, entry),
  }));

  mkdirSync(packagesRoot, { recursive: false });
  const staged = new Map();
  for (const variant of variants) {
    const packageDir = path.join(packagesRoot, variant.name);
    mkdirSync(packageDir);
    const builtSkills = path.join(skillTreesRoot, variant.name);
    const builtStats = safeLstat(builtSkills);
    if (!builtStats?.isDirectory() || builtStats.isSymbolicLink()) {
      throw new Error(`complete built skill tree is missing for ${variant.name}: ${builtSkills}`);
    }

    let customFiles = [];
    if (variant.name === DEFAULT_VARIANT) {
      for (const item of checkedPayload) {
        if (item.entry.replace(/\/$/, "") === "skills") continue;
        if (!existsSync(item.source)) continue;
        copyPayload(item.source, path.join(packageDir, ...item.relative), "default package payload");
      }
    } else {
      customFiles = ["skills", "README.md", "LICENSE"];
      const licensePath = path.join(repoRoot, "LICENSE");
      if (!safeLstat(licensePath)?.isFile()) throw new Error(`custom packages require a LICENSE file: ${licensePath}`);
      copyPayload(licensePath, path.join(packageDir, "LICENSE"), "package license");
      const versionManifest = path.join(repoRoot, "version-manifest.json");
      if (safeLstat(versionManifest)?.isFile()) {
        copyPayload(versionManifest, path.join(packageDir, "version-manifest.json"), "package version manifest");
        customFiles.push("version-manifest.json");
      }
    }

    copyPayload(builtSkills, path.join(packageDir, "skills"), "built skill tree");
    const name = packageName(baseName, variant.name);
    if (variant.name !== DEFAULT_VARIANT) {
      writeFileSync(path.join(packageDir, "README.md"), customPackageReadme(name, variant.name), "utf8");
    }
    const manifest = generatedPackageManifest(sourceManifest, variant.name, customFiles);
    writeFileSync(path.join(packageDir, "package.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
    staged.set(variant.name, { packageName: name, version, packageDir });
  }
  const findings = markerFindings(packagesRoot, "staged npm package");
  if (findings.length) throw new FlavorCompositionError(findings);
  return staged;
}

function readTarString(buffer, start, length) {
  const field = buffer.subarray(start, start + length);
  const nul = field.indexOf(0);
  return field.subarray(0, nul < 0 ? field.length : nul).toString("utf8");
}

function readTarNumber(buffer, start, length) {
  const field = buffer.subarray(start, start + length);
  if (field[0] & 0x80) {
    let value = BigInt(field[0] & 0x7f);
    for (const byte of field.subarray(1)) value = (value << 8n) | BigInt(byte);
    if (value > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error("tar member is too large to verify safely");
    return Number(value);
  }
  const text = field.toString("ascii").replace(/\0.*$/, "").trim();
  if (!text) return 0;
  const value = Number.parseInt(text, 8);
  if (!Number.isFinite(value)) throw new Error(`invalid tar numeric field: ${quote(text)}`);
  return value;
}

function verifyTarChecksum(header) {
  const expected = readTarNumber(header, 148, 8);
  let actual = 0;
  for (let index = 0; index < header.length; index += 1) {
    actual += index >= 148 && index < 156 ? 32 : header[index];
  }
  if (actual !== expected) throw new Error(`invalid tar header checksum: expected ${expected}, got ${actual}`);
}

function parsePax(payload) {
  const values = {};
  let cursor = 0;
  while (cursor < payload.length) {
    const space = payload.indexOf(32, cursor);
    if (space < 0) throw new Error("invalid PAX record length");
    const length = Number.parseInt(payload.subarray(cursor, space).toString("ascii"), 10);
    if (!Number.isInteger(length) || length <= 0 || cursor + length > payload.length) {
      throw new Error("invalid PAX record boundary");
    }
    const record = payload.subarray(space + 1, cursor + length - 1).toString("utf8");
    const equals = record.indexOf("=");
    if (equals >= 0) values[record.slice(0, equals)] = record.slice(equals + 1);
    cursor += length;
  }
  return values;
}

export function readTarballEntries(tarball) {
  const archive = gunzipSync(readFileSync(tarball));
  const entries = new Map();
  let cursor = 0;
  let nextPax = {};
  let globalPax = {};
  let nextLongName = null;
  while (cursor + 512 <= archive.length) {
    const header = archive.subarray(cursor, cursor + 512);
    cursor += 512;
    if (header.every((byte) => byte === 0)) break;
    verifyTarChecksum(header);
    const size = readTarNumber(header, 124, 12);
    if (cursor + size > archive.length) throw new Error(`truncated tar member in ${tarball}`);
    const payload = archive.subarray(cursor, cursor + size);
    cursor += Math.ceil(size / 512) * 512;
    const type = String.fromCharCode(header[156] || 48);
    let name = readTarString(header, 0, 100);
    const prefix = readTarString(header, 345, 155);
    if (prefix) name = `${prefix}/${name}`;

    if (type === "x") {
      nextPax = parsePax(payload);
      continue;
    }
    if (type === "g") {
      globalPax = { ...globalPax, ...parsePax(payload) };
      continue;
    }
    if (type === "L") {
      nextLongName = payload.subarray(0, payload.indexOf(0) < 0 ? payload.length : payload.indexOf(0)).toString("utf8");
      continue;
    }
    name = nextPax.path ?? globalPax.path ?? nextLongName ?? name;
    nextPax = {};
    nextLongName = null;
    if (path.posix.isAbsolute(name) || name.split("/").includes("..") || name.includes("\\")) {
      throw new Error(`unsafe path in npm tarball: ${name}`);
    }
    if (type === "1" || type === "2") throw new Error(`link found in npm tarball: ${name}`);
    if (type !== "0") continue;
    if (entries.has(name)) throw new Error(`duplicate file in npm tarball: ${name}`);
    entries.set(name, Buffer.from(payload));
  }
  return entries;
}

export function treeFileBytes(root) {
  const files = new Map();
  for (const entry of walkTree(root)) {
    if (entry.stats.isFile() && !entry.stats.isSymbolicLink()) {
      files.set(posixRelative(root, entry.path), readFileSync(entry.path));
    }
  }
  return files;
}

export function treeFingerprint(root) {
  root = path.resolve(root);
  const rootStats = safeLstat(root);
  if (!rootStats?.isDirectory() || rootStats.isSymbolicLink()) {
    throw new Error(`cannot fingerprint a non-directory or symlink: ${root}`);
  }

  const hash = createHash("sha256");
  for (const entry of walkTree(root)) {
    const relative = posixRelative(root, entry.path);
    if (entry.stats.isSymbolicLink()) {
      throw new Error(`cannot fingerprint a tree containing symlinks: ${entry.path}`);
    }
    const type = entry.stats.isDirectory() ? "directory" : entry.stats.isFile() ? "file" : "other";
    if (type === "other") throw new Error(`cannot fingerprint unsupported entry: ${entry.path}`);
    hash.update(type);
    hash.update("\0");
    hash.update(relative);
    hash.update("\0");
    hash.update(String(entry.stats.mode & 0o777));
    hash.update("\0");
    if (entry.stats.isFile()) {
      const bytes = readFileSync(entry.path);
      hash.update(String(bytes.length));
      hash.update("\0");
      hash.update(bytes);
      hash.update("\0");
    }
  }
  return hash.digest("hex");
}

function rootPackTransactionPaths(repoRoot) {
  const buildRoot = path.join(repoRoot, "build");
  const transactionRoot = path.join(buildRoot, ROOT_PACK_TRANSACTION_DIRNAME);
  return {
    buildRoot,
    transactionRoot,
    stateFile: path.join(transactionRoot, "state.json"),
    sourceSkills: path.join(transactionRoot, "source-skills"),
    generatedSkills: path.join(transactionRoot, "generated-skills"),
    packedSkills: path.join(transactionRoot, "packed-skills"),
    rootSkills: path.join(repoRoot, "skills"),
  };
}

function rootPackRecoveryHint() {
  return "Run 'npm run skills:recover' after confirming no other npm pack or publish is active.";
}

function loadRootPackState(paths) {
  const transactionStats = safeLstat(paths.transactionRoot);
  if (!transactionStats) return null;
  if (transactionStats.isSymbolicLink() || !transactionStats.isDirectory()) {
    throw new Error(`root package transaction is not a real directory: ${paths.transactionRoot}`);
  }

  let state;
  try {
    state = JSON.parse(readFileSync(paths.stateFile, "utf8"));
  } catch (error) {
    throw new Error(`root package transaction state is invalid: ${paths.stateFile}: ${error.message}`);
  }
  if (
    state?.schema !== ROOT_PACK_STATE_SCHEMA ||
    state.repoRoot !== path.resolve(path.dirname(paths.buildRoot)) ||
    typeof state.sourceFingerprint !== "string" ||
    typeof state.generatedFingerprint !== "string"
  ) {
    throw new Error(`root package transaction state has an unsupported format: ${paths.stateFile}`);
  }
  return state;
}

function preserveUnexpectedTree(paths, source, label, recovery) {
  if (!recovery.root) {
    recovery.root = mkdtempSync(path.join(paths.buildRoot, ".root-pack-recovery-"));
  }
  let destination = path.join(recovery.root, label);
  let suffix = 1;
  while (existsSync(destination)) {
    destination = path.join(recovery.root, `${label}-${suffix}`);
    suffix += 1;
  }
  renameSync(source, destination);
  recovery.paths.push(destination);
  return destination;
}

function cleanupTransactionTree(paths, candidate, expectedFingerprint, label, recovery) {
  const stats = safeLstat(candidate);
  if (!stats) return;
  let fingerprint = null;
  if (stats.isDirectory() && !stats.isSymbolicLink()) {
    try {
      fingerprint = treeFingerprint(candidate);
    } catch {
      fingerprint = null;
    }
  }
  if (fingerprint === expectedFingerprint) {
    rmSync(candidate, REMOVE_OPTIONS);
  } else {
    preserveUnexpectedTree(paths, candidate, label, recovery);
  }
}

function finishRecoveryRecord(recovery) {
  if (!recovery.root) return;
  writeFileSync(
    path.join(recovery.root, "RECOVERY.txt"),
    "Unexpected files found during root npm package restoration were preserved here.\n",
    "utf8",
  );
}

export function restoreRootDefaultPackage(repoRoot = REPO_ROOT) {
  repoRoot = path.resolve(repoRoot);
  const paths = rootPackTransactionPaths(repoRoot);
  const state = loadRootPackState(paths);
  if (!state) return { restored: false, recoveryRoot: null };

  const recovery = { root: null, paths: [] };
  const sourceStats = safeLstat(paths.sourceSkills);
  const rootStats = safeLstat(paths.rootSkills);

  if (sourceStats) {
    if (sourceStats.isSymbolicLink() || !sourceStats.isDirectory()) {
      throw new Error(`canonical skills backup is not a real directory: ${paths.sourceSkills}`);
    }
    const sourceFingerprint = treeFingerprint(paths.sourceSkills);
    if (sourceFingerprint !== state.sourceFingerprint) {
      throw new Error(
        `canonical skills backup changed during npm packaging: ${paths.sourceSkills}; ` +
          rootPackRecoveryHint(),
      );
    }

    if (rootStats) {
      let rootFingerprint = null;
      if (rootStats.isDirectory() && !rootStats.isSymbolicLink()) {
        try {
          rootFingerprint = treeFingerprint(paths.rootSkills);
        } catch {
          rootFingerprint = null;
        }
      }
      if (rootFingerprint === state.generatedFingerprint) {
        cleanupTransactionTree(
          paths,
          paths.packedSkills,
          state.generatedFingerprint,
          "previous-packed-skills",
          recovery,
        );
        renameSync(paths.rootSkills, paths.packedSkills);
      } else if (rootFingerprint === state.sourceFingerprint) {
        rmSync(paths.sourceSkills, REMOVE_OPTIONS);
      } else {
        preserveUnexpectedTree(paths, paths.rootSkills, "modified-packed-skills", recovery);
      }
    }

    if (!existsSync(paths.rootSkills)) renameSync(paths.sourceSkills, paths.rootSkills);
  } else {
    if (!rootStats || rootStats.isSymbolicLink() || !rootStats.isDirectory()) {
      throw new Error(
        `cannot recover canonical skills from transaction ${paths.transactionRoot}; ` +
          rootPackRecoveryHint(),
      );
    }
    if (treeFingerprint(paths.rootSkills) !== state.sourceFingerprint) {
      throw new Error(
        `canonical skills backup is missing and the repository skills tree is not canonical; ` +
          rootPackRecoveryHint(),
      );
    }
  }

  if (treeFingerprint(paths.rootSkills) !== state.sourceFingerprint) {
    throw new Error(`canonical skills restoration verification failed: ${paths.rootSkills}`);
  }

  cleanupTransactionTree(
    paths,
    paths.generatedSkills,
    state.generatedFingerprint,
    "modified-generated-skills",
    recovery,
  );
  cleanupTransactionTree(
    paths,
    paths.packedSkills,
    state.generatedFingerprint,
    "modified-packed-skills",
    recovery,
  );
  rmSync(paths.transactionRoot, REMOVE_OPTIONS);
  finishRecoveryRecord(recovery);

  if (recovery.root) {
    throw new Error(
      `canonical skills were restored, but unexpected packaging-time changes were preserved at ` +
        `${recovery.root}; review them before retrying`,
    );
  }
  return { restored: true, recoveryRoot: null };
}

export function prepareRootDefaultPackage(
  repoRoot = REPO_ROOT,
  { runNpmPack = defaultRunNpmPack } = {},
) {
  repoRoot = path.resolve(repoRoot);
  const paths = rootPackTransactionPaths(repoRoot);
  const existing = safeLstat(paths.transactionRoot);
  if (existing) {
    throw new Error(
      `a root npm package transaction is already active at ${paths.transactionRoot}. ` +
        rootPackRecoveryHint(),
    );
  }

  const rootStats = safeLstat(paths.rootSkills);
  if (!rootStats?.isDirectory() || rootStats.isSymbolicLink()) {
    throw new Error(`canonical skills root is not a real directory: ${paths.rootSkills}`);
  }
  assertTreeHasNoSymlinks(paths.rootSkills, "canonical skills root");

  const initialSourceFingerprint = treeFingerprint(paths.rootSkills);
  const plan = createDefaultPlan(repoRoot);
  prepareBuildRoot(repoRoot);
  const temporaryRoot = mkdtempSync(path.join(paths.buildRoot, ".root-pack-prepare-"));
  const temporarySkills = path.join(temporaryRoot, "skills");
  const temporaryGenerated = path.join(temporarySkills, DEFAULT_VARIANT);
  const temporaryPackages = path.join(temporaryRoot, "packages");
  const temporaryNpm = path.join(temporaryRoot, "npm");
  const transactionDraft = path.join(temporaryRoot, "transaction");
  let transactionInstalled = false;
  try {
    materializeComposition(plan, temporaryGenerated);
    const findings = markerFindings(temporaryGenerated, "root default package tree");
    if (findings.length) throw new FlavorCompositionError(findings);

    const defaultVariant = [{ name: DEFAULT_VARIANT, plan }];
    const staged = stagePackages(
      repoRoot,
      defaultVariant,
      temporarySkills,
      temporaryPackages,
    );
    packStagedPackages(staged, temporaryNpm, runNpmPack);

    if (treeFingerprint(paths.rootSkills) !== initialSourceFingerprint) {
      throw new Error("canonical skills changed while the root package was being prepared; retry");
    }

    const state = {
      schema: ROOT_PACK_STATE_SCHEMA,
      repoRoot,
      sourceFingerprint: initialSourceFingerprint,
      generatedFingerprint: treeFingerprint(temporaryGenerated),
      preparedAt: new Date().toISOString(),
    };
    mkdirSync(transactionDraft);
    renameSync(
      temporaryGenerated,
      path.join(transactionDraft, path.basename(paths.generatedSkills)),
    );
    writeFileSync(
      path.join(transactionDraft, "state.json"),
      `${JSON.stringify(state, null, 2)}\n`,
      "utf8",
    );
    renameSync(transactionDraft, paths.transactionRoot);
    transactionInstalled = true;

    renameSync(paths.rootSkills, paths.sourceSkills);
    renameSync(paths.generatedSkills, paths.rootSkills);
    if (treeFingerprint(paths.rootSkills) !== state.generatedFingerprint) {
      throw new Error(`generated default skills activation verification failed: ${paths.rootSkills}`);
    }
    return {
      skillCount: plan.skills.length,
      fileCount: plan.files.length,
      transactionRoot: paths.transactionRoot,
    };
  } catch (error) {
    if (transactionInstalled) {
      try {
        restoreRootDefaultPackage(repoRoot);
      } catch (restoreError) {
        throw new Error(
          `${error.message}; automatic root skills recovery also failed: ${restoreError.message}. ` +
            rootPackRecoveryHint(),
          { cause: error },
        );
      }
    }
    throw error;
  } finally {
    rmSync(temporaryRoot, REMOVE_OPTIONS);
  }
}

function mapsOfBuffersEqual(left, right) {
  if (left.size !== right.size) return false;
  for (const [key, value] of left) {
    if (!right.get(key)?.equals(value)) return false;
  }
  return true;
}

export function verifyTarball(tarball, packageDir, expectedName, expectedVersion) {
  const entries = readTarballEntries(tarball);
  const manifestBytes = entries.get("package/package.json");
  if (!manifestBytes) throw new Error(`npm tarball has no package.json: ${tarball}`);
  let manifest;
  try {
    manifest = JSON.parse(UTF8_DECODER.decode(manifestBytes));
  } catch (error) {
    throw new Error(`could not read package.json from npm tarball: ${tarball}: ${error.message}`);
  }
  if (manifest.name !== expectedName) {
    throw new Error(`npm tarball name mismatch: expected ${quote(expectedName)}, got ${quote(manifest.name)}`);
  }
  if (manifest.version !== expectedVersion) {
    throw new Error(`npm tarball version mismatch: expected ${quote(expectedVersion)}, got ${quote(manifest.version)}`);
  }

  const packedSkills = new Map();
  for (const [name, data] of entries) {
    if (!name.startsWith("package/skills/")) continue;
    if (containsFlavorMarker(data)) throw new Error(`flavor marker leaked into npm tarball: ${name}`);
    packedSkills.set(name.slice("package/skills/".length), data);
  }
  const stagedSkills = treeFileBytes(path.join(packageDir, "skills"));
  if (!mapsOfBuffersEqual(packedSkills, stagedSkills)) {
    throw new Error(`npm tarball skill tree differs from staged package: ${tarball}`);
  }
  const forbidden = [...entries.keys()].filter(
    (name) =>
      name.startsWith("package/skill-flavors/") ||
      name.startsWith("package/tests/") ||
      (name.startsWith("package/scripts/") &&
        name !== "package/scripts/npm-package-lifecycle.mjs"),
  );
  if (forbidden.length) throw new Error(`npm tarball contains source-only paths: ${forbidden.slice(0, 5).join(", ")}`);
}

function defaultRunNpmPack({ packageDir, npmRoot }) {
  const npmArguments = ["pack", packageDir, "--json", "--pack-destination", npmRoot];
  const env = { ...process.env, npm_config_dry_run: "false" };
  if (process.env.npm_execpath) {
    return spawnSync(process.execPath, [process.env.npm_execpath, ...npmArguments], {
      encoding: "utf8",
      env,
    });
  }
  return spawnSync(process.platform === "win32" ? "npm.cmd" : "npm", npmArguments, {
    encoding: "utf8",
    env,
  });
}

function packStagedPackages(staged, npmRoot, runNpmPack) {
  mkdirSync(npmRoot, { recursive: false });
  const packed = [];
  const variants = [...staged.keys()].sort((left, right) => {
    if (left === DEFAULT_VARIANT) return -1;
    if (right === DEFAULT_VARIANT) return 1;
    return compareCodepoints(left, right);
  });
  for (const variant of variants) {
    const { packageName: name, version, packageDir } = staged.get(variant);
    const result = runNpmPack({
      packageDir,
      npmRoot,
      packageName: name,
      version,
      variant,
    });
    if (!result || typeof result !== "object") {
      throw new Error(`npm pack runner returned no process result for ${name}`);
    }
    if (result.error?.code === "ENOENT") throw new Error("npm is required to build skill package tarballs");
    if (result.status !== 0) {
      const detail = result.stderr.trim() || result.stdout.trim();
      throw new Error(`npm pack failed for ${name}: ${detail}`);
    }
    let filename;
    try {
      const parsed = JSON.parse(result.stdout);
      if (!Array.isArray(parsed) || parsed.length !== 1 || typeof parsed[0]?.filename !== "string") {
        throw new Error("expected one npm pack result");
      }
      filename = parsed[0].filename;
    } catch (error) {
      throw new Error(`could not parse npm pack output for ${name}: ${result.stdout.trim()}`);
    }
    const tarball = path.join(npmRoot, filename);
    if (!safeLstat(tarball)?.isFile()) throw new Error(`npm pack did not create its reported tarball: ${tarball}`);
    verifyTarball(tarball, packageDir, name, version);
    packed.push({ variant, packageName: name, version, packageDir, tarball });
  }
  return packed;
}

export function packAllVariants(
  repoRoot = REPO_ROOT,
  { runNpmPack = defaultRunNpmPack } = {},
) {
  repoRoot = path.resolve(repoRoot);
  const variants = createAllVariants(repoRoot);
  const buildRoot = prepareBuildRoot(repoRoot);
  const temporaryRoot = mkdtempSync(path.join(buildRoot, ".skill-flavor-pack-"));
  const temporarySkills = path.join(temporaryRoot, "skills");
  const temporaryPackages = path.join(temporaryRoot, "packages");
  const temporaryNpm = path.join(temporaryRoot, "npm");
  try {
    materializeVariants(variants, temporarySkills);
    const findings = markerFindings(temporarySkills, "built skill tree");
    if (findings.length) throw new FlavorCompositionError(findings);
    const staged = stagePackages(repoRoot, variants, temporarySkills, temporaryPackages);
    const packed = packStagedPackages(staged, temporaryNpm, runNpmPack);

    const finalSkills = path.join(buildRoot, "skills");
    const finalPackages = path.join(buildRoot, "packages");
    const finalNpm = path.join(buildRoot, "npm");
    replaceGeneratedDirectories([
      [temporarySkills, finalSkills],
      [temporaryPackages, finalPackages],
      [temporaryNpm, finalNpm],
    ]);
    return packed.map((item) => ({
      ...item,
      packageDir: path.join(finalPackages, item.variant),
      tarball: path.join(finalNpm, path.basename(item.tarball)),
    }));
  } finally {
    rmSync(temporaryRoot, REMOVE_OPTIONS);
  }
}

function usage() {
  return `Usage: node scripts/compose-skill-flavor.mjs [--repo-root PATH] <command> [arguments]\n\n` +
    `Commands:\n` +
    `  validate [FLAVOR_ROOT]             Validate all discovered flavors or one explicit flavor\n` +
    `  build-default [OUTPUT_DIR]         Write the complete default skill tree\n` +
    `  build [FLAVOR_ROOT] [OUTPUT_ROOT]  Build all trees or the default and one explicit flavor\n` +
    `  pack                               Build, stage, pack, and verify every package\n` +
    `  prepare-root-pack                  Activate a marker-free default tree for root npm packaging\n` +
    `  restore-root-pack                  Restore canonical sources after root npm packaging\n`;
}

function parseCli(argv) {
  const args = [...argv];
  if (args.includes("--help") || args.includes("-h")) return { help: true };
  let repoRoot = REPO_ROOT;
  const repoIndex = args.indexOf("--repo-root");
  if (repoIndex >= 0) {
    if (!args[repoIndex + 1]) throw new Error("--repo-root requires a path");
    repoRoot = path.resolve(args[repoIndex + 1]);
    args.splice(repoIndex, 2);
  }
  const command = args.shift();
  if (!command) throw new Error("a command is required");
  if (args.some((argument) => argument.startsWith("-"))) throw new Error(`unknown option: ${args.find((argument) => argument.startsWith("-"))}`);
  const limits = {
    validate: 1,
    "build-default": 1,
    build: 2,
    pack: 0,
    "prepare-root-pack": 0,
    "restore-root-pack": 0,
  };
  if (!(command in limits)) throw new Error(`unknown command: ${command}`);
  if (args.length > limits[command]) throw new Error(`too many arguments for ${command}`);
  return { help: false, repoRoot, command, args };
}

export function main(argv = process.argv.slice(2)) {
  try {
    const options = parseCli(argv);
    if (options.help) {
      console.log(usage());
      return 0;
    }
    const { repoRoot, command, args } = options;
    if (command === "validate") {
      if (!args[0]) {
        const variants = createAllVariants(repoRoot);
        const summaries = variants.map(
          ({ name, plan }) =>
            `${name}: ${plan.skills.length} skills, ${plan.files.length} files, ${plan.replacementCount} replacements`,
        );
        console.log(`OK - ${summaries.join("; ")}.`);
      } else {
        const defaultPlan = createDefaultPlan(repoRoot);
        const flavorRoot = path.resolve(args[0]);
        const flavorPlan = createCompositionPlan(repoRoot, flavorRoot);
        console.log(
          `OK - default: ${defaultPlan.skills.length} skills, ${defaultPlan.files.length} files; ` +
            `${path.basename(flavorRoot)}: ${flavorPlan.skills.length} skills, ${flavorPlan.files.length} files, ` +
            `${flavorPlan.replacementCount} replacements.`,
        );
      }
    } else if (command === "build-default") {
      const plan = createDefaultPlan(repoRoot);
      const outputDir = path.resolve(args[0] ?? path.join(repoRoot, "build/skills/default"));
      materializeComposition(plan, outputDir);
      console.log(`Built default: ${plan.files.length} files for ${plan.skills.length} skills at ${outputDir}.`);
    } else if (command === "build" && !args[0]) {
      const { variants, outputRoot } = buildAllSkillTrees(repoRoot);
      console.log(
        `Built ${variants.length} complete marker-free skill trees at ${outputRoot}: ` +
          `${variants.map(({ name, plan }) => `${name} (${plan.skills.length} skills)`).join(", ")}.`,
      );
    } else if (command === "build") {
      const defaultPlan = createDefaultPlan(repoRoot);
      const flavorRoot = path.resolve(args[0]);
      const flavorPlan = createCompositionPlan(repoRoot, flavorRoot);
      const outputRoot = path.resolve(args[1] ?? path.join(repoRoot, "build/skills"));
      const defaultOutput = path.join(outputRoot, DEFAULT_VARIANT);
      const flavorOutput = path.join(outputRoot, path.basename(flavorRoot));
      validateOutputDirectory(defaultOutput);
      validateOutputDirectory(flavorOutput);
      materializeComposition(defaultPlan, defaultOutput);
      materializeComposition(flavorPlan, flavorOutput);
      console.log(
        `Built default (${defaultPlan.files.length} files) and ${path.basename(flavorRoot)} ` +
          `(${flavorPlan.files.length} files, ${flavorPlan.replacementCount} replacements) at ${outputRoot}.`,
      );
    } else if (command === "pack") {
      const packages = packAllVariants(repoRoot);
      console.log(`Built and verified ${packages.length} npm packages:`);
      for (const item of packages) {
        console.log(`  ${item.packageName}@${item.version} [${item.variant}] -> ${item.tarball}`);
      }
    } else if (command === "prepare-root-pack") {
      const prepared = prepareRootDefaultPackage(repoRoot);
      console.log(
        `Prepared marker-free default package tree: ${prepared.fileCount} files for ` +
          `${prepared.skillCount} skills.`,
      );
    } else {
      const restored = restoreRootDefaultPackage(repoRoot);
      console.log(
        restored.restored
          ? "Restored canonical skills after root npm packaging."
          : "No active root npm package transaction was found.",
      );
    }
    return 0;
  } catch (error) {
    if (error instanceof FlavorCompositionError) {
      for (const finding of error.findings) console.error(`ERROR: ${finding}`);
    } else {
      console.error(`ERROR: ${error.message}`);
    }
    return 1;
  }
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  process.exitCode = main();
}
