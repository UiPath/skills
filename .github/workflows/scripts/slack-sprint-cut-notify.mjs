// Posts the sprint-cut announcement to Slack (chat.postMessage; mirrors
// UiPath/cli). Driven by the real step outcomes passed in as env vars, so the
// message reflects what actually happened. Emojis match Studio's Sprint Release
// Bot (#dev-studio-robot): :checkbox_ticked: succeeded · :warning: failed/skipped.

import { postMessage, requireEnv } from "./slack.mjs";

const token = requireEnv("SLACK_BOT_TOKEN");
const channel = requireEnv("CHANNEL_ID");
const repo = process.env.REPO_URL || "https://github.com/UiPath/skills";
const runUrl = process.env.RUN_ID ? `${repo}/actions/runs/${process.env.RUN_ID}` : repo;

const line = requireEnv("CUT_LINE");                 // e.g. 1.199
const version = `${line}.0`;                          // 1.199.0
const nextVersion = `${requireEnv("NEXT_LINE")}.0`;  // 1.200.0

const rehearsal = process.env.REHEARSAL === "true";
const branch = process.env.BRANCH || `release/v${line}`;
const preflightFailed = process.env.PREFLIGHT_OUTCOME === "failure";
const cutOk = process.env.CUT_OUTCOME === "success";
const publishOk = process.env.PUBLISH_OUTCOME === "success";
const bumpOk = process.env.BUMP_OUTCOME === "success";
const bumpUrl = process.env.BUMP_URL || "";

const branchUrl = `${repo}/tree/${branch}`;
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
// A rehearsal branch is deleted at the end of the run, so don't link it.
let branchLine;
if (cutOk) {
  branchLine = rehearsal
    ? `${OK} Branch \`${branch}\` cut from \`main\` (version \`${version}\`; deleted after the run)`
    : `${OK} Release branch \`${branch}\` cut from \`main\` (version \`${version}\`, <${branchUrl}|view branch>)`;
} else if (preflightFailed) {
  branchLine = `${WARN} Preflight FAILED — a ruleset would reject creating \`release/v${line}\` (<${runUrl}|see logs>)`;
} else {
  branchLine = `${WARN} Branch \`${branch}\` cut from \`main\` FAILED (<${runUrl}|see logs>)`;
}

// Package publication line. The publish step covers both dispatched workflow
// runs; the isolated Studio Web jobs run only when custom publishing is enabled.
let previewLine;
if (publishOk && rehearsal) {
  previewLine = `${OK} Dev build published to GitHub Packages from \`${branch}\` (preview to npmjs is skipped in a rehearsal)`;
} else if (publishOk) {
  previewLine = `${OK} Default preview published to npmjs — ${previewLabel} (<${npmUrl}|view on npmjs>); default dev published to GitHub Packages; Studio Web dev/preview published there when custom publishing was enabled`;
} else if (!cutOk) {
  previewLine = `${WARN} Dev/preview package publishing skipped`;
} else {
  previewLine = `${WARN} A dev/preview publish FAILED (Studio Web only runs when custom publishing is enabled) — ${previewLabel} (<${runUrl}|see logs>)`;
}

// Version-bump PR line
let bumpLine;
if (bumpOk && bumpUrl && rehearsal) {
  bumpLine = `${OK} Draft bump PR \`main\` → \`${nextVersion}\` opened and closed (<${bumpUrl}|PR>)`;
} else if (bumpOk && bumpUrl) {
  bumpLine = publishOk
    ? `${OK} Version-bump PR opened: \`main\` → \`${nextVersion}\` (<${bumpUrl}|PR>)`
    : `${OK} Version-bump PR opened anyway: \`main\` → \`${nextVersion}\` (<${bumpUrl}|PR>) — ${WARN} verify the failed publish before merging`;
} else if (bumpOk && !bumpUrl) {
  bumpLine = `${OK} \`main\` already on \`${nextVersion}\` — no bump PR needed`;
} else {
  bumpLine = `${WARN} Version-bump PR not opened — \`main\` stays on \`${version}\``;
}

const overall = cutOk && publishOk && bumpOk ? OK : WARN;
const title = rehearsal
  ? `${overall} :test_tube: *REHEARSAL — sprint release cut \`${line}\`* (nothing real was cut or published to npmjs)`
  : `${overall} *Sprint release cut — \`${line}\`*`;
const text = [
  title,
  branchLine,
  previewLine,
  bumpLine,
].join("\n");

const data = await postMessage(token, { channel, text });
console.log(`Posted sprint-cut announcement to ${channel} (ts=${data.ts}).`);
