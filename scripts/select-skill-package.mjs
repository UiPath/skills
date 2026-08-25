#!/usr/bin/env node

import { lstatSync, readdirSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import {
  CUSTOM_PACKAGE_PUBLISH_CONFIG,
  containsFlavorMarker,
  readTarballEntries,
} from "./compose-skill-flavor.mjs";

function usage() {
  return (
    "Usage: node scripts/select-skill-package.mjs " +
    "--directory PATH --name PACKAGE --flavor FLAVOR --version VERSION"
  );
}

export function parseArguments(argv) {
  const values = new Map();
  for (let index = 0; index < argv.length; index += 2) {
    const option = argv[index];
    const value = argv[index + 1];
    if (!option?.startsWith("--") || !value || value.startsWith("--")) {
      throw new Error(usage());
    }
    if (values.has(option)) throw new Error(`duplicate option: ${option}`);
    values.set(option, value);
  }

  const allowed = new Set(["--directory", "--name", "--flavor", "--version"]);
  for (const option of values.keys()) {
    if (!allowed.has(option)) throw new Error(`unknown option: ${option}`);
  }
  for (const option of allowed) {
    if (!values.has(option)) throw new Error(`missing required option: ${option}`);
  }

  return {
    directory: path.resolve(values.get("--directory")),
    packageName: values.get("--name"),
    flavor: values.get("--flavor"),
    version: values.get("--version"),
  };
}

function readManifest(entries, tarball) {
  const bytes = entries.get("package/package.json");
  if (!bytes) throw new Error(`npm tarball has no package.json: ${tarball}`);
  try {
    return JSON.parse(bytes.toString("utf8"));
  } catch (error) {
    throw new Error(`invalid package.json in ${tarball}: ${error.message}`);
  }
}

function assertMarkerFree(entries, tarball) {
  let skillFileCount = 0;
  for (const [name, bytes] of entries) {
    if (name.startsWith("package/skills/") && bytes.length > 0) skillFileCount += 1;
    if (containsFlavorMarker(bytes)) {
      throw new Error(`flavor marker leaked into selected npm tarball ${tarball}: ${name}`);
    }
  }
  if (!skillFileCount) throw new Error(`selected npm tarball contains no skill files: ${tarball}`);
}

export function selectSkillPackage({ directory, packageName, flavor, version }) {
  const directoryStats = lstatSync(directory, { throwIfNoEntry: false });
  if (!directoryStats?.isDirectory() || directoryStats.isSymbolicLink()) {
    throw new Error(`package directory is not a real directory: ${directory}`);
  }

  const tarballs = readdirSync(directory)
    .filter((name) => name.endsWith(".tgz"))
    .sort()
    .map((name) => path.join(directory, name));
  if (!tarballs.length) throw new Error(`no npm tarballs found in ${directory}`);

  const matches = [];
  for (const tarball of tarballs) {
    const stats = lstatSync(tarball);
    if (!stats.isFile() || stats.isSymbolicLink()) {
      throw new Error(`npm tarball is not a regular file: ${tarball}`);
    }
    const entries = readTarballEntries(tarball);
    const manifest = readManifest(entries, tarball);
    if (manifest.name !== packageName || manifest.uipathSkillsFlavor !== flavor) continue;
    if (flavor !== "default") {
      const actualPublishConfig = manifest.publishConfig;
      const hasExactPublishConfig =
        actualPublishConfig &&
        typeof actualPublishConfig === "object" &&
        !Array.isArray(actualPublishConfig) &&
        Object.keys(actualPublishConfig).length ===
          Object.keys(CUSTOM_PACKAGE_PUBLISH_CONFIG).length &&
        Object.entries(CUSTOM_PACKAGE_PUBLISH_CONFIG).every(
          ([key, value]) => actualPublishConfig[key] === value,
        );
      if (!hasExactPublishConfig) {
        throw new Error(
          `selected custom package must use the GitHub Packages-only publish policy: ${tarball}`,
        );
      }
      if (Object.hasOwn(manifest, "repository")) {
        throw new Error(
          `selected custom package must not define package.json repository: ${tarball}`,
        );
      }
    }
    if (manifest.version !== version) {
      throw new Error(
        `selected package version mismatch: expected ${version}, got ${manifest.version} in ${tarball}`,
      );
    }
    assertMarkerFree(entries, tarball);
    matches.push(tarball);
  }

  if (matches.length !== 1) {
    throw new Error(
      `expected exactly one ${packageName} tarball with flavor ${flavor} and version ${version}; ` +
        `found ${matches.length}`,
    );
  }
  return matches[0];
}

export function main(argv = process.argv.slice(2)) {
  try {
    const selected = selectSkillPackage(parseArguments(argv));
    const outputPath = path.relative(process.cwd(), selected) || path.basename(selected);
    if (/[\r\n]/.test(outputPath)) throw new Error("selected package path contains a newline");
    process.stdout.write(`${outputPath}\n`);
    return 0;
  } catch (error) {
    console.error(`ERROR: ${error.message}`);
    return 1;
  }
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  process.exitCode = main();
}
