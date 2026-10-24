// Derives the manifest for the OpenAI plugin directory ZIP from the committed
// .codex-plugin/plugin.json. The directory rejects ZIPs that declare lifecycle
// hooks or app references (https://developers.openai.com/plugins/deploy/submission),
// while the self-hosted Codex marketplace keeps them — so the directory build
// drops those keys instead of the repo carrying a second manifest.

import { readFile, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

export const DIRECTORY_REJECTED_KEYS = ["hooks", "apps"];

/** Returns a copy of `manifest` without the keys the directory rejects. */
export function directoryManifest(manifest) {
  return Object.fromEntries(
    Object.entries(manifest).filter(([key]) => !DIRECTORY_REJECTED_KEYS.includes(key)),
  );
}

async function main() {
  const [source, target] = process.argv.slice(2);
  if (!source || !target) {
    throw new Error("usage: codex-directory-manifest.mjs <source plugin.json> <target plugin.json>");
  }
  const manifest = directoryManifest(JSON.parse(await readFile(source, "utf8")));
  await writeFile(target, `${JSON.stringify(manifest, null, 2)}\n`);
  console.log(`Wrote directory manifest ${manifest.name}@${manifest.version} to ${target}.`);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
