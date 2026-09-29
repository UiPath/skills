import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const CHECKER = fileURLToPath(new URL("../../scripts/check-skill-links.mjs", import.meta.url));
const ENFORCED = "skills/uipath-maestro-bpmn";

/** A repo root holding the given `relative path -> text` files. */
function tree(files) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "skill-links-"));
  for (const [relative, text] of Object.entries(files)) {
    const target = path.join(root, relative);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, text);
  }
  return root;
}

function run(files) {
  const result = spawnSync(process.execPath, [CHECKER, tree(files)], { encoding: "utf8" });
  return { status: result.status, out: result.stdout + result.stderr };
}

/** A link from the enforced skill to `#<fragment>` under `heading`. */
function linkTo(heading, fragment) {
  return {
    [`${ENFORCED}/SKILL.md`]: `# Skill\n\n[go](references/r.md#${fragment})\n`,
    [`${ENFORCED}/references/r.md`]: `${heading}\n\nbody\n`,
  };
}

test("a dead anchor in an enforced tree fails the run", () => {
  const { status, out } = run(linkTo("## Variables", "variables-gone"));
  assert.equal(status, 1);
  assert.match(out, /1 dead anchor\(s\)/);
  assert.match(out, /SKILL\.md:3 -> references\/r\.md#variables-gone/);
});

test("a dead anchor outside an enforced tree is reported, not failed", () => {
  const { status, out } = run({
    "skills/uipath-platform/SKILL.md": "# Skill\n\n[go](references/r.md#gone)\n",
    "skills/uipath-platform/references/r.md": "## Here\n",
  });
  assert.equal(status, 0);
  assert.match(out, /1 dead anchor\(s\) outside skills\/uipath-maestro-bpmn, not enforced/);
});

test("slugs follow GitHub's rules", () => {
  const cases = [
    ["## Variables (`bpmn:variables`)", "variables-bpmnvariables"],
    ["## Script tasks — Jint authoring contract", "script-tasks--jint-authoring-contract"],
    ["## 7. Use `UIP_LOG_LEVEL=info` for debug runs", "7-use-uip_log_levelinfo-for-debug-runs"],
    ["### Relevance Check → `LC_GUARDRAIL_MISAPPLIED`", "relevance-check--lc_guardrail_misapplied"],
    ["## Aggregated loop output (`$vars.<loopId>.output`)", "aggregated-loop-output-varsloopidoutput"],
    ["## Step 11a: Pull a change (`--source remote`)", "step-11a-pull-a-change---source-remote"],
  ];
  for (const [heading, fragment] of cases) {
    const { status, out } = run(linkTo(heading, fragment));
    assert.equal(status, 0, `${heading} should slug to #${fragment}\n${out}`);
  }
});

test("a repeated heading takes the -1 suffix", () => {
  assert.equal(run(linkTo("## Notes\n\ntext\n\n## Notes", "notes-1")).status, 0);
  assert.equal(run(linkTo("## Notes\n\ntext\n\n## Notes", "notes-2")).status, 1);
});

test("headings and links inside fences and inline code are ignored", () => {
  assert.equal(run(linkTo("```\n## Fenced\n```", "fenced")).status, 1);
  const { status } = run({
    [`${ENFORCED}/SKILL.md`]: "# Skill\n\nFormat `[Red](#,##0)` applies.\n",
  });
  assert.equal(status, 0);
});

test("an `<a name>` target counts as an anchor", () => {
  assert.equal(run(linkTo('<a name="Manual"></a>', "manual")).status, 0);
});

test("a fragment on a missing file reports the file, not the anchor", () => {
  const { status, out } = run({
    [`${ENFORCED}/SKILL.md`]: "# Skill\n\n[go](references/absent.md#any)\n",
  });
  assert.equal(status, 1);
  assert.match(out, /1 broken link\(s\)/);
  assert.doesNotMatch(out, /dead anchor\(s\):/);
});

test("a malformed % escape is reported as a broken link", () => {
  for (const link of ["references/r%zz.md", "references/r.md#bad%zz"]) {
    const { status, out } = run({
      [`${ENFORCED}/SKILL.md`]: `# Skill\n\n[go](${link})\n`,
      [`${ENFORCED}/references/r.md`]: "## Here\n",
    });
    assert.equal(status, 1, out);
    assert.match(out, /1 broken link\(s\)/);
    assert.match(out, /malformed % escape/);
  }
});

// A pinned skill is composed from classic/skills in the pinning flavor and from
// skills/ everywhere else, so a link into it from another skill must land in both.
const PINNED = {
  "skill-flavors/sw/uipath-flow/.canonical": "classic\n",
  "skill-flavors/sw/uipath-flow/SKILL.md": "<!--skill-flavor:x:start-->\n[r](references/old.md)\n<!--skill-flavor:x:end-->\n",
  "skills/uipath-flow/SKILL.md": "# Flow\n\n[r](references/new.md)\n",
  "skills/uipath-flow/references/new.md": "# New\n",
  "classic/skills/uipath-flow/SKILL.md": "# Flow v1\n\n[r](references/old.md)\n",
  "classic/skills/uipath-flow/references/old.md": "# Old\n",
};

test("pinned-skill flavor and classic links resolve against the classic tree", () => {
  const { status, out } = run(PINNED);
  assert.equal(status, 0, out);
});

test("a cross-skill link into a pinned skill must resolve in both generations", () => {
  const onlyNew = run({ ...PINNED, "skills/uipath-other/SKILL.md": "[x](../uipath-flow/references/new.md)\n" });
  assert.equal(onlyNew.status, 1);
  assert.match(onlyNew.out, /no such file in the classic tree the sw flavor\(s\) compose/);

  const both = run({
    ...PINNED,
    "skills/uipath-flow/references/shared.md": "# S\n",
    "classic/skills/uipath-flow/references/shared.md": "# S\n",
    "skills/uipath-other/SKILL.md": "[x](../uipath-flow/references/shared.md)\n",
  });
  assert.equal(both.status, 0, both.out);
});

test("an anchor into a pinned skill must land in both generations", () => {
  const { status, out } = run({
    ...PINNED,
    "skills/uipath-flow/references/shared.md": "# S\n\n## Step 6a\n",
    "classic/skills/uipath-flow/references/shared.md": "# S\n",
    "skills/uipath-other/SKILL.md": "# Other\n\n[x](../uipath-flow/references/shared.md#step-6a)\n",
  });
  assert.equal(status, 0, out); // uipath-other is not an enforced tree, so it is reported, not fatal
  assert.match(out, /shared\.md#step-6a \(in the classic tree the sw flavor\(s\) compose\)/);
});

test("a canonical link inside a block every pinning flavor overrides needs only the current tree", () => {
  const block = (body) => `<!--skill-flavor:flow-pointer:start-->\n${body}\n<!--skill-flavor:flow-pointer:end-->\n`;
  const files = {
    ...PINNED,
    "skills/uipath-other/SKILL.md": `# Other\n\n${block("[x](../uipath-flow/references/new.md)")}`,
  };
  const withoutOverride = run(files);
  assert.equal(withoutOverride.status, 1, "a flavor that composes the block still needs the classic target");
  assert.match(withoutOverride.out, /no such file in the classic tree/);

  const overridden = run({
    ...files,
    "skill-flavors/sw/uipath-other/SKILL.md": block("[x](../uipath-flow/references/old.md)"),
  });
  assert.equal(overridden.status, 0, overridden.out);
});
