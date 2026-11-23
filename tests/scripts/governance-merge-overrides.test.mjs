import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const SCRIPT = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "skills",
  "uipath-governance",
  "scripts",
  "merge-overrides.mjs",
);

/** Runs the script on `base`/`overrides` (JS values, or raw strings) in a temp dir. */
function merge({ base, overrides, args = [], baseFlag = "--base", out = "nested/out.json" }) {
  const dir = mkdtempSync(join(tmpdir(), "mo-"));
  try {
    const put = (name, value) => {
      const file = join(dir, name);
      writeFileSync(file, typeof value === "string" ? value : JSON.stringify(value));
      return file;
    };
    const argv = [];
    if (base !== undefined) argv.push(baseFlag, put("base.json", base));
    if (overrides !== undefined) argv.push("--overrides", put("overrides.json", overrides));
    if (out) argv.push("--out", join(dir, out));
    const result = spawnSync(process.execPath, [SCRIPT, ...argv, ...args], { encoding: "utf8" });
    const outFile = out ? join(dir, out) : null;
    return {
      ...result,
      outFile,
      merged: outFile && existsSync(outFile) ? JSON.parse(readFileSync(outFile, "utf8")) : undefined,
      raw: outFile && existsSync(outFile) ? readFileSync(outFile, "utf8") : undefined,
    };
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

test("deep-merges objects, replaces scalars and arrays, and creates the output directory", () => {
  const base = {
    a: { x: 1, y: { keep: true, change: "old" } },
    list: [1, 2, 3],
    untouched: "same",
  };
  const result = merge({
    base,
    overrides: { a: { y: { change: "new" }, z: 9 }, list: [7], added: { deep: { er: 1 } } },
  });
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(result.merged, {
    a: { x: 1, y: { keep: true, change: "new" }, z: 9 },
    list: [7],
    untouched: "same",
    added: { deep: { er: 1 } },
  });
  assert.match(result.stdout, /^MERGED: .*out\.json\n$/);
  assert.equal(result.raw, JSON.stringify(result.merged, null, 2), "2-space indented JSON");
});

test("null clears a key (kept as null) and an object replaces a scalar at that key", () => {
  const result = merge({
    base: { cleared: { big: 1 }, scalar: "text" },
    overrides: { cleared: null, scalar: { now: "object" } },
  });
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(result.merged, { cleared: null, scalar: { now: "object" } });
});

test("an empty array override replaces a populated base array", () => {
  const result = merge({ base: { a: { l: [1, 2] } }, overrides: { a: { l: [] } } });
  assert.deepEqual(result.merged, { a: { l: [] } });
});

test("--defaults is accepted as an alias of --base", () => {
  const result = merge({ base: { a: 1 }, baseFlag: "--defaults", overrides: { b: 2 } });
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(result.merged, { a: 1, b: 2 });
});

test("--summary lists each overridden path with its operation, then caps at 20", () => {
  const small = merge({
    base: { a: { b: 1 } },
    overrides: { a: { b: 2 }, gone: null, arr: [1, 2, 3] },
    args: ["--summary"],
  });
  assert.match(small.stdout, /Overridden paths: 3\n/);
  assert.match(small.stdout, /^ {2}replace-scalar +a\.b$/m);
  assert.match(small.stdout, /^ {2}clear +gone$/m);
  assert.match(small.stdout, /^ {2}replace-array +arr \(array\[3\]\)$/m);

  const many = Object.fromEntries(Array.from({ length: 25 }, (_, i) => [`k${i}`, i]));
  const big = merge({ base: {}, overrides: many, args: ["--summary"] });
  assert.match(big.stdout, /Overridden paths: 25\n/);
  assert.match(big.stdout, /… and 5 more\n$/);
  assert.ok(!big.stdout.includes("k20"));
});

test("without --summary only the MERGED line is printed", () => {
  const result = merge({ base: {}, overrides: { a: 1 } });
  assert.equal(result.stdout.split("\n").length, 2);
  assert.ok(!result.stdout.includes("Overridden"));
});

for (const [name, options, message] of [
  ["a missing base", { overrides: {}, out: "o.json" }, /error: --base \(or --defaults\) is required/],
  ["missing overrides", { base: {}, out: "o.json" }, /error: --overrides is required/],
  ["a missing out", { base: {}, overrides: {}, out: "" }, /error: --out is required/],
]) {
  test(`exits 2 for ${name}`, () => {
    const result = merge(options);
    assert.equal(result.status, 2);
    assert.match(result.stderr, message);
  });
}

test("exits 2 and names the file when the input is not valid JSON", () => {
  const result = merge({ base: "{oops", overrides: {} });
  assert.equal(result.status, 2);
  assert.match(result.stderr, /^error: .*base\.json: /);
});

test("exits 2 for a non-object base or overrides (arrays and wrapped values included)", () => {
  const baseArray = merge({ base: [], overrides: {} });
  assert.equal(baseArray.status, 2);
  assert.match(baseArray.stderr, /--base must be an object/);

  const overridesNull = merge({ base: {}, overrides: null });
  assert.equal(overridesNull.status, 2);
  assert.match(overridesNull.stderr, /--overrides must be an object/);

  const overridesArray = merge({ base: {}, overrides: [1] });
  assert.equal(overridesArray.status, 2);
  assert.match(overridesArray.stderr, /--overrides must be an object/);
});

test("the MERGED path is absolute", () => {
  const result = merge({ base: {}, overrides: {} });
  const printed = result.stdout.match(/^MERGED: (.*)\n/)[1];
  assert.equal(printed, resolve(printed));
});
