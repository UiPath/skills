import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { parseMaintainers } from "../../.github/workflows/scripts/codeowners-check.mjs";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const YML = readFileSync(join(REPO_ROOT, ".github", "workflows", "optimize-skill.yml"), "utf8");
const README = readFileSync(join(REPO_ROOT, "README.md"), "utf8");

/** The steps of the queue job, in order: [{name, uses, text}]. */
function steps() {
  const start = YML.indexOf("\n    steps:\n");
  assert.notEqual(start, -1, "no steps in the queue job");
  return YML.slice(start)
    .split(/\n {6}- /)
    .slice(1)
    .map((text) => ({
      name: (text.match(/^name: (.+)$/m) ?? [])[1]?.trim(),
      uses: (text.match(/^uses: (\S+)/m) ?? [])[1],
      text,
    }));
}
const indexOf = (pred, what) => {
  const i = steps().findIndex(pred);
  assert.notEqual(i, -1, `no step ${what}`);
  return i;
};

// ---- permissions ----

test("the workflow grants nothing by default; only the queue job may mint an OIDC token", () => {
  assert.match(YML, /^permissions: \{\}$/m);
  assert.equal(YML.match(/^\s+id-token: write/gm)?.length, 1);
  assert.match(YML.slice(YML.indexOf("\n  queue:\n")), /^\s+id-token: write/m);
});

test("the checkout does not persist credentials", () => {
  assert.match(YML, /persist-credentials: false/);
});

// ---- ordering: who is asking is settled before any token exists ----

test("'Run from main only' is the first step", () => {
  assert.equal(steps()[0].name, "Run from main only");
});

test("the ownership check runs before anything reads the OIDC request token", () => {
  const own = indexOf((s) => s.name === "Check that you own the skill", "'Check that you own the skill'");
  assert.match(steps()[own].text, /ALSO_ALLOWED: \$\{\{ env\.OPTIMIZER_MAINTAINERS \}\}/);
  const tok = indexOf((s) => s.text.includes("ACTIONS_ID_TOKEN_REQUEST_TOKEN"), "reading ACTIONS_ID_TOKEN_REQUEST_TOKEN");
  assert.ok(own < tok, "the token exchange must come after the ownership check");
});

test("the skill name is validated before the checkout puts it in a sparse pattern", () => {
  const validate = indexOf((s) => s.name === "Validate the run form", "'Validate the run form'");
  const checkout = indexOf((s) => s.uses?.startsWith("actions/checkout@"), "actions/checkout");
  assert.ok(validate < checkout);
  assert.match(steps()[validate].text, /\[\[ "\$SKILL" =~ \^\[a-z0-9\]\[a-z0-9-\]\*\$ \]\]/);
});

// ---- identity: a re-run is checked against whoever re-runs it ----

test("no step or name uses github.actor (a re-run would pass as the original requester)", () => {
  assert.doesNotMatch(YML, /github\.actor\b/);
  assert.match(YML, /^run-name: .*github\.triggering_actor/m);
  const own = steps().find((s) => s.name === "Check that you own the skill");
  const queue = steps().find((s) => s.name === "Queue the ADO pipeline");
  for (const s of [own, queue]) assert.match(s.text, /ACTOR: \$\{\{ github\.triggering_actor \}\}/);
});

// ---- the credential path fails loudly ----

test("the Entra ids are GUID literals, with no placeholder guard left", () => {
  const guid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
  for (const key of ["AZURE_TENANT_ID", "AZURE_CLIENT_ID"]) {
    const m = YML.match(new RegExp(`^  ${key}: (\\S+)`, "m"));
    assert.ok(m && guid.test(m[1]), `${key} is not a GUID literal`);
  }
  assert.doesNotMatch(YML, /\*TODO\*/);
});

test("no token is captured from `curl -f … | jq -r` (curl -f hides the error body)", () => {
  assert.doesNotMatch(YML, /\$\(curl -f[^)]*\|\s*jq -r/);
  assert.doesNotMatch(YML, /curl -f/);
});

test("every ::add-mask:: follows a validated capture (jq -e + an HTTP status check)", () => {
  const queue = steps().find((s) => s.name === "Queue the ADO pipeline").text;
  const lines = queue.split("\n");
  lines.forEach((line, i) => {
    if (!line.includes("::add-mask::")) return;
    const before = lines.slice(Math.max(0, i - 3), i).join("\n");
    assert.match(before, /jq -er/, `unvalidated capture before: ${line.trim()}`);
    assert.match(before, /"\$code" = 200/, `no status check before: ${line.trim()}`);
  });
});

// ---- duplicate-run guards ----

test("an open optimizer PR or an unfinished ADO run for the skill is refused before queuing", () => {
  const pr = indexOf((s) => s.name === "Refuse while an optimizer PR for the skill is open", "the open-PR guard");
  const queue = indexOf((s) => s.name === "Queue the ADO pipeline", "'Queue the ADO pipeline'");
  assert.ok(pr < queue);
  assert.match(YML, /pull-requests: read/);
  const q = steps()[queue].text;
  assert.ok(q.indexOf("statusFilter=inProgress,notStarted") < q.indexOf("/pipelines/$ADO_PIPELINE_ID/runs"));
});

// ---- the ADO contract (owned by optimize-bundle.yml in UiPath/skill-trimming-optimizer) ----

test("the queued template parameters are exactly the pipeline's self-serve set", () => {
  const m = YML.match(/templateParameters: \{([\s\S]*?)\}/);
  assert.ok(m, "no templateParameters in the queue body");
  const keys = [...m[1].matchAll(/(\w+): \$/g)].map((x) => x[1]).sort();
  assert.deepEqual(keys, ["budgetUsd", "effort", "finalGate", "openPR", "optimizeBody", "optimizeDescription", "optimizeReferences", "requestedBy", "skill"]);
  assert.match(YML, /options: \[luna, opus, terra, opus\+terra\]/);
});

// ---- consistency and drift ----

test("OPTIMIZER_MAINTAINERS holds valid GitHub logins", () => {
  const m = YML.match(/^ {2}OPTIMIZER_MAINTAINERS: (.+)$/m);
  assert.ok(m, "no OPTIMIZER_MAINTAINERS");
  const handles = parseMaintainers(m[1].replace(/\s+#.*$/, ""));
  assert.ok(handles.length > 0);
  for (const h of handles) assert.match(h, /^[A-Za-z0-9](-?[A-Za-z0-9])*$/, `${h} is not a GitHub login`);
});

test("the workflow names no Windows skill (the `windows` task tag decides, not a list)", () => {
  for (const skill of ["uipath-rpa", "uipath-activity-migrator"]) {
    assert.ok(!YML.includes(skill), `optimize-skill.yml names ${skill}; say "skills with windows-tagged tasks"`);
  }
});

test("README points skill owners at the workflow", () => {
  assert.match(README, /actions\/workflows\/optimize-skill\.yml/);
});
