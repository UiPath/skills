import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import {
  adaptBpmnSkill,
  adaptCaseExample,
  adaptCaseSkill,
  adaptFlowApi,
  adaptFlowSkill,
  syncSnapshots,
} from '../../scripts/sync-maestro-sdk-preview.mjs';

const flowSiblingParagraph = [
  'The sibling authoring surfaces have their own:',
  '[`references/case-api.md`](references/case-api.md) for `@uipath/flow-sdk/case`',
  'and [`references/bpmn-api.md`](references/bpmn-api.md) for',
  '`@uipath/flow-sdk/bpmn`. Neither is needed to build a Flow.',
].join('\n');

const flowStagingParagraph = [
  'under `example/` resolve in the curated staged workspace. This guide is a',
  'staged-context artifact: the published package stores those sources separately,',
  'and the workspace stager exposes them at `./example`.',
].join('\n');

function write(root, relativePath, content) {
  const filePath = path.join(root, relativePath);
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content);
}

function read(root, relativePath) {
  return fs.readFileSync(path.join(root, relativePath), 'utf8');
}

function git(root, ...args) {
  return execFileSync('git', ['-C', root, ...args], { encoding: 'utf8' }).trim();
}

function commit(root, message) {
  git(root, 'add', '--all');
  git(root, 'commit', '-m', message);
  return git(root, 'rev-parse', '--short=7', 'HEAD');
}

function sourceBody(text) {
  return text.slice(text.indexOf('# '));
}

function snapshotHeader(name, source, pin) {
  return [
    '---',
    `name: ${name}`,
    'description: "Fixture description"',
    'allowed-tools: Bash, Read',
    '---',
    '<!--',
    'Provenance: snapshot of UiPath/flow-builder-sdk',
    `\`${source}\` @ ${pin}. Canonical source lives there;`,
    'edit upstream and re-sync (see UiPath/flow-builder-sdk#405).',
    '-->',
    '',
  ].join('\n');
}

function createInitialUpstream(upstreamRoot) {
  git(upstreamRoot, 'init', '-b', 'main');
  git(upstreamRoot, 'config', 'user.name', 'Test');
  git(upstreamRoot, 'config', 'user.email', 'test@example.com');

  write(
    upstreamRoot,
    'typescript/sdk/skill/SKILL.md',
    [
      '<!-- upstream header -->',
      '# Flow fixture',
      '',
      '## Project layout',
      '',
      '`example/Foo.flow.ts` is staged.',
      '',
      flowSiblingParagraph,
      '',
      '## Supported node types',
      '',
      flowStagingParagraph,
      '',
      '| Node or surface | Emitted node type | Builder | Section | Reference | Example |',
      '|---|---|---|---|---|---|',
      '| Script | `core.action.script` | `script()` | [Script](#script) | [api.md](references/api.md) | `example/Foo.flow.ts` |',
      '',
      '## Script',
      '',
      'Fixture.',
      '',
    ].join('\n'),
  );
  write(
    upstreamRoot,
    'typescript/sdk/skill/SKILL-case.md',
    [
      '<!-- generated header -->',
      '# Case fixture',
      '',
      '[API](references/case-api.md).',
      '',
      '## Details',
      '',
      'Original guidance.',
      '',
      '`example/NotifyOnApproval.case.ts` uses `example/case-bindings.json`.',
      '',
    ].join('\n'),
  );
  write(
    upstreamRoot,
    'typescript/sdk/skill/SKILL-bpmn.md',
    [
      '# BPMN fixture',
      '',
      '[API](references/bpmn-api.md).',
      '',
      '## Authoring',
      '',
      'Fixture.',
      '',
    ].join('\n'),
  );
  write(
    upstreamRoot,
    'typescript/sdk/skill/references/api.md',
    '# Flow API\n\nWorked example: `example-eval/Foo.flow.ts`\n',
  );
  write(upstreamRoot, 'typescript/sdk/skill/references/guide.md', '# Guide v1\n');
  write(upstreamRoot, 'typescript/sdk/skill/references/case-api.md', '# Case API\n');
  write(upstreamRoot, 'typescript/sdk/skill/references/bpmn-api.md', '# BPMN API\n');
  write(upstreamRoot, 'typescript/sdk/example-eval/Foo.flow.ts', 'export const value = 1;\n');
  write(upstreamRoot, 'typescript/sdk/example-eval/bindings.json', '{}\n');
  write(upstreamRoot, 'typescript/sdk/example/Other.case.ts', 'export const otherCase = 1;\n');
  write(
    upstreamRoot,
    'typescript/sdk/example/NotifyOnApproval.case.ts',
    '// See example/case-bindings.json\nexport const notify = 1;\n',
  );
  write(upstreamRoot, 'typescript/sdk/example/case-bindings.json', '{}\n');
  write(
    upstreamRoot,
    'typescript/sdk/example/NotifyChannel.bpmn.ts',
    'export const notifyBpmn = 1;\n',
  );
  return commit(upstreamRoot, 'initial');
}

function createInitialSnapshot(skillsRoot, upstreamRoot, pin) {
  const skillSpecs = [
    [
      'uipath-maestro-flow',
      'typescript/sdk/skill/SKILL.md',
      'preview/uipath-maestro-flow/SKILL.md',
      adaptFlowSkill,
    ],
    [
      'uipath-maestro-case',
      'typescript/sdk/skill/SKILL-case.md',
      'preview/uipath-maestro-case/SKILL.md',
      adaptCaseSkill,
    ],
    [
      'uipath-maestro-bpmn',
      'typescript/sdk/skill/SKILL-bpmn.md',
      'preview/uipath-maestro-bpmn/SKILL.md',
      adaptBpmnSkill,
    ],
  ];
  for (const [name, source, target, adapt] of skillSpecs) {
    write(
      skillsRoot,
      target,
      snapshotHeader(name, source, pin) + adapt(sourceBody(read(upstreamRoot, source))),
    );
  }

  write(
    skillsRoot,
    'preview/uipath-maestro-flow/references/api.md',
    adaptFlowApi(read(upstreamRoot, 'typescript/sdk/skill/references/api.md')),
  );
  write(
    skillsRoot,
    'preview/uipath-maestro-flow/references/guide.md',
    read(upstreamRoot, 'typescript/sdk/skill/references/guide.md'),
  );
  write(
    skillsRoot,
    'preview/uipath-maestro-case/references/api.md',
    read(upstreamRoot, 'typescript/sdk/skill/references/case-api.md'),
  );
  write(
    skillsRoot,
    'preview/uipath-maestro-bpmn/references/api.md',
    read(upstreamRoot, 'typescript/sdk/skill/references/bpmn-api.md'),
  );
  write(
    skillsRoot,
    'preview/uipath-maestro-flow/examples/Foo.flow.ts',
    read(upstreamRoot, 'typescript/sdk/example-eval/Foo.flow.ts'),
  );
  write(
    skillsRoot,
    'preview/uipath-maestro-flow/examples/bindings.json',
    read(upstreamRoot, 'typescript/sdk/example-eval/bindings.json'),
  );
  write(
    skillsRoot,
    'preview/uipath-maestro-case/examples/Other.case.ts',
    read(upstreamRoot, 'typescript/sdk/example/Other.case.ts'),
  );
  write(
    skillsRoot,
    'preview/uipath-maestro-case/examples/NotifyOnApproval.case.ts',
    adaptCaseExample(read(upstreamRoot, 'typescript/sdk/example/NotifyOnApproval.case.ts')),
  );
  write(
    skillsRoot,
    'preview/uipath-maestro-case/examples/bindings.json',
    read(upstreamRoot, 'typescript/sdk/example/case-bindings.json'),
  );
  write(
    skillsRoot,
    'preview/uipath-maestro-bpmn/examples/NotifyChannel.bpmn.ts',
    read(upstreamRoot, 'typescript/sdk/example/NotifyChannel.bpmn.ts'),
  );
}

test('syncSnapshots three-way merges drift and reapplies only snapshot adaptations', () => {
  const temporaryRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'maestro-sync-test-'));
  const upstreamRoot = path.join(temporaryRoot, 'flow-builder-sdk');
  const skillsRoot = path.join(temporaryRoot, 'skills');
  fs.mkdirSync(upstreamRoot);
  fs.mkdirSync(skillsRoot);
  try {
    const oldPin = createInitialUpstream(upstreamRoot);
    createInitialSnapshot(skillsRoot, upstreamRoot, oldPin);

    write(
      upstreamRoot,
      'typescript/sdk/skill/references/api.md',
      '# Flow API v2\n\nWorked example: `example/Foo.flow.ts`\n',
    );
    fs.unlinkSync(path.join(upstreamRoot, 'typescript/sdk/skill/references/guide.md'));
    write(upstreamRoot, 'typescript/sdk/skill/references/new.md', '# New reference\n');
    write(upstreamRoot, 'typescript/sdk/example-eval/Foo.flow.ts', 'export const value = 2;\n');
    write(
      upstreamRoot,
      'typescript/sdk/skill/SKILL-case.md',
      read(upstreamRoot, 'typescript/sdk/skill/SKILL-case.md').replace(
        'Original guidance.',
        'New upstream Case guidance.',
      ),
    );
    write(
      upstreamRoot,
      'typescript/sdk/skill/SKILL.md',
      read(upstreamRoot, 'typescript/sdk/skill/SKILL.md').replace(
        '| Script | `core.action.script` |',
        '| Script action | `core.action.script` |',
      ),
    );
    write(
      upstreamRoot,
      'typescript/sdk/skill/SKILL-bpmn.md',
      [
        '# BPMN fixture v2',
        '',
        '[API](references/bpmn-api.md).',
        '',
        '## Capability router',
        '',
        '`example/NotifyChannel.bpmn.ts` is the worked example.',
        '',
      ].join('\n'),
    );
    const newPin = commit(upstreamRoot, 'drift');

    const result = syncSnapshots({ skillsRoot, upstreamRoot });
    assert.deepEqual(
      { oldPin: result.oldPin, newPin: result.newPin, changed: result.changed },
      { oldPin, newPin, changed: true },
    );
    assert.equal(
      read(skillsRoot, 'preview/uipath-maestro-flow/references/api.md'),
      '# Flow API v2\n\nWorked example: `examples/Foo.flow.ts`\n',
    );
    assert.equal(
      fs.existsSync(path.join(skillsRoot, 'preview/uipath-maestro-flow/references/guide.md')),
      false,
    );
    assert.equal(
      read(skillsRoot, 'preview/uipath-maestro-flow/references/new.md'),
      '# New reference\n',
    );
    assert.equal(
      read(skillsRoot, 'preview/uipath-maestro-flow/examples/Foo.flow.ts'),
      'export const value = 2;\n',
    );
    assert.match(
      read(skillsRoot, 'preview/uipath-maestro-flow/SKILL.md'),
      /\| Script action \|.*`examples\/Foo\.flow\.ts`/,
    );
    assert.match(
      read(skillsRoot, 'preview/uipath-maestro-case/SKILL.md'),
      /New upstream Case guidance/,
    );
    assert.match(
      read(skillsRoot, 'preview/uipath-maestro-bpmn/SKILL.md'),
      /# BPMN fixture v2[\s\S]*`examples\/NotifyChannel\.bpmn\.ts`/,
    );
    assert.doesNotMatch(
      read(skillsRoot, 'preview/uipath-maestro-bpmn/SKILL.md'),
      /representative process/,
    );
    for (const skill of ['flow', 'case', 'bpmn']) {
      assert.match(
        read(skillsRoot, `preview/uipath-maestro-${skill}/SKILL.md`),
        new RegExp(`@ ${newPin}\\. Canonical source`),
      );
    }

    assert.equal(syncSnapshots({ skillsRoot, upstreamRoot }).changed, false);
  } finally {
    fs.rmSync(temporaryRoot, { recursive: true, force: true });
  }
});

test('Flow API adaptation waits for the upstream staged-path fix', () => {
  assert.equal(
    adaptFlowApi('Worked example: `example-eval/Foo.flow.ts`'),
    'Worked example: `example-eval/Foo.flow.ts`',
  );
  assert.equal(
    adaptFlowApi('Worked example: `example/Foo.flow.ts`'),
    'Worked example: `examples/Foo.flow.ts`',
  );
});
