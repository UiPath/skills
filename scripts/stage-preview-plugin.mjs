#!/usr/bin/env node

import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const replacements = [
  'uipath-maestro-flow',
  'uipath-maestro-case',
  'uipath-maestro-bpmn',
];
const pluginSupportDirectories = ['commands', 'hooks'];

function fail(message) {
  throw new Error(message);
}

function parseArgs(argv) {
  const args = { source: path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..') };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    if (flag === '--source' || flag === '--output') {
      const value = argv[index + 1];
      if (!value || value.startsWith('--')) fail(`${flag} requires a path`);
      args[flag.slice(2)] = path.resolve(value);
      index += 1;
    } else {
      fail(`Unknown argument: ${flag}`);
    }
  }
  if (!args.output) fail('Usage: stage-preview-plugin.mjs --output <empty-directory> [--source <skills-repo>]');
  return args;
}

function git(source, args) {
  return execFileSync('git', ['-C', source, ...args], { encoding: 'utf8' }).trim();
}

function assertCleanPluginInputs(source) {
  const status = git(source, [
    'status',
    '--porcelain',
    '--untracked-files=all',
    '--',
    '.claude-plugin',
    'commands',
    'hooks',
    'skills',
    'preview',
  ]);
  if (status) {
    fail(`Plugin inputs must match HEAD before staging:\n${status}`);
  }
}

function provenancePin(skillPath) {
  const text = fs.readFileSync(skillPath, 'utf8');
  const matches = [...text.matchAll(/`typescript\/sdk\/skill\/[^`]+` @ ([0-9a-f]{7,40})\./g)];
  if (matches.length !== 1) fail(`${skillPath} must contain exactly one upstream provenance pin`);
  return matches[0][1];
}

function copyDirectory(source, target) {
  fs.cpSync(source, target, { recursive: true, errorOnExist: true, force: false });
}

function main() {
  const { source, output } = parseArgs(process.argv.slice(2));
  const pluginManifest = path.join(source, '.claude-plugin', 'plugin.json');
  if (!fs.existsSync(pluginManifest) || !fs.statSync(pluginManifest).isFile()) {
    fail(`Missing plugin manifest: ${pluginManifest}`);
  }

  if (fs.existsSync(output) && fs.readdirSync(output).length > 0) {
    fail(`Output directory must be empty: ${output}`);
  }
  assertCleanPluginInputs(source);
  fs.mkdirSync(output, { recursive: true });

  const sourceCommit = git(source, ['rev-parse', 'HEAD']);
  const pins = replacements.map((name) => provenancePin(path.join(source, 'preview', name, 'SKILL.md')));
  if (new Set(pins).size !== 1) fail(`Preview provenance pins disagree: ${pins.join(', ')}`);

  copyDirectory(path.join(source, '.claude-plugin'), path.join(output, '.claude-plugin'));
  for (const name of pluginSupportDirectories) {
    const sourceDirectory = path.join(source, name);
    if (fs.existsSync(sourceDirectory)) copyDirectory(sourceDirectory, path.join(output, name));
  }
  fs.mkdirSync(path.join(output, 'skills'), { recursive: true });

  for (const entry of fs.readdirSync(path.join(source, 'skills'), { withFileTypes: true })) {
    if (replacements.includes(entry.name)) continue;
    const sourceEntry = path.join(source, 'skills', entry.name);
    const targetEntry = path.join(output, 'skills', entry.name);
    if (entry.isDirectory()) copyDirectory(sourceEntry, targetEntry);
    else if (entry.isFile()) fs.copyFileSync(sourceEntry, targetEntry, fs.constants.COPYFILE_EXCL);
  }

  for (const name of replacements) {
    copyDirectory(path.join(source, 'preview', name), path.join(output, 'skills', name));
  }

  const record = {
    schema_version: 1,
    source_commit: sourceCommit,
    preview_upstream_commit: pins[0],
    replacements: replacements.map((name) => ({
      target: `skills/${name}`,
      source: `preview/${name}`,
    })),
  };
  fs.writeFileSync(path.join(output, '.preview-source.json'), `${JSON.stringify(record, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify(record)}\n`);
}

main();
