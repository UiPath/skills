# Coded App Dashboard Deploy Refinements — Design

Date: 2026-07-14
Skill: `uipath-coded-apps` (dashboards deploy flow)
Status: approved for planning

## Problem

The dashboard deploy flow makes two decisions in a rigid, split way:

1. **Deploy target** is inferred in deploy `impl.md` Step 0 (governance vs standard),
   then a **separate** pinning question fires in Step 4 — only for the governance
   target. The three real end states (governance+pinned, governance+not-pinned,
   standalone) are never presented together as recommendations.
2. **Folder** selection is limited: governance is hard-wired to `AdminDashboards`;
   standard only supports "name an existing folder." There is no Personal-workspace
   option and no create-new-folder option.

Separately, coder-eval dashboard **deploy** tests that run live lack cleanup for the
governance path. Compounding this: `uip codedapp` has **no `delete`/`undeploy`
verb** (verbs are `deploy/init/pack/publish/pull/push`), and the SDK exposes no
app-delete — a deployed Coded App can only be torn down by deleting its **folder**
(cascades to the app; proven by `cleanup_codedapp_folder.py`). The shared
`AdminDashboards` folder must never be deleted, so a live governance deploy has no
safe teardown today.

## Goals

1. Present the deploy target as **one unified 3-way recommendation** (mode), with the
   state.json-inferred option marked Recommended.
2. Offer **3 folder options** (Personal workspace / existing folder / new folder),
   applicable to all modes, reconciled with the governance role model.
3. Add **cleanup** for live governance dashboard deploy tests without ever deleting
   shared/personal folders.

## Non-goals

- No app-level delete mechanism (no CLI/SDK verb exists; not building one).
- No change to build/edit/diagnose plugins — deploy flow only.
- No change to the credential-free command-sequence grading of the existing
  `dashboard_gov_admin_deploy.yaml` test.

## Key finding

- `uip codedapp` verbs: `deploy / init / pack / publish / pull / push`. **No delete.**
- No SDK Apps-delete surface documented.
- Folder teardown is the only supported cleanup; it cascades to the deployed app.
- Personal workspace is a normal folder in `uip or folders list --output json` with
  `Type == "Personal"` — resolvable to a `Key` like any other folder.

## Design

### 1. Deploy mode — unified 3-way structured choice

Replace the Step 0 target inference + Step 4 pinning question with a **single**
structured choice (SKILL.md Rule 18) surfaced at the deploy-plan step. Options, with
the inferred one suffixed `(Recommended)`:

| Mode | `--tags` | Elevated role provisioning |
|------|----------|----------------------------|
| Governance dashboard, pinned to Governance UI | `governance,dashboard` | yes, on the target folder |
| Governance dashboard, not pinned | `governance` | yes, on the target folder |
| Standalone coded app | `dashboard` | none |

- **Inference (unchanged logic):** any widget metric matching the governance list
  (`violations-`, `agents-by-violations`, `agent-governance-violations`,
  `recent-violations`, `rule-evaluations-`, `rule-compliance`,
  `agent-compliance-report`, `policy-denials`, `governance-verdicts`) → a governance
  mode is recommended (default to **pinned**). Otherwise **Standalone** recommended.
- **Prior deploy:** if `deployment.systemName` is already set, keep the previously
  chosen mode/tags — do not re-ask (matches today's "keep that target").
- **Pinning is still a preview feature** — carry over the existing Agentic Governance
  preview caveat text verbatim when a pinned mode is offered/selected.
- Free-text always wins; bare confirm uses the recommended default.

### 2. Folder choice — 3 options for all modes

A **second** structured choice, fired on a short turn **after** mode is settled (never
in the same message as the plan — Rule 18 plan-gate exception):

| Option | Mechanism |
|--------|-----------|
| Personal workspace | `uip or folders list --output json` → `Data[] where Type=="Personal"` → `Key` |
| Existing folder (user names it) | match on `Name`, read `Key` (today's Rule 11 behavior) |
| Create a new folder | `uip or folders create <NAME> --output json` → capture `Key` |

Persist chosen `deployment.folderKey` / `folderName` into `.dashboard/state.json`.

**Coupling rule (reconciles "all modes" with the governance role model):**

- **Governance mode → recommended folder is `AdminDashboards`.** `setup-admin-folder.mjs`
  runs to create it (if missing) and union-assign Folder Administrator to
  Administrators. The script is already parameterized by folder name, so a
  user-created **new shared folder** for a governance dashboard also gets provisioned
  through the same script (pass that folder name).
- **Governance mode + Personal workspace →** skip role provisioning (the owner already
  has full access to their own workspace). Tags still applied.
- **Standalone mode →** recommended default is **Personal workspace** (zero-config,
  least privilege, always available). No role provisioning in any standalone case.

### 3. Cleanup for coder-eval dashboard deploy tests

Because there is no app-delete verb:

- **Live governance deploy e2e** deploys into a **disposable per-run shared folder**
  named `codedapp-govtest-<uuid8>` (passed as the folder-name arg to
  `setup-admin-folder.mjs`), **not** the literal shared `AdminDashboards`. Folder-delete
  then cascades to the deployed app. The test writes that folder name into
  `report.json` under `folder`, and `post_run` runs `cleanup_codedapp_folder.py`
  (contract already used by `e2e_orchestrator_dashboard_web_app.yaml`). If the test
  mints an OAuth external app, `post_run` also runs `cleanup_external_app.py`.
- **Guardrail (defense-in-depth)** in `cleanup_codedapp_folder.py`: in addition to the
  existing `codedapp-` prefix requirement, add an explicit **refuse list** — never
  delete a folder whose name is exactly `AdminDashboards` or `Shared`
  (case-insensitive), or that ends with `'s workspace` (personal-workspace shape).
  Belt-and-suspenders, since such names never match the `codedapp-` prefix anyway.
  The match is exact/suffix — not a bare `contains "workspace"` — so a legit
  `codedapp-workspace-*` test folder is never caught. Refusal prints a SKIP line and
  exits 0.
- The existing **credential-free** `dashboard_gov_admin_deploy.yaml` is unchanged — it
  never touches a live tenant, so it needs no cleanup.

### 4. Files touched

| File | Change |
|------|--------|
| `skills/uipath-coded-apps/references/dashboards/plugins/deploy/impl.md` | Rewrite Steps 0/1/4/8 into the mode + folder choice model; keep pipeline, versioning, retries, preview caveat. |
| `skills/uipath-coded-apps/SKILL.md` | Update deploy summary (~line 167) and Rule 11 to cover Personal-workspace (`Type=="Personal"`) and create-new-folder resolution. |
| `tests/tasks/uipath-coded-apps/_shared/cleanup_codedapp_folder.py` | Add protected-name refuse guardrail. |
| `tests/tasks/uipath-coded-apps/dashboard/deploy/` | Add one live governance deploy e2e (disposable folder + `post_run` cleanup). Keep the credential-free test. |

## Error handling / edge cases

- **Personal workspace not found** (`Type=="Personal"` absent): surface the folder list,
  ask the user to pick another option. Do not fall back silently.
- **`or folders create` name collision:** if create fails "already exists," resolve the
  existing folder's key instead of failing.
- **Governance + new shared folder provisioning failure** ("Folder Administrator role
  not found" / "Administrators group not found"): existing `impl.md` error paths apply
  unchanged.
- **Deploy retries** (409 / indexing / path-name conflict) are unchanged.
- **Cleanup** stays exit-0-always; a refused delete prints SKIP and does not fail the test.

## Testing

- Live governance deploy e2e: asserts disposable `codedapp-govtest-*` folder created,
  `setup-admin-folder.mjs` invoked with that name, pack→publish→deploy ran with
  `--tags governance…`, `report.json.folder` recorded, `post_run` cleanup wired.
- Unit-ish check of the guardrail: feeding `AdminDashboards` / `Shared` / a `*'s workspace`
  name to `cleanup_codedapp_folder.py` prints SKIP and deletes nothing.
- Existing credential-free governance test continues to pass unchanged.
- `/lint-task` on any new/edited task YAML before commit.
