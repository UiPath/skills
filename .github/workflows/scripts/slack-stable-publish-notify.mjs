// Posts the stable-publish announcement to #team-coding-agents as Skills Buddy,
// mirroring UiPath/cli's "Published to npm (stable)" post: a short headline in
// the channel and the full skill list in the thread. Driven by the outcome of
// wait-npmjs-version.mjs so the message never claims more than npmjs serves.

import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import { postMessage, requireEnv } from "./slack.mjs";

const STATUSES = [
  { key: "stable", label: "Stable" },
  { key: "preview", label: "Preview" },
  { key: "in-development", label: "In development" },
];

/**
 * Builds the channel headline and the thread reply for a stable publish.
 * `skillStatus` is the parsed assets/skill-status.json of the published line.
 * Returns `{ text, thread }`; `thread` is null when the version is not served.
 */
export function buildAnnouncement({ version, ref, runUrl, served, skillStatus }) {
  const pkg = `\`@uipath/skills@${version}\``;
  const npmUrl = `https://www.npmjs.com/package/@uipath/skills/v/${version}`;

  if (!served) {
    return {
      text: [
        `:warning: *Stable publish of ${pkg} has not landed on npmjs*`,
        `The registry accepted the publish but is not serving the version yet (<${runUrl}|see logs>). Check <${npmUrl}|npmjs> before announcing.`,
      ].join("\n"),
      thread: null,
    };
  }

  const groups = STATUSES.map(({ key, label }) => ({
    label,
    skills: Object.entries(skillStatus.skills)
      .filter(([, entry]) => entry.status === key)
      .map(([name]) => name)
      .sort(),
  }));
  const total = groups.reduce((n, g) => n + g.skills.length, 0);
  const counts = groups.map((g) => `${g.skills.length} ${g.label.toLowerCase()}`).join("  ·  ");

  return {
    text: [
      `:package: Published to npm (stable) — ${pkg}`,
      `${total} skills  ·  ${counts}`,
      `_From \`${ref}\`. <${npmUrl}|View on npmjs> · <${runUrl}|workflow run>. Skill list in the thread._`,
    ].join("\n"),
    thread: groups
      .filter((g) => g.skills.length > 0)
      .map((g) => `*${g.label} (${g.skills.length})*\n${g.skills.map((s) => `\`${s}\``).join(", ")}`)
      .join("\n\n"),
  };
}

async function main() {
  const token = requireEnv("SLACK_BOT_TOKEN");
  const channel = requireEnv("CHANNEL_ID");
  const statusFile = process.env.STATUS_FILE || "assets/skill-status.json";

  const { text, thread } = buildAnnouncement({
    version: requireEnv("VERSION"),
    ref: requireEnv("PUBLISH_REF"),
    runUrl: requireEnv("RUN_URL"),
    served: process.env.SERVED === "true",
    skillStatus: JSON.parse(await readFile(statusFile, "utf8")),
  });

  const parent = await postMessage(token, { channel, text });
  if (thread) await postMessage(token, { channel, text: thread, thread_ts: parent.ts });
  console.log(`Posted stable-publish announcement to ${channel} (ts=${parent.ts}).`);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
