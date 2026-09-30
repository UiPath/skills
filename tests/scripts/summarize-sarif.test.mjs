import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const SCRIPT = fileURLToPath(new URL("../../skills/uipath-activity-migrator/scripts/summarize-sarif.mjs", import.meta.url));

/** A minimal SARIF 2.1.0 log holding `results`; returns its path. */
function sarif(results, rules = []) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "sarif-"));
  const file = path.join(dir, "analyze-latest.sarif");
  fs.writeFileSync(file, JSON.stringify({ version: "2.1.0", runs: [{ tool: { driver: { name: "UiPath.Upgrade", rules } }, results }] }));
  return file;
}
const at = (uri) => ({ locations: [{ physicalLocation: { artifactLocation: { uri } } }] });
const result = (ruleId, text, extra = {}) => ({ ruleId, message: { text }, ...extra });
// A completed run always carries a validation result; without one the status is `unknown`.
const validated = result("WORKFLOW-VALIDATION-SUCCESS", "Workflow validation passed with no errors.", { level: "note", ...at("Main.xaml") });

function summarize(file, ...flags) {
  const r = spawnSync(process.execPath, [SCRIPT, file, ...flags], { encoding: "utf8" });
  assert.equal(r.status, 0, r.stderr);
  return r.stdout;
}
const json = (file) => JSON.parse(summarize(file, "--json"));

// The tool's SARIF library omits `level` when it equals the default, and the SARIF default is `warning`.
test("a result without level is a warning, and a validation issue lands in needs attention", () => {
  const j = json(sarif([validated, result("WORKFLOW-VALIDATION-ISSUE", "Validation error: You must provide a value for Connection", at("Main.xaml"))]));
  assert.equal(j.totals.warning, 1);
  assert.equal(j.status, "partial");
  assert.equal(j.attention.total, 1);
  assert.match(j.attention.items[0].reasons.join(), /WORKFLOW-VALIDATION-ISSUE/);
});

test("a restore error with no file is a blocker and fails the run", () => {
  const j = json(sarif([result("RESTORE-MISSING-PACKAGE", "Package 'Acme.Internal.Helpers' version '1.0.0' not found in any source.", { level: "error" })]));
  assert.equal(j.status, "failed");
  assert.equal(j.blockers.length, 1);
  assert.equal(j.attention.total, 0);
});

test("the same restore rule without level, the --ignore-missing-dependencies path, is a needs-attention item", () => {
  const j = json(sarif([validated, result("RESTORE-MISSING-PACKAGE", "Package 'Acme.Internal.Helpers' version '1.0.0' not found in any source.")]));
  assert.equal(j.status, "partial");
  assert.equal(j.blockers.length, 0);
  assert.equal(j.attention.total, 1);
  assert.equal(j.attention.items[0].reasons[0], "RESTORE-MISSING-PACKAGE");
});

test("a version raised to the tool minimum is on the Packages line and does not make the run partial", () => {
  const file = sarif([
    validated,
    result("UIAUTOMATION-PACKAGE-UPGRADE", "Cannot use version '25.10.5' for 'UiPath.UIAutomation.Activities'. Minimum required version is '25.10.21'. Using minimum version."),
    result("UIAUTOMATION-PACKAGE-UPGRADE", "Updated package 'UiPath.UIAutomation.Activities' from '24.10.19' to '25.10.21'.", { level: "note" }),
  ]);
  const j = json(file);
  assert.equal(j.status, "success");
  assert.equal(j.totals.warning, 1);
  assert.deepEqual(j.effectiveVersions["UiPath.UIAutomation.Activities"], { requested: "25.10.5", minimum: "25.10.21", from: "24.10.19", to: "25.10.21" });
  assert.match(summarize(file), /Packages: UiPath\.UIAutomation\.Activities 24\.10\.19 → 25\.10\.21 \(requested 25\.10\.5, raised to the tool minimum 25\.10\.21\)/);
});

test("a project already on the target version is reported as unchanged", () => {
  const file = sarif([validated, result("UIAUTOMATION-PACKAGE-UPGRADE", "Using existing project version '25.10.22' for 'UiPath.UIAutomation.Activities'.Update is not needed.", { level: "note" })]);
  assert.deepEqual(json(file).effectiveVersions["UiPath.UIAutomation.Activities"], { from: "25.10.22", to: "25.10.22", unchanged: true });
  assert.match(summarize(file), /Packages: UiPath\.UIAutomation\.Activities 25\.10\.22 \(unchanged\)/);
});

test("a package message no shape parses stays on the Packages line verbatim", () => {
  const file = sarif([
    validated,
    result("UIAUTOMATION-PACKAGE-UPGRADE", "Updated package 'UiPath.UIAutomation.Activities' from '24.10.19' to '26.10.4'.", { level: "note" }),
    result("OFFICE365-PACKAGE-MIGRATION", "Added UiPath.MicrosoftOffice365.Activities package dependency to the project.", { level: "note" }),
  ]);
  assert.match(summarize(file), /Packages: UiPath\.UIAutomation\.Activities 24\.10\.19 → 26\.10\.4; Added UiPath\.MicrosoftOffice365\.Activities package dependency to the project\./);
});
