// Posts the sprint-cut announcement to Slack (chat.postMessage; mirrors
// UiPath/cli). Driven by the real step outcomes passed in as env vars, so the
// message reflects what actually happened. Emojis match Studio's Sprint Release
// Bot (#dev-studio-robot): :checkbox_ticked: succeeded · :warning: failed/skipped.

const SLACK_URL = "https://slack.com/api/chat.postMessage";

const token = requireEnv("SLACK_BOT_TOKEN");
const channel = requireEnv("CHANNEL_ID");
const repo = process.env.REPO_URL || "https://github.com/UiPath/skills";
const runUrl = process.env.RUN_ID ? `${repo}/actions/runs/${process.env.RUN_ID}` : repo;

const line = requireEnv("CUT_LINE");                 // e.g. 1.199
const version = `${line}.0`;                          // 1.199.0
const nextVersion = `${requireEnv("NEXT_LINE")}.0`;  // 1.200.0

const cutOk = process.env.CUT_OUTCOME === "success";
const publishOk = process.env.PUBLISH_OUTCOME === "success";
const bumpOk = process.env.BUMP_OUTCOME === "success";
const bumpUrl = process.env.BUMP_URL || "";

const branchUrl = `${repo}/tree/release/v${line}`;
// Exact preview version is stamped by publish.yml (<version>-preview.<run>).
// If we have it, link the precise npmjs version; else fall back to versions tab.
const previewVersion = process.env.PREVIEW_VERSION || "";
const npmUrl = previewVersion
  ? `https://www.npmjs.com/package/@uipath/skills/v/${previewVersion}`
  : "https://www.npmjs.com/package/@uipath/skills?activeTab=versions";
const previewLabel = previewVersion
  ? `\`@uipath/skills@${previewVersion}\``
  : `\`@uipath/skills@${version}-preview\``;

const OK = ":checkbox_ticked:";
const WARN = ":warning:";

// Branch line
const branchLine = cutOk
  ? `${OK} Release branch \`release/v${line}\` cut from \`main\` (version \`${version}\`, <${branchUrl}|view branch>)`
  : `${WARN} Release branch \`release/v${line}\` cut from \`main\` FAILED (<${runUrl}|see logs>)`;

// Preview package line
let previewLine;
if (publishOk) {
  previewLine = `${OK} Preview package published to npmjs — ${previewLabel} (<${npmUrl}|view on npmjs>)`;
} else if (!cutOk) {
  previewLine = `${WARN} Preview package publish skipped`;
} else {
  previewLine = `${WARN} Preview package publish to npmjs FAILED — ${previewLabel} (<${runUrl}|see logs>)`;
}

// Version-bump PR line
let bumpLine;
if (bumpOk && bumpUrl) {
  bumpLine = publishOk
    ? `${OK} Version-bump PR opened: \`main\` → \`${nextVersion}\` (<${bumpUrl}|PR>)`
    : `${OK} Version-bump PR opened anyway: \`main\` → \`${nextVersion}\` (<${bumpUrl}|PR>) — ${WARN} verify the failed publish before merging`;
} else if (bumpOk && !bumpUrl) {
  bumpLine = `${OK} \`main\` already on \`${nextVersion}\` — no bump PR needed`;
} else {
  bumpLine = `${WARN} Version-bump PR not opened — \`main\` stays on \`${version}\``;
}

const overall = cutOk && publishOk ? OK : WARN;
const text = [
  `${overall} *Sprint release cut — \`${line}\`*`,
  branchLine,
  previewLine,
  bumpLine,
].join("\n");

const res = await fetch(SLACK_URL, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json; charset=utf-8",
  },
  body: JSON.stringify({ channel, text, unfurl_links: false }),
});
const data = await res.json();
// Slack returns HTTP 200 even on logical failure — check the ok field.
if (!res.ok || data.ok !== true) {
  throw new Error(`Slack post failed: ${data.error || `${res.status} ${res.statusText}`}`);
}
console.log(`Posted sprint-cut announcement to ${channel} (ts=${data.ts}).`);

function requireEnv(name) {
  const v = process.env[name];
  if (!v) throw new Error(`Missing ${name} environment variable.`);
  return v;
}
