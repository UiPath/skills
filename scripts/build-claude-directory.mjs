#!/usr/bin/env node

/**
 * Build the Claude plugin directory edition of the default plugin.
 *
 * The directory scans every file on the branch it tracks. From an organization
 * that is not Verified it refuses command hooks, `allowed-tools` grants beyond
 * read-only tools, and any file that is not Markdown, text, JSON, YAML, or an
 * image. This build reduces the marker-free default tree to what it accepts:
 *
 * - Only skills marked `stable` in `assets/skill-status.json` ship.
 * - The plugin root is `.claude-plugin/plugin.json`, `commands/`, `README.md`,
 *   and `LICENSE`: no `hooks/`, other hosts' manifests, or repository tooling.
 * - `allowed-tools` keeps only Read, Grep, Glob, and LS; a line left empty is
 *   removed.
 * - A refused file under an `examples/` or `templates/` directory is read by
 *   the agent, never run. It ships as `<name>.md` holding one fenced block,
 *   and citations of it in the skill gain the `.md` suffix.
 * - A refused file under a `scripts/` or `fixtures/` directory is run or
 *   unpacked. It is omitted, so skill steps that run it do not work here.
 *
 * Any other refused file fails the build instead of shipping or vanishing
 * silently; `tests/scripts/build-claude-directory.test.mjs` builds the real
 * repository, so the pull request that adds such a file is the one that fails.
 *
 * Usage: node scripts/build-claude-directory.mjs [<output-dir>]
 * The output (default `build/claude-directory`) must be absent or empty.
 */

import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import { REPO_ROOT, createDefaultPlan } from "./compose-skill-flavor.mjs";

const ACCEPTED_FILE = /\.(md|txt|json|ya?ml|png|jpe?g|gif|webp|ico)$/i;
const ACCEPTED_NAMES = new Set(["LICENSE"]);
const ACCEPTED_TOOLS = new Set(["Read", "Grep", "Glob", "LS"]);
const CONVERTED_DIRS = new Set(["examples", "templates"]);
const OMITTED_DIRS = new Set(["scripts", "fixtures"]);
const ROOT_FILES = [".claude-plugin/plugin.json", "README.md", "LICENSE"];
const ROOT_TREES = ["commands"];
const MANIFEST = ".claude-plugin/plugin.json";

const UTF8 = new TextDecoder("utf-8", { fatal: true });

const isAccepted = (relativePath) =>
  ACCEPTED_FILE.test(relativePath) || ACCEPTED_NAMES.has(path.posix.basename(relativePath));

/** Classify a refused skill file by the directories between the skill folder and the file. */
function refusedFileRule(skillRelativePath) {
  const directories = skillRelativePath.split("/").slice(1, -1);
  if (directories.some((name) => OMITTED_DIRS.has(name))) return "omit";
  if (directories.some((name) => CONVERTED_DIRS.has(name))) return "convert";
  return null;
}

/** Markdown whose single fenced block is exactly `text`. */
function asMarkdown(name, text) {
  let longestRun = 0;
  for (const [run] of text.matchAll(/`+/g)) longestRun = Math.max(longestRun, run.length);
  const fence = "`".repeat(Math.max(3, longestRun + 1));
  const language = path.posix.extname(name).slice(1).toLowerCase();
  const body = text.endsWith("\n") ? text : `${text}\n`;
  return `# ${name}\n\nThe code block is the exact content of \`${name}\`.\n\n${fence}${language}\n${body}${fence}\n`;
}

function globMatcher(glob) {
  const escaped = glob.split("*").map((part) => part.replace(/[.+?^${}()|[\]\\]/g, "\\$&"));
  const pattern = new RegExp(`^${escaped.join("[^/]*")}$`);
  return (name) => pattern.test(name);
}

/**
 * Append `.md` to every path token citing a converted file: `<dir>/<name>`,
 * a `<dir>/` glob such as `examples/*.case.ts`, or the bare `<name>`. A bare
 * glob is left alone; it usually means the user's files. `converted` maps a
 * directory name to the file names converted inside it.
 */
function rewriteCitations(text, converted) {
  const allNames = [...converted.values()].flat();
  return text.replace(/[\w.*/-]+/g, (token) => {
    const cited = token.replace(/\.+$/, "");
    const segments = cited.split("/");
    const leaf = segments.at(-1);
    const names = segments.length > 1 ? converted.get(segments.at(-2)) : leaf.includes("*") ? undefined : allNames;
    if (!names || !leaf) return token;
    const matches = leaf.includes("*") ? globMatcher(leaf) : (name) => name === leaf;
    return names.some(matches) ? `${cited}.md${token.slice(cited.length)}` : token;
  });
}

/** Keep only the `allowed-tools` grants the directory accepts. */
function narrowToolGrants(text, file, findings) {
  const frontmatter = text.match(/^---\r?\n[\s\S]*?\r?\n---\r?\n/)?.[0];
  const line = frontmatter?.match(/^allowed-tools:[ \t]*(.*?)\r?\n/m);
  if (!line) return text;
  const value = line[1].trim().replace(/^\[(.*)\]$/, "$1").replace(/^(["'])(.*)\1$/, "$2");
  if (!value) {
    findings.push(`${file}: write allowed-tools as a one-line list`);
    return text;
  }
  const kept = value
    .split(/,(?![^(]*\))/)
    .map((tool) => tool.trim())
    .filter((tool) => ACCEPTED_TOOLS.has(tool));
  const replacement = kept.length ? `allowed-tools: ${kept.join(", ")}\n` : "";
  return text.slice(0, line.index) + replacement + text.slice(line.index + line[0].length);
}

/** Relative link targets in Markdown, resolved against the file's directory. */
function linkedPaths(text, file) {
  const targets = [];
  for (const [, raw] of text.matchAll(/\]\(<?([^)\s>]+)>?\)/g)) {
    const target = raw.split("#")[0];
    if (!target || target.startsWith("/") || /^[a-z][a-z0-9+.-]*:/i.test(target)) continue;
    targets.push(path.posix.normalize(path.posix.join(path.posix.dirname(file), target)));
  }
  return targets;
}

function stableSkillNames(repoRoot) {
  const { skills } = JSON.parse(readFileSync(path.join(repoRoot, "assets", "skill-status.json"), "utf8"));
  return new Set(
    Object.entries(skills)
      .filter(([, entry]) => entry?.status === "stable")
      .map(([name]) => name),
  );
}

function rootFiles(repoRoot, findings) {
  const relativePaths = [...ROOT_FILES];
  for (const tree of ROOT_TREES) {
    const root = path.join(repoRoot, tree);
    if (!existsSync(root)) continue;
    for (const entry of readdirSync(root, { recursive: true, withFileTypes: true })) {
      const relativePath = path.relative(repoRoot, path.join(entry.parentPath, entry.name)).split(path.sep).join("/");
      if (entry.isSymbolicLink()) findings.push(`${relativePath}: symbolic links are refused`);
      else if (entry.isFile()) relativePaths.push(relativePath);
    }
  }
  return relativePaths.map((relativePath) => ({
    relativePath,
    bytes: readFileSync(path.join(repoRoot, ...relativePath.split("/"))),
  }));
}

/**
 * Plan the directory edition: the exact files to write, or every reason the
 * repository cannot produce one. Reads the repository; writes nothing.
 */
function planClaudeDirectory(repoRoot) {
  const findings = [];
  const stable = stableSkillNames(repoRoot);
  const plan = createDefaultPlan(repoRoot);
  const files = new Map();
  const omitted = [];
  const convertedBySkill = new Map();
  const convertedSources = new Set();

  for (const item of plan.files) {
    const skill = item.relativePath.split("/")[0];
    if (!stable.has(skill)) continue;
    const relativePath = `skills/${item.relativePath}`;
    const bytes = item.composedBytes ?? readFileSync(item.sourcePath);
    if (isAccepted(relativePath)) {
      files.set(relativePath, bytes);
      continue;
    }
    const rule = refusedFileRule(item.relativePath);
    if (rule === "omit") {
      omitted.push(relativePath);
    } else if (rule === "convert") {
      const name = path.posix.basename(relativePath);
      let text;
      try {
        text = UTF8.decode(bytes);
      } catch {
        findings.push(`${relativePath}: not UTF-8 text, so it cannot ship as Markdown`);
        continue;
      }
      files.set(`${relativePath}.md`, Buffer.from(asMarkdown(name, text), "utf8"));
      convertedSources.add(relativePath);
      const directory = path.posix.basename(path.posix.dirname(relativePath));
      const converted = convertedBySkill.get(skill) ?? new Map();
      converted.set(directory, [...(converted.get(directory) ?? []), name]);
      convertedBySkill.set(skill, converted);
    } else {
      findings.push(
        `${relativePath}: the directory refuses this file type; put it under ` +
          `${[...CONVERTED_DIRS].join("/ or ")}/ (shipped as Markdown) or ` +
          `${[...OMITTED_DIRS].join("/ or ")}/ (omitted)`,
      );
    }
  }

  for (const [relativePath, bytes] of files) {
    if (!relativePath.endsWith(".md") || convertedSources.has(relativePath.slice(0, -3))) continue;
    const skill = relativePath.split("/")[1];
    const original = bytes.toString("utf8");
    let text = original;
    const converted = convertedBySkill.get(skill);
    if (converted) text = rewriteCitations(text, converted);
    if (path.posix.basename(relativePath) === "SKILL.md") text = narrowToolGrants(text, relativePath, findings);
    for (const target of linkedPaths(text, relativePath)) {
      if (convertedSources.has(target)) findings.push(`${relativePath}: links ${target}, which ships as ${target}.md`);
    }
    if (text !== original) files.set(relativePath, Buffer.from(text, "utf8"));
  }

  for (const { relativePath, bytes } of rootFiles(repoRoot, findings)) {
    if (!isAccepted(relativePath)) findings.push(`${relativePath}: the directory refuses this file type`);
    files.set(relativePath, bytes);
  }

  for (const [relativePath, bytes] of files) {
    if (bytes.subarray(0, 2).toString("latin1") === "#!") findings.push(`${relativePath}: files starting with #! are refused`);
  }

  const manifest = JSON.parse(files.get(MANIFEST).toString("utf8"));
  if ("hooks" in manifest) findings.push(`${MANIFEST}: declares hooks, which the directory refuses`);
  for (const agent of [manifest.agents ?? []].flat()) {
    const agentPath = path.posix.normalize(agent);
    if (!files.has(agentPath)) findings.push(`${MANIFEST}: agent ${agent} is not in the directory edition`);
  }

  if (findings.length) throw new Error(`Claude directory edition refused:\n${findings.join("\n")}`);
  const skills = [...new Set([...files.keys()].filter((p) => p.startsWith("skills/")).map((p) => p.split("/")[1]))];
  return { files, omitted, skills };
}

/**
 * Write the directory edition of `repoRoot` to `outputDir`. Throws, writing
 * nothing, when any file would be refused.
 * @returns {{ files: Map<string, Buffer>, omitted: string[], skills: string[] }}
 */
export function buildClaudeDirectory(repoRoot, outputDir) {
  if (existsSync(outputDir) && readdirSync(outputDir).length) {
    throw new Error(`Claude directory output must be empty: ${outputDir}`);
  }
  const edition = planClaudeDirectory(path.resolve(repoRoot));
  for (const [relativePath, bytes] of edition.files) {
    const destination = path.join(outputDir, ...relativePath.split("/"));
    mkdirSync(path.dirname(destination), { recursive: true });
    writeFileSync(destination, bytes);
  }
  return edition;
}

export function main(argv = process.argv.slice(2)) {
  if (argv.length > 1 || argv[0]?.startsWith("-")) {
    console.error("Usage: node scripts/build-claude-directory.mjs [<output-dir>]");
    return 2;
  }
  const outputDir = path.resolve(argv[0] ?? path.join(REPO_ROOT, "build", "claude-directory"));
  try {
    const { files, omitted, skills } = buildClaudeDirectory(REPO_ROOT, outputDir);
    console.log(`Built Claude directory edition: ${files.size} files, ${skills.length} stable skills at ${outputDir}.`);
    if (omitted.length) console.log(`Omitted ${omitted.length} scripts and fixtures:\n  ${omitted.join("\n  ")}`);
    return 0;
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    return 1;
  }
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  process.exitCode = main();
}
