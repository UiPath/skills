import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const SCRIPT = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "skills",
  "uipath-governance",
  "scripts",
  "synthesize-formdata.mjs",
);

const policy = (productIdentifier, contributions) => ({ productIdentifier, contributions });
const clause = (clauseId, ...editorialPolicies) => ({ clauseId, editorialPolicies });

function synthesize({ catalog, product = "Studio", clauseIds = "C1", omit = [], out = "deep/out.json" }) {
  const dir = mkdtempSync(join(tmpdir(), "sf-"));
  try {
    const file = join(dir, "catalog.json");
    writeFileSync(file, typeof catalog === "string" ? catalog : JSON.stringify(catalog));
    const options = { catalog: file, product, "clause-ids": clauseIds, out: join(dir, out) };
    const argv = Object.entries(options)
      .filter(([key]) => !omit.includes(key))
      .flatMap(([key, value]) => [`--${key}`, value]);
    const result = spawnSync(process.execPath, [SCRIPT, ...argv], { encoding: "utf8" });
    const outFile = join(dir, out);
    return {
      ...result,
      formData: existsSync(outFile) ? JSON.parse(readFileSync(outFile, "utf8")) : undefined,
    };
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

test("writes each required value under its dotted key, using eq, gte, lte and contains", () => {
  const result = synthesize({
    catalog: {
      packId: "p",
      clauses: [
        clause("C1", policy("Studio", [
          { key: "a.b.c", required: { eq: false } },
          { key: "limits.min", required: { gte: 3 } },
          { key: "limits.max", required: { lte: 10 } },
          { key: "allowed", required: { contains: ["x", "y"] } },
          { key: "a.b.d", required: { eq: "text" } },
        ])),
      ],
    },
  });
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(result.formData, {
    a: { b: { c: false, d: "text" } },
    limits: { min: 3, max: 10 },
    allowed: ["x", "y"],
  });
  assert.match(result.stdout, /^SYNTHESIZED: .*out\.json \(5 contributions\)\n$/);
});

test("eq takes precedence over the other operators and 0/false/empty values still count", () => {
  const result = synthesize({
    catalog: {
      packId: "p",
      clauses: [
        clause("C1", policy("Studio", [
          { key: "k", required: { eq: 0, gte: 5 } },
          { key: "flag", required: { gte: 0 } },
        ])),
      ],
    },
  });
  assert.deepEqual(result.formData, { k: 0, flag: 0 });
});

test("accepts the CLI's PascalCase output wrapped in Data", () => {
  const result = synthesize({
    catalog: {
      Data: {
        PackId: "p",
        Clauses: [
          {
            ClauseId: "C1",
            EditorialPolicies: [
              {
                ProductIdentifier: "Studio",
                Contributions: [
                  { Key: "x.y", Required: { Eq: 1 } },
                  { Key: "z", Required: { Contains: ["q"] } },
                ],
              },
            ],
          },
        ],
      },
    },
  });
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(result.formData, { x: { y: 1 }, z: ["q"] });
});

test("accepts a bare PascalCase catalog (PackId at the top level)", () => {
  const result = synthesize({
    catalog: {
      PackId: "p",
      Clauses: [{ ClauseId: "C1", EditorialPolicies: [{ ProductIdentifier: "Studio", Contributions: [{ Key: "k", Required: { Gte: 2 } }] }] }],
    },
  });
  assert.deepEqual(result.formData, { k: 2 });
});

test("only the requested clauses and product contribute, and clause ids are trimmed", () => {
  const result = synthesize({
    catalog: {
      packId: "p",
      clauses: [
        clause("C1", policy("Studio", [{ key: "one", required: { eq: 1 } }]), policy("Robot", [{ key: "robot", required: { eq: 1 } }])),
        clause("C2", policy("Studio", [{ key: "two", required: { eq: 2 } }])),
        clause("C3", policy("Studio", [{ key: "three", required: { eq: 3 } }])),
      ],
    },
    clauseIds: " C1 , C3 ,,",
  });
  assert.deepEqual(result.formData, { one: 1, three: 3 });
});

test("a later key can overwrite a scalar parent with a nested object", () => {
  const result = synthesize({
    catalog: {
      packId: "p",
      clauses: [clause("C1", policy("Studio", [
        { key: "a", required: { eq: 1 } },
        { key: "a.b", required: { eq: 2 } },
      ]))],
    },
  });
  assert.deepEqual(result.formData, { a: { b: 2 } });
});

test("notEmpty, exists and unknown operators warn on stderr and write nothing for that key", () => {
  const result = synthesize({
    catalog: {
      packId: "p",
      clauses: [clause("C1", policy("Studio", [
        { key: "real", required: { eq: true } },
        { key: "needs.value", required: { notEmpty: true } },
        { key: "needs.access", required: { exists: true } },
        { key: "weird", required: { between: [1, 2] } },
        { key: "no-required" },
        { key: "falsy-notEmpty", required: { notEmpty: false } },
      ]))],
    },
  });
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(result.formData, { real: true });
  assert.match(result.stderr, /⚠ "needs\.value": notEmpty — value is org-specific; configure manually/);
  assert.match(result.stderr, /⚠ "needs\.access": exists — access policy check, not a formData key/);
  assert.match(result.stderr, /⚠ "weird": unknown operator \{\}/);
  assert.match(result.stderr, /⚠ "no-required": unknown operator \{\}/);
  assert.match(result.stderr, /⚠ "falsy-notEmpty": unknown operator \{"notEmpty":false\}/);
  assert.match(result.stdout, /\(1 contributions\)/);
});

test("exits 3 when nothing applies, naming the product and clauses, and writes no file", () => {
  const result = synthesize({
    catalog: { packId: "p", clauses: [clause("C1", policy("Robot", [{ key: "k", required: { eq: 1 } }]))] },
    product: "Studio",
    clauseIds: "C1,C9",
  });
  assert.equal(result.status, 3);
  assert.match(result.stderr, /error: no contributions for product "Studio" in clauses \[C1, C9\]/);
  assert.equal(result.formData, undefined);
});

test("a catalog with only warnings (count 0) also exits 3", () => {
  const result = synthesize({
    catalog: { packId: "p", clauses: [clause("C1", policy("Studio", [{ key: "k", required: { notEmpty: true } }]))] },
  });
  assert.equal(result.status, 3);
});

for (const option of ["catalog", "product", "clause-ids", "out"]) {
  test(`exits 2 when --${option} is missing`, () => {
    const result = synthesize({ catalog: { packId: "p", clauses: [] }, omit: [option] });
    assert.equal(result.status, 2);
    assert.match(result.stderr, new RegExp(`error: --${option} is required`));
  });
}

test("exits 2 for an unreadable or non-JSON catalog", () => {
  const result = synthesize({ catalog: "{not json" });
  assert.equal(result.status, 2);
  assert.match(result.stderr, /^error reading .*catalog\.json: /);
});

test("a catalog with no clauses array is treated as empty and exits 3", () => {
  const result = synthesize({ catalog: { packId: "p" } });
  assert.equal(result.status, 3);
});
