# Choose Roles

Give users, robot accounts, and groups Orchestrator access by assigning **standard roles**. Create a custom role only when no standard role carries the permission needed.

---

## When to Use

- Granting someone access to a folder or the tenant.
- Onboarding a robot account that runs unattended jobs.
- Request says "create a role for X" — check the standard roles first.
- Debugging "user can't do X" and deciding which role to add.

For the role and assignment commands in full (create, update, delete, audit), see [setup-environment.md § Step 3](setup-environment.md#step-3-create-roles).

---

## Critical Rules

1. **Prefer a standard role over a custom one.** Standard roles are pre-configured by UiPath with the permissions needed to work in folders; a custom role is one more thing the tenant owner must maintain.
2. **Assign standard roles in pairs.** Each folder role has a matching `Allow to be …` tenant role. Assign both: the folder role in each folder, the tenant role once at tenant level.
3. **Standard roles cannot be changed.** `roles list` / `roles get` show them with `IsEditable: false`; `roles get` also shows `IsStatic: true`. Never `roles update` or `roles delete` them. Organization-level Identity roles (`uip admin authorization roles`) follow their own read-only rule — see [uipath-admin](/uipath:uipath-admin).
4. **Create a custom role only after naming the missing permission.** Run `roles get` on the closest standard role, find the permission it lacks in `roles permissions list`, and state that permission to the user before creating anything.
5. **All three assign commands replace.** `users assign-roles`, `users assign`, and `roles assign` overwrite the principal's role list at their scope. Read current roles first and pass the full union. Full warning and the additive `roles users set` alternative: [setup-environment.md § Step 3](setup-environment.md#step-3-create-roles).
6. **Never assign the legacy `Administrator` or `Robot` roles.** Both are mixed roles, unavailable on new tenants. Use their replacements in the table below.

---

## Decision Tree

Pick the first row that matches the need.

| Need | Folder role (each folder) | Tenant role (once) |
|------|---------------------------|--------------------|
| Run processes unattended or from Assistant (robot account, business user) | `Automation User` | `Allow to be Automation User` |
| Create automation projects, publish packages, and run them in the folder (developer) | `Automation Developer` | `Allow to be Automation Developer` |
| Publish packages only, no job start (CI/CD publisher) | `Automation Publisher` | `Allow to be Automation Publisher` |
| Publish **and** run, no project creation | `Automation Publisher` + `Automation User` | `Allow to be Automation Publisher` + `Allow to be Automation User` |
| Manage one folder and its subfolders | `Folder Administrator` | `Allow to Be Folder Administrator` (capital `B` in the docs; match case-insensitively, Step 2) |
| Manage all tenant entities (tenant-wide admin) | `Folder Administrator` in each folder to manage | `Orchestrator Administrator` |
| Create, edit, delete solution packages and manage solution deployments | — | `Solutions Administrator` |
| View, edit, create solution packages and package versions | — | `Solutions Contributor` |
| None of the above carries the permission | Custom role — see [Custom Role](#custom-role-only-when-needed) | Custom role |

Notes:

- `Automation Developer` has no direct access to expensive resources such as storage buckets. Need those → custom role for the missing permission (Rule 4).
- `Automation Publisher` has no `Jobs` permissions. Pair it with `Automation User` to run what it publishes.
- `Orchestrator Administrator` holds all tenant-level permissions. The legacy `Administrator` role maps to `Orchestrator Administrator` (tenant) + `Folder Administrator` (folder); `Robot` maps to `Allow to be Automation User` + `Automation User`.
- **Tenant Administrator** is an Automation Cloud tenant role (Admin portal, `uip admin`), not an Orchestrator role. It holds the same Orchestrator permissions as `Orchestrator Administrator`. It does not appear in `uip or roles list`.

Source for names and permissions: [Orchestrator default roles — Standard roles](https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/default-roles#standard-roles). Read the per-role permission tables there before deciding a permission is missing.

---

## Steps

### Step 1: Find the principal and read current roles

```bash
uip or users list --username "<USERNAME>" --output json
uip or roles user-roles list "<USERNAME>" --output json
```

`users list` returns the user key (`Key`; `--username` is a contains match, so pick the exact `UserName`). `roles user-roles list` returns one row per assignment — `Scope` (`Tenant` or `Folder`), `FolderPath`, `Role` (the role name). For a robot account, a group, or an external application, pass `--type Robot`, `--type Group`, or `--type ExternalApplication`. Note every role already held at the scope you change.

### Step 2: Find the role keys

Assign commands take role keys (GUIDs), and Step 1 gives names. Look up the new standard roles **and** the roles from Step 1. Filter on the shared part of the pair's name — one call returns the folder role and its `Allow to be …` tenant role:

```bash
uip or roles list --limit 1000 --output json \
  --output-filter "[?contains(Name, 'Automation User')].{Key: Key, Name: Name, Type: Type, IsEditable: IsEditable}"
```

`Type` tells which assign command takes the key: `Tenant` → `users assign-roles`, `Folder` → `users assign` / `roles assign`. `contains` is case-sensitive: use a fragment with no varying case (`'Folder Administrator'`, not `'Allow to be Folder'`). Empty result → rerun without `--output-filter` and match `Name` or `DisplayName` ignoring case.

### Step 3: Assign the tenant role

```bash
uip or users assign-roles <USER_KEY> --role-keys <TENANT_ROLE_KEYS> --output json
```

`<TENANT_ROLE_KEYS>`: comma-separated GUIDs — the new tenant role **plus** every `Tenant`-scope role from Step 1. To add one tenant role without rebuilding the list, `uip or roles users set <TENANT_ROLE_KEY> --add-user-keys <USER_KEY> --output json` is additive.

### Step 4: Assign the folder role

```bash
uip or users assign --user-key <USER_KEY> --folder-path "<FOLDER_PATH>" --role-keys <FOLDER_ROLE_KEYS> --output json
```

`--folder-key <FOLDER_KEY>` works in place of `--folder-path`. `uip or roles assign` takes the same options. `<FOLDER_ROLE_KEYS>`: the new folder role plus every role the principal already holds in that folder. Repeat per folder.

### Step 5: Check effective permissions

```bash
uip or roles user-permissions list "<USERNAME>" --output json
uip or roles user-permissions list "<USERNAME>" --folder-path "<FOLDER_PATH>" --output json
```

Without a folder option: tenant-level roles and permissions. With one: roles and permissions in that folder. Expected permission missing → recheck Step 3–4 payloads before considering a custom role.

---

## Custom Role (only when needed)

1. Pick the closest standard role from the [Decision Tree](#decision-tree) and read its grants:

   ```bash
   uip or roles get <STANDARD_ROLE_KEY> --output json
   ```

2. Find the exact name of the missing permission:

   ```bash
   uip or roles permissions list --limit 1000 --output json
   ```

3. Tell the user which permission no standard role carries. Proceed only after they agree.
4. Create a small custom role holding **only** the missing permissions, and assign it **on top of** the standard role — a principal's permissions are the union of its roles, so the standard role keeps its UiPath-maintained grants:

   ```bash
   uip or roles create --name "<ROLE_NAME>" --type Folder --output json
   uip or roles update <CUSTOM_ROLE_KEY> --add-permissions "<PERMISSION_NAMES>" --output json
   ```

   `--type Tenant` for a tenant permission. `roles update` refuses a permission whose scope does not fit the role type.
5. Add the custom role key to the union in Step 3 or Step 4, then verify with Step 5.

---

## Anti-Patterns

- **Creating a custom role that copies a standard role's permissions.** Assign the standard role instead; add a custom role only for the missing permissions.
- **Assigning only the folder role.** The matching `Allow to be …` tenant role is missing; assign both (Rule 2).
- **Assigning a role key with only the new role.** Replaces every other role at that scope (Rule 5).
- **Running `roles update --add-permissions` on a standard role.** Standard roles cannot be changed (Rule 3).
- **Looking for Tenant Administrator in `uip or roles list`.** It is an Automation Cloud role; manage it with `uip admin`.
