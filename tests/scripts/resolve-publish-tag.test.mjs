import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { main, previewTag, resolveChannel } from "../../scripts/resolve-publish-tag.mjs";

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const BASE = JSON.parse(readFileSync(join(REPO_ROOT, "package.json"), "utf8")).version;

test("only release pushes and preview/latest dispatches reach npmjs", () => {
  const push = (ref) => ({ eventName: "push", ref, channel: "" });
  const dispatch = (channel) => ({ eventName: "workflow_dispatch", ref: "refs/heads/main", channel });
  assert.equal(resolveChannel(push("refs/heads/release/v1.207")), "preview");
  assert.equal(resolveChannel(dispatch("preview")), "preview");
  assert.equal(resolveChannel(dispatch("latest")), "latest");
  for (const event of [push("refs/heads/main"), dispatch("dev"), dispatch("")]) {
    assert.throws(() => resolveChannel(event), /not an npmjs publish/);
  }
});

test("only the highest release line takes the bare preview tag", () => {
  assert.equal(previewTag("1.207.0", ""), "preview");
  assert.equal(previewTag("1.207.0", "1.207.0-preview.12"), "preview");
  assert.equal(previewTag("1.207.0", "1.206.0-preview.9"), "preview");
  assert.equal(previewTag("1.207.0", "1.208.0-preview.3"), "preview-v1.207");
  assert.equal(previewTag("1.207.0", "1.207.1-preview.2"), "preview-v1.207");
  // Fails open, as the inline guard did.
  assert.equal(previewTag("1.207.0", "not-a-version"), "preview");
  assert.throws(() => previewTag("1.207.0-preview.1", ""), /not a plain release/);
});

function runMain(t, argv, env, responses = {}) {
  const outputDir = mkdtempSync(join(tmpdir(), "resolve-publish-tag-"));
  t.after(() => rmSync(outputDir, { recursive: true, force: true }));
  const output = join(outputDir, "github-output");
  const calls = [];
  const run = (command, args) => {
    calls.push([command, ...args].join(" "));
    return responses[args[0]] ?? { status: 0, stdout: "", stderr: "" };
  };
  const status = main(argv, { env: { ...env, GITHUB_OUTPUT: output }, run });
  let written = "";
  try {
    written = readFileSync(output, "utf8");
  } catch {}
  return { status, calls, written };
}

test("a preview publish stamps the run version and asks the package's own preview tag", (t) => {
  const { status, calls, written } = runMain(
    t,
    ["@uipath/skills-automation-suite"],
    { EVENT_NAME: "push", PUBLISH_REF: "refs/heads/release/v1.207", RUN_NUMBER: "88" },
    { view: { status: 0, stdout: "99.0.0-preview.1\n", stderr: "" } },
  );
  assert.equal(status, 0);
  assert.equal(calls[0], `npm version ${BASE}-preview.88 --no-git-tag-version --allow-same-version`);
  assert.match(calls[1], /scripts[\\/]sync-version\.mjs$/);
  assert.equal(
    calls[2],
    "npm view @uipath/skills-automation-suite@preview version --@uipath:registry=https://registry.npmjs.org/",
  );
  const [major, minor] = BASE.split(".");
  assert.equal(written, `tag=preview-v${major}.${minor}\n`);
});

test("an unpublished package or unreachable registry keeps preview", (t) => {
  const { status, written } = runMain(
    t,
    ["@uipath/skills-automation-suite"],
    { EVENT_NAME: "workflow_dispatch", CHANNEL: "preview", RUN_NUMBER: "5" },
    { view: { status: 1, stdout: "", stderr: "E404 Not Found" } },
  );
  assert.equal(status, 0);
  assert.equal(written, "tag=preview\n");
});

test("a latest publish keeps the committed version", (t) => {
  const { status, calls, written } = runMain(t, ["@uipath/skills"], {
    EVENT_NAME: "workflow_dispatch",
    CHANNEL: "latest",
  });
  assert.equal(status, 0);
  assert.deepEqual(calls, []);
  assert.equal(written, "tag=latest\n");
});

test("a failed stamp or a bad run number stops the publish", (t) => {
  const failedStamp = runMain(
    t,
    ["@uipath/skills"],
    { EVENT_NAME: "workflow_dispatch", CHANNEL: "preview", RUN_NUMBER: "5" },
    { version: { status: 1, stdout: "", stderr: "EINVALIDVERSION" } },
  );
  assert.equal(failedStamp.status, 1);
  assert.equal(failedStamp.written, "");

  const badRun = runMain(t, ["@uipath/skills"], {
    EVENT_NAME: "workflow_dispatch",
    CHANNEL: "preview",
    RUN_NUMBER: "5; rm -rf /",
  });
  assert.equal(badRun.status, 1);
  assert.deepEqual(badRun.calls, []);

  assert.equal(runMain(t, [], { EVENT_NAME: "workflow_dispatch", CHANNEL: "latest" }).status, 1);
});
