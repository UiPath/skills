#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { pathToFileURL } from 'node:url';

function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith('--') || value === undefined) throw new Error(`Invalid argument near ${key ?? '<end>'}`);
    args[key.slice(2)] = value;
  }
  return args;
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

export function loadTaskManifest(repository, manifestPath) {
  const taskPaths = fs
    .readFileSync(manifestPath, 'utf8')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#'));
  if (taskPaths.length !== 9 || new Set(taskPaths).size !== 9) {
    throw new Error(`Preview nightly manifest must contain exactly 9 unique task paths; found ${taskPaths.length}`);
  }
  return taskPaths.map((taskPath) => {
    const taskFile = path.join(repository, 'tests', taskPath);
    const source = fs.readFileSync(taskFile, 'utf8');
    const taskId = source.match(/^task_id:\s*([^\s#]+)\s*$/m)?.[1];
    if (!taskId) throw new Error(`Missing task_id in ${taskPath}`);
    return { task_id: taskId, task_path: taskPath };
  });
}

function taskRows(run) {
  if (!Array.isArray(run.task_results)) throw new Error('run.json has no task_results array');
  return run.task_results;
}

function oneTask(rows, taskId, label) {
  const matches = rows.filter((row) => row.task_id === taskId);
  if (matches.length !== 1) throw new Error(`${label} must contain exactly one ${taskId} row; found ${matches.length}`);
  return matches[0];
}

function singleModel(rows) {
  const models = new Set(rows.map((row) => row.model_used ?? row.agent_config?.model).filter(Boolean));
  if (models.size !== 1) throw new Error(`Preview run must use exactly one model; found ${[...models].join(', ') || 'none'}`);
  return [...models][0];
}

function baselineMatches(run, config, expectedIds) {
  if (run.environment_info?.preview_nightly) return false;
  const rows = taskRows(run);
  if (!expectedIds.every((taskId) => rows.some((row) => row.task_id === taskId))) return false;
  const recorded = run.environment_info?.run_config;
  if (recorded) {
    return (
      recorded.harness === config.harness &&
      recorded.model === config.model &&
      recorded.environment === config.environment
    );
  }
  if (config.harness !== 'claude-code' || config.environment !== 'alpha') return false;
  const models = new Set(
    rows.filter((row) => expectedIds.includes(row.task_id)).map((row) => row.model_used).filter(Boolean),
  );
  return models.size === 1 && models.has(config.model);
}

function runTimestamp(run, filePath) {
  const parsed = Date.parse(run.end_time ?? run.start_time ?? '');
  return Number.isNaN(parsed) ? fs.statSync(filePath).mtimeMs : parsed;
}

export function selectBaseline(baselineFiles, config, tasks) {
  const expectedIds = tasks.map(({ task_id: taskId }) => taskId);
  const candidates = baselineFiles
    .map((filePath) => ({ filePath, run: readJson(filePath) }))
    .filter(({ run }) => baselineMatches(run, config, expectedIds))
    .sort((left, right) => runTimestamp(right.run, right.filePath) - runTimestamp(left.run, left.filePath));
  if (!candidates.length) {
    throw new Error(`No regular-nightly baseline matches ${config.harness}/${config.model}/${config.environment}`);
  }
  return candidates[0];
}

function numeric(value) {
  return Number.isFinite(value) ? value : null;
}

function metrics(row) {
  const iterationTurns = row.iterations?.reduce((sum, iteration) => sum + (iteration.assistant_turn_count ?? 0), 0);
  const iterationWall = row.iterations?.reduce((sum, iteration) => sum + (iteration.duration_seconds ?? 0), 0);
  return {
    status: row.final_status ?? row.status ?? 'UNKNOWN',
    score: numeric(row.weighted_score),
    turns: numeric(row.total_turns ?? row.visible_turns ?? iterationTurns),
    cost_usd: numeric(row.total_cost_usd),
    wall_seconds: numeric(row.duration ?? iterationWall),
  };
}

function delta(preview, live) {
  const subtract = (left, right) => (left === null || right === null ? null : left - right);
  return {
    score: subtract(preview.score, live.score),
    turns: subtract(preview.turns, live.turns),
    cost_usd: subtract(preview.cost_usd, live.cost_usd),
    wall_seconds: subtract(preview.wall_seconds, live.wall_seconds),
  };
}

function average(values) {
  const present = values.filter((value) => value !== null);
  return present.length ? present.reduce((sum, value) => sum + value, 0) / present.length : null;
}

function aggregate(rows, arm) {
  const values = rows.map((row) => row[arm]);
  return {
    succeeded: values.filter(({ status }) => status === 'SUCCESS').length,
    tasks: values.length,
    average_score: average(values.map(({ score }) => score)),
    average_turns: average(values.map(({ turns }) => turns)),
    total_cost_usd: values.some(({ cost_usd: cost }) => cost !== null)
      ? values.reduce((sum, { cost_usd: cost }) => sum + (cost ?? 0), 0)
      : null,
    total_wall_seconds: values.some(({ wall_seconds: wall }) => wall !== null)
      ? values.reduce((sum, { wall_seconds: wall }) => sum + (wall ?? 0), 0)
      : null,
  };
}

export function buildComparison({
  preview,
  previewFile,
  previewRunId,
  baseline,
  baselineFile,
  tasks,
  harness,
  previewEnvironment,
  baselineEnvironment,
}) {
  const previewRows = taskRows(preview);
  const config = {
    harness,
    model: singleModel(previewRows),
    preview_environment: previewEnvironment,
    live_v1_environment: baselineEnvironment,
  };
  const rows = tasks.map(({ task_id: taskId, task_path: taskPath }) => {
    const previewMetrics = metrics(oneTask(previewRows, taskId, 'Preview run'));
    const liveMetrics = metrics(oneTask(taskRows(baseline), taskId, 'Regular nightly'));
    return {
      task_id: taskId,
      task_path: taskPath,
      preview: previewMetrics,
      live_v1: liveMetrics,
      delta: delta(previewMetrics, liveMetrics),
    };
  });
  return {
    generated_at: new Date().toISOString(),
    config,
    preview: { run_id: previewRunId ?? preview.run_id ?? null, source: previewFile },
    baseline: { run_id: baseline.run_id ?? null, source: baselineFile },
    aggregate: { preview: aggregate(rows, 'preview'), live_v1: aggregate(rows, 'live_v1') },
    tasks: rows,
  };
}

function format(value, digits = 2) {
  return value === null ? '—' : value.toFixed(digits);
}

export function renderMarkdown(comparison) {
  const { config, aggregate: totals } = comparison;
  const lines = [
    '# Maestro preview nightly comparison',
    '',
    `Config: \`${config.harness}\` / \`${config.model}\` · preview \`${config.preview_environment}\`, live v1 \`${config.live_v1_environment}\``,
    '',
    `Preview: \`${comparison.preview.run_id ?? 'unknown'}\` · regular nightly: \`${comparison.baseline.run_id ?? 'unknown'}\``,
    '',
    '| Task | Preview | Live v1 | Δ score | Turns P/V1 | Cost P/V1 | Wall P/V1 |',
    '|---|---:|---:|---:|---:|---:|---:|',
  ];
  for (const row of comparison.tasks) {
    lines.push(
      `| ${row.task_id} | ${row.preview.status} ${format(row.preview.score)} | ${row.live_v1.status} ${format(row.live_v1.score)} | ${format(row.delta.score)} | ${format(row.preview.turns, 0)} / ${format(row.live_v1.turns, 0)} | $${format(row.preview.cost_usd, 3)} / $${format(row.live_v1.cost_usd, 3)} | ${format(row.preview.wall_seconds, 0)}s / ${format(row.live_v1.wall_seconds, 0)}s |`,
    );
  }
  lines.push(
    '',
    `Summary: preview ${totals.preview.succeeded}/${totals.preview.tasks} succeeded at ${format(totals.preview.average_score)} average score; live v1 ${totals.live_v1.succeeded}/${totals.live_v1.tasks} at ${format(totals.live_v1.average_score)}.`,
    '',
  );
  return lines.join('\n');
}

function baselineFiles(directory) {
  return fs
    .readdirSync(directory, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith('.json'))
    .map((entry) => path.join(directory, entry.name));
}

export function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  for (const required of [
    'repository',
    'manifest',
    'preview',
    'baselines',
    'harness',
    'preview-environment',
    'baseline-environment',
    'output-json',
    'output-md',
  ]) {
    if (!args[required]) throw new Error(`--${required} is required`);
  }
  const tasks = loadTaskManifest(args.repository, args.manifest);
  const preview = readJson(args.preview);
  const config = {
    harness: args.harness,
    model: singleModel(taskRows(preview)),
    environment: args['baseline-environment'],
  };
  const selected = selectBaseline(baselineFiles(args.baselines), config, tasks);
  const comparison = buildComparison({
    preview,
    previewFile: args.preview,
    previewRunId: args['preview-run-id'],
    baseline: selected.run,
    baselineFile: selected.filePath,
    tasks,
    harness: args.harness,
    previewEnvironment: args['preview-environment'],
    baselineEnvironment: args['baseline-environment'],
  });
  fs.writeFileSync(args['output-json'], `${JSON.stringify(comparison, null, 2)}\n`);
  const markdown = renderMarkdown(comparison);
  fs.writeFileSync(args['output-md'], markdown);
  process.stdout.write(markdown);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    main();
  } catch (error) {
    console.error(`compare-preview-nightly: ${error.message}`);
    process.exitCode = 1;
  }
}
