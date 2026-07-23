#!/usr/bin/env bash
set -euo pipefail

# Run from the coder_eval dir so the relative --run-dir paths (runs/...) resolve here.
cd /home/azureuser/projects/skills/tmp/coder_eval

echo "=== [1/2] optimized (scripted-skill) run ==="
coder-eval run \
  /home/azureuser/projects/skills/tmp/experiments/tasks/uipath-maestro-bpmn/*/*.yaml \
  -e /home/azureuser/projects/skills/tmp/experiments/scripted-skill.yaml \
  --repeats 3 \
  --max-parallel 16 \
  --run-dir runs/maestro-bpmn-optimized-no-prompt \
  --resume

echo "=== pausing 2 minutes before the baseline run ==="
sleep 120

echo "=== [2/2] baseline run ==="
coder-eval run \
  /home/azureuser/projects/skills/tmp/experiments/tasks/uipath-maestro-bpmn/*/*.yaml \
  -e /home/azureuser/projects/skills/tmp/experiments/baseline.yaml \
  --repeats 3 \
  --max-parallel 16 \
  --run-dir runs/maestro-bpmn-baseline \
  --resume

echo "=== done ==="
