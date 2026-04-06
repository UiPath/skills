# Access Control Guide

Manage users and roles via `uip or users` and `uip or roles`.

## Concepts

Access control operates at two scopes: **Tenant** (global) and **Folder** (per-folder). Match role type to assignment scope.

- **User key** — GUID from `users list`
- **Role key** — GUID from `roles list-roles`

---

## User Commands

### 1. List Users

```bash
uip or users list --output json                                          # Tenant-wide
uip or users list-in-folder --folder-path "<FOLDER_PATH>" --output json  # In folder (--include-inherited for parent)
uip or users list-available --folder-path "<FOLDER_PATH>" --output json  # Available for folder assignment
uip or users current --output json                                       # Current user
uip or users get <USER_KEY> --output json                                # User details
```

### 2. Create a User

```bash
uip or users create \
  --username "<USERNAME>" --name "<FIRST>" --surname "<LAST>" \
  --email "<EMAIL>" --role-keys "<ROLE_KEY>" --output json
```

| Option | Required | Description |
|---|---|---|
| `--username`, `--name`, `--surname`, `--email` | Yes | Identity fields |
| `--role-keys` | Yes | Comma-separated tenant role GUIDs |
| `--type` | No | `User` (default) or `Robot` |
| `--license-type` | No | `Attended`, `Unattended`, `StudioPro` |
| `--allow-unattended` / `--deny-unattended` | No | Unattended robot license |
| `--allow-attended` / `--deny-attended` | No | Attended robot license |
| `--allow-login` / `--deny-login` | No | Interactive login |
| `--active` / `--inactive` | No | Initial state |

### 3. Edit / Delete a User

```bash
uip or users edit <USER_KEY> --name "<NEW_NAME>" --output json
uip or users delete <USER_KEY> --output json
```

`edit` accepts all `create` options. `delete` is irreversible.

### 4. Folder Assignment

```bash
uip or users assign --user-key <KEY> --folder-path "<PATH>" --role-keys "<ROLE_KEY>" --output json
uip or users unassign --user-key <KEY> --folder-path "<PATH>" --output json
```

> `--role-keys` is **required** for folders with fine-grained permissions (the default). Use folder-scoped role GUIDs from `roles list-roles`.

### 5. Tenant Role Assignment

```bash
uip or users assign-roles <USER_KEY> --role-keys "<ROLE_KEY>" --output json
```

---

## Role Commands

```bash
uip or roles list-permissions --output json         # All grantable permissions
uip or roles list-roles --output json               # All roles (key, name, type, editable)
uip or roles get-role <ROLE_KEY> --output json       # Role details + permissions
uip or roles create-role --name "<NAME>" --type <Tenant|Folder> --output json
uip or roles edit-role <ROLE_KEY> --output json      # Update permissions
uip or roles delete-role <ROLE_KEY> --output json    # User-defined only
uip or roles list-role-users <ROLE_KEY> --output json
uip or roles set-role-users <ROLE_KEY> --add-user-keys "<K1>,<K2>" --remove-user-keys "<K3>" --output json
uip or roles list-user-roles "<USERNAME>" --output json   # All assignments (tenant + folder)
uip or roles assign --user-key <KEY> --role-keys "<RK>" --folder-path "<PATH>" --output json
```

---

## Anti-Patterns

- **Do not assume role keys** — always retrieve GUIDs from `list-roles`.
- **Do not mix role types** — assigning a Tenant role via folder `users assign` fails. Match role type to scope.
- **Do not create a user without `--role-keys`** — required even if you only need folder-level roles. Use a minimal tenant role.
- **Do not delete built-in roles** — `delete-role` fails on non-editable roles.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `users create` fails "role not found" | Invalid GUID in `--role-keys` | Get exact key from `roles list-roles` |
| `users assign` fails "role type mismatch" | Tenant role used for folder assignment | Use Folder-scoped roles only |
| `users assign` fails "Users should only be assigned with specific roles" | `--role-keys` omitted on fine-grained folder | Add at least one folder-scoped role GUID |
