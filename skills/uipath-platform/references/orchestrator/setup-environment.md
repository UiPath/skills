# Setup Environment

Create folders, assign users and roles, provision machines, and configure licenses.

---

## When to Use

- Set up a new tenant for a team or project.
- Onboard users into an existing Orchestrator environment.
- Provision machine templates and license slots for CI/CD.
- Script repeatable dev/staging/prod environments.

## Prerequisites

1. Verify authentication with `uip login status`; if needed, ask the user to run `uip login` (interactive browser flow).
2. Select a tenant: `uip login tenant set <tenant-name>`.
3. Have tenant-level admin or folder-create rights.

---

## Flow

Run in order: create folders, create and update roles, import and assign users, create and assign machines, then toggle licenses. Folder keys feed assignments, user keys feed role bindings, and machine keys feed license toggles.

---

## Steps

### Step 1: Create Folders

Create folders first; later resources target them. Save response `Key` for later `--folder-path` or `--folder-key`.

```bash
uip or folders create "Finance" --output json
uip or folders create "Invoicing" --parent "Finance" -d "Invoice processing" --output json
```

Options: `--parent <key-or-path>` (GUID key or path such as `"Shared"`); `--description <text>`; `--permission-model <model>`: `FineGrained` (default, per-folder RBAC) or `InheritFromTenant`; `--feed-type <type>`: `Processes` (default; shares the **tenant-level** processes feed), `FolderHierarchy` (own **folder-scoped** feed inherited by sub-folders), or `Libraries` (tenant libraries feed).

### Step 2: Explore Folders

Verify folders before proceeding:

```bash
uip or folders list --output json
uip or folders list --all --output json
uip or folders list --all --type standard --top-level --output json
uip or folders get "Finance" --output json
uip or folders get <folder-key-guid> --output json
uip or folders runtimes "Finance" --output json
uip or folders move "Finance/Invoicing" --parent "Operations" --output json
uip or folders move <folder-key-guid> --root --output json
uip or folders delete "Finance/Invoicing" --output json
uip or folders delete <folder-key-guid> --output json
```

`--all` enables `--type`, `--name`, `--path`, `--top-level`, and `--sort-by`; without it, list returns only folders assigned to the current user and rejects filter flags. `move` and `delete` require admin rights and accept a path or GUID. `delete` requires no processes, queues, assets, or sub-folders; clean or move them first. `folders list --all` includes `FeedType` (for example `FolderHierarchy`, `Processes`); plain `folders list` does not. Use `--all` or `folders get` for `FeedType`.

### Step 3: Create Roles

Roles start with zero permissions and are tenant- or folder-scoped. For every Orchestrator role/permission lifecycle—create, add/remove permissions, assign to users/folders—use `uip or roles`; use `admin authorization roles` only for org-level Identity roles spanning services. The catalogs are disjoint: a role created with `admin authorization roles` does NOT appear in `uip or roles list`, and vice versa; both support Tenant-scoped roles, so that phrase alone is ambiguous. `uip or roles` is distinct from Identity/organization authorization roles (`uip admin authorization roles`, see [uipath-admin](/uipath:uipath-admin)).

```bash
uip or roles create --name "FinanceOperator" --type Folder --output json
uip or roles update <role-key> \
  --add-permissions "Assets.View,Assets.Edit,Queues.View,Jobs.Create,Jobs.View" \
  --output json
```

Discover the complete grants catalogue with `uip or roles permissions list --limit 1000`; the default `--limit` of 50 is incomplete. Inspect grants with `uip or roles get <key>`.

Role types: **Tenant** applies across the tenant and is assigned with `uip or users assign-roles`; **Folder** applies within folders and is assigned with `uip or users assign` or `uip or roles assign`.

> **⚠️ All three role-assign commands are destructive.** `users assign-roles`, `users assign`, and `roles assign` each **replace** the user's role list at their respective scope (tenant or per-folder). Roles not in `--role-keys` are removed silently. Always read the current roles first with `uip or roles user-roles list <username> --output json` and pass the full desired union. For additive membership on one role, run `uip or roles users set <role-key> --add-user-keys <user-key>`; this does not replace other assignees.

#### Inspect / Audit / Delete Roles

```bash
uip or roles list --limit 1000 --output json
uip or roles permissions list --limit 1000 --output json
uip or roles user-permissions list <username> --folder-path "Finance" --output json
uip or roles user-roles list <username> --output json
uip or roles users set <role-key> --add-user-keys <user-key-1>,<user-key-2> --output json
uip or roles users set <role-key> --remove-user-keys <user-key-1> --output json
uip or roles delete <role-key> --output json
uip or roles users list <role-key> --output json
```

The permissions catalogue default is 50; `--output-filter` requires explicit `--limit`; use 1000 for the full catalogue. `user-permissions` reports effective tenant-plus-folder permissions, including inherited roles and tenant overrides; `user-roles` reports assignments. `permissions`, `user-roles`, `user-permissions`, and `users` are groups: without `list` (or `set`) they print help and exit 1 or reject a following value as an unknown command.

`uip or roles users list <role-key> --output json` lists users, groups, robots, and external applications. `Pagination.Total` is the complete membership count; an empty role returns `Data: []` and `Total: 0`. For tenant audit, use one call per role, not a directory sweep per principal.

### Step 4: Import Users from Identity Service

Identity Service (IS) owns principals. `users import` is the single IS-to-tenant integration point; downstream commands use the resolved Orchestrator user-key and make no further IS round-trips. Legacy `users create` / `users delete` are gone because they target `ProvisionType=Manual`, not cloud or IS-backed users.

```bash
uip or users import --username "jane.doe@example.com" --type DirectoryUser --domain "uipath" --output json
uip admin robot-accounts create "InvoiceRunner" --output json
uip or users import --directory-id <id-from-above> --type DirectoryRobot --domain autogen --output json
uip admin external-apps list --search "MyApp" --output json
uip or users import --directory-id <id-from-above> --type DirectoryExternalApplication --domain autogen --output json
```

`--type <type>` is required; the CLI will not guess. Values: `DirectoryUser` (human user), `DirectoryGroup` (directory group; folder grants apply to members), `DirectoryRobot` (IS robot account and standard unattended identity), and `DirectoryExternalApplication` (IS-registered client-credentials principal). Without `DirectoryRobot`, or a `DirectoryUser` with unattended permissions, `jobs start` returns `HTTP 409: Couldn't find any user with unattended robot permissions in the current folder.`

`--domain <domain>` is the IS directory domain: use `autogen` for `DirectoryRobot` / `DirectoryExternalApplication`; for `DirectoryUser` / `DirectoryGroup`, use the tenant IS domain (typically cloud org slug or on-prem AD domain).

Provide exactly one identifier: `--username <name>` or `--directory-id <uuid>`. `--username` works for `DirectoryUser` / `DirectoryGroup` when IS resolves `<domain>\<name>` (on-prem AD/classic IS); cloud SSO lookup typically fails, so use `--directory-id`. `--directory-id` is required for `DirectoryRobot` and `DirectoryExternalApplication`. Server-side `UserService.CreateAsync` rejects those types with HTTP 400 unless tenant-user `Key` matches the IS identifier; that `Key` is populated only with `--directory-id`.

Find UUIDs with `uip admin robot-accounts create <name>` (new robot `.Data.id`), `uip admin robot-accounts list --search <name>` (existing robot `.Data[].id`), `uip admin external-apps list` (IS app `.Data[].appId`), or `uip admin users list --search <name>` (human `.Data[].id`).

Optional one-shot folder assignment uses `--folder-path <path>` or `--folder-key <key>` plus `--role-keys <guids>`; pass both together or neither. After import, save the Orchestrator `Key`, returned by `users list --username "<imported-name>"`, for `users assign`, `users assign-roles`, `roles assign`, and related commands.

### Step 4b: Inspect / Edit / Unassign / Remove Users

```bash
uip or users current --output json
uip or users get <user-key-guid> --output json
uip or users list-available --folder-path "Finance" --search "jane" --output json
uip or users update <user-key-guid> \
  --allow-unattended \
  --license-type Unattended \
  --unattended-username "DOMAIN\\jane.doe" --unattended-password "<secret-or-cred-store-name>" \
  --output json
uip or users unassign <user-key-guid> --folder-path "Finance" --output json
```

`users get` takes a user key (or numeric id). `list-available` filters users not assigned to a folder. `users update` is the only place to grant unattended on a `DirectoryUser`; it does not change roles. Use `uip or users assign`, `uip or users assign-roles`, or `uip or roles users set <role-key> --add-user-keys/--remove-user-keys` for roles.

Mutually exclusive toggle pairs are `--allow-unattended`/`--deny-unattended`, `--allow-attended`/`--deny-attended`, `--allow-login`/`--deny-login`, `--allow-personal-workspace`/`--deny-personal-workspace`, and `--active`/`--inactive`. Other flags: `--license-type <Attended|Unattended|...>`, `--unattended-username <user>`, `--unattended-password <pass>`, and `--credential-store-key <guid>`. When first enabling unattended for a `DirectoryUser`, provide username and password together; username is typically `DOMAIN\\name`, and password may be a literal or credential-store entry paired with `--credential-store-key <guid>`.

`DirectoryRobot` import needs no unattended username/password because IS carries its credentials; run `users update --license-type Unattended` on its key. Directory identity fields such as `--name`, `--surname`, and `--email` come from IS sync; updating them changes only the cached Orchestrator copy and may be overwritten.

### Step 5: Assign Users to Folders

```bash
uip or users assign \
  --user-key <user-key-guid> \
  --folder-path "Finance" \
  --role-keys <role-key-guid> \
  --output json
uip or users list-in-folder --folder-path "Finance" --output json
```

`--role-keys` is optional: assignment without roles grants folder access but no permissions until roles are added. Use `--folder-path` such as `"Finance"` or `"Finance/Invoicing"`, or `--folder-key` (GUID).

> **⚠️ Destructive — REPLACE semantics.** `users assign` (and the equivalent `roles assign`) **replaces** the user's folder-level role list in the target folder with whatever you pass in `--role-keys`. Roles not in the payload are removed silently. To **add** a role without dropping others, first read the existing folder roles with `uip or roles user-roles list <user-key> --output json`, then pass the full desired union to `--role-keys`. The same applies to `users assign-roles` for tenant-level roles.

### Step 6: Create Machines

Machines are tenant-scoped execution hosts with license slots; assign them to folders separately.

```bash
uip or machines create --name "finance-runner-01" --output json
```

Options: `--serverless`; `--unattended-slots <n>`; `--headless-slots <n>`; `--non-production-slots <n>`; `--testing-slots <n>`; and `-d, --description <text>`.

### Step 7: Assign Machines to Folders

Assign machines before jobs in the folder can use them.

```bash
uip or machines assign <machine-key-guid> --folder-path "Finance" --output json
uip or machines assign <key1> <key2> <key3> --folder-path "Finance" --output json
uip or machines list --folder-path "Finance" --output json
```

### Step 7b: Inspect / Edit / Unassign / Delete Machines

```bash
uip or machines get <machine-key-guid> --output json
uip or machines update <machine-key-guid> \
  --unattended-slots 4 --headless-slots 2 \
  --name "finance-runner-01-renamed" --output json
uip or machines unassign <machine-key-guid> --folder-path "Finance" --output json
uip or machines delete <machine-key-guid> --yes --output json
uip or machines delete <key1> <key2> --yes --output json
```

`machines update` and `machines delete` resolve cross-folder by GUID and need no `--folder-path`; update echoes a renamed machine and has PATCH semantics (only provided fields change); `unassign` removes the machine from a folder but it still exists at tenant level. Slot flags (`--unattended-slots`, `--headless-slots`, `--non-production-slots`, `--testing-slots`) are whole numbers `>= 0`; `0` is allowed. Delete removes the machine and all folder assignments without requiring unassign or `--force`.

Each folder accepts one Cloud Robots / Serverless machine; assigning a second returns `HTTP 409: Only one Cloud Robots - Serverless is allowed per folder.` `machines list` defaults to all visible machines; `--folder-path`/`--folder-key` filters assignments and includes `IsAssignedToFolder`. `--all-fields` emits the raw camelCase DTO, including slot subtypes such as `automationCloudSlots` and `automationCloudTestAutomationSlots`.

### Step 8: Configure Licenses

Check capacity, then toggle runtime licensing:

```bash
uip or licenses info --output json
uip or licenses toggle <machine-key-guid> --type Unattended --enable --output json
uip or licenses list --type Unattended --output json
```

Supported toggle types are `Unattended`, `NonProduction`, `Headless`, and `TestAutomation`. Named-user types (`Attended`, `Development`, `Studio`, etc.) cannot be toggled and are managed differently.

---

## Complete Example

End-to-end script setting up a "Finance" folder with a user, role, and machine:

```bash
# 1. Authenticate
uip login --output json
uip login tenant set "Production" --output json

# 2. Create the folder
uip or folders create "Finance" -d "Finance department automations" --output json
# Response: { "Data": { "Key": "a1b2c3d4-...", "Path": "Finance" } }

# 3. Create a folder role and add permissions
uip or roles create --name "FinanceOperator" --type Folder --output json
# Response: { "Data": { "Key": "r1r2r3r4-..." } }

uip or roles update r1r2r3r4-... \
  --add-permissions "Assets.View,Assets.Edit,Queues.View,Jobs.Create,Jobs.View,Processes.View" \
  --output json

# 4. Import a user from Identity Service (--type is required; --directory-id required for Robot/ExtApp)
uip or users import --username "jane.doe@example.com" --type DirectoryUser --domain "uipath" --output json
# (Look up the assigned Key with: uip or users list --username "jane.doe@example.com")

# 5. Assign user to folder with role
uip or users assign \
  --user-key u1u2u3u4-... \
  --folder-path "Finance" \
  --role-keys r1r2r3r4-... \
  --output json

# 6. Create a machine
uip or machines create --name "finance-runner-01" \
  --unattended-slots 2 -d "Finance department runner" --output json
# Response: { "Data": { "Key": "m1m2m3m4-..." } }

# 7. Assign machine to folder
uip or machines assign m1m2m3m4-... --folder-path "Finance" --output json

# 8. Enable licensing
uip or licenses toggle m1m2m3m4-... --type Unattended --enable --output json

# 9. Verify the setup
uip or folders runtimes "Finance" --output json
uip or users list-in-folder --folder-path "Finance" --output json
uip or machines list --folder-path "Finance" --output json
```

---

## Variations and Gotchas

### The mutation verb is `update` (`edit` is a deprecated alias)

Use `update` for all five admin nouns: `uip or folders update <key>`, `machines update`, `processes update`, `roles update`, and `users update`. `edit` remains a hidden backward-compatible alias; new scripts should use `update`.

### Users can be assigned without roles

`--role-keys` on `uip or users assign` is optional. Such users appear in the folder user list but have no permissions until roles are added.

### Machine scopes

| Scope | Description |
|-------|-------------|
| `Default` | Standard on-premises machine template. |
| `Shared` | Shared across folders. |
| `Serverless` | Cloud-hosted, created with `--serverless`. |
| `Cloud` | UiPath cloud machine. |
| `AutomationCloudRobot` | Automation Cloud Robot. |
| `ElasticRobot` | Elastic (auto-scaling) cloud machine. |
| `PersonalWorkspace` | Bound to a personal workspace. |

### Role resolver pages all roles client-side

The role resolver fetches all roles to map GUIDs to numeric IDs, adding a brief first-use delay in large custom-role tenants.

### Personal workspaces are flat

`uip or folders list --all --type personal` returns personal workspaces with shape `Key`, `Name`, `OwnerName`, `OwnerKey`, `LastLogin`. `--path` and `--top-level` are unsupported because personal workspaces have no hierarchy.

---

## Related

- [Run Jobs](run-jobs.md) — After setup, deploy packages and start jobs in the folder.
- Create assets, queues, and buckets in the folder → [resources.md](resources.md)