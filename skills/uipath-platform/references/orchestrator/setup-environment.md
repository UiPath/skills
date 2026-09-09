# Setup Environment

Create folders, assign users and roles, provision machines, and configure licenses.

## When to Use

- Set up a tenant or onboard users.
- Provision machine templates and CI/CD license slots.
- Script repeatable dev/staging/prod environments.

## Prerequisites

1. Run `uip login status`; if unauthenticated, ask the user to run `uip login` (interactive browser flow).
2. Run `uip login tenant set <tenant-name>`.
3. Confirm tenant-admin or folder-create permissions.

Create folders, roles, and permissions; import and assign users; create and assign machines; then configure licenses. Save response keys: folder keys feed assignments, user keys feed role bindings, and machine keys feed license operations.

## Step 1: Create Folders

Create folders first because later resources target them. Run:

```bash
uip or folders create "Finance" --output json
uip or folders create "Invoicing" --parent "Finance" -d "Invoice processing" --output json
```

Options:

- `--parent <key-or-path>` — GUID key or path such as `"Shared"`.
- `--description <text>` / `-d <text>` — description.
- `--permission-model <model>` — `FineGrained` (default) or `InheritFromTenant`.
- `--feed-type <type>` — `Processes` (default; tenant-level processes feed), `FolderHierarchy` (folder-scoped feed inherited by subfolders), or `Libraries` (tenant libraries feed).

Save `Data.Key` for later `--folder-path` or `--folder-key` use.

## Step 2: Explore Folders

Run:

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

Without `--all`, `folders list` returns only folders assigned to the current user. Run `folders list --all` before using `--type`, `--name`, `--path`, `--top-level`, or `--sort-by`. `folders move` and `folders delete` require admin permissions and accept paths or GUIDs. Delete only empty folders; first remove or move their processes, queues, assets, and subfolders.

## Step 3: Create Roles

`uip or roles` is the Orchestrator RBAC catalog, separate from Identity/organization roles (`uipath-admin`: `uip admin authorization roles`). Roles in one store do not appear in the other. Use `uip or roles` for Orchestrator roles, permissions, and user/folder assignments; use `admin authorization roles` only for org-level Identity roles spanning services.

Run:

```bash
uip or roles create --name "FinanceOperator" --type Folder --output json
uip or roles update <role-key> --add-permissions "Assets.View,Assets.Edit,Queues.View,Jobs.Create,Jobs.View" --output json
uip or roles permissions --output json
uip or roles get <key> --output json
```

Role types are `Tenant` (tenant-wide; assign with `uip or users assign-roles`) and `Folder` (folder-scoped; assign with `uip or users assign` or `uip or roles assign`).

`users assign-roles`, `users assign`, and `roles assign` destructively replace role lists at their respective scopes. Run `uip or roles user-roles list <user-key> --output json` first and pass the complete desired union. For additive membership on one role, run `uip or roles users <role-key> --add-users <user-key>`; this does not replace other assignees.

Run:

```bash
uip or roles list --output json
uip or roles permissions --output json
uip or roles user-permissions <user-key-guid> --folder-path "Finance" --output json
uip or roles user-roles <user-key-guid> --output json
uip or roles users <role-key> --add-users <user-key-1>,<user-key-2> --output json
uip or roles users <role-key> --remove-users <user-key-1> --output json
uip or roles delete <role-key> --output json
uip or roles users list <role-key> --output json
```

Use `user-permissions` for effective tenant-plus-folder permissions, `user-roles` for assignments, and `roles users list` for forward lookup of users, groups, robots, and external applications. `Pagination.Total` is the complete role-membership count; an empty role returns `Data: []` and `Total: 0`.

## Step 4: Import Users from Identity Service

Identity Service (IS) owns principals. `users import` is the only IS-to-tenant integration point; downstream commands use the resolved Orchestrator user key. Legacy `users create` and `users delete` are unavailable. Run:

```bash
uip or users import --username "jane.doe@example.com" --type DirectoryUser --domain "uipath" --output json
uip admin robot-accounts create "InvoiceRunner" --output json
uip or users import --directory-id <id-from-above> --type DirectoryRobot --domain autogen --output json
uip admin external-apps list --search "MyApp" --output json
uip or users import --directory-id <id-from-above> --type DirectoryExternalApplication --domain autogen --output json
```

`--type <type>` is required: `DirectoryUser` (human), `DirectoryGroup` (directory group; folder grants apply to members), `DirectoryRobot` (IS robot account; standard unattended identity — without it, or a `DirectoryUser` with unattended permissions, `jobs start` returns `HTTP 409: Couldn't find any user with unattended robot permissions in the current folder.`), or `DirectoryExternalApplication` (IS client-credentials application). `--domain <domain>` is required. Use `autogen` for `DirectoryRobot` and `DirectoryExternalApplication`; use the tenant IS directory domain for `DirectoryUser` and `DirectoryGroup`.

Provide exactly one principal identifier. `--username <name>` resolves `<domain>\\<name>` and suits `DirectoryUser`/`DirectoryGroup` in on-prem AD or classic IS; cloud SSO lookups typically require `--directory-id`. `--directory-id <uuid>` is required for `DirectoryRobot` and `DirectoryExternalApplication` — the server-side `UserService.CreateAsync` rejects these types with HTTP 400 unless the tenant user-record `Key` matches the IS identifier, and `Key` is only populated when `--directory-id` is set. Find IDs by running:

```bash
uip admin robot-accounts create <name>
uip admin robot-accounts list --search <name>
uip admin external-apps list
uip admin users list --search <name>
```

Use `.Data.id` for robot-account creation, `.Data[].id` for robot-account listings, `.Data[].appId` for external apps, and `.Data[].id` for human users.

For one-shot folder assignment, pass `--folder-path <path>` or `--folder-key <key>` together with `--role-keys <guids>`; pass neither for import-only. Save the Orchestrator `Key`, obtainable by running `uip or users list --username "<imported-name>"`.

### Step 4b: Inspect, Edit, Unassign, or Remove Users

Run:

```bash
uip or users current --output json
uip or users get <user-key-guid> --output json
uip or users list-available --folder-path "Finance" --search "jane" --output json
uip or users update <user-key-guid> --allow-unattended --license-type Unattended --unattended-username "DOMAIN\\jane.doe" --unattended-password "<secret-or-cred-store-name>" --output json
uip or users unassign <user-key-guid> --folder-path "Finance" --output json
```

`users update` changes tenant-side flags only. Mutually exclusive pairs are `--allow-unattended`/`--deny-unattended`, `--allow-attended`/`--deny-attended`, `--allow-login`/`--deny-login`, `--allow-personal-workspace`/`--deny-personal-workspace`, and `--active`/`--inactive`. `--license-type <Attended|Unattended|...>` sets the license profile.

For a `DirectoryUser`, first enabling unattended requires both `--unattended-username <user>` and `--unattended-password <pass>`, using `DOMAIN\\name`. The password may be literal or a credential-store entry; use `--credential-store-key <guid>` when stored externally. `DirectoryRobot` imports need no unattended credentials; run `users update --license-type Unattended` on its key.

Do not use `users update` for roles. Run `uip or users assign`, `uip or users assign-roles`, or `uip or roles users <role-key> --add-users/--remove-users`. IS sync owns `--name`, `--surname`, and `--email`; local edits may be overwritten.

## Step 5: Assign Users to Folders

Run:

```bash
uip or users assign --user-key <user-key-guid> --folder-path "Finance" --role-keys <role-key-guid> --output json
uip or users list-in-folder --folder-path "Finance" --output json
```

Use `--folder-path` or `--folder-key`. `--role-keys` is optional: assignment without roles grants folder membership but no permissions. `users assign` and `roles assign` replace the target folder's role list. Run `uip or roles user-roles list <user-key> --output json` first and pass the complete desired union; the same replacement rule applies to `users assign-roles` for tenant roles.

## Step 6: Create Machines

Machines are tenant-scoped and require separate folder assignment. Run:

```bash
uip or machines create --name "finance-runner-01" --output json
```

Options: `--serverless`, `--unattended-slots <n>`, `--headless-slots <n>`, `--non-production-slots <n>`, `--testing-slots <n>`, and `-d, --description <text>`. Slot values must be whole numbers `>= 0`; `0` is allowed.

## Step 7: Assign Machines to Folders

Run:

```bash
uip or machines assign <machine-key-guid> --folder-path "Finance" --output json
uip or machines assign <key1> <key2> <key3> --folder-path "Finance" --output json
uip or machines list --folder-path "Finance" --output json
```

Assign a machine before folder jobs use it.

### Step 7b: Inspect, Edit, Unassign, or Delete Machines

Run:

```bash
uip or machines get <machine-key-guid> --output json
uip or machines update <machine-key-guid> --unattended-slots 4 --headless-slots 2 --name "finance-runner-01-renamed" --output json
uip or machines unassign <machine-key-guid> --folder-path "Finance" --output json
uip or machines delete <machine-key-guid> --yes --output json
uip or machines delete <key1> <key2> --yes --output json
```

`machines update` uses PATCH semantics. `machines update` and `machines delete` resolve cross-folder by GUID without `--folder-path`; delete removes the machine and all folder assignments without requiring unassignment. Each folder accepts one Cloud Robots / Serverless machine; a second returns `HTTP 409: Only one Cloud Robots - Serverless is allowed per folder.` `machines list` defaults to visible machines; folder filtering includes `IsAssignedToFolder`. Use `--all-fields` for raw camelCase DTOs, including `automationCloudSlots`, `automationCloudTestAutomationSlots`, and other slot subtypes.

Machine scopes are `Default` (standard on-premises template), `Shared`, `Serverless`, `Cloud`, `AutomationCloudRobot`, `ElasticRobot`, and `PersonalWorkspace`.

## Step 8: Configure Licenses

Check capacity, then toggle runtime licensing. Run:

```bash
uip or licenses info --output json
uip or licenses toggle <machine-key-guid> --type Unattended --enable --output json
uip or licenses list --type Unattended --output json
```

Supported runtime types are `Unattended`, `NonProduction`, `Headless`, and `TestAutomation`. Named-user types such as `Attended`, `Development`, and `Studio` cannot be toggled this way.

## Variations and Gotchas

- Use `update`, not `edit`: `uip or folders update <key>`, `machines update`, `processes update`, `roles update`, and `users update`. `edit` remains a deprecated hidden alias.
- Users may belong to folders without roles.
- The role resolver pages all roles client-side to map GUIDs to numeric IDs, which can delay the first role command in large tenants.
- `folders list --all` is required for filtering and exposes `FeedType` such as `FolderHierarchy` and `Processes`; plain `folders list` does not.
- `uip or folders list --all --type personal` returns personal workspaces with `Key`, `Name`, `OwnerName`, `OwnerKey`, and `LastLogin`; `--path` and `--top-level` are unsupported because personal workspaces are flat.

## Related

- [Run Jobs](run-jobs.md) — After setup, deploy packages and start jobs in the folder.
- Create assets, queues, and buckets in the folder → [resources.md](resources.md)