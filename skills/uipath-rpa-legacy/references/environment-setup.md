# Phase 0: Environment Readiness

**Goal:** Establish the project root and verify the project is a legacy framework project before any other operations.

**Key difference from modern (`uip rpa`):** The `uip rpa-legacy` CLI is standalone — it does **not** require Studio Desktop to be running. It resolves dependencies from NuGet directly and uses UiRobot for execution.

---

## Step 0.1: Establish Project Root

All `uip rpa-legacy` commands require a `<project-path>` argument pointing to the folder containing `project.json` (or the `project.json` file itself).

```bash
# Check if project.json exists in the CWD
ls {cwd}/project.json
```

If the CWD is not the project root:
- Locate the project root by finding `project.json`: `Glob: pattern="**/project.json"`
- Ask the user where their project is located if multiple `project.json` files are found

Store the project root path and use it consistently as `{projectRoot}` throughout all subsequent operations.

---

## Step 0.2: Verify Legacy Project

Read `project.json` and confirm this is a legacy framework project:

```
Read: file_path="{projectRoot}/project.json"
```

**Check these fields:**

| Field | Legacy Value | Notes |
|-------|-------------|-------|
| `targetFramework` | `"Legacy"` | May be absent in very old projects (pre-2021), which implies Legacy |
| `expressionLanguage` | `"VisualBasic"` (most common) or `"CSharp"` | Determines expression syntax in XAML |
| `studioVersion` | Typically `< 23.x` | Older Studio versions |
| `dependencies` | Classic package versions (no modern package IDs) | Very old projects (pre-2021) may have lower versions like ≤ 22.x |

**If `targetFramework` is `"Windows"` or `"Portable"`**, this is a modern project — use the `uipath-rpa` skill instead.

**If `targetFramework` is absent**, check the `studioVersion` and `dependencies` fields. Old projects without explicit `targetFramework` are Legacy by default.

---

## Step 0.3: Authentication (If Needed)

Some operations (cloud-based NuGet feeds, Orchestrator assets) may require authentication:

```bash
uip login
```

This opens a browser-based login flow. Authentication is typically needed only for:
- Projects that use private NuGet feeds requiring authentication
- `build` commands that push packages to Orchestrator
- Accessing Orchestrator resources (assets, queues) during `debug` execution

For most local development tasks (validate, edit, find-activities), authentication is **not required**.

---

## Step 0.4: Package Restore

After creating or modifying `project.json` dependencies, packages must be restored before `find-activities` or `type-definition` will work.

**Trigger restore** by running validate on the project directory:

```bash
uip rpa-legacy validate "{projectRoot}" --output json
```

This resolves NuGet packages from configured feeds. After this completes, `find-activities` and `type-definition` will have access to the package assemblies.

**If `find-activities` returns "No assemblies resolved from package dependencies"**, run validate first to trigger restore.
