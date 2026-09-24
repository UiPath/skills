#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const deny = (reason) => process.stdout.write(JSON.stringify({
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: reason,
  },
}));
const within = (root, item) => {
  const relative = path.relative(root, item);
  return relative === "" ||
    (!relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative));
};

let input;
try { input = JSON.parse(fs.readFileSync(0, "utf8")); } catch { process.exit(0); }
const raw = input?.tool_input?.file_path || input?.tool_input?.path;
if (!raw || path.basename(raw).toLowerCase() !== "caseplan.json") process.exit(0);

const cwd = path.resolve(input.cwd || process.cwd());
const target = path.resolve(cwd, raw);
if (!within(cwd, target)) process.exit(0);

let dir = path.dirname(target);
let sdd;
while (within(cwd, dir)) {
  const candidate = path.join(dir, "sdd.md");
  if (fs.existsSync(candidate)) { sdd = candidate; break; }
  if (dir === cwd || path.dirname(dir) === dir) break;
  dir = path.dirname(dir);
}
if (!sdd) process.exit(0);

const planPath = path.join(path.dirname(sdd), "tasks", "tasks.md");
let plan = "";
try { plan = fs.readFileSync(planPath, "utf8"); } catch {}
const entries = plan.match(/^## T\d+:\s/gm) || [];
if (!/^## Inventory(?:\s|$)/m.test(plan) ||
    !entries.some((entry) => entry.startsWith("## T01:")) ||
    entries.length < 3) {
  deny(`Greenfield case build blocked: create ${planPath} with a ` +
    "'## Inventory' section and at least three numbered entries beginning " +
    "'## T01:' before writing caseplan.json.");
}
