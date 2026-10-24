// Bumps our external-plugin entry in a checkout of github/awesome-copilot to a
// new stable release. Upstream keeps the entry in two files — the source list
// plugins/external.json and the generated .github/plugin/marketplace.json —
// and maintainers merge bump PRs that edit both (e.g. github/awesome-copilot#2011).
// Only version, source.ref and source.sha change; every other field stays as
// the maintainers approved it.

import { existsSync } from "node:fs";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const SHA_PATTERN = /^[0-9a-f]{40}$/;

function requireEnv(name) {
  const v = process.env[name];
  if (!v) throw new Error(`Missing ${name} environment variable.`);
  return v;
}

/**
 * Returns `plugins` with the entry named `name` pointed at `tag`/`sha`.
 * Throws when the entry is missing or is not a GitHub-sourced listing, so a
 * renamed or delisted entry fails loudly instead of opening an empty PR.
 */
export function bumpEntry(plugins, { name, version, tag, sha }) {
  if (!SHA_PATTERN.test(sha)) throw new Error(`Expected a 40-character commit SHA, got "${sha}".`);
  const index = plugins.findIndex((plugin) => plugin.name === name);
  if (index === -1) throw new Error(`No awesome-copilot entry named "${name}".`);
  const entry = plugins[index];
  if (entry.source?.source !== "github") {
    throw new Error(`Entry "${name}" has source "${entry.source?.source}", expected "github".`);
  }
  const bumped = plugins.slice();
  bumped[index] = { ...entry, version, source: { ...entry.source, ref: tag, sha } };
  return bumped;
}

async function bumpFile(file, listOf, wrap, target) {
  const text = await readFile(file, "utf8");
  const json = JSON.parse(text);
  const updated = wrap(json, bumpEntry(listOf(json), target));
  await writeFile(file, `${JSON.stringify(updated, null, 2)}${text.endsWith("\n") ? "\n" : ""}`);
  console.log(`Bumped ${target.name} to ${target.version} (${target.sha}) in ${file}.`);
}

async function main() {
  const checkout = requireEnv("CHECKOUT_DIR");
  const target = {
    name: requireEnv("PLUGIN_NAME"),
    version: requireEnv("VERSION"),
    tag: requireEnv("TAG"),
    sha: requireEnv("SHA"),
  };

  await bumpFile(
    path.join(checkout, "plugins", "external.json"),
    (json) => json,
    (_json, plugins) => plugins,
    target,
  );

  // Generated from external.json upstream; edit it too when it lists us so
  // the PR matches what their generator would produce.
  const marketplace = path.join(checkout, ".github", "plugin", "marketplace.json");
  if (existsSync(marketplace)) {
    const { plugins = [] } = JSON.parse(await readFile(marketplace, "utf8"));
    if (plugins.some((plugin) => plugin.name === target.name)) {
      await bumpFile(marketplace, (json) => json.plugins, (json, bumped) => ({ ...json, plugins: bumped }), target);
    }
  }
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
