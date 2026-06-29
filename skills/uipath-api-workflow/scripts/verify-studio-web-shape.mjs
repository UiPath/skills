#!/usr/bin/env node
// Verify every Type:"Api" project in a solution conforms to the Studio Web editable contract.
// Runtime success (validate / run / pack) does NOT prove a project opens in Studio Web — this gate does.
// Usage: node verify-studio-web-shape.mjs [solutionDir]   (default ".")
// Exit 0 = all Api projects openable in Studio Web (warnings allowed); exit 1 = at least one will NOT open.

import { readFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { join, dirname, basename } from "node:path";

const solDir = process.argv[2] ?? ".";
const errors = [];
const warnings = [];

function readJson(p) {
  return JSON.parse(readFileSync(p, "utf8"));
}

// Locate the .uipx
const uipx = existsSync(solDir)
  ? readdirSync(solDir).find((f) => f.endsWith(".uipx"))
  : null;
if (!uipx) {
  console.error(`No .uipx solution file found in ${solDir}`);
  process.exit(1);
}
const sol = readJson(join(solDir, uipx));
const apiProjects = (sol.Projects ?? []).filter((p) => p.Type === "Api");
if (apiProjects.length === 0) {
  console.log(`No Type:"Api" projects in ${uipx} — nothing to check.`);
  process.exit(0);
}

for (const proj of apiProjects) {
  const rel = proj.ProjectRelativePath ?? "";
  const label = rel || proj.Id || "<unknown>";

  // HARD: .uipx must point at project.uiproj, never project.json
  if (basename(rel) !== "project.uiproj") {
    errors.push(
      `${label}: .uipx ProjectRelativePath must end with /project.uiproj (got "${rel}"). ` +
        `Studio Web only recognizes a folder as a project if it contains a .uiproj file; project.json alone is rejected as invalid_project_folder.`
    );
    continue;
  }

  const uiprojPath = join(solDir, rel);
  const projDir = dirname(uiprojPath);

  // HARD: project.uiproj must exist
  if (!existsSync(uiprojPath)) {
    errors.push(`${label}: project.uiproj not found at ${uiprojPath}.`);
    continue;
  }
  const uiproj = readJson(uiprojPath);

  // HARD: ProjectType must be exactly "Api" (Studio Web strict enum; "api" is rejected)
  if (uiproj.ProjectType !== "Api") {
    errors.push(
      `${label}: project.uiproj ProjectType must be exactly "Api" (got ${JSON.stringify(uiproj.ProjectType)}). Studio Web rejects any other casing/value.`
    );
  }

  // HARD: MainFile must be set and the file must exist
  const mainFile = uiproj.MainFile;
  if (!mainFile) {
    errors.push(`${label}: project.uiproj MainFile is missing.`);
  } else {
    if (mainFile !== "Workflow.json") {
      warnings.push(`${label}: MainFile is "${mainFile}", not the canonical "Workflow.json". CLI reconcile/pack assume Workflow.json.`);
    }
    if (!existsSync(join(projDir, mainFile))) {
      errors.push(`${label}: MainFile "${mainFile}" does not exist at ${join(projDir, mainFile)}.`);
    }
  }

  // HARD: entry-points.json must exist and its filePath must be relative (no leading slash)
  const epPath = join(projDir, "entry-points.json");
  if (!existsSync(epPath)) {
    errors.push(`${label}: entry-points.json not found at ${epPath}.`);
  } else {
    const ep = readJson(epPath);
    const first = ep.entryPoints?.[0];
    if (!first) {
      errors.push(`${label}: entry-points.json has no entryPoints[0].`);
    } else {
      if (typeof first.filePath === "string" && first.filePath.startsWith("/")) {
        errors.push(`${label}: entry-points.json filePath "${first.filePath}" has a leading slash. Use a relative path: "content/${mainFile ?? "Workflow.json"}".`);
      }
      const expected = `content/${mainFile ?? "Workflow.json"}`;
      if (first.filePath !== expected) {
        warnings.push(`${label}: entry-points.json filePath is "${first.filePath}", expected "${expected}".`);
      }
      if (first.type !== "Api") {
        warnings.push(`${label}: entry-points.json type is ${JSON.stringify(first.type)}, canonical is "Api".`);
      }
    }
  }

  // SMELL: bindings_v2.json is part of the init shape; Studio Web uses it to wire connectors
  if (!existsSync(join(projDir, "bindings_v2.json"))) {
    warnings.push(`${label}: bindings_v2.json missing. 'uip api-workflow init' creates it ({"version":"2.0","resources":[]}); add it for connector wiring.`);
  }

  // SMELL: leftover runtime-only shape inside the project folder
  if (existsSync(join(projDir, "project.json"))) {
    warnings.push(`${label}: a project.json sits next to project.uiproj. If kept, its name/main must match the .uiproj or Studio Web throws ProjectMetadataMismatchError. Prefer removing it.`);
  }
  const wfDir = join(projDir, "workflows");
  if (existsSync(wfDir) && statSync(wfDir).isDirectory()) {
    warnings.push(`${label}: a workflows/ folder is present (runtime-only shape). The Studio Web main workflow is the root-level ${mainFile ?? "Workflow.json"}.`);
  }
}

for (const w of warnings) console.log(`WARN  ${w}`);
for (const e of errors) console.error(`FAIL  ${e}`);

if (errors.length) {
  console.error(`\n${errors.length} Api project(s) will NOT open in Studio Web. Fix the shape before packing/publishing.`);
  process.exit(1);
}
console.log(`\nOK — ${apiProjects.length} Api project(s) conform to the Studio Web editable contract${warnings.length ? ` (${warnings.length} warning(s))` : ""}.`);
process.exit(0);
