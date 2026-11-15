# Prepare Guide — the `prepare` verb

`prepare` runs the start of a build on the machine that will build, and stops before anything is built, so that every question is answered ahead in the genome's readiness file.

1. **Start as a build starts:** [build-guide.md](build-guide.md) § Start and the reads of § Read Plan, then [execution-guide.md](execution-guide.md) § 1.1 and its § 1.2, the preflight discovery the options are built from.
2. **Read the readiness file** beside the genome as the user's file of answers ([configuration-questions-guide.md](configuration-questions-guide.md) rule 4a), its genome edits not yet made going to `uipath-planner` first, as at build. No readiness file beside the genome: say that `uipath-planner` writes it ("Write the readiness file"), and stop.
3. **Select every question this build would ask** — the genome, refactor, split and scaffolding questions and the run-level ones ([configuration-questions-guide.md](configuration-questions-guide.md)) — and drop each one the request or the decided-values table answers, and each one the file already holds as an item, answered or not: a Configuration Question, a project to build into, a system's reachability. A question the file holds in part is kept for the rest alone, worded for it: Location, when Existing projects holds the project to build into.
4. **Ask each owning skill how it builds each capability the genome uses** — mail, documents and PDFs, spreadsheets, databases, files and shares, web and desktop applications, SAP, APIs and connectors, AI and document understanding, people in the loop — through the skill invoked for preflight discovery: its recommended activity package, connector or API, and the alternatives it supports. Never from memory. Where the skill's discovery needs a project — the docs an installed package brings, its activity search — create a scratch project through the skill's project-creation step, in a temporary folder outside the genome's folder and every folder the build will use, and install there the packages the options name at the feed's latest stable versions. An install there chooses nothing for the build and takes no question: the build's package questions stay in Build setup. A requirement an option carries — an extension, an installed application, a connection, the platforms it runs on — is written as the owning skill or the package's docs state it, never from the genome or the source.
4a. **Look for libraries earlier work deployed** to the tenant feed, through the owning skill's tenant library search, its keywords the genome's library components and the capabilities of step 4; its candidates are options, never a question. Install each candidate in the scratch project and read its activities: a deployed library that holds a library component's public workflows, or a capability, is an option of the decision that component or capability falls under, by package id and version, with the workflows it lacks and the arguments that differ from the genome's Interface — Recommended for a library component when it lacks no workflow.
5. **Write the Architecture decisions section**, in place of its "Not prepared yet" line, as § The Architecture decisions section states.
6. **Write the Build setup section**, in place of its line: every other selected question, grouped by topic (rule 1). A first line names the date and the machine's facts the options rest on, those alone: the host, the packages discovery found, the template feed, the deployed libraries the search found or that it could not run, the source export found. An application's prerequisites are the Systems and applications section's, which `prepare` leaves as it stands; the line never names a signed-in account, a user name or a tenant URL, since the file travels with the genome.
7. **Every question** in both sections is worded as rules 2–2b state, in the readiness file's item form, a block of labelled lines: the question in bold; the `Context:` lines rule 2a gives; `Recommended:` the Recommended option with what it gives; `Instead:` each other option with what it gives; `Change:`. A question with no option the build can recommend (a path only the user knows) ends instead on `Until answered:` — what the build does while it stays open — and `Answer:`. Each section opens with a `Confirmed:` line. These two sections, and the counts the file's header and Contents give for them, are the only parts of the file `prepare` writes.
8. **Build nothing:** no project or install but the scratch project of step 4, no tenant write, no question asked. End by naming the file, how many decisions and questions the two sections hold, and how many of them are needed.

## The Architecture decisions section

The decisions that shape what gets built, each with the build's proposal: the Recommended option, from the preflight and each owning skill's way for its capability. What the genome already shows — its Process Map and Components, Platform Dependencies, the Transactional Shape, Deployment, the Source Map — is named by section where a decision rests on it, never redrawn. Four groups, in this order, a group with no decision left out:

1. **Processes and their work items** — for each flow of the Transactional Shape without a `Decided:` line, its split questions ([transactional-execution-guide.md § Split questions](transactional-execution-guide.md)), each `Context:` naming the flow and the facts of its As-is the answer rests on.
2. **Libraries and reusable parts** — the Library layout question, its `Context:` naming the libraries and the source units each is built from, as the Source Map names them.
3. **Technology per capability** — one decision per capability the automation uses, in the order step 4 lists them: `Today:` how the source does it (the application, the client, the protocol), as the genome states it; `Recommended:` the owning skill's way — the activity package, connector or API by name; `Instead:` each alternative with when it fits (for mail: Microsoft 365 activities over Graph, the desktop Outlook activities, IMAP and SMTP). A migration keeps the source's technology unless an option names a gain the source never had and what it requires (a connection, a licence, an app registration); a choice a Configuration Question already asks is named there, never asked twice.
4. **Other decisions** — Target framework, Settings store, Workflow type, Source fidelity, Log target and, in a refactor, the refactor questions.

Each decision has a `Recorded in:` line naming the genome section that states its subject — the flow's `Decided:` line, the Target Applications row of the component that uses a capability, Deployment's Runtime and machines or Logging and retention bullet — or `the build` when no section does: `uipath-planner`'s "Apply the readiness answers" writes the answer there. Lines are one or two sentences, names in backticks, a split option's letter only beside its meaning. **A gap preparing finds in the genome** — a requirement of the source's platform written as the target's, a handoff the target runs another way, a fact the build cannot read — is a line of the section's closing block, `Edits for uipath-planner`, which is left out when there is none: where the genome states it, what is wrong, and the fact that shows it. `prepare` edits no genome ([SKILL.md](../SKILL.md) Critical Rule 2): "Apply the readiness answers" makes each line, and a build hands any line not yet applied to `uipath-planner` first.

`prepare` run again keeps every change and the `Confirmed:` line; drops each decision whose question the genome now answers ([configuration-questions-guide.md](configuration-questions-guide.md) rule 5, the decided-values table), unless it carries a change, which stays as the record of the decision, and each edit line marked applied; and redraws a decision whose Recommended option rests on an answer since changed (a settings store that names the template a change removed), opening it with `New since confirmed`, which the `Confirmed:` line no longer covers.

````markdown
## 1. Architecture decisions

Usually answered by: the engineer, with the customer's architect.

Prepared <YYYY-MM-DD> by `uipath-genome` `prepare`. What gets built is the genome's Process Map and Components; what it replaces, the Source Map. Each decision carries the build's proposal: confirm it, or change it.

Confirmed:

### Processes and their work items

1. **<The split question in plain words>**
   - Context: <the flow, and the facts of its As-is the answer rests on>
   - Recommended: <the option, with what it gives and why it fits this genome>
   - Instead: <each alternative, with what it gives>
   - Recorded in: <the flow's `Decided:` line>
   - Change:

### Libraries and reusable parts

<n>. **<The Library layout question>**
   - Context: <the libraries, and the source units each is built from>
   - Recommended: …
   - Instead: …
   - Recorded in: the build
   - Change:

### Technology per capability

<n>. **<Capability>: how should the automation <do it>?**
   - Today: <how the source does it>
   - Recommended: <the owning skill's way>
   - Instead: <an alternative, with when it fits>
   - Recorded in: <the component's Target Applications row>
   - Change:

### Other decisions

<n>. **<The question in plain words>**
   - Context: <the facts the answer rests on>
   - Recommended: <the option, with what it gives>
   - Instead: <each alternative, with what it gives>
   - Recorded in: <the genome section, or the build>
   - Change:

### Edits for `uipath-planner`

Gaps found in the genome while preparing; applying the answers fixes each one. Delete a line you disagree with.

- <where the genome states it>: <what is wrong, and the fact that shows it>
````

## Read Plan

`prepare` reads what the rows of [build-guide.md § Read Plan](build-guide.md) whose phase is "start, before any question" name for the conditions that hold, read as that section says.
