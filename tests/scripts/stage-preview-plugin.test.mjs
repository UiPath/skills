import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const repository = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const script = path.join(repository, 'scripts', 'stage-preview-plugin.mjs');
const maestroSkills = ['uipath-maestro-flow', 'uipath-maestro-case', 'uipath-maestro-bpmn'];

function write(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content);
}

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'preview-plugin-test-'));
  write(path.join(root, '.claude-plugin', 'plugin.json'), '{"name":"fixture","skills":"./skills/"}\n');
  write(path.join(root, 'commands', 'fixture.md'), 'command\n');
  write(path.join(root, 'hooks', 'hooks.json'), '{"hooks":{}}\n');
  write(path.join(root, 'skills', 'uipath-other', 'SKILL.md'), 'other\n');
  for (const name of maestroSkills) {
    write(path.join(root, 'skills', name, 'SKILL.md'), `live-${name}\n`);
    write(
      path.join(root, 'preview', name, 'SKILL.md'),
      `snapshot-${name}\n\`typescript/sdk/skill/${name}.md\` @ abc1234.\n`,
    );
    write(path.join(root, 'preview', name, 'references', 'guide.md'), `${name}-reference\n`);
  }
  execFileSync('git', ['init', '-q'], { cwd: root });
  execFileSync('git', ['config', 'user.name', 'Fixture'], { cwd: root });
  execFileSync('git', ['config', 'user.email', 'fixture@example.test'], { cwd: root });
  execFileSync('git', ['add', '.'], { cwd: root });
  execFileSync('git', ['commit', '-qm', 'fixture'], { cwd: root });
  return root;
}

test('stages the catalog with all three Maestro skills replaced by preview', () => {
  const source = fixture();
  const output = path.join(source, 'staged');
  execFileSync(process.execPath, [script, '--source', source, '--output', output]);

  assert.equal(fs.readFileSync(path.join(output, 'skills', 'uipath-other', 'SKILL.md'), 'utf8'), 'other\n');
  assert.equal(fs.readFileSync(path.join(output, 'commands', 'fixture.md'), 'utf8'), 'command\n');
  assert.equal(fs.readFileSync(path.join(output, 'hooks', 'hooks.json'), 'utf8'), '{"hooks":{}}\n');
  for (const name of maestroSkills) {
    const skill = fs.readFileSync(path.join(output, 'skills', name, 'SKILL.md'), 'utf8');
    assert.match(skill, new RegExp(`^snapshot-${name}`));
    assert.doesNotMatch(skill, new RegExp(`live-${name}`));
    assert.equal(
      fs.readFileSync(path.join(output, 'skills', name, 'references', 'guide.md'), 'utf8'),
      `${name}-reference\n`,
    );
  }

  const record = JSON.parse(fs.readFileSync(path.join(output, '.preview-source.json'), 'utf8'));
  assert.match(record.source_commit, /^[0-9a-f]{40}$/);
  assert.equal(record.preview_upstream_commit, 'abc1234');
  assert.equal(record.replacements.length, 3);
});

test('refuses a non-empty destination instead of overwriting it', () => {
  const source = fixture();
  const output = path.join(source, 'occupied');
  write(path.join(output, 'keep.txt'), 'keep\n');
  const result = spawnSync(process.execPath, [script, '--source', source, '--output', output], { encoding: 'utf8' });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Output directory must be empty/);
  assert.equal(fs.readFileSync(path.join(output, 'keep.txt'), 'utf8'), 'keep\n');
});

test('refuses staged inputs that do not match the recorded commit', () => {
  const source = fixture();
  const output = path.join(source, 'staged');
  write(path.join(source, 'preview', maestroSkills[0], 'SKILL.md'), 'dirty\n');
  const result = spawnSync(
    process.execPath,
    [script, '--source', source, '--output', output],
    { encoding: 'utf8' },
  );
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Plugin inputs must match HEAD/);
  assert.equal(fs.existsSync(output), false);
});

test('preview experiment keeps frozen checkers and tenant auth reachable', () => {
  const experiment = fs.readFileSync(
    path.join(repository, 'tests', 'experiments', 'maestro-flow-sdk.yaml'),
    'utf8',
  );
  const workflow = fs.readFileSync(
    path.join(repository, '.github', 'workflows', 'run-coder-eval.yml'),
    'utf8',
  );
  assert.match(
    experiment,
    /\$\{SKILLS_REPO_HOST_PATH\}:\/skills-repo:ro/,
  );
  assert.match(experiment, /~\/\.uipath:\/\.uipath:rw/);
  assert.match(experiment, /^\s+- PREVIEW_SKILLS_PLUGIN_PATH$/m);
  assert.match(experiment, /^\s+- PYTHONPATH$/m);
  assert.match(workflow, /SKILLS_REPO_PATH:.*'\/skills-repo'/);
  assert.match(workflow, /PYTHONPATH:.*'\/skills-repo\/tests\/tasks\/uipath-maestro-flow'/);
});
