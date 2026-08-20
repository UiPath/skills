import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import { buildComparison, loadTaskManifest, renderMarkdown, selectBaseline } from './compare-preview-nightly.mjs';

const taskIds = Array.from({ length: 9 }, (_, index) => `task-${index + 1}`);
const tasks = taskIds.map((task_id, index) => ({ task_id, task_path: `tasks/task-${index + 1}.yaml` }));

function rows(score, model = 'claude-sonnet-5') {
  return taskIds.map((task_id, index) => ({
    task_id,
    status: 'SUCCESS',
    weighted_score: score + index / 100,
    total_turns: 20 + index,
    total_cost_usd: 0.1 + index / 100,
    duration: 100 + index,
    model_used: model,
  }));
}

function run(run_id, score, runConfig) {
  return {
    run_id,
    end_time: `${run_id}T05:00:00Z`,
    environment_info: runConfig ? { run_config: runConfig } : {},
    task_results: rows(score),
  };
}

function writeJson(directory, name, value) {
  const filePath = path.join(directory, name);
  fs.writeFileSync(filePath, JSON.stringify(value));
  return filePath;
}

test('selects the newest baseline with the exact run config and all nine tasks', () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'preview-compare-'));
  const config = { harness: 'claude-code', model: 'claude-sonnet-5', environment: 'alpha' };
  const older = writeJson(directory, 'older.json', run('2026-08-18', 0.7, config));
  const newest = writeJson(directory, 'newest.json', run('2026-08-19', 0.8, config));
  const wrongModel = writeJson(
    directory,
    'wrong-model.json',
    run('2026-08-20', 0.9, { ...config, model: 'claude-opus-5' }),
  );
  const selected = selectBaseline([older, wrongModel, newest], config, tasks);
  assert.equal(selected.filePath, newest);
});

test('rejects a baseline from a different harness', () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'preview-compare-'));
  const file = writeJson(
    directory,
    'codex.json',
    run('2026-08-20', 0.9, { harness: 'codex', model: 'claude-sonnet-5', environment: 'alpha' }),
  );
  assert.throws(
    () => selectBaseline([file], { harness: 'claude-code', model: 'claude-sonnet-5', environment: 'alpha' }, tasks),
    /No regular-nightly baseline matches/,
  );
});

test('builds per-task deltas and a readable table', () => {
  const preview = run('2026-08-20', 0.9);
  const baseline = run('2026-08-19', 0.8);
  const comparison = buildComparison({
    preview,
    previewFile: 'preview.json',
    baseline,
    baselineFile: 'baseline.json',
    tasks,
    harness: 'claude-code',
    environment: 'alpha',
  });
  assert.equal(comparison.tasks.length, 9);
  assert.ok(Math.abs(comparison.tasks[0].delta.score - 0.1) < 1e-9);
  assert.equal(comparison.aggregate.preview.succeeded, 9);
  assert.match(renderMarkdown(comparison), /task-9/);
});

test('manifest requires exactly nine unique, existing task files with ids', () => {
  const repository = fs.mkdtempSync(path.join(os.tmpdir(), 'preview-manifest-'));
  const manifest = path.join(repository, 'manifest.txt');
  const lines = taskIds.map((taskId, index) => {
    const relative = `tasks/task-${index + 1}.yaml`;
    const taskFile = path.join(repository, 'tests', relative);
    fs.mkdirSync(path.dirname(taskFile), { recursive: true });
    fs.writeFileSync(taskFile, `task_id: ${taskId}\n`);
    return relative;
  });
  fs.writeFileSync(manifest, `${lines.join('\n')}\n`);
  assert.deepEqual(loadTaskManifest(repository, manifest), tasks);
});
