// Names of the files attached to each stable GitHub Release.
//
// Gemini CLI installs a GitHub extension from its latest release and picks the
// asset by name (findReleaseAsset in google-gemini/gemini-cli
// packages/cli/src/config/extensions/github.ts): first `<platform>.<arch>.*`,
// then `<platform>.*`, and otherwise the sole asset when there is exactly one.
// The Gemini archive is therefore uploaded once per platform prefix, so Gemini
// never takes the Codex ZIP, whose name must not contain a platform name.

import { appendFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

export const GEMINI_PLATFORMS = ["darwin", "linux", "win32"];

/** Returns `{ codex, gemini }`: the Codex ZIP name and one Gemini name per platform. */
export function releaseAssetNames(version) {
  return {
    codex: `uipath-codex-plugin-${version}.zip`,
    gemini: GEMINI_PLATFORMS.map((platform) => `${platform}.uipath-gemini-extension-${version}.zip`),
  };
}

async function main() {
  const version = process.env.VERSION;
  if (!version) throw new Error("Missing VERSION environment variable.");
  const { codex, gemini } = releaseAssetNames(version);
  await appendFile(process.env.GITHUB_OUTPUT, `codex=${codex}\ngemini=${gemini.join(" ")}\n`);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
