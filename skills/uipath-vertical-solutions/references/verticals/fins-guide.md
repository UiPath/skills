# FINS (Financial Services)

What a first deploy of a FINS package needs, the access a **user login** needs to deploy and seed it with `uip vss deploy`, and how to set up who may use a deployed solution.

## Packages

| Package | `--package-name` | Steps that run |
|---------|------------------|----------------|
| Lending QA/QC | `fins.qaqc-uipath` | PRE_VERIFY, SOLUTION, BUCKET_FILES, ASSETS, PROCESS_CONFIG, TRIGGERS |
| Loan Setup | `fins.loan-setup` | PRE_VERIFY, SOLUTION, PROCESS_CONFIG, TRIGGERS |

Package names are the ones the service lists for the `fins` vertical at the time of writing. The picker in `uip vss deploy` shows the current list.

Both packages install their Data Fabric entities inside the solution folder, so they are folder-level, not tenant-level.

## Values you will be asked for

From the package manifests and a dry run. The dry run names any value a newer version adds.

| Package | Value | How to pass it | What it is |
|---------|-------|----------------|------------|
| Loan Setup | `LOAN_SETUP_MANAGER_EMAIL` (required) | `--config LOAN_SETUP_MANAGER_EMAIL=<MANAGER_EMAIL>` | The Loan Setup manager's email address. The package gives no description, and its sample value is a placeholder address: ask the user for a real one |
| Both | `Webapp.routingName` | `deploy-config.json` | Name used in the web app's address. The package does not state its rules: to be safe, use lowercase letters, numbers and hyphens, unique on the tenant, such as `loan-setup`. The portal checks it |
| Both | `Webapp.externalClientId` | `deploy-config.json` | Client id of the external application the web app signs in with (see [Before the first deploy](#before-the-first-deploy)) |

```json
{
  "version": 1,
  "resources": [
    {
      "name": "Webapp",
      "configuration": {
        "routingName": "loan-setup",
        "externalClientId": "<CLIENT_ID>"
      }
    }
  ]
}
```

When the user does not have the client id yet, leave `externalClientId` out and keep `routingName`. The deploy then pauses on the portal's configuration wizard, where the client id can be filled in, and you resume the job after.

On an upgrade, pass `LOAN_SETUP_MANAGER_EMAIL` again. The web app values are kept by the deployment.

## Before the first deploy

An administrator does these once. The deploy does not:

- **The web app's external application**: non-confidential (**Admin** → **External Applications**). Its client id is `Webapp.externalClientId`. Managing external applications needs organization-level rights.
- **The `Vertical.Unlimited` entitlement** on the organization. The service refuses the job without it. It is a license, not a user permission.
- **The access** in the tables below, for the person who deploys.

## Set up a deployed solution

A separate task from the deploy, run when the user asks ("help me set up QA/QC", "who can use Loan Setup"), on any deployed copy. The deploy does not need it, and it does not need a new deploy.

It decides who may use the web app. Until it is done, **Lending QA/QC shows every user an access-denied screen**: it only lets in members of the groups below. Loan Setup limits only its admin portal, settings pages, feedback dashboard and solution tests to them. Source: the FINS team's role setup guide (`public_docs/rbac_setup.md` in the FINS solution repository).

**Who can do it.** Creating groups and adding members needs an organization administrator. Adding the role rows needs record access in the solution folder (the same as a seed, see [Seed](#seed-uip-vss-deploy-seed-on-the-solution-folder)). When the logged-in user cannot do a step, give them that step for an administrator, with the portal path, and go on with the rest.

Read first, then change. Show what is already there and what is missing, and ask for a yes before each change (Critical Rule 6).

**1. Find the deployment and its solution folder.**

```bash
uip solution deploy list --output json --output-filter "[].{Name:Name,PackageName:PackageName,Version:PackageVersion,FolderPath:FolderPath,FolderKey:FolderKey,Operation:Operation,OperationStatus:OperationStatus}"
```

Skip rows whose `Operation` is `Uninstall` or whose `OperationStatus` is `Failed`. `FolderKey` is the solution folder's key (`<SOLUTION_FOLDER_KEY>`). When several copies are installed, list them and ask which.

**2. The Identity groups.** One group per role:

| Role | Suggested group name | Who goes in it |
|------|----------------------|----------------|
| `ADMIN` | `FINS-Admin` | The solution's administrators |
| `BUSINESS_USER` | `FINS-BusinessUser` | Everyone who uses the solution day to day. Leaving it empty locks them all out of Lending QA/QC |
| `SOLUTION_TEST_ADMIN` | `FINS-SolutionTestAdmin` | Who may create and run solution tests. For now it also opens the admin portal and settings pages |

The names are the user's choice. They are case-sensitive and cannot contain a comma. A user may be in more than one group, and the groups are shared by every copy on the organization.

```bash
uip admin groups list --output json                                   # which groups exist
uip admin groups create "<GROUP_NAME>" --output json                  # a missing group
uip admin users list --search "<NAME_OR_EMAIL>" --limit 10 --output json   # a member's user id
uip admin groups members add <GROUP_ID> --user-ids "<USER_ID_1>,<USER_ID_2>" --output json
uip admin groups members list <GROUP_ID> --output json                # check
```

In the portal: **Admin**, then **Accounts & Groups**, then **Groups**, then **Add group**.

**3. Link each role to its group** in the `FINSRoleGroupMapping` entity in the solution folder, one row per role:

| Role | GroupName |
|------|-----------|
| `ADMIN` | `FINS-Admin` |
| `BUSINESS_USER` | `FINS-BusinessUser` |
| `SOLUTION_TEST_ADMIN` | `FINS-SolutionTestAdmin` |

```bash
uip df entities list --folder-key <SOLUTION_FOLDER_KEY> --output-filter "[?Name=='FINSRoleGroupMapping'].{Id:Id}" --output json
uip df records list <ENTITY_ID> --folder-key <SOLUTION_FOLDER_KEY> --output json
uip df records insert <ENTITY_ID> --folder-key <SOLUTION_FOLDER_KEY> --body '[{"Role":"ADMIN","GroupName":"FINS-Admin"}]' --output json
uip df records update <ENTITY_ID> --folder-key <SOLUTION_FOLDER_KEY> --body '{"Id":"<RECORD_ID>","GroupName":"<GROUP_NAME>"}' --output json
```

- `Role` must be exactly one of the three values, and is unique: insert only the roles that have no row, and fix a wrong name with `update`. Every role needs a row: a missing row is an error, not "no access needed".
- `GroupName` must match the group's name exactly. To give a role to several groups, list them comma-separated in that one row (`FINS-Admin,RPA-Ops`). A mistyped name in such a list is skipped without a warning, so access can seem to work while one group is left out: check each name against step 2.
- **Loan Setup:** its seed templates include `FINSRoleGroupMapping.csv` with the suggested names, so a seeded copy may already have the rows. Check them against the real group names. When the rows are set up here before a seed, tell the user to make the CSV match them first (or remove its rows), so the seed does not clash with them.
- **Lending QA/QC:** its seed templates do not include this entity, so the rows are added here.

A fixed row takes effect when the app reloads, with no redeploy. An administrator who is locked out of the app can still fix the rows.

**4. Solution tests (Loan Setup).** No command does this: an administrator sets each trigger that starts a solution test to run as a robot account, not "Run as HTTP Caller". That robot account needs a scope that reads group membership, such as `PM.Group.Read`, or whichever scope the tenant requires.

## Access

Permission names are the ones `uip or roles user-permissions list` prints, so the list can be compared with its output line by line. **Source** marks where each line comes from:

- *FINS docs*: the developer-permissions grids in the FINS technical solution overviews for Lending QA/QC and Loan Setup.
- *Seen*: a refusal seen on a real deploy.
- *Inferred*: worked out from what the deploy creates. Not documented by FINS.

### Tenant level

Grant these in a tenant role assigned to the deploying user, on the tenant the deploy goes to.

| Permission | Why | Source |
|------------|-----|--------|
| `SolutionDeployments.View` | Find the deployment by name (PRE_VERIFY, upgrade, seed) | FINS docs |
| `SolutionDeployments.Create` | Install the solution (SOLUTION) | FINS docs, Seen |
| `SolutionDeployments.Edit` | Upgrade, activate | FINS docs |
| `SolutionDeployments.Delete` | Only to uninstall or clean up | FINS docs |
| `SolutionPackages.View` | Read the solution package | FINS docs |
| `SolutionPackages.Create`, `SolutionPackages.Edit` | Upload the package when the tenant feed does not have it yet | FINS docs |
| `Units.View` | Read the target folder (Orchestrator shows the tenant **Folders** permission as `Units`) | Inferred |
| `Packages.View`, `Packages.Create` | Listed in the FINS developer grid | FINS docs |
| `AppVersions.View` | Listed in the FINS developer grid (the solution ships a coded app) | FINS docs |

Data Fabric (tenant roles, not in the output above): **Data Reader** and **Data Writer** for seeding. The FINS docs also list **Designer**. It may no longer be needed, because both packages now create their entities inside the solution folder. Source: FINS docs.

### Folder level, on the target folder

The deploy creates the solution's own folder under the target folder you pick, and the solution folder inherits the roles on the target. Grant these in a folder role on the target folder, or assign **Folder Administrator** there.

| Permission | Why | Source |
|------------|-----|--------|
| `SubFolders.View`, `SubFolders.Create`, `SubFolders.Edit` | Create the solution folder | Inferred |
| `Processes.View`, `Processes.Create`, `Processes.Edit` | Install the agents, Maestro and RPA processes. PROCESS_CONFIG edits them | Inferred |
| `FolderPackages.View`, `FolderPackages.Create`, `FolderPackages.Edit` | Install the packages into the folder | Inferred |
| `Apps.View`, `Apps.Create`, `Apps.Edit` | Install the coded web app | Inferred |
| `EntitySchema.View`, `EntitySchema.Create`, `EntitySchema.Edit` | Create the entities and choice sets | Inferred |
| `Schedules.View`, `Schedules.Create`, `Schedules.Edit` | Create and enable the HTTP API triggers (TRIGGERS) | Inferred |
| `Queues.View`, `Queues.Create`, `Queues.Edit` | Lending QA/QC only: the `LoanQAQC` queue | Inferred |
| `Buckets.View`, `Buckets.Create`, `Buckets.Edit` | Both: the solution's storage bucket (`LoanQAQC` or `LoanSetup`), created at SOLUTION. Lending QA/QC also uses it at BUCKET_FILES | Inferred |
| `BlobFiles.View`, `BlobFiles.Create`, `BlobFiles.Edit` | Lending QA/QC only: bucket files (BUCKET_FILES) | Inferred |
| `Assets.View`, `Assets.Create`, `Assets.Edit` | Lending QA/QC only: the `StorageBucket` asset (ASSETS) | Inferred |

### Seed (`uip vss deploy seed`), on the solution folder

Inherited from the target folder.

| Permission | Why | Source |
|------------|-----|--------|
| `EntitySchema.View` | Read the entities and choice sets | Inferred |
| `EntityRecords.View`, `EntityRecords.Create`, `EntityRecords.Edit` | Read, insert and update the seed rows | Inferred |
| `EntityRecords.Delete` | Loan Setup only: replace file attachments (`FINSCustomerConfig`, `FINSAgentKnowledgeBase`) | Inferred |
| `Processes.View` | Lending QA/QC only: CSV cells that name a process | Inferred |

## Not yet known

- No FINS document states the folder role the deployer needs. The folder lines above are inferred. A deploy as a user that holds only these lists confirms them: each missing permission is refused with its name.
- No FINS document names a per-user license type for the deployer.
