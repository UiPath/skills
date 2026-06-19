# Task Authoring Rules

Standards for coder-eval task YAMLs under `tests/tasks/`.

## Sandbox Configuration

### Never install `@uipath/cli` via `env_packages`

The GH smoke runner (`smoke-skills.yml`) installs `@uipath/cli@latest` globally before any task runs. Do **not** list it under `sandbox.node.env_packages`.

**Forbidden patterns:**
```yaml
sandbox:
  node:
    env_packages:
      - "@uipath/cli"          # redundant
      - "@uipath/cli@0.1.21"   # pinned — version skew
      - "@uipath/cli@latest"   # redundant
```

**Correct:**
```yaml
sandbox:
  node: {}
```

Or omit `node:` entirely if no other Node packages are needed.

**Why:** Re-installing the CLI installs a second copy into `node_modules`, potentially shadowing the global binary. A pinned version freezes the CLI at a specific release and silently diverges from the runner's `@latest` install, causing version skew between local runs and CI.

## Template

Base every new task on `tests/templates/test-task-template.yaml`. The template does not include `env_packages` — do not add it unless installing a package other than `@uipath/cli`.
