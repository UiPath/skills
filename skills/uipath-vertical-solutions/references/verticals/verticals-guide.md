# Verticals

Each Vertical Solution installs different things. One file per vertical lists its packages, the values a deploy asks for, what must exist before the first deploy, the setup after it, and the tenant and folder access the deploy needs.

| Vertical | File | Packages |
|----------|------|----------|
| FINS (Financial Services) | [fins-guide.md](fins-guide.md) | `fins.qaqc-uipath`, `fins.loan-setup` |

## Check a user against a vertical

1. Find the vertical's file from the package name in the table above. When the package is not listed, no access list exists for it yet: say so, and fall back to the per-step table in [access-troubleshooting-guide.md](../access-troubleshooting-guide.md).
2. Read the user's live permissions. Reading them needs the Roles and Users view permissions. When that is refused, follow the `403` case in [Check the Access](../../SKILL.md#check-the-access):

   ```bash
   uip or roles user-permissions list <USER_NAME> --output json
   uip or roles user-permissions list <USER_NAME> --folder-path "<TARGET_FOLDER>" --output json
   ```

   The first reads the tenant level, the second the folder level. `--folder-path` counts only the roles assigned on that one folder. When the target is a subfolder (`Shared/Production`), a role on a parent folder also applies. Check each parent folder too, or read `uip or roles user-roles list <USER_NAME> --output json`, before you report a folder line as missing.
3. Compare each table in the vertical's file with the matching output, using the exact permission names. Skip lines marked for the other package.
4. Report what is missing at each level, with the line's **Source**. A missing *Inferred* line may not be needed: say so, and let the deploy confirm it.
5. Do not grant anything without being asked. Give the exact change.

## Add a vertical

The skill works for a vertical with no file, but it can only ask the user for the package name and fall back to the general access table. A file makes the deploy guided. When a vertical onboards, its team adds one in a pull request to this skill:

1. **Packages.** Run `uip vss deploy` at a terminal, pick the vertical, and note each package's name as the picker lists it. Stop at the next question.
2. **Values.** For each package, run the dry run without `--yes`:

   ```bash
   uip vss deploy --package-name <PACKAGE_NAME> --folder-path "<FOLDER_PATH>" --no-seed --no-interactive --output json
   ```

   Each `Configuration for ... is required` names a `--config` value, and each `<RESOURCE>.<PROPERTY> is declared required` warning names a `deploy-config.json` value. Say in plain words what each one is.
3. **Before the first deploy.** List what must exist before a deploy can run that the deploy does not create: external applications, entitlements, licenses.
4. **After the deploy.** List only the setup this vertical's solutions need and the deploy does not do, such as the vertical's own groups or role mappings. For each step, say who does it, where (the exact menu path or entity), the names to use, and what breaks without it. Take it from the vertical team's own docs and name them. Leave out the platform's generic checklist (accounts, robots, machines, assets): it is not specific to the vertical.
5. **Access.** Use the permission names `uip or roles user-permissions list` prints. Mark each line's **Source**: the vertical's own documentation, a refusal seen on a real deploy, or inferred from what the package installs.
6. **Confirm.** Deploy once as a user who holds only the listed access. Each missing permission is refused by name: add it, and mark it *Seen*.
7. Copy the block below to `<VERTICAL>-guide.md` in this folder, fill it in, and add a row to the table above. `SKILL.md` does not need to change.

```markdown
# <VERTICAL>

## Packages

| Package | `--package-name` | Steps that run |
|---------|------------------|----------------|
| <DISPLAY_NAME> | `<PACKAGE_NAME>` | PRE_VERIFY, SOLUTION, ... |

Say where the package names were seen, and whether the Data Fabric entities
are tenant-level or folder-level.

## Values you will be asked for

| Package | Value | How to pass it | What it is |
|---------|-------|----------------|------------|

Take them from a dry run (without `--yes`), and say which an upgrade asks for again.

## Before the first deploy

## After the deploy

Who does each step, where, the names to use, and what breaks without it.

## Access

### Tenant level

| Permission | Why | Source |
|------------|-----|--------|

### Folder level, on the target folder

| Permission | Why | Source |
|------------|-----|--------|

### Seed (`uip vss deploy seed`), on the solution folder

| Permission | Why | Source |
|------------|-----|--------|

## Not yet known
```
