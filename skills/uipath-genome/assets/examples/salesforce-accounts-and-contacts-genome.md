<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     To build it, invoke the uipath-genome skill (Execute mode): it asks the configuration questions,
     then invokes the skills referenced in Build With. Do NOT execute these steps directly, and do NOT
     start from a Build With skill. -->

# Genome: Salesforce Accounts and Contacts

> Creates the account Get Cloudy in Salesforce Lightning through the browser, adds two contacts to it and logs a call on one of them.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Build it with the **uipath-genome** skill, which hands each part to the skill listed in **Build With** below.

## Overview

Completes the hands-on steps of the Trailhead module "Accounts and Contacts for Lightning Experience" in a Salesforce org by driving the Lightning web interface as a learner would. It creates the account Get Cloudy with its phone, account number, site, type, industry and billing city and state. It then adds the contacts Alan Johnson and Leung Chan from that account's page, opens Leung Chan's record and logs a call with a short comment. Every record value is fixed in the automation, so each run enters the same data. It serves a Trailhead learner, or a demonstration of browser automation on Lightning *[Inferred]*.

The run starts as a job with no input and works in a browser already signed in to the org. It attaches to the open Salesforce tab, or opens the org's home page when no such tab is open, and never signs in itself. Nothing on screen is confirmed beyond finding the next element. The run writes one log line at its start and one after the last record is saved.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Salesforce Lightning Experience | Output target | Web interface of the org in Configuration Question 1, opened in the browser of question 2 with a session already signed in (question 3). Pages used: the Accounts tab, the New Account form, the account record page with its New Contact action and contact cards, the New Contact form, the contact record page with its Log a Call action. Needs an interactive desktop session, since the browser is driven on screen. |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Steps 1–7 | `uipath-rpa` | Browser UI automation of Salesforce Lightning in one browser session, with the source's Object Repository targets carried over. The source creates every record through the user interface; an Integration Service connector or an API workflow would create them through the API, which changes the automation rather than rebuilding it. |

## Platform Dependencies

No Orchestrator or Integration Service resources required.

## Interface

Runs unattended with no arguments; outputs are the side effects listed in Workflow.

## Configuration Questions

1. Which Salesforce org does the run work in — the Lightning home page it opens when no org tab is open, and the Lightning address under which an open tab is accepted? (setting; default: home page `https://<ORG_DOMAIN>.lightning.force.com/lightning/page/home`; open tabs accepted under `https://<ORG_DOMAIN>.lightning.force.com/lightning`)
2. Which browser does the run use? (setting; default: Chrome)
3. How does the run get a signed-in Salesforce session, and as which user? (setting; default: the browser's existing signed-in session, as the source expects — no sign-in step and no credential asset; a sign-in instead needs one credential asset for the Salesforce user)

## Workflow

Each value below is entered by clicking its field, emptying it, then typing the value.

1. **Trigger** (input: none; output: start log line): Started as a job with no arguments, in an interactive desktop session. Writes the information log line `Starting Trailhead 'Accounts and Contacts for Lightning Experience' automation`.
2. **Attach to Salesforce in the browser** (input: org address — question 1; output: the org's Lightning tab, in front):
   a. Use the open browser tab whose title contains `Salesforce` and whose address starts with the org's Lightning address; when no such tab is open, open the browser at the org's Lightning home page.
   b. Do not sign in: the tab must already hold a signed-in session (question 3).
   c. Steps 3–6 act in this one tab and bring it to the front before every action.
   d. When the run ends, close the browser only when this step opened it; an attached tab stays open.
3. **Create the account Get Cloudy** (input: none, values fixed below; output: saved account Get Cloudy, its record page open):
   a. Open the Accounts tab from the navigation bar.
   b. Choose New; the New Account form opens.
   c. Set Account Name to `Get Cloudy`, Phone to `<ACCOUNT_PHONE>`, Account Number to `117` and Account Site to `Single Location`.
   d. Type picklist (showing `--None--`): open it and pick the option labelled `Customer - Direct`.
   e. Industry picklist (showing `--None--`): open it and pick the option labelled `Consulting`.
   f. In the Billing Address group, set Billing City to `Reno` and Billing State/Province to `NV`; street, postal code and country stay empty.
   g. Save the form. Salesforce opens the new account's record page, where step 4 acts.
   h. The run does not look for an existing Get Cloudy account first: every run creates a new one.
4. **Add the contact Alan Johnson** (input: Get Cloudy's record page; output: saved contact Alan Johnson; an empty contact form open):
   a. On the account's record page, choose New Contact. The form opens from the account, which links the contact to Get Cloudy; the run never enters the account in the form *[Inferred]*.
   b. Set First Name to `Alan`, Last Name to `Johnson`, Title to `Sales Manager`, Phone to `<CONTACT_PHONE>` and Email to `alan@gogetcloudy.com`.
   c. Choose Save & New: Alan Johnson is saved and an empty contact form takes its place, still linked to Get Cloudy *[Inferred]*.
5. **Add the contact Leung Chan** (input: the empty contact form; output: saved contact Leung Chan; Get Cloudy's record page open):
   a. Wait 1 second for the new form to settle, then set First Name to `Leung`.
   b. Set Last Name to `Chan`, Title to `Marketing Manager` and Email to `leung@gogetcloudy.com`; Phone stays empty.
   c. Save the form; the run is back on Get Cloudy's record page.
6. **Log a call on Leung Chan** (input: Get Cloudy's record page; output: a call logged on Leung Chan's record):
   a. Open Leung Chan's contact record from the contact card named `Leung Chan` on the account's page.
   b. On the contact's record page, choose Log a Call. Act on this page's visible button: the tab still holds a hidden Log a Call button from the account page *[Inferred]*.
   c. Set Comments to `Discussed account setup and confirmed contact details.`; every other field of the call keeps what Salesforce fills in.
   d. Save the call.
7. **Output** (input: none; output: completion log line): Writes the information log line `Trailhead unit steps completed: account 'Get Cloudy' created with contacts Alan Johnson and Leung Chan, and a call was logged on Leung Chan's record` and ends. The run returns nothing; its results are the account, the two contacts and the logged call in Salesforce.

## Business Rules

No business rules beyond the Workflow substeps.

## Error Handling

### Step 2: Attach to Salesforce in the browser
- Browser not signed in: the run has no sign-in step. The org's sign-in page is outside the org's Lightning address, so the first action of step 3 finds no tab, fails after its 30-second search and the job ends faulted *[Inferred]*.

### Step 5: Add the contact Leung Chan
- New form after Save & New: a fixed 1-second wait before the first field is typed; no other step adds a wait of its own.

### Step 6: Log a call on Leung Chan
- Two Log a Call buttons in the tab: the action has to take the visible one on the contact's page. Taking the account page's hidden one fails the step, or logs the call on the account instead of on Leung Chan *[Inferred]*.

### Global
- Every UI action waits for the page to become interactive and searches up to 30 seconds for its element, pausing 0.2 seconds before and 0.3 seconds after acting.
- No step confirms a save (no message or record check). Finding the next element is the only sign the previous save worked.
- Unhandled exception: no step catches or retries a failure. The first failed action ends the job faulted, without the completion log line. Records saved before the failure stay in Salesforce. A rerun starts again at step 3 and creates another Get Cloudy account and new contacts; whether the org's duplicate rules warn about them or block them depends on the org *[Inferred]*.
- UI self-healing of a target that is not found follows the job's Healing Agent setting in Orchestrator *[Inferred]*.
- Browser dialogs are not dismissed automatically; the pages used raise none.

## Transactional Shape

Not transactional: the run is one unit of work — one fixed account with its two contacts and one logged call, entered once per run from values fixed in the automation; nothing is iterated.

## Acceptance Criteria

1. Given a browser tab signed in to the configured org, a run creates an account named Get Cloudy with Phone `<ACCOUNT_PHONE>`, Account Number 117, Account Site Single Location, Type Customer - Direct, Industry Consulting, Billing City Reno and Billing State/Province NV, and with billing street, postal code and country empty.
2. After the run, Get Cloudy has the contact Alan Johnson with Title Sales Manager, Phone `<CONTACT_PHONE>` and Email alan@gogetcloudy.com.
3. After the run, Get Cloudy has the contact Leung Chan with Title Marketing Manager, Email leung@gogetcloudy.com and no phone, and Alan Johnson's values were saved before any of Leung Chan's were typed.
4. After the run, Leung Chan's record shows one logged call whose comment reads exactly `Discussed account setup and confirmed contact details.`; neither Get Cloudy nor Alan Johnson gets a call from the run.
5. Given a browser tab already open on the org, the run works in that tab and leaves it open at the end.
6. Given no open tab on the org, the run opens the browser at the org's Lightning home page and closes it at the end.
7. The job log holds the start line `Starting Trailhead 'Accounts and Contacts for Lightning Experience' automation` first and the completion line quoted in step 7 last, both at information level.
8. When an element is not found within 30 seconds, the job ends faulted without the completion log line, and the records saved before that action remain in Salesforce.
9. A second run creates a second Get Cloudy account with its own two contacts and call; it does not reuse the first run's records.

## Complexity

simple

## Tags

crm, salesforce, salesforce-lightning, trailhead, chrome, browser-automation, data-entry, object-repository

## Source Map

| Row | Source artifact | Notes |
|-----|-----------------|-------|
| Source framework | UiPath — Studio 26.0, project schema 4.0, `targetFramework: Windows`, C# expressions; packages `UiPath.System.Activities` 26.6.1, `UiPath.UIAutomation.Activities` 26.10.2 | Process project (`outputType: Process`), unattended (`isAttended: false`) with `requiresUserInteraction: true` |
| Source export | `<SOURCE_DIR>/SalesforceAccountsAndContacts` — project `SalesforceAccountsAndContacts`, projectId `<PROJECT_ID>`, projectVersion 1.0.0 | Not in a git repository |
| UI targets | UiPath: Object Repository store `.objects/` — application `Salesforce Lightning_App` 1.0.0, screen `Salesforce Lightning` | Every UI action references the store; no inline-only targets. Carried over at execution, confidence high (captured against the live org) |
| Project settings | UiPath: the UI Automation and System settings files under `.settings/Release/` | Read for the Release (run) profile: timeout 30 s, wait for ready Interactive, delays 0.2 s before / 0.3 s after, click before typing Single, empty field SingleLine, clipboard typing Never, scope opens if not open and closes only if opened by it, no dialog dismissal. `Debug` and `Design` profiles not used |
| Inventory | 1 XAML workflow (`Main.xaml`), 0 coded workflows, 0 test cases, 0 data files; 30 activities: 1 browser scope, 27 UI actions (9 clicks, 16 type-intos, 2 picklist selections), 2 log lines; Object Repository: 1 application, 1 screen, 22 elements, all used; 0 login accounts (signed-in session) | `.templates/` and `.entities/` empty |
| Not covered | none | The one entry point is the whole Workflow |
| Excluded | UiPath: Object Repository element `Accounts Nav Link` | Orphan: its parent node and the folders above it have no node files; no workflow references it. Generated or cache folders skipped: `.local/`, `.storage/`, `.screenshots/`, `.tmh/`, `.project/` |
| Author notes | UiPath: `AGENTS.md`, `.claude/rules/project-context.md` | Used for the module name (also in the log text) and the hidden Log a Call note. `project-context.md` matches the Object Repository. `AGENTS.md` is stale: it describes an application "Chrome HTML Forms" with one element that `.objects/` no longer holds |
| Inferred | Overview audience; 4a and 4c (contact linked to the account by the form opened from it, kept by Save & New); 6b (hidden button); Error Handling Step 2 (failure when not signed in), Step 6 (wrong button), Global (duplicate rules, healing semantics) | Each turns on Salesforce or package behaviour the project does not hold |
| Verification | UiPath: `Main.xaml` | No source defect arose: one linear sequence with no condition, handler, flag or result binding. `Main.xaml` read in full through the designer-noise filter; the raw file checked for variables, arguments, handlers, retries, verifications, annotations and invocations — none |
| Test coverage | none | No test project, test case or variation file |
| Related resources | none | User gave none |

### Steps

| Step | Source objects | Data sets | Captures | Notes |
|------|----------------|-----------|----------|-------|
| 1 | `Main.xaml` | none | 0 | Log line `LogMessage_1`; the only entry point (`project.json`, `entry-points.json`), no arguments |
| 2 | `Main.xaml` | none | 0 | Browser scope `NApplicationCard_1`, attach by instance; open-if-not-open and close-only-if-opened come from the Project settings row; the scope's healing behaviour defers to the job |
| 3 | `Main.xaml` | none | 0 | `NClick_1`, `NClick_2`, `NTypeInto_1`–`NTypeInto_6`, `NSelectItem_1`, `NSelectItem_2`, `NClick_3`; values are activity literals |
| 4 | `Main.xaml` | none | 0 | `NClick_4`, `NTypeInto_7`–`NTypeInto_11`, `NClick_5`; the contact form's field targets sit in the related-list create panel, which is the basis for the account link inferred in 4a and 4c |
| 5 | `Main.xaml` | none | 0 | `NTypeInto_12`–`NTypeInto_15`, `NClick_6`; `NTypeInto_12` carries the 1-second delay before; no phone action for this contact |
| 6 | `Main.xaml` | none | 0 | `NClick_7`, `NClick_8`, `NTypeInto_16`, `NClick_9`. The Log a Call target takes the second matching button by position among interactive elements; `project-context.md` attributes the first match to a hidden copy the account page leaves in the tab. The target is consistent with that note but cannot be verified offline (6b *[Inferred]*). The position depends on the tab's history: an attached tab that visited other record pages may hold a different number of copies |
| 7 | `Main.xaml` | none | 0 | Log line `LogMessage_2` |
