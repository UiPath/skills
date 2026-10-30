// Renders the follow-up issue opened after a stable release reaches the
// coding-agent marketplaces. Each listed catalog is one a pipeline cannot
// finish on its own: OpenAI has no upload API, Cursor reviews every update by
// hand, the Anthropic Directory may hold a version for review, and an
// awesome-copilot bump PR waits for a maintainer merge. The issue keeps those
// steps from being forgotten between sprints.

import { appendFile, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

/**
 * Builds the issue `{ title, body }` for stable `version`.
 * `copilot` is the awesome-copilot job outcome: `{ result, prUrl }`, where
 * `result` is a GitHub Actions job result (`success`, `failure`, `skipped`, …).
 */
export function buildChecklist({ version, releaseUrl, zipName, runUrl, copilot }) {
  const items = [
    `- [ ] **OpenAI / Codex directory:** download \`${zipName}\` from the [release](${releaseUrl}), upload it at https://platform.openai.com/plugins and publish the approved version. Only one review can be active per plugin — if the previous one is still open, skip this release.`,
    `- [ ] **Cursor Marketplace:** request a re-index at https://cursor.com/marketplace/publish. Every update is reviewed by hand; aim for about one update a month.`,
    `- [ ] **Anthropic Directory:** confirm v${version} was picked up and passed review at https://claude.ai/directory/manage.`,
  ];
  if (copilot.result === "success" && copilot.prUrl) {
    items.push(`- [ ] **awesome-copilot:** follow ${copilot.prUrl} until a maintainer merges it.`);
  } else if (copilot.result === "failure" || copilot.result === "cancelled") {
    items.push(`- [ ] **awesome-copilot:** the bump PR was not opened (job ${copilot.result}); see the [workflow run](${runUrl}).`);
  }

  return {
    title: `Marketplace follow-ups for v${version}`,
    body: [
      `Stable \`@uipath/skills@${version}\` was released as ${releaseUrl}. The steps below are manual.`,
      "",
      ...items,
      "",
      `_Opened by the [marketplace publish run](${runUrl}). See docs/RELEASE.md § Publishing to coding-agent marketplaces._`,
    ].join("\n"),
  };
}

function requireEnv(name) {
  const v = process.env[name];
  if (!v) throw new Error(`Missing ${name} environment variable.`);
  return v;
}

async function main() {
  const { title, body } = buildChecklist({
    version: requireEnv("VERSION"),
    releaseUrl: requireEnv("RELEASE_URL"),
    zipName: requireEnv("ZIP_NAME"),
    runUrl: requireEnv("RUN_URL"),
    copilot: { result: process.env.COPILOT_RESULT || "skipped", prUrl: process.env.COPILOT_PR_URL || "" },
  });
  await writeFile(requireEnv("BODY_FILE"), `${body}\n`);
  await appendFile(requireEnv("GITHUB_OUTPUT"), `title=${title}\n`);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
