import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, isAbsolute, join, relative, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const SKILL_DIR = join(REPO_ROOT, ".claude", "skills", "manage-skill-flavors");
const SKILL_FILE = join(SKILL_DIR, "SKILL.md");

function frontmatterMetadata() {
  const lines = readFileSync(SKILL_FILE, "utf8").split(/\r?\n/);
  assert.equal(lines[0], "---", "SKILL.md must start with YAML frontmatter");
  const closing = lines.indexOf("---", 1);
  assert.notEqual(closing, -1, "SKILL.md frontmatter needs a closing delimiter");

  return Object.fromEntries(
    lines.slice(1, closing).map((line) => {
      const match = /^([a-z_]+):\s*(.+)$/.exec(line);
      assert.ok(match, `unsupported frontmatter line: ${line}`);
      const [, key, rawValue] = match;
      const value = rawValue.startsWith('"') ? JSON.parse(rawValue) : rawValue;
      return [key, value];
    }),
  );
}

test("contributor skill frontmatter has the expected trigger contract", () => {
  const metadata = frontmatterMetadata();
  assert.deepEqual(Object.keys(metadata).sort(), ["description", "name"]);
  assert.equal(metadata.name, "manage-skill-flavors");
  assert.equal(metadata.description, metadata.description.trim());
  assert.ok(metadata.description.length >= 1 && metadata.description.length <= 1024);
  assert.match(metadata.description.toLowerCase(), /skill flavors?/);
  assert.doesNotMatch(metadata.description, /[<>]/);
});

test("every relative Markdown link stays inside the skill and resolves", () => {
  const source = readFileSync(SKILL_FILE, "utf8");
  const targets = [...source.matchAll(/(?<!!)\[[^\]]+\]\(([^)]+)\)/g)]
    .map((match) => match[1].trim())
    .filter((target) => !target.startsWith("#") && !/^[a-z]+:/i.test(target));

  assert.ok(targets.length > 0, "SKILL.md should link to its detailed reference");
  for (const target of targets) {
    const pathname = decodeURIComponent(target.split("#", 1)[0]);
    const linked = resolve(SKILL_DIR, pathname);
    const inside = relative(SKILL_DIR, linked);
    assert.ok(
      inside && !inside.startsWith("..") && !isAbsolute(inside),
      `relative skill link escapes the skill directory: ${target}`,
    );
    assert.doesNotThrow(
      () => readFileSync(linked),
      `relative skill link does not exist: ${target}`,
    );
  }
});

test("contributor guidance documents the full-catalog Node flavor contract", () => {
  const source = [
    readFileSync(SKILL_FILE, "utf8"),
    readFileSync(
      join(SKILL_DIR, "references", "flavor-test-matrix.md"),
      "utf8",
    ),
  ].join("\n");
  const authoringRules = readFileSync(
    join(REPO_ROOT, ".claude", "rules", "skill-structure.md"),
    "utf8",
  );
  const flavorGuidance = `${source}\n${authoringRules}`;

  assert.doesNotMatch(
    source,
    /skills\.allowlist|allowlisted|compose-skill-flavor\.py|pytest|python3 .*compose-skill-flavor/i,
  );
  assert.match(source, /every custom flavor package contains every canonical skill/i);
  assert.match(source, /sparse (?:files|overrides)/i);
  assert.match(source, /scripts\/compose-skill-flavor\.mjs/);
  assert.match(source, /npm run skills:test/);
  assert.match(source, /@uipath\/skills-<flavor>/);
  assert.match(source, /verified \.tgz files|verify tarballs/i);
  assert.match(source, /`npm pack` and `npm publish`.*backward\s+compatible/is);
  assert.match(source, /npm run skills:recover/);
  assert.match(source, /`npm run skills:pack`.*all-flavor/is);
  assert.match(source, /https:\/\/npm\.pkg\.github\.com\//);
  assert.match(source, /ENABLE_SKILL_FLAVOR_PUBLISH/);
  assert.match(source, /confirmed Internal/i);
  assert.match(flavorGuidance, /column 1/i);
  assert.match(flavorGuidance, /compact marker form|compact.*whitespace-free/is);
  assert.match(flavorGuidance, /no (?:internal, )?leading,? or trailing whitespace/i);
  assert.match(
    flavorGuidance,
    /empty (?:canonical )?(?:<name>-extra|extension) block/i,
  );
  assert.match(flavorGuidance, /do not replace a complete shared table/i);
  assert.match(authoringRules, /inspect the matching sparse override/i);
  assert.match(
    source,
    /review every new or materially changed canonical skill against every existing flavor/i,
  );
  assert.match(
    source,
    /update or add the smallest necessary sparse override wherever the canonical guidance is not correct for that flavor/i,
  );
});
