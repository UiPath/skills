# ECB FX Rates: build readiness

Genome: [`ecb-fx-rates-genome.md`](ecb-fx-rates-genome.md). Prepared 2026-11-22 by `uipath-genome` `prepare`, on these machine facts:
- Host: Windows 11, Node v24.22.3, UiPath CLI `uip` 1.207.0-preview.340.
- Packages found: `@uipath/maestro-builder-sdk` 6.120.31, installed globally.
- Integration Service: connector `uipath-microsoft-outlook365` (Microsoft Outlook 365, GA) is in the tenant's catalog, with no connection of it in any folder.
- Template feed: not searched. The genome is not transactional, so no REFramework template is needed.
- Deployed libraries: not searched. `uipath-maestro-flow` names no tenant library search, and a Flow consumes no library packages.
- Source export: none. The genome was authored, not extracted.

Needed before the build: 1 answer and 4 tasks.
- Decisions still open: 1 answer (CQ5, the sender mailbox, which has no default).
- Systems and applications: 2 tasks.
- Build environment: 2 tasks.

Every other item has a default.

Write the letter of the option you choose, or your own words, after each `Answer:`. Write the state of each task after its `Status:`. An item left blank stays open, and the build asks it. Then ask `uipath-planner` to "apply the answers", which writes the Genome edits and the answered decisions into the genome. Then build with `uipath-genome`: it asks nothing this file answers.

## Contents

1. [Architecture decisions](#1-architecture-decisions) — 1 decision, 1 answered (the mail choice is answered on CQ4)
2. [Genome edits](#2-genome-edits) — 1 to rule on, 1 edit
3. [Build setup](#3-build-setup) — 0 needed, 4 to confirm
4. [Systems and applications](#4-systems-and-applications) — 2 to arrange
5. [Build environment](#5-build-environment) — 4 tasks, 2 to arrange
6. [Decisions still open](#6-decisions-still-open) — 12 items, 1 answered

## 1. Architecture decisions

Usually answered by: the engineer, with the architect.

Each decision carries the build's proposal, marked `(recommended)`.

### Processes and their work items

None. The Transactional Shape says the run is one unit of work, so there is no split to decide. The genome builds one component as one Flow.

### Libraries and reusable parts

None. The genome is an authored component with no library component.

### Technology per capability

The Flow skill (`uipath-maestro-flow`) builds each of these one way only, so they are not asked:
- Reading the ECB file: a managed HTTP step. It goes out through Integration Service's shared egress.
- Parsing the XML: a script step. The Flow has no XML node, so the script parses the body itself.
- Waiting between checks: a 30-minute delay inside a loop.
- Starting the run: the Flow's scheduled trigger (but see R2).

The mail choice is the genome's own question CQ4. It is answered under Decisions still open › Configuration values: Outlook 365.

**R1. Keeping the four currencies: how should the Flow pick USD, GBP, CHF and RON from the ECB list?**
- **Context:** Step 5 also puts the currencies in the configured order. It adds a "not published by the ECB" row for any currency that is missing. The genome's Build With table says it is a script step.
- **See:** Build With step 5; Workflow step 5.
- **Options:**
  - a. One script step that filters, orders and adds the missing rows. The same script can also parse the XML. (recommended)
  - b. The Flow's built-in Transform filter step drops the other currencies. A small script step then orders them and adds the missing rows.
- **Answer:** a (the user, in prepare, 2026-11-22)

## 2. Genome edits

Usually answered by: the engineer, with the architect.

What preparing found wrong in the genome. Applying the answers writes each into the genome.

### Genome gaps to rule on

**R2. The genome starts the run at 07:00 in a configurable time zone, but the Flow's scheduled trigger has no time-zone setting. How should the 07:00 start be kept?**
- **Context:** `uipath-maestro-flow` says the schedule's "only field" is its timing, with "no time-zone setting". The genome's default zone, Europe/Berlin, moves by an hour for summer time. The Flow's scripts also have no time-zone library. So under every option, the run date and the 10:00 cut-off in that zone are worked out with written-in summer-time rules.
- **See:** Platform Dependencies › Triggers; Workflow step 1; Configuration Questions 1 and 2.
- **Options:**
  - a. Schedule the Flow on weekdays at both 05:00 and 06:00 UTC. The first script step works out the local time and ends the run that is not 07:00 local, with no mail. CQ1 is then limited to the zones whose rules the script holds. (recommended)
  - b. Schedule a fixed UTC time, for example 06:00 UTC. That is 07:00 in Berlin in winter and 08:00 in summer. The genome's times are restated in UTC.
  - c. Start the published Flow from an Orchestrator time trigger with its own time-zone setting, instead of the Flow's own trigger. The Flow skill does not say this is supported. It would be checked at build.
- **Answer:**

### Edits for `uipath-planner`

Each gap with its fix. Delete a line you disagree with.

- The genome as a whole: it has no `## Source Map` section, not even the stub an authored genome carries. Add the stub.

## 3. Build setup

Usually answered by: the engineer.

**R3. Where should the build create the project?**
- **Context:** A Flow is built inside a UiPath solution. No solution or project exists in the genome's folder yet.
- **Options:**
  - a. A new solution, ECB FX Rates, in the genome's folder, holding one Flow project named after the genome. (recommended)
  - b. Another path, which you name.
- **Answer:**

**R4. Which Maestro product should the Flow be created for?**
- **Context:** The Flow skill creates the project with one command. Its only choice is the product.
- **Options:**
  - a. Maestro Flow, the skill's default. (recommended)
  - b. Maestro Automate. This writes its run profile into the project.
- **Answer:**

**R5. Should the build pin the Flow builder SDK to the installed version, or take the latest stable version?**
- **Context:** `@uipath/maestro-builder-sdk` 6.120.31 is installed on this machine.
- **Options:**
  - a. Pin to 6.120.31, the installed version. (recommended)
  - b. Take the latest stable version from npm.
- **Answer:**

**R6. Where should the genome's settings and constants live?**
- **Context:** The settings change per environment: time zone, schedule, recipients and sender mailbox (CQ1, CQ2, CQ3, CQ5). The constants do not: provider, currencies, file address and subjects (CQ4, CQ6, CQ7, CQ8). Whether a Flow reads Orchestrator assets is to be checked at build with the Flow skill.
- **Options:**
  - a. Each setting as an Orchestrator asset, so each environment sets its own value, and the constants in the Flow's own configuration. (recommended)
  - b. Every value as an Orchestrator asset.
  - c. Every value written into the Flow. A change means a new version.
- **Answer:**

## 4. Systems and applications

Usually answered by: each system's owner.

**R7. European Central Bank euro foreign exchange reference rates**
- **Reached through:** API: one unauthenticated HTTPS GET of `https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml`.
- **The build uses it for:** checking the file's shape, and test runs of the Flow.
- **To arrange:**
  - No account is needed.
  - The Flow's managed HTTP step reaches the file through Integration Service's shared egress. That egress needs network access to the ECB site.
  - Shared egress can be rate-limited. A test run that is refused is not a build fault.
- **Status:**

**R8. Microsoft Outlook 365: connection FinanceRatesMail**
- **Reached through:** the Integration Service connector `uipath-microsoft-outlook365`, Send Email.
- **The build uses it for:** binding steps 6 and 7 to the connection, and for test runs. Without a connection and its folder, the Flow's check reports a missing binding.
- **To arrange:**
  - A connection named FinanceRatesMail, signed in as the sender mailbox (CQ5), in the folder the Flow will run in. None exists in the tenant the build machine is signed in to.
  - The mailbox's permission to send to the recipients (CQ3).
- **Status:**

## 5. Build environment

Usually answered by: the engineer, with the tenant admin.

**R9. A Robot on the build machine** — the Flow runs in the cloud and occupies no robot.
- **Status:** Not needed.

**R10. The UiPath CLI signed in to a tenant the build may read** — for the Flow skill's registry and connection lookups and its check.
- **Status:** Signed in on 2026-11-22. Confirm that it is the tenant the build should use.

**R11. The package feed** — the build needs the Flow builder SDK from npm. The automation consumes no library.
- **Status:** `@uipath/maestro-builder-sdk` 6.120.31 is installed.

**R12. Data the build's test runs may change** — each test run sends a real mail. Name a test recipient to use in place of finance@contoso.com. The ECB file is only read.
- **Status:**

## 6. Decisions still open

Usually answered by: as each item names.

### Business decisions

**D1. On a run day whose expected set is one finance already received (the day or days after a TARGET closing day), what does finance receive?**
- **Context:** Answered by the process owner. This is a business outcome for step 6, Send the rates e-mail.
- **See:** Open Decisions 1; Workflow steps 2b and 6e; Acceptance Criteria 3.
- **Options:**
  - a. The same set again, with a line saying the ECB has published no new rates since the set date. The build builds this now.
  - b. No mail that day.
  - c. A short note only, saying that no new rates were published.
- **Answer:**

**D2. When the expected set is published but one of the four currencies is not in it, what does finance receive?**
- **Context:** Answered by the process owner. This is a business outcome for step 5, Keep the four currencies.
- **See:** Open Decisions 2; Workflow step 5b; Acceptance Criteria 8.
- **Options:**
  - a. The table, with that currency's row reading "not published by the ECB". The build builds this now.
  - b. Treat the set as missing, keep checking until the cut-off, then send the missing notice.
- **Answer:** b (the process owner, 2026-11-20)

**D3. When the ECB file cannot be read at a check, what does the run do?**
- **Context:** Answered by the process owner. This is run behaviour for step 3, Read the latest ECB rates. The build does not ask it, and builds the recommended option until it is answered.
- **See:** Open Decisions 3; Error Handling › Step 3; Acceptance Criteria 7.
- **Options:**
  - a. Count that check as "not yet published" and check again at the next interval. At the cut-off, the missing notice says the file could not be read and gives the last error. (recommended)
  - b. Your own words.
- **Answer:**

**D4. When the rates e-mail or the missing notice cannot be sent, what does the run do?**
- **Context:** Answered by the process owner. This is run behaviour for steps 6 and 7. The build does not ask it, and builds the recommended option until it is answered.
- **See:** Open Decisions 4; Error Handling › Steps 6 and 7; Acceptance Criteria 10.
- **Options:**
  - a. Try the send twice more, one minute apart, then fail the run so it shows as faulted in Orchestrator. No other alert is sent. (recommended)
  - b. Your own words.
- **Answer:**

### Configuration values

**CQ1. In which time zone are the 07:00 start and the 10:00 cut-off, and in which time zone is the run date counted?**
- **Context:** A setting, answered by the environment's owners. R2 limits what the Flow can honour here.
- **See:** Configuration Questions 1; Workflow step 1.
- **Options:**
  - a. Europe/Berlin, the ECB's own time (CET/CEST). (recommended)
  - b. Another time zone, which you name.
- **Answer:**

**CQ2. When does the run start, how long does it wait between checks, and at what time does it stop checking and send the missing notice?**
- **Context:** A setting, answered by the environment's owners.
- **See:** Configuration Questions 2; Workflow step 4.
- **Options:**
  - a. Weekdays at 07:00, every 30 minutes, last check at 10:00. (recommended)
  - b. Other times, which you name.
- **Answer:**

**CQ3. Who receives the rates e-mail and the missing notice?**
- **Context:** A setting, answered by the environment's owners.
- **See:** Configuration Questions 3.
- **Options:**
  - a. finance@contoso.com. (recommended)
  - b. Other addresses, which you name.
- **Answer:**

**CQ4. Which email provider sends the mails?**
- **Context:** A constant, answered by the process owner. It is also the mail technology choice of Architecture decisions.
- **See:** Configuration Questions 4; Target Applications; Platform Dependencies › Connections.
- **Options:**
  - a. Microsoft Outlook 365, through an Integration Service connection, with the connector's Send Email step. (recommended)
  - b. Gmail, through its connector's Send Email step.
  - c. Another mail connector, which you name.
- **Answer:** a (the user, in prepare, 2026-11-22)

**CQ5. Which mailbox sends the mails, that is, the account the connection signs in as?**
- **Context:** A setting, answered by the environment's owners. The genome gives no default.
- **See:** Configuration Questions 5; Platform Dependencies › Connections.
- **Until answered:** the build binds steps 6 and 7 to the FinanceRatesMail connection by name. The mailbox is set when the connection is created (R8).
- **Answer:** rates@contoso.com (the environment's owners, 2026-11-20)

**CQ6. Which currencies does finance receive, and in what order?**
- **Context:** A constant, answered by the process owner.
- **See:** Configuration Questions 6; Workflow step 5.
- **Options:**
  - a. USD, GBP, CHF, RON, in that order. (recommended)
  - b. Others, which you name in order.
- **Answer:**

**CQ7. What is the address of the ECB's daily reference-rates file?**
- **Context:** A constant, answered by the process owner.
- **See:** Configuration Questions 7; Workflow step 3.
- **Options:**
  - a. `https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml` (recommended)
  - b. Another address, which you name.
- **Answer:**

**CQ8. What are the subject lines of the two mails?**
- **Context:** A constant, answered by the process owner.
- **See:** Configuration Questions 8; Workflow steps 6a and 7a.
- **Options:**
  - a. "ECB euro reference rates – {set date}" for the rates e-mail, and "ECB euro reference rates missing – {expected date}" for the notice. (recommended)
  - b. Other subjects, which you name.
- **Answer:**
