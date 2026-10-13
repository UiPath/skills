# FINS (Financial Services)

What a first deploy of a FINS package needs, and the access a **user login** needs to deploy and seed it with `uip vss deploy`.

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
