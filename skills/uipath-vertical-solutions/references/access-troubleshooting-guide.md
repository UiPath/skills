# Access Troubleshooting for `uip vss deploy`

The deploy runs as the identity that ran `uip login`. Every platform call is made as that identity, so a missing permission is a refusal on the step that needs it. The step fails, and the job keeps its checkpoint. Grant the permission, then resume the same job:

```bash
uip vss deploy resume <JOB_ID> --no-interactive --output json
```

A role change applies without a new login. An external application that was missing a **scope** must run `uip login` again, so its token carries the scope, before the resume.

## 1. Who is deploying, and where

```bash
uip login status --output json
```

| Field | Check |
|-------|-------|
| `Identity`, `UserId` | Account the job runs as. `uip login` with another account replaces the session: check again after every login |
| `IdentityType` | `User` for a person. An external application has no folder roles of its own unless assigned to the folder |
| `Tenant` | Roles are per tenant. A role on another tenant of the same organization does nothing here |

## 2. Read the user's roles and permissions

Reading a user's roles needs the Orchestrator **Roles** and **Users** view permissions. A user without them gets `403` from these commands. That does not mean the deploy is missing the same permissions. An administrator can run the check in their own session. Do not switch the deploying session to the administrator's login: the deploy would then run as the administrator.

Role assignments, at tenant and folder level:

```bash
uip or roles user-roles list <USER_NAME> --output json
```

Permissions, deduplicated across the user's roles. With `--folder-path`, only the roles assigned on that folder count:

```bash
uip or roles user-permissions list <USER_NAME> --output json
uip or roles user-permissions list <USER_NAME> --folder-path "<FOLDER_PATH>" --output json
```

- Tenant level holds the `Solution*` permissions; folder level holds everything the solution installs.
- Orchestrator names the tenant **Folders** permission `Units.*` in this output (`Units.View`, `Units.Edit`).
- A folder role on a parent folder applies to its subfolders, including the solution folder the deploy creates. `--folder-path` reads only the roles on that one folder, so an empty result does not rule out a role on a parent folder. Check `user-roles list` for the parent folders.
- Data Fabric tenant roles (Designer, Data Writer, Data Reader) are not in this output. Check them in the Data Fabric admin page.

Compare the result with the access the vertical lists for its packages.

## 3. Access by deploy step

Step keys come from the service; which steps run depends on the package. The table covers common steps only. Its access column is a best guess from what each step creates: the refusal message names the permission that was really missing. Each vertical lists the exact permissions its packages need.

| Step | Level | Access it uses |
|------|-------|----------------|
| PRE_VERIFY | Tenant | Solution deployments View (finds the deployment by name), Folders View |
| SOLUTION | Tenant | Solution deployments Create/Edit, Solution packages View (Create/Edit when the package is not on the tenant feed yet) |
| SOLUTION | Target folder | SubFolders Create (solution's own folder is created under the target), plus Create on everything the solution installs: processes, folder packages, queues, buckets, assets, apps, entities, choice sets |
| BUCKET_FILES | Solution folder | Buckets and Files View/Create/Edit |
| ASSETS | Solution folder | Assets View/Create/Edit |
| PROCESS_CONFIG | Solution folder | Processes View/Edit |
| TRIGGERS | Solution folder | Processes View, Schedules (triggers) View/Create/Edit |
| Seed | Solution folder (tenant for a package with tenant-level entities) | Entity Schema View, Entity Records View/Create/Edit, plus Edit/Delete for attachments |

## 4. Known failures

### `User doesn't have permissions SolutionDeployments.Create granted`

The deploying user has no tenant role that grants **Solution deployments Create**. It is a tenant permission, so no folder role can satisfy it.

1. Run `uip or roles user-permissions list <USER_NAME> --output json` (tenant level). When `SolutionDeployments.Create` is absent, the user has no such role on this tenant.
2. Check `uip or roles user-roles list <USER_NAME> --output json` for the tenant-scope role you expect. A role that is right but missing from this list is assigned to someone else, to another tenant, or was never saved. An administrator editing roles while logged in as themselves can easily assign the role to their own account.
3. Give the deploying user a tenant role with Solution deployments View/Create/Edit (Delete only to uninstall), on the deploy's tenant. After the user agrees (section 5), add the user to the role with `uip or roles users set <ROLE_KEY> --add-user-keys <USER_KEY>`, which keeps the user's other roles. Read section 5 before you use `uip or users assign-roles`.
4. Run `uip vss deploy resume <JOB_ID> --no-interactive --output json`.

### `Seems like you don't have access on Orchestrator. Please check with your administrator!`

Orchestrator shows this when the user opens it, even when the user holds roles. A cause seen in practice: the user is **restricted to its personal workspace** but is **not allowed a personal workspace**. That leaves the user nowhere to go. It happens to a user added by hand with the restriction ticked.

An administrator fixes it in Orchestrator: **Tenant → Manage Access → Users → the user → Edit**. Untick the restriction to the personal workspace, then save. `uip or users update` has no flag for the restriction. It can allow the personal workspace instead (`--allow-personal-workspace`, with the user's key from `uip or users list`), which also gives the user somewhere to go. Either way, ask before changing the user.

### A step after SOLUTION is refused with `403`

The solution folder inherits the roles on the target folder. Read the folder level of the target folder:

```bash
uip or roles user-permissions list <USER_NAME> --folder-path "<TARGET_FOLDER>" --output json
```

If that comes back empty, the role may sit on a parent folder: check `uip or roles user-roles list <USER_NAME> --output json`. Then either add the user to a folder role that has the missing permission, on the target folder, or assign **Folder Administrator** there, then resume. Adding the permission to the user's existing role (`uip or roles update`) changes that role for every user who holds it: say so when you name the change.

### `uip or roles ...` returns `403`

The account running the check may not read roles. That is about the account doing the check, not about the deploy. Ask an administrator to run the check in their own session, with the deploying user's name.

## 5. Change access only when asked

Reading roles and permissions changes nothing. Assigning a role or editing a role changes the tenant. Name the exact change and wait for the user to agree before running it.

- For a tenant role, `uip or roles users set <ROLE_KEY> --add-user-keys <USER_KEY>` adds the user to that role and keeps their other roles. Prefer it.
- `uip or users assign-roles` (tenant roles), and `uip or roles assign` and `uip or users assign` (folder roles), **replace** the user's whole role list at that level. Roles you do not pass are removed. Read the current roles first with `uip or roles user-roles list <USER_NAME> --output json`, and pass the full set.
- `uip or roles update` edits the role itself, so the change reaches every user who holds that role.
