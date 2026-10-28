import { test } from "node:test";
import assert from "node:assert/strict";
import { buildAnnouncement } from "../../.github/workflows/scripts/slack-stable-publish-notify.mjs";

const skillStatus = {
  skills: {
    "uipath-rpa": { status: "stable" },
    "uipath-admin": { status: "stable" },
    "uipath-test": { status: "preview" },
    "uipath-maestro-bpmn": { status: "in-development" },
  },
};
const input = {
  version: "1.202.0",
  ref: "release/v1.202",
  runUrl: "https://github.com/UiPath/skills/actions/runs/1",
  skillStatus,
};

test("served publish: headline counts skills per status and links the exact npm version", () => {
  const { text, thread } = buildAnnouncement({ ...input, served: true });
  assert.match(text, /^:package: Published to npm \(stable\) — `@uipath\/skills@1\.202\.0`$/m);
  assert.match(text, /^4 skills {2}· {2}2 stable {2}· {2}1 preview {2}· {2}1 in development$/m);
  assert.ok(text.includes("<https://www.npmjs.com/package/@uipath/skills/v/1.202.0|View on npmjs>"));
  assert.ok(text.includes("<https://github.com/UiPath/skills/actions/runs/1|workflow run>"));
  assert.ok(text.includes("From `release/v1.202`"));
  assert.equal(
    thread,
    "*Stable (2)*\n`uipath-admin`, `uipath-rpa`\n\n*Preview (1)*\n`uipath-test`\n\n*In development (1)*\n`uipath-maestro-bpmn`",
  );
});

test("served publish: statuses with no skills are omitted from the thread", () => {
  const { thread } = buildAnnouncement({
    ...input,
    served: true,
    skillStatus: { skills: { "uipath-rpa": { status: "stable" } } },
  });
  assert.equal(thread, "*Stable (1)*\n`uipath-rpa`");
});

test("unserved publish: warns with the run link and posts no thread", () => {
  const { text, thread } = buildAnnouncement({ ...input, served: false });
  assert.match(text, /^:warning: \*Stable publish of `@uipath\/skills@1\.202\.0` has not landed on npmjs\*$/m);
  assert.ok(text.includes("<https://github.com/UiPath/skills/actions/runs/1|see logs>"));
  assert.equal(thread, null);
});
