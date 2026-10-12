# Test Templates

Starter YAML for new coder_eval test tasks. Anything in `tests/tasks/` is
auto-discovered and executed by the `smoke` / `integration` / `e2e` make
targets, so templates and scaffolding live here instead.

## Adding a new test

1. Copy `test-task-template.yaml` to `tests/tasks/<skill-folder>/<feature>/<feature>_<scenario>.yaml`.
2. Replace every `<PLACEHOLDER>` value.
3. Set the second tag to the test tier:
   - `activation` — does the right skill trigger?
   - `smoke` — skill + CLI produces a valid project (simple)
   - `integration` — correct output across varied scenarios
   - `e2e` — full loop: Explore → Plan → Build → Validate → Deploy → Run
4. Run locally:
   ```
   cd tests
   SKILLS_REPO_PATH=$(cd .. && pwd) \
     .venv/bin/coder-eval run tasks/<skill>/<feature>/<file>.yaml \
     -e experiments/default.yaml
   ```

See [`../README.md`](../README.md) for the full coder_eval task schema and
success-criterion types.
