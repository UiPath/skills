// Posts DEMO sprint-cut Slack notifications (mock data) so the team can preview
// how the real biweekly cut notification renders in each outcome. No real cut,
// no publish. Mechanism mirrors UiPath/cli: SLACK_BOT_TOKEN + chat.postMessage.
//
// Emojis match Studio's Sprint Release Bot (#dev-studio-robot):
//   :checkbox_ticked: = succeeded   ·   :warning: = failed / skipped.

import { readFileSync } from "node:fs";

const SLACK_URL = "https://slack.com/api/chat.postMessage";

const token = requireEnv("SLACK_BOT_TOKEN");
const channel = process.env.CHANNEL_ID || process.env.DEFAULT_CHANNEL_ID;
if (!channel) throw new Error("No channel id (CHANNEL_ID / DEFAULT_CHANNEL_ID).");

const repo = process.env.REPO_URL || "https://github.com/UiPath/skills";
const runUrl = process.env.RUN_ID ? `${repo}/actions/runs/${process.env.RUN_ID}` : repo;

// Read the REAL current version from main so the demo shows the line the next
// cut would actually target (main carries M.N.0; the cut branches at M.N.0 and
// main then advances to M.(N+1).0).
const version = JSON.parse(readFileSync("package.json", "utf8")).version; // e.g. 1.199.0
const [major, minor] = version.split(".");
const line = `${major}.${minor}`;                 // 1.199
const nextLine = `${major}.${Number(minor) + 1}`; // 1.200
const nextVersion = `${nextLine}.0`;              // 1.200.0

// Illustrative build/PR identifiers (real runs stamp the run number / PR id).
const run = "18052309";
const previewVer = `${version}-preview.${run}`;   // 1.199.0-preview.18052309
const npmUrl = `https://www.npmjs.com/package/@uipath/skills/v/${previewVer}`;
const prUrl = `${repo}/pull/1234`;

const OK = ":checkbox_ticked:";
const WARN = ":warning:";

const scenarios = [
  {
    title: `${OK} *Sprint release cut — \`${line}\`*  ·  _[DEMO 1/3: success]_`,
    lines: [
      `${OK} Release branch \`release/v${line}\` cut from \`main\` (version \`${version}\`)`,
      `${OK} Preview package published to npmjs — \`@uipath/skills@${previewVer}\` (<${npmUrl}|view on npmjs>)`,
      `${OK} Version-bump PR opened: \`main\` → \`${nextVersion}\` (<${prUrl}|#1234>)`,
    ],
  },
  {
    title: `${WARN} *Sprint release cut — \`${line}\`*  ·  _[DEMO 2/3: preview publish failed]_`,
    lines: [
      `${OK} Release branch \`release/v${line}\` cut from \`main\` (version \`${version}\`)`,
      `${WARN} Preview package publish to npmjs FAILED — \`@uipath/skills@${previewVer}\` (<${runUrl}|see logs>)`,
      `${OK} Version-bump PR opened anyway: \`main\` → \`${nextVersion}\` (<${prUrl}|#1234>) — ${WARN} verify the failed publish before merging`,
    ],
  },
  {
    title: `${WARN} *Sprint release cut — \`${line}\`*  ·  _[DEMO 3/3: branch cut failed]_`,
    lines: [
      `${WARN} Release branch \`release/v${line}\` cut from \`main\` FAILED (<${runUrl}|see logs>)`,
      `${WARN} Preview package publish skipped`,
      `${WARN} Version-bump PR skipped — no branch was cut`,
    ],
  },
];

const banner =
  ":test_tube: *Sprint-cut Slack notification — DEMO previews (mock data, no real cut)*\n" +
  "The threaded replies below show how the biweekly `sprint-release-cut.yml` " +
  "notification will look in each outcome. Emojis: :checkbox_ticked: succeeded · :warning: failed / skipped.";

async function post(text, threadTs) {
  const body = { channel, text, unfurl_links: false };
  if (threadTs) body.thread_ts = threadTs;
  const res = await fetch(SLACK_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json; charset=utf-8",
    },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  // Slack returns HTTP 200 even on logical failure — check the ok field.
  if (!res.ok || data.ok !== true) {
    throw new Error(`Slack post failed: ${data.error || `${res.status} ${res.statusText}`}`);
  }
  return data.ts;
}

const parentTs = await post(banner);
console.log(`Posted banner (ts=${parentTs}).`);
for (const s of scenarios) {
  const text = `${s.title}\n${s.lines.join("\n")}`;
  await post(text, parentTs);
  console.log(`Posted: ${s.title.replace(/[*_`]/g, "")}`);
}
console.log(`Done — 1 banner + ${scenarios.length} scenarios to ${channel}.`);

function requireEnv(name) {
  const v = process.env[name];
  if (!v) throw new Error(`Missing ${name} environment variable.`);
  return v;
}
