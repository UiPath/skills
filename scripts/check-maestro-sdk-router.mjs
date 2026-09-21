/**
 * Router-integrity gate for the Maestro skills in `preview/skills/`.
 *
 * Each guide is a router: `SKILL.md`'s `## Supported node types` table maps a
 * builder surface to a governed H2, a reference file and one worked example.
 * This checks, per skill folder:
 *
 *   - the table parses, and every row names a node type
 *   - Section links a governed H2 that exists in the same file
 *   - Reference and Example exist, and Example is an `examples/*.flow.ts` path
 *   - the example contains the builder call for its surface
 *   - every reference is routed to by a row, or listed as cross-cutting
 *   - governed sections are within MAX_SECTION_BYTES
 *   - every relative link and anchor in the skill resolves
 *
 * Skills whose `SKILL.md` has no router table are skipped.
 *
 *   node scripts/check-maestro-sdk-router.mjs [<skill-dir> ...]
 *
 * With no arguments, checks every `preview/skills/uipath-maestro-*`. Prints one
 * line per problem and exits non-zero if there are any.
 */
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..");

/**
 * Byte budget for a governed section, in place of a line count: a line costs
 * between ~1 token (blank) and ~65 (a wide table row), so line counts do not
 * track what a section costs to load.
 *
 * 1450 = the largest governed section today (`## Human task`, 1364 bytes) plus
 * ~6% slack.
 */
export const MAX_SECTION_BYTES = 1450;

/** Surface -> the builder call a worked example must contain to demonstrate it. */
export const CAPABILITY_MARKERS = {
  "Manual trigger": "export default flow(",
  "Scheduled trigger": "scheduled(",
  "Connector event trigger": "onEvent(",
  "Connector event wait": "waitForEvent(",
  "Standalone HTTP": "managed: false",
  "Managed HTTP": "managed: true",
  Script: "script(",
  Transform: "transform({",
  Filter: "variant: 'filter'",
  Map: "variant: 'map'",
  "Group by": "variant: 'group-by'",
  "Integration Service action": "connector(",
  Subflow: "subflow(",
  "Human task": "hitl({",
  "Human quick form": "variant: 'quick-form'",
  "Human action app": "variant: 'action-app'",
  "RPA workflow": "rpaWorkflow(",
  "Queue item": "queueItem(",
  Summarize: "summarize(",
  "Batch transform": "batchTransform(",
  Branch: ".branch(",
  Switch: ".switch(",
  "Parallel / Merge": ".parallel(",
  Loop: ".loop(",
  "Return / End": ".return(",
  Terminate: ".terminate(",
  Placeholder: "mock()",
  "Error handler": ".onError(",
  Delay: "delay(",
  "API workflow": "apiWorkflow(",
  "Agentic process": "agenticProcess(",
  "Agent resource": "agent(",
  "Inline agent": "inlineAgent(",
  "IxP extraction": "ixpExtract(",
  "Form trigger": "formTrigger(",
  "Conversation trigger": "conversationTrigger(",
  "Voice trigger": "voiceTrigger(",
  "Data Fabric read": "dataFabricRead(",
  "Data Fabric update": "dataFabricUpdate(",
  "Do while": ".doWhile(",
  "Document classify": "documentClassify(",
  "Dynamic extract": "dynamicExtract(",
  "Published function": "publishedFunction(",
  "Conversation message wait": "waitForMessage(",
  "Conversational agent": "conversationalAgent(",
  "Conversation send message": "sendMessage(",
  "Voice outgoing call": "createOutgoingCall(",
  "Voice agent": "voiceAgent(",
  "Voice end call": "endCall(",
};

/** References with no router row by design: cross-cutting guides, not one node's detail. */
export const NON_CAPABILITY_REFERENCES = new Set([
  "references/CLI-LOOP.md",
  "references/agent-resources.md",
  "references/bindings.md",
  "references/brownfield.md",
  "references/error-handling.md",
  "references/evaluate.md",
  "references/loops.md",
  "references/or-processes.md",
]);

const portable = (value) => value.split("\\").join("/");

/**
 * Fence tracking, so a `##` inside a code block is not read as a heading and a
 * link inside one is not read as a link. A closing fence must match the opening
 * character and be at least as long.
 */
function nextFence(line, current) {
  const match = line.match(/^\s*(`{3,}|~{3,})/);
  if (!match) return current;
  const candidate = { char: match[1][0], length: match[1].length };
  if (!current) return candidate;
  return candidate.char === current.char && candidate.length >= current.length
    ? undefined
    : current;
}

/** H2s only, with GitHub's anchor slug, skipping fenced blocks. */
export function markdownHeadings(markdown) {
  const headings = [];
  let fence;
  for (const [index, line] of markdown.replaceAll("\r\n", "\n").split("\n").entries()) {
    const next = nextFence(line, fence);
    if (next !== fence) {
      fence = next;
      continue;
    }
    if (fence) continue;
    const match = line.match(/^##(?!#)\s+(.+?)\s*#*\s*$/);
    if (!match) continue;
    const text = match[1].trim();
    const anchor = text
      .replace(/<[^>]*>/g, "")
      .replace(/[`*_~]/g, "")
      .toLowerCase()
      .replace(/[^\p{Letter}\p{Number}\s-]/gu, "")
      .replace(/\s/g, "-");
    headings.push({ anchor, line: index, text });
  }
  return headings;
}

/** Link targets, skipping fenced blocks. */
export function markdownLinks(markdown) {
  const links = [];
  let fence;
  for (const line of markdown.replaceAll("\r\n", "\n").split("\n")) {
    const next = nextFence(line, fence);
    if (next !== fence) {
      fence = next;
      continue;
    }
    if (fence) continue;
    for (const match of line.matchAll(
      /!?\[[^\]]*\]\((<[^>]+>|[^\s)]+)(?:\s+['"][^)]*['"])?\)/g,
    )) {
      links.push(match[1].replace(/^<|>$/g, ""));
    }
  }
  return links;
}

/** Resolve a relative link against its source file. Absolute and scheme URLs are skipped. */
export function relativeLinkTarget(source, href) {
  if (/^[a-z][a-z\d+.-]*:/i.test(href) || href.startsWith("//") || href.startsWith("/")) {
    return undefined;
  }
  const hash = href.indexOf("#");
  const rawPath = hash < 0 ? href : href.slice(0, hash);
  const anchor = hash < 0 ? undefined : href.slice(hash + 1);
  let decodedPath;
  try {
    decodedPath = decodeURIComponent(rawPath);
  } catch {
    decodedPath = rawPath;
  }
  const path = portable(
    normalize(join(dirname(source), decodedPath || source.split("/").at(-1))),
  );
  return anchor ? { path, anchor } : { path };
}

const tableCells = (line) =>
  line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((cell) => cell.trim());

/** A cell's single backticked value, or '' when it is absent or ambiguous. */
function inlineCode(cell) {
  const values = [...cell.matchAll(/`([^`]+)`/g)].map((match) => match[1]);
  return values.length === 1 ? values[0] : "";
}

/** Parse `## Supported node types`' table. */
export function routerRows(skill) {
  const lines = skill.replaceAll("\r\n", "\n").split("\n");
  const headings = markdownHeadings(skill);
  const supported = headings.find((heading) => heading.text === "Supported node types");
  if (!supported) {
    return { problems: ["SKILL.md: missing `## Supported node types`"], rows: [] };
  }
  const nextH2 = headings.find((heading) => heading.line > supported.line)?.line ?? lines.length;
  const headerLine = lines.findIndex(
    (line, index) => index > supported.line && index < nextH2 && /^\s*\|.*\|\s*$/.test(line),
  );
  if (headerLine < 0 || !/^\s*\|?(?:\s*:?-+:?\s*\|)+\s*$/.test(lines[headerLine + 1] ?? "")) {
    return {
      problems: ["SKILL.md: `## Supported node types` must contain a Markdown router table"],
      rows: [],
    };
  }

  const headers = tableCells(lines[headerLine]).map((cell) => cell.toLowerCase());
  const index = {
    surface: headers.findIndex((cell) => cell.includes("surface")),
    nodeType: headers.findIndex((cell) => cell.includes("node type")),
    section: headers.indexOf("section"),
    reference: headers.indexOf("reference"),
    example: headers.indexOf("example"),
  };
  const problems = [];
  for (const [name, label] of [
    ["surface", "a Surface"],
    ["nodeType", "a Node type"],
    ["section", "a Section"],
    ["reference", "a Reference"],
    ["example", "an Example"],
  ]) {
    if (index[name] < 0) problems.push(`SKILL.md: router table is missing ${label} column`);
  }
  if (problems.length > 0) return { problems, rows: [] };

  const rows = [];
  for (let line = headerLine + 2; line < nextH2; line++) {
    if (!/^\s*\|.*\|\s*$/.test(lines[line])) break;
    const cells = tableCells(lines[line]);
    rows.push({
      example: inlineCode(cells[index.example] ?? ""),
      line: line + 1,
      nodeType: cells[index.nodeType] ?? "",
      section: markdownLinks(cells[index.section] ?? "")[0] ?? "",
      reference: markdownLinks(cells[index.reference] ?? "")[0] ?? "",
      surface: cells[index.surface] ?? "",
    });
  }
  return { problems, rows };
}

/**
 * Every row names a node type, links a governed H2 that exists, points at a
 * reference that exists, and names an example that exists AND demonstrates the
 * surface.
 */
export function lintRouter(skill, files, expectedRows) {
  const parsed = routerRows(skill);
  const problems = [...parsed.problems];
  const sectionAnchors = new Set();
  const anchors = new Set(markdownHeadings(skill).map((heading) => heading.anchor));

  if (expectedRows !== undefined && parsed.rows.length !== expectedRows) {
    problems.push(
      `SKILL.md: router table has ${parsed.rows.length} rows; expected ${expectedRows}`,
    );
  }
  for (const row of parsed.rows) {
    const where = `SKILL.md:${row.line} (${row.surface || "unnamed surface"})`;
    // The RAW cell, not a single backticked value: several rows name a family
    // plus its variants, which `inlineCode` would read as ambiguous.
    if (row.nodeType.trim() === "") {
      problems.push(`${where}: row has no node type`);
    }
    if (!/^examples\/[^/]+\.flow\.ts$/.test(row.example)) {
      problems.push(`${where}: Example must be one examples/<file>.flow.ts path`);
    }
    if (!row.section.startsWith("#")) {
      problems.push(`${where}: Section must link a governed H2 in this file`);
    } else {
      const anchor = row.section.slice(1);
      sectionAnchors.add(anchor);
      if (!anchors.has(anchor)) problems.push(`${where}: no H2 matches #${anchor}`);
    }
    if (!row.reference) {
      problems.push(`${where}: Reference is empty`);
    } else if (!files.has(portable(normalize(row.reference)))) {
      problems.push(`${where}: Reference ${row.reference} does not exist`);
    }
    if (!row.example) {
      problems.push(`${where}: Example is empty`);
    } else if (!files.has(portable(normalize(row.example)))) {
      problems.push(`${where}: Example ${row.example} does not exist`);
    } else {
      const marker = CAPABILITY_MARKERS[row.surface];
      if (marker === undefined) {
        problems.push(`${where}: no capability marker known for this surface`);
      } else if (!files.get(portable(normalize(row.example))).includes(marker)) {
        problems.push(`${where}: ${row.example} does not demonstrate ${row.surface}`);
      }
    }
  }
  return { problems, rows: parsed.rows, sectionAnchors };
}

/** Every reference is either routed to by a row or listed as cross-cutting. */
export function lintReferenceCoverage(rows, files) {
  const routed = new Set(rows.map((row) => portable(normalize(row.reference))));
  return [...files.keys()]
    .filter((path) => path.startsWith("references/") && path.endsWith(".md"))
    .filter((path) => !routed.has(path) && !NON_CAPABILITY_REFERENCES.has(path))
    .sort()
    .map((path) => `${path}: no router row points at it, and it is not a cross-cutting guide`);
}

/** Governed sections are capped by BYTES — see the constant. */
export function lintSectionBudgets(skill, anchors, maximum = MAX_SECTION_BYTES) {
  const lines = skill.replaceAll("\r\n", "\n").split("\n");
  const headings = markdownHeadings(skill);
  const problems = [];
  for (const anchor of [...anchors].sort()) {
    const index = headings.findIndex((heading) => heading.anchor === anchor);
    if (index < 0) continue;
    const start = headings[index].line;
    const end = headings[index + 1]?.line ?? lines.length;
    const bytes = lines.slice(start, end).join("\n").length;
    if (bytes > maximum) {
      problems.push(
        `SKILL.md: section "## ${headings[index].text}" is ${bytes} bytes `
          + `(~${Math.round(bytes / 4)} tok); maximum is ${maximum}`,
      );
    }
  }
  return problems;
}

/** Every relative Markdown link in the skill resolves, anchors included. */
export function lintRelativeLinks(files) {
  const problems = [];
  for (const [source, markdown] of files) {
    if (!source.endsWith(".md")) continue;
    for (const href of markdownLinks(markdown)) {
      const target = relativeLinkTarget(source, href);
      if (!target) continue;
      const body = files.get(target.path);
      if (body === undefined) {
        problems.push(`${source}: link ${href} does not resolve`);
        continue;
      }
      if (target.anchor && !markdownHeadings(body).some((h) => h.anchor === target.anchor)) {
        problems.push(`${source}: link ${href} has no matching H2 in ${target.path}`);
      }
    }
  }
  return problems;
}

/** Read one skill folder into a path -> contents map, paths relative to it. */
export function readSkill(skillDir) {
  const files = new Map();
  const walk = (dir, prefix) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = prefix ? `${prefix}/${entry.name}` : entry.name;
      if (entry.isDirectory()) walk(join(dir, entry.name), path);
      else files.set(path, readFileSync(join(dir, entry.name), "utf8"));
    }
  };
  walk(skillDir, "");
  return files;
}

/** All problems for one skill folder. `expectedRows` is optional. */
export function lintSkill(files, expectedRows) {
  const skill = files.get("SKILL.md") ?? "";
  if (!skill) return ["SKILL.md: missing"];
  const router = lintRouter(skill, files, expectedRows);
  return [
    ...router.problems,
    ...lintReferenceCoverage(router.rows, files),
    ...lintSectionBudgets(skill, router.sectionAnchors),
    ...lintRelativeLinks(files),
  ];
}

function main(argv) {
  const dirs = argv.length > 0
    ? argv
    : readdirSync(join(REPO, "preview", "skills"))
        .filter((name) => name.startsWith("uipath-maestro-"))
        .map((name) => join("preview", "skills", name))
        .filter((dir) => existsSync(join(REPO, dir, "SKILL.md")));

  let failed = 0;
  for (const dir of dirs) {
    const absolute = resolve(REPO, dir);
    const files = readSkill(absolute);
    // Case and BPMN route through prose and their own `## API index`.
    if (!(files.get("SKILL.md") ?? "").includes("## Supported node types")) {
      console.log(`${dir}: no router table, skipped`);
      continue;
    }
    const problems = lintSkill(files);
    if (problems.length === 0) {
      console.log(`${dir}: OK`);
      continue;
    }
    failed += problems.length;
    for (const problem of problems) console.error(`${dir}/${problem}`);
  }
  if (failed > 0) {
    console.error(`\ncheck-maestro-sdk-router: ${failed} problem(s)`);
    process.exitCode = 1;
  }
}

if (import.meta.url === `file://${process.argv[1]}`) main(process.argv.slice(2));
