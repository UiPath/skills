# Coded App Dashboard Deploy Refinements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the dashboard deploy flow into a unified 3-way deploy-mode recommendation plus a 3-option folder choice, and add safe cleanup for live governance deploy tests.

**Architecture:** Documentation-driven skill changes (the skill *is* markdown the agent follows) plus one Python cleanup-script guardrail and one new coder-eval test. The deploy `impl.md` decision flow is reordered so the mode + folder are chosen *after* the plan-confirm and *before* folder provisioning. No new CLI/SDK capability is built — teardown of a deployed Coded App remains folder-delete only.

**Tech Stack:** Markdown skill docs (`SKILL.md`, `references/…/impl.md`), Python 3 cleanup scripts, coder-eval task YAML.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-14-coded-apps-dashboard-deploy-refinements-design.md`.
- `uip codedapp` has NO `delete`/`undeploy` verb; SDK has no app-delete. Only folder-delete tears down a deployed app.
- Personal workspace = a folder in `uip or folders list --output json` with `Type == "Personal"`.
- Deploy-mode → tags: governance+pinned=`governance,dashboard`; governance+not-pinned=`governance`; standalone=`dashboard`.
- Structured choices use SKILL.md Rule 18: ≤4 options, recommended first suffixed `(Recommended)`, free-text always wins, NEVER in the same message as the plan (plan gate is free-text).
- CLI output parsed programmatically MUST use `--output json`.
- Cleanup scripts exit 0 always; a refused delete prints a `SKIP:` line to stderr and deletes nothing.
- Test authoring: follow `.claude/rules/test-writing.md` — required tags `skill`+`tier`+`mode:*`; inherit `agent:`; `sandbox.node: {}` (never pin `@uipath/cli`); base on `tests/templates/test-task-template.yaml`; `/lint-task` before commit.
- Preview caveat text for pinning must be carried over verbatim (Agentic Governance preview).

---

### Task 1: Protected-folder guardrail in `cleanup_codedapp_folder.py`

Add a refuse-list so cleanup never deletes a shared/personal folder even if a test misconfigures `report.json`. This is real code — TDD it.

**Files:**
- Modify: `tests/tasks/uipath-coded-apps/_shared/cleanup_codedapp_folder.py` (guard after the `codedapp-` prefix check, ~line 48)
- Test: `tests/tasks/uipath-coded-apps/_shared/test_cleanup_codedapp_folder.py` (create)

**Interfaces:**
- Consumes: nothing new.
- Produces: an inline refuse-check (exact case-insensitive match against `"admindashboards"`/`"shared"`, or name ending `"'s workspace"`) placed before the existing `codedapp-` prefix check. No new public helper — kept inline to match the script's existing flat style.

- [ ] **Step 1: Write the failing test**

Create `tests/tasks/uipath-coded-apps/_shared/test_cleanup_codedapp_folder.py`:

```python
#!/usr/bin/env python3
"""Guardrail unit test for cleanup_codedapp_folder.py.

Runs the cleanup script in a temp dir with a crafted report.json and asserts
it refuses protected folder names (prints SKIP, deletes nothing, exits 0).
No live tenant / uip binary needed: the guardrail returns before any uip call.
"""
import json
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(__file__), "cleanup_codedapp_folder.py")


def run_with_folder(folder: str):
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "report.json"), "w") as f:
            json.dump({"folder": folder}, f)
        return subprocess.run(
            [sys.executable, SCRIPT],
            cwd=d, capture_output=True, text=True, timeout=30,
        )


def main() -> int:
    failures = []

    # Protected names must be refused with a SKIP and exit 0.
    for name in ["AdminDashboards", "admindashboards", "Shared",
                 "nishank.siddharth@uipath.com's workspace"]:
        r = run_with_folder(name)
        if r.returncode != 0:
            failures.append(f"{name!r}: expected exit 0, got {r.returncode}")
        if "SKIP" not in r.stderr:
            failures.append(f"{name!r}: expected SKIP on stderr, got {r.stderr!r}")

    # A legit codedapp-* name is NOT caught by the protected guard. (It will
    # still fall through to the uip call, which fails without a tenant; we only
    # assert the guard did not print a protected-name SKIP for it.)
    r = run_with_folder("codedapp-workspace-abc123")
    if "refusing to delete" in r.stderr and "protected" in r.stderr.lower():
        failures.append("codedapp-workspace-* wrongly caught by protected guard")

    if failures:
        print("FAIL:\n  " + "\n  ".join(failures), file=sys.stderr)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tests/tasks/uipath-coded-apps/_shared/test_cleanup_codedapp_folder.py`
Expected: FAIL — `Shared` and the `'s workspace` name are NOT yet refused (current script only checks the `codedapp-` prefix, so `Shared`/`AdminDashboards` already fail the prefix check and DO print a SKIP — but the message text differs). The test asserts a SKIP appears for each; the current prefix message is `does not start with 'codedapp-'`, which DOES contain `SKIP`, so this particular assertion may pass. The meaningful new coverage: confirm the message is unchanged-safe. Run and record actual output; if all pass already, still add the explicit guard in Step 3 for defense-in-depth and message clarity.

> Note: because the existing prefix check already blocks non-`codedapp-` names, the test may partially pass pre-change. The guard in Step 3 adds an explicit, clearly-labelled protected refusal (distinct message) so intent is documented and a future prefix-loosening can't regress it.

- [ ] **Step 3: Add the guardrail**

In `cleanup_codedapp_folder.py`, immediately BEFORE the existing prefix check (`if not folder.lower().startswith("codedapp-")`), insert:

```python
# Hard refuse-list: never delete shared or personal folders, regardless of the
# prefix check below. AdminDashboards is the shared governance home; Shared is
# the tenant default; a "<user>'s workspace" name is a personal workspace.
# There is no `codedapp delete` verb, so a deployed governance dashboard is torn
# down by deleting a DISPOSABLE per-run folder — never one of these.
_name = folder.strip().lower()
if _name in ("admindashboards", "shared") or _name.endswith("'s workspace"):
    print(f"SKIP: folder '{folder}' is protected — refusing to delete", file=sys.stderr)
    sys.exit(0)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 tests/tasks/uipath-coded-apps/_shared/test_cleanup_codedapp_folder.py`
Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add tests/tasks/uipath-coded-apps/_shared/cleanup_codedapp_folder.py \
        tests/tasks/uipath-coded-apps/_shared/test_cleanup_codedapp_folder.py
git commit -m "test(uipath-coded-apps): refuse-list guardrail for cleanup_codedapp_folder"
```

---

### Task 2: Rewrite the deploy `impl.md` decision flow (mode + folder)

Replace the governance-vs-standard target model + separate pinning question with: (Step 0) classify deploy type, (Step 1) version, (Step 2) compute recommended mode+folder, (Step 3) plan, (Step 4) structured mode+folder choices on confirm, (Step 5) resolve/provision the chosen folder, then the unchanged pipeline. Reorder is required because the folder is now chosen AFTER the plan and BEFORE provisioning.

**Files:**
- Modify: `skills/uipath-coded-apps/references/dashboards/plugins/deploy/impl.md` (full restructure of Steps 0–8; preserve pipeline mechanics verbatim, renumbered)

**Interfaces:**
- Consumes: `.dashboard/state.json` fields `app.name/routingName/semver`, `deployment.systemName/folderKey/folderName/pinnedToGovernance`, `widgets`.
- Produces (for Task 4's test to rely on): the governance shared-folder path still invokes `setup-admin-folder.mjs "<FOLDER_NAME>" "<PROJECT_DIR>"`; deploy still runs `uip codedapp pack|publish|deploy`; tags come from mode.

- [ ] **Step 1: Replace the header note + Steps 0–4 (through the plan) and the pinning question**

Replace the current lines from the `> **What the user should see:**` blockquote through the end of `## Step 4 — Show deploy plan …` with the following. Keep `## Pre-flight` unchanged.

Header blockquote becomes:
```markdown
> **What the user should see:** The deploy plan (Step 3), the mode/folder choices (Step 4), progress ticks, and the final URL. All other steps are silent — run commands, read outputs in context, never echo raw JSON or bash output to the user.
```

Then, after Pre-flight, the steps in this order:

````markdown
## Step 0 — Classify deploy type

- `deployment.systemName` empty → **Fresh deploy**
- `deployment.systemName` set → **Upgrade** — keep the mode and folder from the prior deploy (`deployment.pinnedToGovernance` + `deployment.folderName`/`folderKey`); the plan re-confirms but Step 4 asks nothing.

---

## Step 1 — Set the publish version

The version used for pack + publish is `NEXT_SEMVER`, by deploy type:

- **Fresh deploy** (`deployment.systemName` empty): first publish — use `app.semver` as-is. `NEXT_SEMVER = <CURRENT_SEMVER>` (no bump; the version doesn't exist yet).
- **Upgrade** (`deployment.systemName` set): the current version is **already published**, so you **MUST** bump before pack/publish. Compute the next patch:

  ```bash
  node -e "
  const [a,b,c] = process.argv[1].split('.').map(Number)
  process.stdout.write([a, b, c + 1].join('.'))
  " <CURRENT_SEMVER>
  ```

  Pack (Step 7) and Publish (Step 8) MUST pass `--version "<NEXT_SEMVER>"`. Publish still auto-bumps on a 409 as a backstop, but bump here first on an upgrade.

---

## Step 2 — Compute recommended mode and folder (no side effects)

Two independent decisions drive the deploy: **mode** (governance treatment → tags) and **folder** (where it lands).

**Mode** — three end states:

| Mode | `--tags` | Elevated role provisioning |
|------|----------|----------------------------|
| Governance dashboard, pinned to Governance UI | `governance,dashboard` | yes, on the target **shared** folder |
| Governance dashboard, not pinned | `governance` | yes, on the target **shared** folder |
| Standalone coded app | `dashboard` | none |

Recommend a mode from `.dashboard/state.json` `widgets`:
- **Governance (pinned)** when any widget metric starts with / equals `violations-`, `agents-by-violations`, `agent-governance-violations`, `recent-violations`, `rule-evaluations-`, `rule-compliance`, `agent-compliance-report`, `policy-denials`, `governance-verdicts`.
- **Standalone** otherwise — a dashboard that happens to show agent health / jobs / KPIs is a normal app, not a governance dashboard.

**Folder** — three options: **Personal workspace** · **Existing folder** (user names it) · **Create a new folder**. Recommend:
- **Governance modes → `AdminDashboards`** (the governance home; provisioned in Step 5).
- **Standalone → Personal workspace** (zero-config, private).

**Upgrade short-circuit:** if `deployment.systemName` is set, keep the state-implied mode and folder; Step 4 asks nothing.

**Capture user wording:** if the request already names a mode ("as a governance dashboard, pinned") and/or a folder ("in a new folder called X" / "to my personal workspace"), treat those as settled — the matching Step-4 question is skipped.

---

## Step 3 — Show deploy plan

`<MODE_LABEL>` / `<FOLDER_LABEL>` are the recommended (or wording-settled) values from Step 2.

```
Your **<APP_NAME>** is ready to be deployed.

📦  Version:    <SEMVER> → <NEXT_SEMVER>   (or "1.0.0 (first publish)" on a fresh deploy)
🔗  URL path:   <ROUTING_NAME>
🎯  Mode:       <MODE_LABEL>   (recommended — <why>, or "kept from last deploy" on upgrade)
📁  Folder:     <FOLDER_LABEL>   (recommended — <why>)
🔄  Type:       Fresh deploy  OR  Updating existing deployment
```

**Governance mode + fresh deploy + shared-folder target** — also show:
```
⚠️  Governance deploy provisions the <FOLDER_LABEL> folder and grants Administrators
    Folder Administrator on it — an elevated permission the coding agent will ask you
    to approve once.
```
**Governance + pinned** — append:
```
    Pinning surfaces the dashboard in the Governance section, an Agentic Governance
    preview feature — effective only if your org is enrolled in the preview. Either
    way the dashboard deploys and is reachable at its URL.
```
**Standalone, or ANY Personal-workspace target** — show no elevated-permissions warning.

End with: `Confirm to deploy, or tell me what to change.` — **pure text, no tool calls in this response. HALT.**

---

## Step 4 — On confirm: settle mode, then folder

On the user's reply:
- **Change request / cancel** → handle it; re-present the plan if changed.
- **Upgrade** (systemName set) → skip both questions; go to Step 5 with the kept mode/folder.
- **Wording settled both** (Step 2) → skip both; go to Step 5.

Otherwise ask up to two SHORT structured-choice questions (SKILL.md Rule 18), recommended option first, suffixed `(Recommended)`. Skip either question the wording already settled. **Never** in the same message as the plan — this is a later, short turn.

**Question 1 — mode** (skip if settled):

| Option | Meaning |
|--------|---------|
| **Governance dashboard, pinned to Governance UI** | governance access + surfaced in the Governance section (`governance,dashboard`) |
| **Governance dashboard, not pinned** | governance access only (`governance`) |
| **Standalone coded app** | a regular dashboard app (`dashboard`) |

> ⚠️ **Pinning is a preview feature.** When offering a pinned option, state: *"Pinning surfaces the dashboard in the Governance section — an Agentic Governance preview feature, so it only takes effect if your org is enrolled in the preview. Either way the dashboard deploys and is reachable at its URL."*

**Question 2 — folder** (skip if settled):

| Option | Mechanism |
|--------|-----------|
| **Personal workspace** | your own workspace, private to you |
| **Existing folder** | you provide the name |
| **Create a new folder** | you provide the name |

For a governance mode, present **`AdminDashboards`** as the recommended **Existing folder** default; "Create a new folder" covers a differently-named shared governance folder. For standalone, **Personal workspace** is recommended.

Free-text replies remain valid and take precedence.
````

- [ ] **Step 2: Replace old "Step 1 — Provision AdminDashboards folder" with the new "Step 5 — Resolve and provision the chosen folder"**

Delete the old `## Step 1 — Provision AdminDashboards folder …` block and the old `## Step 2 — Classify deploy type` / `## Step 3 — Set the publish version` blocks (their content moved to new Steps 0/1 above). Insert after Step 4:

````markdown
## Step 5 — Resolve and provision the chosen folder

Resolve the chosen folder to `folderKey` and persist `deployment.folderKey`/`folderName` in `.dashboard/state.json`. **If `deployment.folderKey` is already set (upgrade / prior run) — skip this entire step.**

**Governance mode targeting a SHARED folder** (AdminDashboards, or any user-named/new shared folder — anything except Personal workspace) — provision via the script (silent until "…folder is ready"):

```bash
node "<SKILL_BASE_DIR>/assets/scripts/dashboards/setup-admin-folder.mjs" "<FOLDER_NAME>" "<PROJECT_DIR>"
```

`<FOLDER_NAME>` is the chosen governance folder (`AdminDashboards` by default). `<PROJECT_DIR>` is the dashboard project dir. The script reads `.dashboard/state.json`, exits immediately if already provisioned, else: looks up the Folder Administrator role + Administrators group + folder in parallel, creates the folder if missing, reads existing role assignments and assigns the **union** (`roles assign` replaces all roles), and persists `folderKey`/`folderName`.

> ⚠️ The script grants elevated folder permissions — the coding agent will ask for explicit approval. Expected.

If it fails "Administrators group not found": run `uip or users list --username "Administrators" --output json` and show available groups.

Then tell the user: "<FOLDER_NAME> folder is ready."

**Personal workspace** (any mode) — resolve, no provisioning:

```bash
uip or folders list --output json
```
Pick `Data[]` where `Type == "Personal"`, read `Key`. Persist `folderKey`/`folderName`. No folder created, no roles assigned. (A governance dashboard in a personal workspace needs no role provisioning — the owner already has full access.) If no `Personal` folder is found, show the folder list and ask the user to pick another option.

**Existing folder by name** (standalone) — resolve per SKILL.md Rule 11:

```bash
uip or folders list --output json
```
Match on `Name`, read `Key`. Persist.

**Create a new folder** (standalone) —

```bash
uip or folders create "<FOLDER_NAME>" --output json
```
Capture `Data.Key`. If it fails "already exists," resolve the existing folder's key from `uip or folders list` instead. Persist.

---
````

- [ ] **Step 3: Renumber the remaining pipeline steps (preserve their content verbatim)**

The following steps keep their EXISTING content unchanged except the heading number. Renumber in place:
- old `## Step 5 — Production build` → `## Step 6 — Production build`
- old `### Step 6b — Template packaging …` → `### Step 7b — Template packaging …` (update its internal "Step 6b" / "(Step 6b)" / "Skip the CONFIG_OK check (Step 5)" references to "Step 7b" / "Step 6")
- old `## Step 6 — Pack (silent)` → `## Step 7 — Pack (silent)`
- old `## Step 7 — Publish (silent)` → `## Step 8 — Publish (silent)`
- old `## Step 8 — Deploy` → `## Step 9 — Deploy`
- old `## Step 9 — Update state.json` → `## Step 10 — Update state.json`
- old `## Step 10 — Report` → `## Step 11 — Report`

In the CONFIG_OK check (now Step 6) and Template packaging (now Step 7b), fix cross-references: "Step 6b" → "Step 7b", "(Step 5)" → "(Step 6)".

- [ ] **Step 4: Rewrite the Deploy tags intro (now Step 9) to source tags from mode**

Replace the "Set tags based on the deployment target …" lines at the top of the Deploy step with:

```markdown
Set tags from the chosen **mode** (Step 2/4):
- **Standalone** → tags = `"dashboard"`
- **Governance, pinned** → tags = `"governance,dashboard"`
- **Governance, not pinned** → tags = `"governance"`
```

Leave the `--version`/`--path-name` rules, fresh-vs-upgrade commands, and all retry logic UNCHANGED.

- [ ] **Step 5: Update the Report step (now Step 11), the Error reference table, and the Rules section**

In the Report step, keep the governance pinned/not-pinned notes as-is. In the **Rules** section, replace the final rule ("Determine governance vs standard target first (Step 0) …") with:

```markdown
- Choose **mode** and **folder** as two independent decisions (Steps 2–4). Mode sets `--tags`; only a governance mode targeting a **shared** folder provisions `setup-admin-folder.mjs` and assigns elevated roles. A Personal-workspace target never provisions roles. Standalone never provisions roles.
- Recommend the mode from state.json metrics and the folder from the mode (governance→AdminDashboards, standalone→Personal workspace); the user can override either via the Step-4 structured choice or free-text.
```

Update any remaining "target (governance/standard)" phrasing in the Rules/Error-reference rows to "mode". Keep every retry/caveat row (Folder Administrator not found, Administrators group not found, publish 409/5xx, deploy indexing/routing-name/path-name, Agentic Governance preview) UNCHANGED.

- [ ] **Step 6: Verify structural consistency**

Run:
```bash
grep -nE '^#{2,3} Step ' skills/uipath-coded-apps/references/dashboards/plugins/deploy/impl.md
```
Expected: a single ascending sequence Step 0 … Step 11 (plus Step 7b), no duplicate numbers, no gaps.

Run:
```bash
grep -nE 'Step [0-9]+b?|standard target|governance vs standard' skills/uipath-coded-apps/references/dashboards/plugins/deploy/impl.md
```
Expected: no stale cross-references to old numbers; no "governance vs standard target" phrasing remains.

- [ ] **Step 7: Commit**

```bash
git add skills/uipath-coded-apps/references/dashboards/plugins/deploy/impl.md
git commit -m "docs(uipath-coded-apps): deploy flow = 3-way mode + 3-option folder choice"
```

---

### Task 3: Update SKILL.md deploy summary and Rule 11

Bring the top-level deploy summary and folder-resolution rule in line with the new folder options.

**Files:**
- Modify: `skills/uipath-coded-apps/SKILL.md` (Rule 11 ~line 45; deploy summary ~line 167)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing structural — prose only.

- [ ] **Step 1: Extend Rule 11 to cover Personal workspace + new folder**

In Rule 11, after the sentence "If the user provides a folder **name**, resolve it to a key with `uip or folders list --output json` and match on the `Name` field …", append:

```markdown
 A **personal workspace** is the row with `Type == "Personal"` — resolve its `Key` the same way. To deploy into a **new** folder, create it first with `uip or folders create "<NAME>" --output json` and read `Data.Key`.
```

- [ ] **Step 2: Update the deploy summary (step 5 of the Quick Start)**

Replace the deploy summary line (currently "**Deploy** — `uip codedapp deploy -n <name> --folder-key <GUID>`. Resolve the GUID from a user-provided folder name …") with:

```markdown
5. **Deploy** — `uip codedapp deploy -n <name> --folder-key <GUID>`. Resolve the GUID from the chosen folder: a personal workspace (`Type == "Personal"`), a named existing folder, or a freshly `uip or folders create`d one — via `uip or folders list --output json`. Dashboards additionally choose a **deploy mode** (standalone / governance-pinned / governance) that sets `--tags`; see [dashboards deploy impl](references/dashboards/plugins/deploy/impl.md). Never let the command go interactive. Share the app URL with the user.
```

- [ ] **Step 3: Verify no contradictions**

Run:
```bash
grep -nE 'governance vs standard|standard dashboard app|standard target' skills/uipath-coded-apps/SKILL.md
```
Expected: no matches (the SKILL.md body should not describe the retired governance/standard split).

- [ ] **Step 4: Commit**

```bash
git add skills/uipath-coded-apps/SKILL.md
git commit -m "docs(uipath-coded-apps): SKILL.md deploy summary + Rule 11 for folder options"
```

---

### Task 4: Live governance deploy e2e with disposable folder + cleanup

Add an e2e that exercises the governance mode against a **disposable** shared folder so `post_run` folder-delete cascades to the deployed app (the real AdminDashboards is never used). Keep the existing credential-free `dashboard_gov_admin_deploy.yaml` untouched.

**Files:**
- Create: `tests/tasks/uipath-coded-apps/dashboard/deploy/dashboard_gov_live_deploy_e2e.yaml`

**Interfaces:**
- Consumes: `_shared/cleanup_codedapp_folder.py` (Task 1 guardrail), `_shared/cleanup_external_app.py`, `setup-admin-folder.mjs`.
- Produces: nothing downstream.

- [ ] **Step 1: Write the task YAML**

Create `tests/tasks/uipath-coded-apps/dashboard/deploy/dashboard_gov_live_deploy_e2e.yaml`:

```yaml
task_id: uipath-coded-apps-dashboard-gov-live-deploy-e2e
description: >
  Live governance-mode deploy of a runtime-compliance dashboard into a
  DISPOSABLE per-run shared folder (codedapp-govtest-<uuid>), NOT the real
  shared AdminDashboards — because `uip codedapp` has no delete verb, the only
  teardown is folder-delete, which cascades to the deployed app. Exercises the
  governance branch end-to-end: provision the disposable folder via
  setup-admin-folder.mjs, pack -> publish -> deploy with governance tags, and
  record the folder in report.json so post_run cleans it up.
tags: [uipath-coded-apps, e2e, dashboard, mode:operate, lifecycle:setup]

run_limits:
  turn_timeout: 1200
  task_timeout: 1500

sandbox:
  driver: tempdir
  node: {}

pre_run:
  - command: |
      mkdir -p .dashboard dist
      echo "<html></html>" > dist/index.html
      cat > .dashboard/state.json << 'EOF'
      {
        "app": { "name": "Runtime Compliance Dashboard", "routingName": "runtime-compliance-live", "semver": "1.0.0" },
        "env": "alpha", "org": "testorg", "tenant": "testTenant",
        "cloudUrl": "https://alpha.uipath.com",
        "widgets": ["policy-denials", "rule-compliance"],
        "deployment": { "systemName": null, "folderKey": null, "folderName": null, "appUrl": null, "pinnedToGovernance": false, "lastDeployedAt": null }
      }
      EOF
    timeout: 15
    fail_on_error: true

initial_prompt: |
  Deploy my Runtime Compliance dashboard to Automation Cloud as a governance
  dashboard, pinned to the Governance UI.

  This dashboard is a governance dashboard, so it needs a governance home
  folder with elevated access. Do NOT use the real shared AdminDashboards
  folder for this run — instead provision a fresh per-run shared folder named
  exactly `codedapp-govtest-<EPOCH>` (substitute a unique value for <EPOCH>)
  using the skill's governance provisioning script, and deploy into it. This
  isolates the run so it can be cleaned up afterward.

  IMMEDIATELY after `uip codedapp deploy` succeeds — before any further work —
  write `report.json` at the sandbox root:
    {
      "app_name": "Runtime Compliance Dashboard",
      "deployment_id": "<systemName or deploymentId from .uipath/app.config.json>",
      "folder": "<the codedapp-govtest-<EPOCH> folder name you created>"
    }
  The `folder` field is REQUIRED — post_run reads it to clean up.

  This is a non-interactive automated test — treat the plan as pre-approved and
  complete the whole deploy in this same turn. Do NOT wait for confirmation and
  do NOT ask any question. Before starting, load the uipath-coded-apps skill.

success_criteria:
  - type: skill_triggered
    description: "Agent invoked the uipath-coded-apps skill"
    skill_name: "uipath-coded-apps"
    expected_skill: "uipath-coded-apps"
    weight: 1.0
    pass_threshold: 1.0

  - type: command_executed
    description: "Governance provisioning ran against a DISPOSABLE codedapp-govtest-* folder, not the real AdminDashboards"
    tool_name: "Bash"
    command_pattern: 'setup-admin-folder\.mjs.*codedapp-govtest-'
    min_count: 1
    weight: 3.0
    pass_threshold: 1.0

  - type: command_executed
    description: "Agent did NOT provision the real shared AdminDashboards folder"
    tool_name: "Bash"
    command_pattern: 'setup-admin-folder\.mjs.*AdminDashboards'
    min_count: 0
    max_count: 0
    weight: 2.0
    pass_threshold: 1.0

  - type: command_executed
    description: "Agent ran the pack -> publish -> deploy sequence"
    tool_name: "Bash"
    command_pattern: 'uip\s+codedapp\s+(pack|publish|deploy)'
    min_count: 3
    weight: 2.5
    pass_threshold: 1.0

  - type: command_executed
    description: "Deploy used governance tags (governance or governance,dashboard)"
    tool_name: "Bash"
    command_pattern: 'uip\s+codedapp\s+deploy\b.*--tags\s+"?governance'
    min_count: 1
    weight: 2.0
    pass_threshold: 1.0

  - type: run_command
    description: "report.json records the codedapp-govtest-* folder name so post_run can clean it up"
    command: "python3 -c \"import json,sys; f=str(json.load(open('report.json')).get('folder','')); sys.exit(0 if f.startswith('codedapp-govtest-') else 1)\""
    timeout: 5
    expected_exit_code: 0
    weight: 1.5
    pass_threshold: 1.0

post_run:
  - command: "python3 $SKILLS_REPO_PATH/tests/tasks/uipath-coded-apps/_shared/cleanup_codedapp_folder.py"
    timeout: 60
  - command: "python3 $SKILLS_REPO_PATH/tests/tasks/uipath-coded-apps/_shared/cleanup_external_app.py"
    timeout: 60
```

- [ ] **Step 2: Lint the task**

Run: `/lint-task tests/tasks/uipath-coded-apps/dashboard/deploy/dashboard_gov_live_deploy_e2e.yaml`
Expected: no High findings. If it flags "missing passing-run claim," add the claim to the PR description after a real run (do not fabricate). If it flags CLI-verb reachability, run `/audit-verbs`.

- [ ] **Step 3: Sanity-check the cleanup guardrail does not block the disposable folder**

Run: `python3 tests/tasks/uipath-coded-apps/_shared/test_cleanup_codedapp_folder.py`
Expected: `PASS` (the `codedapp-govtest-*` name is not in the refuse-list; the `codedapp-workspace-*` assertion covers the near-miss).

- [ ] **Step 4: Commit**

```bash
git add tests/tasks/uipath-coded-apps/dashboard/deploy/dashboard_gov_live_deploy_e2e.yaml
git commit -m "test(uipath-coded-apps): live governance deploy e2e with disposable-folder cleanup"
```

---

## Notes for the executor

- Tasks 2 and 3 are documentation; there is no runtime unit test — verification is the `grep` consistency checks in each task plus `/lint-task` (Task 4) and, if a live tenant is available, running `dashboard_gov_admin_deploy.yaml` (must still pass unchanged) and the new e2e.
- Do NOT attempt to build a `codedapp delete` path — none exists; that is the whole reason for the disposable-folder cleanup strategy.
- Preserve every retry/caveat block in `impl.md`; this change is about the decision flow, not the pipeline mechanics.
