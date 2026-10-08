# Open Items Guide — what the target environment needs before the first run

The build is often made on another machine and another Orchestrator connection than the one the automation runs on. Execution ends by writing, for the engineer who deploys it, strictly what the target environment needs before the automation runs there. The files are written when the target environment needs at least one setup step — a package to deploy, an asset, a queue, a trigger, a connection, a machine prerequisite; an automation that needs none of them gets no open-items file. Build results, acceptance verdicts and review notes stay in the completion report ([execution-guide.md § 3.3](execution-guide.md)) and never enter these files. They are written last.

**Files and placement.** Write them in the folder that holds the solution or project folder (the location the scaffolding answer gave) — never inside a project folder (a file there ships in the project's package) and never inside the solution folder:

| Executed genome | Files |
|---|---|
| Component genome (one project) | `<project-slug>-open-items.md` |
| Process genome (a solution) | `<solution-slug>-open-items.md`, plus `<solution-slug>-open-items/<project-slug>-open-items.md` for every project built — per project, not per component: a split that materialises one component as several projects gives each project its own file |

Slugs follow [genome-format-guide.md § File Naming and Location](genome-format-guide.md).

**Content.** Every step the target environment needs, whether or not this run did it in its own tenant — a queue, asset or trigger the run created there does not exist in the target tenant. Derive the steps from the genome's Platform Dependencies and Target Applications, the configuration answers and the projects built. Each file has one section per kind of setup, in this order, so that nothing a trigger starts runs before its setup exists. **Access, Package and deployment, Assets, Others and Triggers are always present** and read "None." when empty. **Every other UiPath service the automation uses gets a section of its own, named after the service**, after Package and deployment and before Others — one per service the Platform Dependencies name, whatever it is (Queues, Storage Buckets, Integration Service, Data Fabric, Action Center, Document Understanding, Test Manager, Context Grounding, …); a service the automation does not use has no section. The template shows the common ones:

````markdown
# Open items: <project or solution> in <target environment>

Complete these steps in order in the target Orchestrator before the automation's first run. Tick each box when the step is done.

## Access
Give the automation a folder and the robots that run it.

- [ ] Create or choose the folder **`<folder>`**.
  - Robot accounts: `<accounts>` (unattended)
  - Machines: `<machine or machine template>`
  - Roles: `<roles>` for the people who operate the automation

## Package and deployment
Publish the packages first, then deploy them to the folder.

- [ ] Publish the library **`<Library>`** version `<version>` to the `<feed>` feed. Do this before the projects that use it.
- [ ] Deploy **`<package or solution>`** version `<version>` to the folder `<folder>`.
  - A solution deployment also creates the queues and assets the solution declares. The sections below then check their settings and fill in their values.

## Queues
Create each queue in the folder. After a solution deployment, check that the queue the deployment created has these settings.

- [ ] **`<QueueName>`**
  - Folder: `<folder>`
  - Unique reference: <on, so an item whose reference is already in the queue is refused | off>
  - Auto retry: <n> times
  - Description: <what one item is, which process adds the items and which process works them>

## Assets
Create each asset in the folder `<folder>` unless the asset says otherwise. The values are the ones the build used; replace them with this environment's values.

- [ ] **`<AssetName>`**
  - Type: <Text | Integer | Bool>
  - Value: `<the build's value>` (replace it with this environment's value)
  - Description: <what the automation uses it for>
- [ ] **`<CredentialAssetName>`**
  - Type: Credential
  - Value: the username is `<account>`; enter the password in Orchestrator. It is not written in this file.
  - Description: <which system it signs in to, and as whom>

## Storage Buckets
- [ ] **`<Bucket>`**
  - Folder: `<folder>`
  - Description: <what the automation stores there>

## Integration Service
- [ ] Create the **`<Connector>`** connection in the folder `<folder>` and sign it in with the account `<account>`.

## Data Fabric
Create each entity from its JSON definition below: save it as a file and run `uip df entities create "<Entity>" --file <file>`, or enter the same definition in Data Fabric by hand. Then give the robot accounts access to the entity.

- [ ] Create the entity **`<Entity>`** in <the folder `<folder>` | the tenant> and give `<accounts>` access to it.

  ```json
  <the entity's definition, in the JSON file format that `uip df entities create --file` accepts>
  ```

## <Service>
- [ ] <What to create or configure in that service: its name, where it goes, and who uses it.>

## Others
Setup outside UiPath that the robot machines and the network need.

- [ ] Allow outbound network access from the robot machines to these hosts. They are the endpoints the build used; use this environment's equivalents.
  - `<host>`: <what the automation uses it for>
  - `<host>:<port>`: <what the automation uses it for>
- [ ] Install `<application>` on the robot machines and sign it in with `<account>`.
- [ ] Install the UiPath extension in `<browser>` on the robot machines and allow it to run in incognito mode. <Only when the automation opens the browser in incognito.>

## Triggers
Create the triggers last: once a trigger is on, the automation starts running.

- [ ] **`<TriggerName>`**
  - Process: `<process>`
  - Type: <Time | Queue>
  - When it starts: <the schedule in words — the days and the time | when new items arrive in the queue `<QueueName>`>
  - Robots: at most <n> at a time
````

Rules:

1. **Write for the person who sets up the environment.** Full sentences, one step per checkbox, each detail on its own line, names in backticks, the section's opening line saying what to do. No shorthand, no symbols standing in for words, no internal vocabulary (genome section names, split options, step numbers); where the template offers alternatives in angle brackets, write only the one that applies. An agent with the proper tooling follows the same file.
2. **Assets are one block per asset, credentials included.** The block's type is the Orchestrator asset type. A setting gives the value this build used, as a reference to set per environment. A credential gives its username; the password never appears in an open-items file. Description is the text to enter as the asset's description in Orchestrator, taken from the Configuration Question or Platform Dependencies row the asset came from.
3. **Queues carry the settings the genome implies:** the unique-reference rule and retry count from the Transactional Shape's outcomes and the split answer. Under a solution deployment the deploy creates the declared queue, and the step checks its settings.
4. **A Data Fabric entity is one JSON definition, in the file format `uip df entities create --file` accepts.** Take that format from the CLI (`uip df entities create --help`), never from memory, and build the definition from the entity's fields in Platform Dependencies. The engineer can then create the entity from the file as it is.
5. **Triggers come from the split and trigger answers:** type, schedule or queue, and runner count per process.
6. **The solution file holds the steps several projects share** — the folder, packages and deployment, a queue between projects, a shared connection or asset — in the same sections, and ends with one line per project linking its file, with that project's step count. A step that spans projects is written once, in the solution file; a project file links to it instead of repeating it.
7. **A project file holds that project's own steps** in the same sections: its assets, its process and triggers, its Others items.
8. **Others holds every setup step outside UiPath's services.** Network access is one item listing every host the robot must reach — each target system's hosts, the identity and API endpoints behind it, the mail relay with its port — taken from the build's configuration answers and Target Applications, as values to set per environment. Robot machine setup is Others too: the applications installed and signed in (from Target Applications), the UiPath browser extension and its settings (allowed in incognito mode when the automation runs the browser incognito), accounts and permissions inside a target system, certificates.

## Anti-patterns

1. **An open-items file that assumes the build's tenant is the target, mixes in build results, holds a secret, or sits inside a project or solution folder** — the target environment misses a queue or asset the build created only in its own tenant, the engineer wades through review notes, a credential leaks into a shared file, or the file ships in a package.
