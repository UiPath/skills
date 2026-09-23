import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, readdirSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, relative, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  createCompositionPlan,
  createDefaultPlan,
  materializeComposition,
} from "../../scripts/compose-skill-flavor.mjs";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const FLAVOR_ROOT = join(REPO_ROOT, "skill-flavors");

// A skill's numbered Critical Rules get cited by number from its own references
// AND from every flavor override. Insert one rule and every citation at or above
// it points one rule too low -- silently, because nothing reads a number and
// checks what it landed on. Observed: inserting "Convert before authoring" as
// Rule 4 left the studioweb tree with a scaffold override still numbered 23
// inside a 26-rule list, `Never auto-run (Rule 12)` resolving to Build-review
// preference, and `SKILL.md Rule 6` resolving to Use plugin references. All
// three shipped green -- CI's only flavor guard matches forbidden CONTENT.
//
// OPT-IN, deliberately. A repo-wide version of this fails on skills where
// "Rule N" means something other than a Critical Rule (uipath-agents guardrail
// rules) and on SKILL.md files with a second numbered list after the rules
// (uipath-admin). Both are false positives, not findings: `^\d+\. \*\*` is
// ADJACENT to "Critical Rule heading", not equal to it. Add a skill here only
// once its `Rule N` citations genuinely mean its own Critical Rules.
const SCOPED_SKILLS = ["uipath-maestro-case"];

function criticalRuleNumbers(skillMd) {
  const section = /^## Critical Rules\s*$([\s\S]*?)(?=^## )/m.exec(skillMd);
  if (!section) return [];
  return [...section[1].matchAll(/^(\d+)\. \*\*/gm)].map((m) => Number(m[1]));
}

function markdownFiles(root) {
  const out = [];
  const walk = (dir) => {
    for (const entry of readdirSync(dir)) {
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) walk(full);
      else if (entry.endsWith(".md")) out.push(full);
    }
  };
  walk(root);
  return out;
}

function builtTrees(t) {
  const plans = [["default", createDefaultPlan(REPO_ROOT)]];
  let names = [];
  try {
    names = readdirSync(FLAVOR_ROOT).filter((d) =>
      statSync(join(FLAVOR_ROOT, d)).isDirectory(),
    );
  } catch {
    names = [];
  }
  for (const name of names) {
    plans.push([name, createCompositionPlan(REPO_ROOT, join(FLAVOR_ROOT, name))]);
  }
  return plans.map(([name, plan]) => {
    const out = mkdtempSync(join(tmpdir(), `rule-citations-${name}-`));
    t.after(() => rmSync(out, { recursive: true, force: true }));
    materializeComposition(plan, out);
    return [name, out];
  });
}

test("every built tree numbers the scoped skills' Critical Rules 1..N", (t) => {
  let checked = 0;
  for (const [variant, root] of builtTrees(t)) {
    for (const skill of SCOPED_SKILLS) {
      const nums = criticalRuleNumbers(
        readFileSync(join(root, skill, "SKILL.md"), "utf8"),
      );
      assert.ok(nums.length >= 2, `${variant}/${skill}: no numbered Critical Rules found`);
      assert.deepEqual(
        nums,
        Array.from({ length: nums.length }, (_, i) => i + 1),
        `${variant}/${skill}/SKILL.md numbers its rules ${nums.join(",")} — expected a contiguous 1..${nums.length}. A flavor override keeping an old number lands here.`,
      );
      checked += 1;
    }
  }
  assert.ok(checked >= 2, "expected the default tree plus at least one flavor");
});

test("every `Rule N` citation resolves, in every built tree", (t) => {
  for (const [variant, root] of builtTrees(t)) {
    for (const skill of SCOPED_SKILLS) {
      const skillRoot = join(root, skill);
      const present = new Set(
        criticalRuleNumbers(readFileSync(join(skillRoot, "SKILL.md"), "utf8")),
      );
      const dangling = [];
      for (const file of markdownFiles(skillRoot)) {
        for (const m of readFileSync(file, "utf8").matchAll(/\bRule (\d+)\b/g)) {
          if (!present.has(Number(m[1]))) {
            dangling.push(`${relative(root, file)} cites Rule ${m[1]}`);
          }
        }
      }
      assert.deepEqual(
        dangling,
        [],
        `${variant}/${skill}: citation(s) point at a rule this tree lacks (highest is ${Math.max(...present)}):\n  ${dangling.join("\n  ")}`,
      );
    }
  }
});
