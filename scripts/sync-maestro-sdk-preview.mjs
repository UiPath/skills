#!/usr/bin/env node

import { execFileSync, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const defaultSkillsRoot = path.resolve(scriptDir, '..');
const sourceRoot = 'typescript/sdk';

const skillMappings = [
  {
    source: `${sourceRoot}/skill/SKILL.md`,
    target: 'preview/uipath-maestro-flow/SKILL.md',
  },
  {
    source: `${sourceRoot}/skill/SKILL-case.md`,
    target: 'preview/uipath-maestro-case/SKILL.md',
  },
  {
    source: `${sourceRoot}/skill/SKILL-bpmn.md`,
    target: 'preview/uipath-maestro-bpmn/SKILL.md',
  },
];

const provenanceFiles = [
  ['preview/uipath-maestro-flow/SKILL.md', 'typescript/sdk/skill/SKILL.md'],
  ['preview/uipath-maestro-case/SKILL.md', 'typescript/sdk/skill/SKILL-case.md'],
  ['preview/uipath-maestro-bpmn/SKILL.md', 'typescript/sdk/skill/SKILL-bpmn.md'],
];

const managedDirectories = [
  'preview/uipath-maestro-flow/references',
  'preview/uipath-maestro-flow/examples',
  'preview/uipath-maestro-case/references',
  'preview/uipath-maestro-case/examples',
  'preview/uipath-maestro-bpmn/references',
  'preview/uipath-maestro-bpmn/examples',
];

const oldSiblingParagraph = [
  'The sibling authoring surfaces have their own:',
  '[`references/case-api.md`](references/case-api.md) for `@uipath/flow-sdk/case`',
  'and [`references/bpmn-api.md`](references/bpmn-api.md) for',
  '`@uipath/flow-sdk/bpmn`. Neither is needed to build a Flow.',
].join('\n');

const newSiblingParagraph = [
  'The sibling authoring surfaces have their own skills:',
  '`uipath-maestro-case` for `@uipath/flow-sdk/case` and `uipath-maestro-bpmn`',
  'for `@uipath/flow-sdk/bpmn`. Neither is needed to build a Flow.',
].join('\n');

const oldStagingParagraph = [
  'under `examples/` resolve in the curated staged workspace. This guide is a',
  'staged-context artifact: the published package stores those sources separately,',
  'and the workspace stager exposes them at `./example`.',
].join('\n');

const newStagingParagraph = 'under `examples/` resolve inside this skill folder.';
const bpmnWorkedExample =
  'A worked example is available at `examples/NotifyChannel.bpmn.ts`.';

function fail(message) {
  throw new Error(message);
}

function normalizeRelative(filePath) {
  return filePath.split(path.sep).join('/');
}

function runGit(repository, args, options = {}) {
  try {
    return execFileSync('git', ['-C', repository, ...args], {
      encoding: 'utf8',
      maxBuffer: 64 * 1024 * 1024,
      ...options,
    }).trimEnd();
  } catch (error) {
    const detail = error.stderr?.toString().trim() || error.message;
    fail(`git ${args.join(' ')} failed in ${repository}: ${detail}`);
  }
}

function gitObjectExists(repository, ref, sourcePath) {
  const result = spawnSync(
    'git',
    ['-C', repository, 'cat-file', '-e', `${ref}:${sourcePath}`],
    { encoding: 'utf8' },
  );
  if (result.status === 0) return true;
  if (result.status === 1 || result.status === 128) return false;
  fail(
    `Could not inspect ${sourcePath}@${ref}: ${result.stderr?.trim() || 'unknown git error'}`,
  );
}

function gitShow(repository, ref, sourcePath) {
  if (!gitObjectExists(repository, ref, sourcePath)) return null;
  return execFileSync('git', ['-C', repository, 'show', `${ref}:${sourcePath}`], {
    maxBuffer: 64 * 1024 * 1024,
  });
}

function gitFiles(repository, ref, sourceDirectory) {
  if (!gitObjectExists(repository, ref, sourceDirectory)) return [];
  const output = runGit(repository, [
    'ls-tree',
    '-r',
    '--name-only',
    ref,
    '--',
    sourceDirectory,
  ]);
  return output ? output.split('\n') : [];
}

function walkFiles(directory) {
  if (!fs.existsSync(directory)) return [];
  const files = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...walkFiles(entryPath));
    } else if (entry.isFile()) {
      files.push(entryPath);
    }
  }
  return files;
}

function readText(filePath) {
  return fs.readFileSync(filePath, 'utf8');
}

function writeIfChanged(filePath, content) {
  const buffer = Buffer.isBuffer(content) ? content : Buffer.from(content);
  if (fs.existsSync(filePath) && fs.readFileSync(filePath).equals(buffer)) return false;
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, buffer);
  return true;
}

function provenancePin(skillsRoot) {
  const pins = provenanceFiles.map(([target, source]) => {
    const text = readText(path.join(skillsRoot, target));
    const escapedSource = source.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const matches = [...text.matchAll(new RegExp(`\`${escapedSource}\` @ ([0-9a-f]{7,40})\\.`, 'g'))];
    if (matches.length !== 1) {
      fail(`${target} must contain exactly one provenance pin for ${source}`);
    }
    return matches[0][1];
  });
  if (new Set(pins).size !== 1) {
    fail(`Maestro preview provenance pins disagree: ${pins.join(', ')}`);
  }
  return pins[0];
}

function collectMappings(upstreamRoot, refs) {
  const mappings = new Map(skillMappings.map((mapping) => [mapping.target, mapping]));
  const add = (source, target) => {
    const existing = mappings.get(target);
    if (existing && existing.source !== source) {
      fail(`Two upstream files map to ${target}: ${existing.source} and ${source}`);
    }
    mappings.set(target, { source, target });
  };

  for (const ref of refs) {
    const referencesRoot = `${sourceRoot}/skill/references`;
    for (const source of gitFiles(upstreamRoot, ref, referencesRoot)) {
      const name = path.posix.basename(source);
      if (!source.endsWith('.md') || ['case-api.md', 'bpmn-api.md'].includes(name)) continue;
      const relative = path.posix.relative(referencesRoot, source);
      add(source, `preview/uipath-maestro-flow/references/${relative}`);
    }

    const flowExamplesRoot = `${sourceRoot}/example-eval`;
    for (const source of gitFiles(upstreamRoot, ref, flowExamplesRoot)) {
      const relative = path.posix.relative(flowExamplesRoot, source);
      add(source, `preview/uipath-maestro-flow/examples/${relative}`);
    }

    const sharedExamplesRoot = `${sourceRoot}/example`;
    for (const source of gitFiles(upstreamRoot, ref, sharedExamplesRoot)) {
      const name = path.posix.basename(source);
      const relative = path.posix.relative(sharedExamplesRoot, source);
      if (name.endsWith('.case.ts')) {
        add(source, `preview/uipath-maestro-case/examples/${relative}`);
      } else if (relative === 'case-bindings.json') {
        add(source, 'preview/uipath-maestro-case/examples/bindings.json');
      } else if (name.endsWith('.bpmn.ts')) {
        add(source, `preview/uipath-maestro-bpmn/examples/${relative}`);
      }
    }
  }

  add(
    `${sourceRoot}/skill/references/case-api.md`,
    'preview/uipath-maestro-case/references/api.md',
  );
  add(
    `${sourceRoot}/skill/references/bpmn-api.md`,
    'preview/uipath-maestro-bpmn/references/api.md',
  );
  return [...mappings.values()].sort((left, right) => left.target.localeCompare(right.target));
}

function assertManagedInventory(skillsRoot, mappings, label) {
  const expected = new Set(mappings.map(({ target }) => target));
  for (const relativeDirectory of managedDirectories) {
    const absoluteDirectory = path.join(skillsRoot, relativeDirectory);
    for (const absoluteFile of walkFiles(absoluteDirectory)) {
      const relativeFile = normalizeRelative(path.relative(skillsRoot, absoluteFile));
      if (!expected.has(relativeFile)) {
        fail(`${label}: unmanaged file in snapshot surface: ${relativeFile}`);
      }
    }
  }
}

function mergeBuffers(ours, base, theirs, labels) {
  const temporaryRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'maestro-preview-sync-'));
  const oursPath = path.join(temporaryRoot, 'ours');
  const basePath = path.join(temporaryRoot, 'base');
  const theirsPath = path.join(temporaryRoot, 'theirs');
  try {
    fs.writeFileSync(oursPath, ours);
    fs.writeFileSync(basePath, base);
    fs.writeFileSync(theirsPath, theirs);
    const result = spawnSync(
      'git',
      [
        'merge-file',
        '-p',
        '-L',
        labels.ours,
        '-L',
        labels.base,
        '-L',
        labels.theirs,
        oursPath,
        basePath,
        theirsPath,
      ],
      { maxBuffer: 64 * 1024 * 1024 },
    );
    if (result.status === 0) return result.stdout;
    if (result.status === 1) {
      fail(
        `Three-way merge conflict in ${labels.ours}:\n${result.stdout.toString().slice(0, 4000)}`,
      );
    }
    fail(
      `git merge-file failed for ${labels.ours}: ${result.stderr?.toString().trim() || 'unknown error'}`,
    );
  } finally {
    fs.rmSync(temporaryRoot, { recursive: true, force: true });
  }
}

function mergeMapping({ skillsRoot, upstreamRoot, oldPin, newCommit, mapping }) {
  const targetPath = path.join(skillsRoot, mapping.target);
  const base = gitShow(upstreamRoot, oldPin, mapping.source);
  const theirs = gitShow(upstreamRoot, newCommit, mapping.source);
  const ours = fs.existsSync(targetPath) ? fs.readFileSync(targetPath) : null;
  const adapt = snapshotAdaptationFor(mapping.target);
  const snapshotBase = base === null || !adapt
    ? base
    : Buffer.from(adapt(base.toString('utf8')));
  const snapshotTheirs = theirs === null || !adapt
    ? theirs
    : Buffer.from(adapt(theirs.toString('utf8')));

  if (base === null && theirs === null) return false;
  if (base === null) {
    if (ours === null) return writeIfChanged(targetPath, snapshotTheirs);
    if (ours.equals(snapshotTheirs)) return false;
    fail(`Add/add conflict for ${mapping.target} from ${mapping.source}`);
  }
  if (theirs === null) {
    if (ours === null) return false;
    if (!ours.equals(snapshotBase)) {
      fail(`Modify/delete conflict for ${mapping.target} from ${mapping.source}`);
    }
    fs.unlinkSync(targetPath);
    return true;
  }
  if (ours === null) {
    fail(`Snapshot deleted ${mapping.target} while upstream still contains ${mapping.source}`);
  }

  const merged = mergeBuffers(ours, snapshotBase, snapshotTheirs, {
    ours: `${mapping.target} (snapshot)`,
    base: `${mapping.source}@${oldPin}`,
    theirs: `${mapping.source}@${newCommit.slice(0, 7)}`,
  });
  return writeIfChanged(targetPath, merged);
}

function replaceRequired(text, before, after, label) {
  if (text.includes(after)) return text;
  if (!text.includes(before)) fail(`Could not apply ${label}; expected source text is absent`);
  return text.replace(before, after);
}

export function adaptFlowSkill(text) {
  let adapted = text.replaceAll('`example/', '`examples/');
  adapted = replaceRequired(
    adapted,
    oldSiblingParagraph,
    newSiblingParagraph,
    'Flow sibling-skill adaptation',
  );
  adapted = replaceRequired(
    adapted,
    oldStagingParagraph,
    newStagingParagraph,
    'Flow staged-path explanation',
  );
  return adapted;
}

export function adaptCaseSkill(text) {
  return text
    .replaceAll('references/case-api.md', 'references/api.md')
    .replaceAll('example/NotifyOnApproval.case.ts', 'examples/NotifyOnApproval.case.ts')
    .replaceAll('example/case-bindings.json', 'examples/bindings.json');
}

export function adaptBpmnSkill(text) {
  let adapted = text.replaceAll('references/bpmn-api.md', 'references/api.md');
  if (!adapted.includes(bpmnWorkedExample)) {
    adapted = replaceRequired(
      adapted,
      '## Authoring\n\n',
      `## Authoring\n\n${bpmnWorkedExample}\n\n`,
      'BPMN worked-example adaptation',
    );
  }
  return adapted;
}

export function adaptFlowApi(text) {
  return text.replaceAll('Worked example: `example/', 'Worked example: `examples/');
}

export function adaptCaseExample(text) {
  return text.replaceAll('example/case-bindings.json', 'examples/bindings.json');
}

const snapshotAdaptations = new Map([
  ['preview/uipath-maestro-flow/SKILL.md', adaptFlowSkill],
  ['preview/uipath-maestro-case/SKILL.md', adaptCaseSkill],
  ['preview/uipath-maestro-bpmn/SKILL.md', adaptBpmnSkill],
  ['preview/uipath-maestro-flow/references/api.md', adaptFlowApi],
  ['preview/uipath-maestro-case/examples/NotifyOnApproval.case.ts', adaptCaseExample],
]);

function snapshotAdaptationFor(target) {
  return snapshotAdaptations.get(target);
}

function updateProvenance(text, source, newPin, target) {
  const escapedSource = source.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const pattern = new RegExp(`(\`${escapedSource}\` @ )[0-9a-f]{7,40}(\\. Canonical source)`, 'g');
  const matches = [...text.matchAll(pattern)];
  if (matches.length !== 1) {
    fail(`${target} must contain exactly one provenance line for ${source}`);
  }
  return text.replace(pattern, `$1${newPin}$2`);
}

function applyAdaptations(skillsRoot, newPin) {
  let changed = false;
  for (const [target, source] of provenanceFiles) {
    const targetPath = path.join(skillsRoot, target);
    changed = writeIfChanged(
      targetPath,
      updateProvenance(readText(targetPath), source, newPin, target),
    ) || changed;
  }

  for (const [target, adapt] of snapshotAdaptations) {
    const targetPath = path.join(skillsRoot, target);
    if (!fs.existsSync(targetPath)) continue;
    changed = writeIfChanged(targetPath, adapt(readText(targetPath))) || changed;
  }
  return changed;
}

function bodyFromFirstHeading(text, label) {
  const heading = text.indexOf('# ');
  if (heading === -1) fail(`${label} has no top-level heading`);
  return text.slice(heading);
}

function assertEqual(actual, expected, label) {
  if (actual !== expected) fail(`${label} differs outside the approved snapshot adaptations`);
}

function verifySkillBody(skillsRoot, upstreamRoot, newCommit, target, source, adapt) {
  const targetText = readText(path.join(skillsRoot, target));
  const sourceText = gitShow(upstreamRoot, newCommit, source)?.toString('utf8');
  if (sourceText === undefined || sourceText === null) fail(`Missing upstream skill ${source}`);
  assertEqual(
    bodyFromFirstHeading(targetText, target),
    adapt(bodyFromFirstHeading(sourceText, source)),
    target,
  );
}

function verifyExactMappings(skillsRoot, upstreamRoot, newCommit, mappings) {
  const adaptedTargets = new Map([
    ['preview/uipath-maestro-flow/references/api.md', adaptFlowApi],
    ['preview/uipath-maestro-case/examples/NotifyOnApproval.case.ts', adaptCaseExample],
  ]);
  const skillTargets = new Set(skillMappings.map(({ target }) => target));
  for (const mapping of mappings) {
    if (skillTargets.has(mapping.target)) continue;
    const source = gitShow(upstreamRoot, newCommit, mapping.source);
    if (source === null) fail(`Mapped source disappeared at target pin: ${mapping.source}`);
    const transform = adaptedTargets.get(mapping.target);
    const expected = transform ? Buffer.from(transform(source.toString('utf8'))) : source;
    const targetPath = path.join(skillsRoot, mapping.target);
    if (!fs.existsSync(targetPath)) fail(`Missing snapshot file ${mapping.target}`);
    if (!fs.readFileSync(targetPath).equals(expected)) {
      fail(`${mapping.target} differs from ${mapping.source} outside the approved adaptations`);
    }
  }
}

function verifyFrontmatterAndPins(skillsRoot, newPin) {
  for (const skill of ['flow', 'case', 'bpmn']) {
    const target = `preview/uipath-maestro-${skill}/SKILL.md`;
    const text = readText(path.join(skillsRoot, target));
    const frontmatter = text.match(/^---\n([\s\S]*?)\n---\n/);
    if (!frontmatter) fail(`${target} is missing YAML frontmatter`);
    const name = frontmatter[1].match(/^name:\s*(.+)$/m)?.[1];
    const description = frontmatter[1].match(/^description:\s*"([\s\S]*?)"$/m)?.[1];
    assertEqual(name, `uipath-maestro-${skill}`, `${target} frontmatter name`);
    if (!description || description.length >= 1024) {
      fail(`${target} description must contain 1-1023 characters`);
    }
    if (!text.includes(`@ ${newPin}. Canonical source lives there;`)) {
      fail(`${target} does not carry provenance pin ${newPin}`);
    }
  }
}

function verifyDeadLinks(skillsRoot) {
  for (const skill of ['flow', 'case', 'bpmn']) {
    const skillRoot = path.join(skillsRoot, `preview/uipath-maestro-${skill}`);
    const documents = [path.join(skillRoot, 'SKILL.md')];
    documents.push(
      ...walkFiles(path.join(skillRoot, 'references')).filter((file) => file.endsWith('.md')),
    );
    for (const document of documents) {
      const text = readText(document);
      for (const match of text.matchAll(/\]\(([^)]+)\)/g)) {
        const raw = match[1].trim().split(/\s+/)[0].replace(/^<|>$/g, '');
        if (!raw || raw.startsWith('#') || /^[a-z]+:/i.test(raw)) continue;
        const relativeTarget = raw.split('#')[0];
        if (!relativeTarget) continue;
        const resolved = path.resolve(path.dirname(document), decodeURIComponent(relativeTarget));
        if (!fs.existsSync(resolved)) {
          fail(`${normalizeRelative(path.relative(skillsRoot, document))} has dead link ${raw}`);
        }
      }
    }
  }
}

function routerRows(text) {
  const section = text.split('## Supported node types\n')[1]?.split('\n## ')[0];
  if (!section) fail('Flow SKILL.md is missing the Supported node types section');
  return section
    .split('\n')
    .filter(
      (line) =>
        /^\| .* \|$/.test(line) &&
        !line.includes('|---|') &&
        !line.startsWith('| Node or surface'),
    );
}

function verifyRouter(skillsRoot, upstreamRoot, newCommit) {
  const target = readText(path.join(skillsRoot, 'preview/uipath-maestro-flow/SKILL.md'));
  const source = gitShow(upstreamRoot, newCommit, `${sourceRoot}/skill/SKILL.md`).toString('utf8');
  const rows = routerRows(target);
  const sourceRows = routerRows(source);
  if (rows.length !== sourceRows.length) {
    fail(`Flow router has ${rows.length} data rows; upstream has ${sourceRows.length}`);
  }
  for (const row of rows) {
    const reference = row.match(/\]\(references\/([^)]+)\)/)?.[1];
    const example = row.match(/`examples\/([^`]+)`/)?.[1];
    if (!reference || !fs.existsSync(path.join(skillsRoot, 'preview/uipath-maestro-flow/references', reference))) {
      fail(`Flow router row has a missing reference: ${row}`);
    }
    if (!example || !fs.existsSync(path.join(skillsRoot, 'preview/uipath-maestro-flow/examples', example))) {
      fail(`Flow router row has a missing example: ${row}`);
    }
  }
}

function verifyStalePaths(skillsRoot) {
  const flow = readText(path.join(skillsRoot, 'preview/uipath-maestro-flow/SKILL.md'));
  const caseSkill = readText(path.join(skillsRoot, 'preview/uipath-maestro-case/SKILL.md'));
  const bpmn = readText(path.join(skillsRoot, 'preview/uipath-maestro-bpmn/SKILL.md'));
  if (/\bexample\//.test(flow) || /references\/(?:case|bpmn)-api\.md/.test(flow)) {
    fail('Flow SKILL.md contains an upstream-only path');
  }
  if (/case-api|case-bindings|\bexample\//.test(caseSkill)) {
    fail('Case SKILL.md contains an upstream-only path');
  }
  if (/bpmn-api|\bexample\//.test(bpmn)) {
    fail('BPMN SKILL.md contains an upstream-only path');
  }
  for (const file of walkFiles(path.join(skillsRoot, 'preview/uipath-maestro-case/examples'))) {
    if (/case-bindings|\bexample\//.test(readText(file))) {
      fail(`${normalizeRelative(path.relative(skillsRoot, file))} contains an upstream-only path`);
    }
  }

  for (const [target, source] of provenanceFiles) {
    const lines = readText(path.join(skillsRoot, target))
      .split('\n')
      .filter((line) => /SKILL-(?:case|bpmn)\.md/.test(line));
    const expected = /SKILL-(?:case|bpmn)\.md/.test(source) ? [`\`${source}\``] : [];
    if (lines.length !== expected.length || lines.some((line, index) => !line.includes(expected[index]))) {
      fail(`${target} has a stale SKILL-case.md or SKILL-bpmn.md reference`);
    }
  }
}

function verifyConflictMarkers(skillsRoot) {
  const conflictMarker = /^(?:<<<<<<< .+|=======|>>>>>>> .+)$/m;
  for (const relativeDirectory of managedDirectories) {
    for (const file of walkFiles(path.join(skillsRoot, relativeDirectory))) {
      if (conflictMarker.test(readText(file))) {
        fail(`${normalizeRelative(path.relative(skillsRoot, file))} contains merge conflict markers`);
      }
    }
  }
  for (const { target } of skillMappings) {
    if (conflictMarker.test(readText(path.join(skillsRoot, target)))) {
      fail(`${target} contains merge conflict markers`);
    }
  }
}

export function verifySnapshot({ skillsRoot, upstreamRoot, newCommit, newPin, mappings }) {
  const currentMappings = collectMappings(upstreamRoot, [newCommit]);
  assertManagedInventory(skillsRoot, currentMappings, 'post-sync inventory');
  verifyExactMappings(skillsRoot, upstreamRoot, newCommit, currentMappings);
  verifySkillBody(
    skillsRoot,
    upstreamRoot,
    newCommit,
    'preview/uipath-maestro-flow/SKILL.md',
    `${sourceRoot}/skill/SKILL.md`,
    adaptFlowSkill,
  );
  verifySkillBody(
    skillsRoot,
    upstreamRoot,
    newCommit,
    'preview/uipath-maestro-case/SKILL.md',
    `${sourceRoot}/skill/SKILL-case.md`,
    adaptCaseSkill,
  );
  verifySkillBody(
    skillsRoot,
    upstreamRoot,
    newCommit,
    'preview/uipath-maestro-bpmn/SKILL.md',
    `${sourceRoot}/skill/SKILL-bpmn.md`,
    adaptBpmnSkill,
  );
  verifyFrontmatterAndPins(skillsRoot, newPin);
  verifyDeadLinks(skillsRoot);
  verifyRouter(skillsRoot, upstreamRoot, newCommit);
  verifyStalePaths(skillsRoot);
  verifyConflictMarkers(skillsRoot);

  const expectedTargets = new Set(currentMappings.map(({ target }) => target));
  for (const mapping of mappings) {
    if (!expectedTargets.has(mapping.target) && fs.existsSync(path.join(skillsRoot, mapping.target))) {
      fail(`Deleted upstream file remains in snapshot: ${mapping.target}`);
    }
  }
}

export function syncSnapshots({
  skillsRoot = defaultSkillsRoot,
  upstreamRoot,
  ref = 'HEAD',
}) {
  if (!upstreamRoot) fail('--upstream is required');
  const resolvedSkillsRoot = path.resolve(skillsRoot);
  const resolvedUpstreamRoot = path.resolve(upstreamRoot);
  const oldPin = provenancePin(resolvedSkillsRoot);
  const newCommit = runGit(resolvedUpstreamRoot, ['rev-parse', '--verify', `${ref}^{commit}`]);
  const newPin = runGit(resolvedUpstreamRoot, ['rev-parse', '--short=7', newCommit]);
  runGit(resolvedUpstreamRoot, ['cat-file', '-e', `${oldPin}^{commit}`]);

  const mappings = collectMappings(resolvedUpstreamRoot, [oldPin, newCommit]);
  assertManagedInventory(resolvedSkillsRoot, mappings, 'pre-sync inventory');

  let changed = false;
  for (const mapping of mappings) {
    changed = mergeMapping({
      skillsRoot: resolvedSkillsRoot,
      upstreamRoot: resolvedUpstreamRoot,
      oldPin,
      newCommit,
      mapping,
    }) || changed;
  }
  changed = applyAdaptations(resolvedSkillsRoot, newPin) || changed;
  verifySnapshot({
    skillsRoot: resolvedSkillsRoot,
    upstreamRoot: resolvedUpstreamRoot,
    newCommit,
    newPin,
    mappings,
  });

  return { oldPin, newPin, newCommit, changed };
}

function parseArguments(argv) {
  const options = { skillsRoot: defaultSkillsRoot, ref: 'HEAD' };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === '--upstream') options.upstreamRoot = argv[++index];
    else if (argument === '--skills-root') options.skillsRoot = argv[++index];
    else if (argument === '--ref') options.ref = argv[++index];
    else fail(`Unknown argument: ${argument}`);
  }
  return options;
}

function appendGitHubOutputs(result) {
  if (!process.env.GITHUB_OUTPUT) return;
  fs.appendFileSync(
    process.env.GITHUB_OUTPUT,
    [
      `old_pin=${result.oldPin}`,
      `new_pin=${result.newPin}`,
      `changed=${result.changed}`,
      '',
    ].join('\n'),
  );
}

function main() {
  const result = syncSnapshots(parseArguments(process.argv.slice(2)));
  appendGitHubOutputs(result);
  console.log(
    result.changed
      ? `Maestro SDK preview merged ${result.oldPin} -> ${result.newPin}; all snapshot gates passed.`
      : `Maestro SDK preview is current at ${result.newPin}; all snapshot gates passed.`,
  );
}

const invokedAsScript =
  process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;
if (invokedAsScript) main();
