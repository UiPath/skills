import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, relative } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

import { CUSTOM_PACKAGE_PUBLISH_CONFIG } from "../../scripts/compose-skill-flavor.mjs";
import { main, parseArguments, selectSkillPackage } from "../../scripts/select-skill-package.mjs";

const SCRIPT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "scripts", "select-skill-package.mjs");

/** Minimal ustar writer: `files` maps a tar member name to its text. */
function tarGz(files) {
  const blocks = [];
  for (const [name, text] of Object.entries(files)) {
    const body = Buffer.from(text);
    const header = Buffer.alloc(512);
    header.write(name, 0, "utf8");
    header.write("0000644\0", 100);
    header.write("0000000\0", 108);
    header.write("0000000\0", 116);
    header.write(`${body.length.toString(8).padStart(11, "0")}\0`, 124);
    header.write("00000000000\0", 136);
    header.write("        ", 148);
    header.write("0", 156);
    header.write("ustar\0", 257);
    header.write("00", 263);
    const sum = [...header].reduce((a, b) => a + b, 0);
    header.write(`${sum.toString(8).padStart(6, "0")}\0 `, 148);
    blocks.push(header, body, Buffer.alloc((512 - (body.length % 512)) % 512));
  }
  blocks.push(Buffer.alloc(1024));
  return gzipSync(Buffer.concat(blocks));
}

function manifestOf(overrides) {
  return { name: "@uipath/skills", version: "1.2.3", uipathSkillsFlavor: "default", ...overrides };
}

function pack(dir, fileName, { manifest, files }) {
  const entries = {
    "package/package.json": JSON.stringify(manifest),
    ...(files ?? { "package/skills/uipath-x/SKILL.md": "# skill\n" }),
  };
  writeFileSync(join(dir, fileName), tarGz(entries));
}

function withDir(body) {
  const dir = mkdtempSync(join(tmpdir(), "ssp-"));
  try {
    return body(dir);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

const selection = (dir, extra) => ({
  directory: dir,
  packageName: "@uipath/skills",
  flavor: "default",
  version: "1.2.3",
  ...extra,
});

test("parseArguments resolves the directory and returns the four options", () => {
  const parsed = parseArguments(["--directory", "pkgs", "--name", "n", "--flavor", "f", "--version", "1.0.0"]);
  assert.equal(parsed.directory, join(process.cwd(), "pkgs"));
  assert.deepEqual([parsed.packageName, parsed.flavor, parsed.version], ["n", "f", "1.0.0"]);
});

for (const [name, argv, message] of [
  ["an option without a value", ["--directory"], /Usage: node scripts\/select-skill-package\.mjs/],
  ["a value that looks like an option", ["--directory", "--name"], /Usage:/],
  ["a bare word", ["directory", "x"], /Usage:/],
  [
    "a repeated option",
    ["--directory", "a", "--directory", "b"],
    /duplicate option: --directory/,
  ],
  ["an unknown option", ["--directory", "a", "--bogus", "b"], /unknown option: --bogus/],
  ["a missing option", ["--directory", "a", "--name", "n", "--flavor", "f"], /missing required option: --version/],
]) {
  test(`parseArguments rejects ${name}`, () => {
    assert.throws(() => parseArguments(argv), message);
  });
}

test("selects the single tarball matching name, flavor and version", () => {
  withDir((dir) => {
    pack(dir, "a-default.tgz", { manifest: manifestOf({}) });
    pack(dir, "b-other.tgz", { manifest: manifestOf({ name: "@uipath/other" }) });
    pack(dir, "c-flavor.tgz", {
      manifest: manifestOf({ uipathSkillsFlavor: "acme", publishConfig: { ...CUSTOM_PACKAGE_PUBLISH_CONFIG } }),
    });
    writeFileSync(join(dir, "ignored.txt"), "not a tarball");
    assert.equal(selectSkillPackage(selection(dir)), join(dir, "a-default.tgz"));
  });
});

test("a custom flavor is accepted only with the GitHub Packages-only publish config and no repository", () => {
  withDir((dir) => {
    pack(dir, "custom.tgz", {
      manifest: manifestOf({
        name: "@uipath/skills-acme",
        uipathSkillsFlavor: "acme",
        publishConfig: { ...CUSTOM_PACKAGE_PUBLISH_CONFIG },
      }),
    });
    assert.equal(
      selectSkillPackage(selection(dir, { packageName: "@uipath/skills-acme", flavor: "acme" })),
      join(dir, "custom.tgz"),
    );
  });
});

for (const [name, extra, message] of [
  ["no publishConfig", {}, /GitHub Packages-only publish policy/],
  ["an array publishConfig", { publishConfig: [] }, /GitHub Packages-only publish policy/],
  [
    "an extra publishConfig key",
    { publishConfig: { ...CUSTOM_PACKAGE_PUBLISH_CONFIG, access: "public" } },
    /GitHub Packages-only publish policy/,
  ],
  [
    "a wrong publishConfig value",
    { publishConfig: { ...CUSTOM_PACKAGE_PUBLISH_CONFIG, registry: "https://registry.npmjs.org/" } },
    /GitHub Packages-only publish policy/,
  ],
  [
    "a repository field",
    { publishConfig: { ...CUSTOM_PACKAGE_PUBLISH_CONFIG }, repository: "github:UiPath/skills" },
    /must not define package\.json repository/,
  ],
]) {
  test(`rejects a custom package with ${name}`, () => {
    withDir((dir) => {
      pack(dir, "custom.tgz", { manifest: manifestOf({ uipathSkillsFlavor: "acme", ...extra }) });
      assert.throws(() => selectSkillPackage(selection(dir, { flavor: "acme" })), message);
    });
  });
}

test("rejects a version mismatch", () => {
  withDir((dir) => {
    pack(dir, "a.tgz", { manifest: manifestOf({ version: "9.9.9" }) });
    assert.throws(() => selectSkillPackage(selection(dir)), /version mismatch: expected 1\.2\.3, got 9\.9\.9/);
  });
});

test("rejects a tarball that leaks a flavor marker", () => {
  withDir((dir) => {
    pack(dir, "a.tgz", {
      manifest: manifestOf({}),
      files: { "package/skills/uipath-x/SKILL.md": "<!-- skill-flavor: begin x -->\n" },
    });
    assert.throws(() => selectSkillPackage(selection(dir)), /flavor marker leaked into selected npm tarball .*SKILL\.md/);
  });
});

test("rejects a tarball with no skill files", () => {
  withDir((dir) => {
    pack(dir, "a.tgz", { manifest: manifestOf({}), files: { "package/README.md": "hi" } });
    assert.throws(() => selectSkillPackage(selection(dir)), /contains no skill files/);
  });
});

test("rejects a tarball without package.json", () => {
  withDir((dir) => {
    writeFileSync(join(dir, "a.tgz"), tarGz({ "package/skills/x/SKILL.md": "x" }));
    assert.throws(() => selectSkillPackage(selection(dir)), /npm tarball has no package\.json/);
  });
});

test("rejects a tarball whose package.json is not JSON", () => {
  withDir((dir) => {
    writeFileSync(join(dir, "a.tgz"), tarGz({ "package/package.json": "{nope" }));
    assert.throws(() => selectSkillPackage(selection(dir)), /invalid package\.json in .*a\.tgz/);
  });
});

test("rejects zero or several matching tarballs", () => {
  withDir((dir) => {
    pack(dir, "a.tgz", { manifest: manifestOf({}) });
    assert.throws(
      () => selectSkillPackage(selection(dir, { version: "1.2.3", flavor: "missing" })),
      /expected exactly one @uipath\/skills tarball with flavor missing and version 1\.2\.3; found 0/,
    );
    pack(dir, "b.tgz", { manifest: manifestOf({}) });
    assert.throws(() => selectSkillPackage(selection(dir)), /found 2/);
  });
});

test("rejects a missing directory, an empty directory and a file", () => {
  withDir((dir) => {
    assert.throws(() => selectSkillPackage(selection(join(dir, "nope"))), /not a real directory/);
    assert.throws(() => selectSkillPackage(selection(dir)), /no npm tarballs found/);
    writeFileSync(join(dir, "file"), "x");
    assert.throws(() => selectSkillPackage(selection(join(dir, "file"))), /not a real directory/);
  });
});

test("rejects a directory that is a symlink and a tarball that is not a regular file", (t) => {
  withDir((dir) => {
    const real = join(dir, "real");
    mkdirSync(real);
    pack(real, "a.tgz", { manifest: manifestOf({}) });
    try {
      symlinkSync(real, join(dir, "link"), "dir");
      symlinkSync(join(real, "a.tgz"), join(dir, "real", "b.tgz"));
    } catch {
      t.skip("symlinks are not available here");
      return;
    }
    assert.throws(() => selectSkillPackage(selection(join(dir, "link"))), /not a real directory/);
    assert.throws(() => selectSkillPackage(selection(real)), /npm tarball is not a regular file/);
  });
});

function runCli(args, cwd) {
  return spawnSync(process.execPath, [SCRIPT, ...args], { cwd, encoding: "utf8" });
}

test("CLI prints the selected tarball path relative to the cwd and exits 0", () => {
  withDir((dir) => {
    mkdirSync(join(dir, "out"));
    pack(join(dir, "out"), "a.tgz", { manifest: manifestOf({}) });
    const result = runCli(
      ["--directory", "out", "--name", "@uipath/skills", "--flavor", "default", "--version", "1.2.3"],
      dir,
    );
    assert.equal(result.status, 0, result.stderr);
    assert.equal(result.stdout, `${relative(dir, join(dir, "out", "a.tgz"))}\n`);
  });
});

test("CLI reports selection failures on stderr and exits 1", () => {
  withDir((dir) => {
    const result = runCli(
      ["--directory", dir, "--name", "@uipath/skills", "--flavor", "default", "--version", "1.2.3"],
      dir,
    );
    assert.equal(result.status, 1);
    assert.match(result.stderr, /^ERROR: no npm tarballs found/);
    assert.equal(result.stdout, "");
  });
});

test("main returns 1 with a usage error for bad arguments and 0 on success", () => {
  assert.equal(main([]), 1);
  withDir((dir) => {
    pack(dir, "a.tgz", { manifest: manifestOf({}) });
    const original = process.stdout.write;
    let written = "";
    process.stdout.write = (chunk) => {
      written += chunk;
      return true;
    };
    try {
      assert.equal(
        main(["--directory", dir, "--name", "@uipath/skills", "--flavor", "default", "--version", "1.2.3"]),
        0,
      );
    } finally {
      process.stdout.write = original;
    }
    assert.match(written, /a\.tgz\n$/);
  });
});
