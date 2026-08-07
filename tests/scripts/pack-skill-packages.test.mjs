import assert from "node:assert/strict";
import test from "node:test";

import { validateCoworkReport } from "../../scripts/pack-skill-packages.mjs";

function report() {
  return {
    format_version: 1,
    generator: "scripts/export-cowork.py",
    source_package_version: "1.2.3-preview.4",
    skill_count: 2,
    plugin_package_count: 1,
    skills: [
      { name: "uipath-alpha", archive: "skills/uipath-alpha.skill" },
      { name: "uipath-beta", archive: "skills/uipath-beta.skill" },
    ],
    plugin_packages: [
      {
        archive: "plugins/uipath-skills-cowork.zip",
        skills: ["uipath-alpha", "uipath-beta"],
      },
    ],
  };
}

test("Cowork report validation returns its exact artifact contract", () => {
  assert.deepEqual(
    validateCoworkReport(report(), "1.2.3-preview.4"),
    new Set([
      "report.json",
      "skills/uipath-alpha.skill",
      "skills/uipath-beta.skill",
      "plugins/uipath-skills-cowork.zip",
    ]),
  );
});

test("Cowork report validation rejects unsafe or inconsistent contracts", () => {
  const cases = [
    (value) => {
      value.skills[0].archive = "skills/../uipath-alpha.skill";
    },
    (value) => {
      value.skills[1].name = "uipath-alpha";
      value.skills[1].archive = "skills/uipath-alpha.skill";
    },
    (value) => {
      value.plugin_packages[0].skills = ["uipath-alpha", "uipath-alpha"];
    },
    (value) => {
      value.plugin_packages[0].archive = "plugins/unexpected.zip";
    },
  ];

  for (const mutate of cases) {
    const value = report();
    mutate(value);
    assert.throws(() => validateCoworkReport(value, "1.2.3-preview.4"), /Cowork report/);
  }
  assert.throws(
    () => validateCoworkReport(report(), "1.2.3-preview.5"),
    /does not match package version/,
  );
});
