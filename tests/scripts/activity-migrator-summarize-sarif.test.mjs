import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, utimesSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test, { after } from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SCRIPT = join(REPO_ROOT, "skills", "uipath-activity-migrator", "scripts", "summarize-sarif.mjs");

const tmp = mkdtempSync(join(tmpdir(), "sarif-"));
after(() => rmSync(tmp, { recursive: true, force: true }));
let n = 0;

const res = (ruleId, level, file, text, props) => ({
  ruleId,
  ...(level ? { level } : {}),
  message: { text },
  ...(file ? { locations: [{ physicalLocation: { artifactLocation: { uri: file } } }] } : {}),
  ...(props ? { properties: props } : {}),
});
const log = (results, extra) => ({ runs: [{ tool: { driver: { rules: [] } }, results, ...extra }] });
const write = (obj, name) => {
  const p = join(tmp, name || `l${n++}.sarif`);
  writeFileSync(p, typeof obj === "string" || Buffer.isBuffer(obj) ? obj : JSON.stringify(obj));
  return p;
};
const run = (...args) => spawnSync(process.execPath, [SCRIPT, ...args], { encoding: "utf8" });
const json = (obj) => JSON.parse(run(write(obj), "--json").stdout);
const escapeRe = (s) => s.replace(/[\\^$.*+?()[\]{}|]/g, "\\$&");

const VALIDATION = res("WORKFLOW-VALIDATION-ISSUE", "note", "ok.xaml", "validated");

test("exits 2 with usage when no target is given", () => {
  const r = run();
  assert.equal(r.status, 2);
  assert.match(r.stderr, /usage: node summarize-sarif\.mjs/);
});

test("exits 2 for a file without JSON and for malformed JSON", () => {
  const bad = run(write("not json at all"));
  assert.equal(bad.status, 2);
  assert.match(bad.stderr, /cannot parse .*no JSON object found/);
  const broken = run(write("noise { not: json } noise"));
  assert.equal(broken.status, 2);
  assert.match(broken.stderr, /cannot parse/);
});

test("extracts the JSON object from surrounding console noise", () => {
  const s = JSON.parse(run(write("log line\n" + JSON.stringify(log([VALIDATION])) + "\ntrailer"), "--json").stdout);
  assert.equal(s.status, "success");
});

test("decodes UTF-8 BOM, UTF-16 LE and UTF-16 BE input", () => {
  const text = JSON.stringify(log([VALIDATION]));
  const utf8 = Buffer.concat([Buffer.from([0xef, 0xbb, 0xbf]), Buffer.from(text, "utf8")]);
  const le = Buffer.concat([Buffer.from([0xff, 0xfe]), Buffer.from(text, "utf16le")]);
  const be = Buffer.from(le);
  for (let i = 2; i + 1 < be.length; i += 2) [be[i], be[i + 1]] = [be[i + 1], be[i]];
  be[0] = 0xfe;
  be[1] = 0xff;
  for (const buf of [utf8, le, be]) {
    const s = JSON.parse(run(write(buf), "--json").stdout);
    assert.equal(s.status, "success");
    assert.equal(s.totals.results, 1);
  }
});

test("a folder target uses the newest .sarif file and ignores other files", () => {
  const dir = mkdtempSync(join(tmp, "dir-"));
  const old = join(dir, "old.sarif");
  const fresh = join(dir, "NEW.SARIF");
  writeFileSync(old, JSON.stringify(log([])));
  writeFileSync(fresh, JSON.stringify(log([VALIDATION])));
  writeFileSync(join(dir, "notes.txt"), "x");
  utimesSync(old, new Date(2020, 1, 1), new Date(2020, 1, 1));
  utimesSync(fresh, new Date(2024, 1, 1), new Date(2024, 1, 1));
  const s = JSON.parse(run(dir, "--json").stdout);
  assert.ok(s.file.endsWith("NEW.SARIF"));
  assert.equal(s.status, "success");
});

test("an empty folder exits 2", () => {
  const dir = mkdtempSync(join(tmp, "empty-"));
  const r = run(dir);
  assert.equal(r.status, 2);
  assert.match(r.stderr, /no \.sarif files in/);
});

test("a log with no results is unknown with a reason", () => {
  const r = run(write(log([])));
  assert.equal(r.status, 0);
  assert.match(r.stdout, /Status: \*\*unknown\*\* \| 0 activities migrated/);
  assert.match(r.stdout, /Reason: the log has no results/);
});

test("a log missing runs entirely is unknown", () => {
  assert.equal(json({}).status, "unknown");
});

test("a clean run with validation results is success and reports a framework change", () => {
  const l = log([VALIDATION, res("PROJECT-FRAMEWORK-UPDATE", "note", "", "fw")]);
  const s = json(l);
  assert.equal(s.status, "success");
  assert.equal(s.frameworkChanged, true);
  assert.match(run(write(l)).stdout, /Framework: Legacy → Windows/);
});

test("a project copy alone counts as a completed run", () => {
  assert.equal(json(log([res("PROJECT-COPY", "note", "", "copied")])).status, "success");
});

test("an error without a file location (core rule) is a critical failure and a blocker", () => {
  const p = write(log([res("RESTORE-MISSING-PACKAGE", "error", "", "Package X is missing")]));
  const s = JSON.parse(run(p, "--json").stdout);
  assert.equal(s.status, "failed");
  assert.equal(s.blockers.length, 1);
  assert.equal(s.blockers[0].rule, "RESTORE-MISSING-PACKAGE");
  const out = run(p).stdout;
  assert.match(out, /## Blockers \(1\)/);
  assert.match(out, /\*\*RESTORE-MISSING-PACKAGE\*\* — Package X is missing/);
});

test("warning-level project blockers from the UIA extension fail the run and show the file", () => {
  const p = write(log([VALIDATION, res("UIAUTOMATION-INVALID-UIA-PACKAGE", "warning", "project.json", "bad pkg")]));
  const out = run(p).stdout;
  assert.match(out, /Status: \*\*failed\*\*/);
  assert.match(out, /bad pkg \(project\.json\)/);
});

test("a per-file error does not stop the run: it is partial and listed as a per-file issue", () => {
  const s = json(log([VALIDATION, res("WORKFLOW-COMPILATION-ERROR", "error", "a.xaml", "does not compile")]));
  assert.equal(s.status, "partial");
  assert.equal(s.blockers.length, 0);
  assert.equal(s.typeIssues.length, 1);
  assert.equal(s.typeIssues[0].file, "a.xaml");
});

test("a result without level defaults to warning, or to the rule's default level", () => {
  const withRule = {
    runs: [
      {
        tool: { driver: { rules: [{ id: "XAML-X", defaultConfiguration: { level: "error" } }] } },
        results: [VALIDATION, res("XAML-X", undefined, "", "defaults to error"), res("TYPE-CHECK", undefined, "b.xaml", "warn")],
      },
    ],
  };
  const s = json(withRule);
  assert.equal(s.totals.error, 1);
  assert.equal(s.totals.warning, 1);
  assert.equal(s.status, "failed");
});

test("message text falls back to markdown and long messages are truncated", () => {
  const long = "x".repeat(400);
  const s = json(
    log([
      VALIDATION,
      {
        ruleId: "TYPE-CHECK",
        level: "warning",
        message: { markdown: "md body" },
        locations: [{ physicalLocation: { artifactLocation: { description: "desc.xaml" } } }],
      },
      res("TYPE-MISSING", "warning", "c.xaml", long),
      { ruleId: "TYPE-MISSING", level: "warning" },
    ]),
  );
  assert.equal(s.typeIssues[0].message, "md body");
  assert.equal(s.typeIssues[0].file, "desc.xaml");
  assert.equal(s.typeIssues[1].message.length, 321);
  assert.ok(s.typeIssues[1].message.endsWith("…"));
  assert.equal(s.typeIssues[2].message, "");
});

test("package results are parsed into effective versions and the Packages line", () => {
  const results = [
    VALIDATION,
    res("RESTORE-PACKAGE-UPGRADE", "note", "", "Updated package 'UiPath.System.Activities' from '24.10.1' to '25.10.0'."),
    res("UIAUTOMATION-PACKAGE-UPGRADE", "note", "", "Using existing project version '25.10.5' for 'UiPath.UIAutomation.Activities'.Update is not needed."),
    res("X-PACKAGE-MIGRATION", "note", "", "Cannot use version '1.0.0' for 'Foo.Bar'. Minimum required version is '2.0.0'. Using minimum version."),
    res("X-PACKAGE-MIGRATION", "note", "", "Updated package 'Foo.Bar' from '1.0.0' to '2.0.0'."),
    res("Y-PACKAGE-MIGRATION", "note", "", "Cannot use version '3.0.0' for 'Only.Raised'. Minimum required version is '4.0.0'. Using minimum version."),
    res("Z-PACKAGE-UPGRADE", "note", "", "something unrecognisable"),
  ];
  const s = json(log(results));
  assert.deepEqual(s.effectiveVersions["UiPath.System.Activities"], { from: "24.10.1", to: "25.10.0" });
  assert.equal(s.effectiveVersions["UiPath.UIAutomation.Activities"].unchanged, true);
  assert.equal(s.packages.length, 6);
  const out = run(write(log(results))).stdout;
  assert.match(out, /UiPath\.System\.Activities 24\.10\.1 → 25\.10\.0/);
  assert.match(out, /UiPath\.UIAutomation\.Activities 25\.10\.5 \(unchanged\)/);
  assert.match(out, /Foo\.Bar 1\.0\.0 → 2\.0\.0 \(requested 1\.0\.0, raised to the tool minimum 2\.0\.0\)/);
  assert.match(out, /Only\.Raised requested 3\.0\.0, raised to the tool minimum 4\.0\.0/);
  assert.match(out, /something unrecognisable/);
});

// A full UIA + productivity + core + step scenario, checked through both outputs.
const UIA = [
  VALIDATION,
  res("UIAUTOMATION-ACTIVITY-UiPath.UIAutomation.Activities.Click-MIGRATION-SUCCESS", "note", "a.xaml", "ok", { activityGuid: "g1", sourceActivity: "Click A" }),
  res("UIAUTOMATION-ACTIVITY-TypeInto-MIGRATION-SUCCESS", "note", "a.xaml", "ok", { activityType: "UiPath.UIAutomation.Activities.TypeInto", activityGuid: "g2" }),
  res("UIAUTOMATION-ACTIVITY-TypeInto-MIGRATION-SUCCESS", "note", "a.xaml", "ok", { activityGuid: "g3" }),
  // left classic: bare error plus the property-level result of the same activity
  res("UIAUTOMATION-ACTIVITY-MIGRATION-ERROR", "error", "b.xaml", "Click B failed", { activityGuid: "g4", sourceActivity: "Click B" }),
  res("UIAUTOMATION-ACTIVITY-MIGRATION-ERROR-VariableSelector", "error", "b.xaml", "selector is a variable", { activityGuid: "g4", sourceActivity: "Click B", propertyName: "Target" }),
  res("UIAUTOMATION-ACTIVITY-MIGRATION-PARTIAL", "warning", "c.xaml", "partly", { activityGuid: "g5", destinationActivity: "Click C" }),
  res("UIAUTOMATION-ACTIVITY-MIGRATION-WARNING", "warning", "c.xaml", "Click - Type: Click migrated with warnings in 5 ms. Warnings: Property: Target - Selector needs review. More text.", { activityGuid: "g6" }),
  res("UIAUTOMATION-ACTIVITY-PROPERTY-MIGRATION-WARNING-Foo", "warning", "c.xaml", "prop warn [PostMigration Action Required]", { activityGuid: "g7", propertyName: "P" }),
  res("UIAUTOMATION-WORKFLOW-SOMETHING", "warning", "d.xaml", "workflow level"),
  res("UIAUTOMATION-WORKFLOW-INFO", "note", "d.xaml", "just info"),
  res("UIAUTOMATION-OTHER", "note", "d.xaml", "unclassified uia"),
  res("MAIL-ACTIVITY-MIGRATION", "error", "e.xaml", "left classic mail", { activityGuid: "m1" }),
  res("MAIL-ACTIVITY-MIGRATION", "warning", "e.xaml", "no ConnectionId", { activityGuid: "m2" }),
  res("MAIL-ACTIVITY-MIGRATION", "note", "e.xaml", "clean", { activityGuid: "m3" }),
  res("WARNING", "warning", "", "Step failed: Foo - boom"),
  res("ERROR", "error", "f.xaml", "Error processing workflow f.xaml"),
  res("CUSTOM-RULE", "warning", "", "mystery"),
  res("CUSTOM-FILE", "warning", "g.xaml", "mystery with file"),
  res("", "note", "", "no rule id"),
];

test("classifies UIA, productivity, step and unknown results into the JSON summary", () => {
  const s = json(log(UIA, { properties: { outputPath: "C:/out" } }));
  assert.equal(s.status, "partial");
  assert.equal(s.outputPath, "C:/out");
  assert.equal(s.uia.migrated, 3);
  assert.deepEqual(s.uia.migratedByType, { Click: 1, TypeInto: 2 });
  assert.equal(s.uia.migratedItems[0].activity, "Click A");
  assert.equal(s.uia.notMigrated.length, 2);
  assert.equal(s.uia.partial.length, 1);
  assert.equal(s.uia.warnings.length, 2);
  assert.equal(s.uia.workflow.length, 2);
  assert.equal(s.productivity.migrated, 2);
  assert.equal(s.productivity.notMigrated.length, 1);
  assert.equal(s.productivity.warnings.length, 1);
  assert.equal(s.totals.migrated, 5);
  // the two results of Click B collapse to one left-classic activity that keeps its reason
  assert.equal(s.leftClassic.total, 1);
  assert.equal(s.leftClassic.results, 2);
  assert.deepEqual(Object.keys(s.leftClassic.byReason), ["VariableSelector"]);
  assert.equal(s.stepFailures.length, 1);
  assert.equal(s.actionRequired.length, 1);
  assert.ok(s.unknownRules["CUSTOM-RULE"]);
  assert.deepEqual(s.files, ["a.xaml", "b.xaml", "c.xaml", "d.xaml", "e.xaml", "f.xaml", "g.xaml", "ok.xaml"]);
  assert.ok(s.attention.byReason["Selector needs review"]);
  assert.ok(s.attention.byReason["step failed"]);
  assert.ok(s.attention.byReason["partial"]);
});

test("stdout summary lists attention by reason and file, inline while there are few", () => {
  const out = run(write(log(UIA))).stdout;
  assert.match(out, /^# Migration summary — l\d+\.sarif/);
  assert.match(out, /Status: \*\*partial\*\* \| 5 activities migrated \| 1 left classic \| \d+ need attention \| 0 blockers/);
  assert.match(out, /Left classic \(1\): still run as classic; listed under "UIA not migrated" in the --out file/);
  assert.match(out, /## Step failures \(1\): the run continued without these steps\n- Step failed: Foo - boom/);
  assert.match(out, /- By reason: .*step failed ×2/);
  assert.match(out, /- By file: /);
  assert.match(out, /- e\.xaml — MAIL-ACTIVITY-MIGRATION: no ConnectionId/);
  assert.doesNotMatch(out, /Full list/);
  assert.match(out, /## Rules outside the known families[\s\S]*- CUSTOM-RULE \[warning\] ×1/);
});

test("--out writes the full report and stdout names the file", () => {
  const outFile = join(tmp, "report.md");
  const r = run(write(log(UIA)), "--out", outFile);
  assert.equal(r.status, 0);
  assert.match(r.stdout, new RegExp(`listed under "UIA not migrated" in ${escapeRe(outFile)}`));
  const md = readFileSync(outFile, "utf8");
  assert.match(md, /^# Migration report — l\d+\.sarif/);
  assert.match(md, /Migrated by classic type: Click ×1, TypeInto ×2/);
  assert.match(md, /## UIA not migrated \(2\)/);
  assert.match(md, /## UIA partial \(1\)/);
  assert.match(md, /## Manual action required \(1\)/);
  assert.match(md, /## Productivity not migrated \(1\)/);
  assert.match(md, /## Productivity warnings \(1\)/);
  assert.match(md, /## UIA warnings \(activity and property\), informational \(1\)/);
  assert.match(md, /## UIA workflow-level \(2\)/);
  assert.match(md, /## Step failures \(run continued without the step\) \(1\)/);
  assert.match(md, /## Per-file issues/);
  assert.match(md, /## Rule counts\n\| Rule \| Level \| Count \|/);
  assert.match(md, /- b\.xaml: Click B \/ Target — VariableSelector: selector is a variable/);
});

test("with --out and many attention items stdout points at the report file", () => {
  const many = [VALIDATION];
  for (let i = 0; i < 12; i++) many.push(res("TYPE-CHECK", "warning", `f${i}.xaml`, `issue ${i}`));
  const outFile = join(tmp, "many.md");
  const r = run(write(log(many)), "--out", outFile);
  assert.match(r.stdout, new RegExp(`- Full list: ${escapeRe(outFile)}`));
});

test("--out with a blocker and package info mirrors them in the report", () => {
  const outFile = join(tmp, "blocked.md");
  const results = [
    res("RESTORE-PACKAGE-UPGRADE", "note", "", "Updated package 'A' from '1' to '2'."),
    res("PROJECT-X", "error", "", "fatal"),
    res("PROJECT-FRAMEWORK-UPDATE", "note", "", "fw"),
  ];
  run(write(log(results, { properties: { outputPath: "/o" } })), "--out", outFile);
  const md = readFileSync(outFile, "utf8");
  assert.match(md, /Status: \*\*failed\*\*.*Output: \/o/);
  assert.match(md, /Framework: Legacy → Windows/);
  assert.match(md, /Packages: A 1 → 2/);
  assert.match(md, /## Blockers \(1\)\n- \*\*PROJECT-X\*\* — fatal/);
});

test("a dangling --out flag writes no report file", () => {
  const r = run(write(log([VALIDATION])), "--out");
  assert.equal(r.status, 0);
  assert.match(r.stdout, /Status: \*\*success\*\*/);
});

test("without validation or project copy: unknown, or failed when errors exist; a step failure is named", () => {
  const unk = json(log([res("CUSTOM", "note", "", "x")]));
  assert.equal(unk.status, "unknown");
  assert.match(unk.reason, /validation never reported/);
  const failed = json(log([res("ERROR", "error", "x.xaml", "Error processing workflow")]));
  assert.equal(failed.status, "failed");
  assert.match(failed.reason, /1 error-level result\(s\) explain it/);
  const stepped = json(log([res("WARNING", "warning", "", "Step failed: Y - bad")]));
  assert.equal(stepped.status, "unknown");
  assert.match(stepped.reason, /a step failed as a whole \(Step failed: Y - bad\)/);
});

test("more than ten attention items are not listed inline; fewer are", () => {
  const many = [VALIDATION];
  for (let i = 0; i < 12; i++) many.push(res("TYPE-CHECK", "warning", `f${i}.xaml`, `issue ${i}`));
  const out = run(write(log(many))).stdout;
  assert.match(out, /… 7 more files/);
  assert.match(out, /Full list: rerun/);
  const few = run(write(log([VALIDATION, res("TYPE-CHECK", "warning", "one.xaml", "single issue")]))).stdout;
  assert.match(few, /- one\.xaml — TYPE-CHECK: single issue/);
  assert.doesNotMatch(few, /Full list/);
});

test("ignored restore issues and activity-scoped errors are attention items, not blockers", () => {
  const s = json(
    log([
      VALIDATION,
      res("RESTORE-MISSING-PACKAGE", "warning", "", "ignored missing"),
      res("UIAUTOMATION-ACTIVITY-MIGRATION-ERROR-X", "error", "z.xaml", "activity scoped"),
    ]),
  );
  assert.equal(s.status, "partial");
  assert.equal(s.blockers.length, 0);
  assert.equal(s.typeIssues.length, 1);
  assert.equal(s.typeIssues[0].rule, "RESTORE-MISSING-PACKAGE");
  assert.equal(s.uia.notMigrated.length, 1);
});
