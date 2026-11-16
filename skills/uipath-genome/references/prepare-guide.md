# Prepare Guide — the `prepare` verb

`prepare` runs the start of a build on the machine that will build, and stops before anything is built. It writes every question the build would ask into a readiness file beside the genome, together with the questions the SDD still holds open, so the people who answer them can do so ahead of the build.

1. **Start as a build starts:** [build-guide.md](build-guide.md) § Start and the reads of § Read Plan, then [execution-guide.md](execution-guide.md) § 1.1 and its § 1.2, the preflight discovery the options are built from.
2. **Read the answers already given.** That means the SDD beside the genome, and an earlier readiness file, both as the user's files of answers ([configuration-questions-guide.md](configuration-questions-guide.md) rules 4 and 4a). Their genome edits not yet made go to `uipath-planner` first, as at build. A genome with no SDD beside it is read for its open entries and its Configuration Questions directly.
3. **Select every question this build would ask** — the genome, refactor, split and scaffolding questions and the run-level ones ([configuration-questions-guide.md](configuration-questions-guide.md)). Drop each one answered by the request, the decided-values table, the preferences file the genome names, or the SDD (an item answered there, or under a filled `Confirmed:` line). An SDD item still open is kept under its id, in Still open in the SDD. A question an answer settles only in part is kept for the rest alone, worded for it: Location, when Existing projects holds the project to build into.
4. **Ask each owning skill how it builds each capability the genome uses**, through the skill invoked for preflight discovery: its recommended activity package, connector or API, and the alternatives it supports. Never from memory.
   - **The capabilities:** mail, documents and PDFs, spreadsheets, databases, files and shares, web and desktop applications, SAP, APIs and connectors, AI and document understanding, people in the loop.
   - **When the skill's discovery needs a project** (the docs an installed package brings, its activity search), create a scratch project through the skill's project-creation step, in a temporary folder outside the genome's folder and every folder the build will use. Install there the packages the options name, at the feed's latest stable versions. An install there chooses nothing for the build and takes no question: the build's package questions stay in Build setup.
   - **A requirement an option carries** (an extension, an installed application, a connection, the platforms it runs on) is written as the owning skill or the package's docs state it, never from the genome or the source.
4a. **Look for libraries earlier work deployed** to the tenant feed, through the owning skill's tenant library search. Its keywords are the genome's library components and the capabilities of step 4. Its candidates are options, never a question. Install each candidate in the scratch project and read its activities. A deployed library that holds a library component's public workflows, or a capability, is an option of the decision that component or capability falls under:
   - it is named by package id and version;
   - with the workflows it lacks, and the arguments that differ from the genome's Interface;
   - it is Recommended for a library component when it lacks no workflow.
5. **Write the readiness file**, `<slug>-readiness.md` beside the genome (the genome's file name with `-readiness.md` in place of `-genome.md`). A process genome has one, covering its components. It holds the sections of § The readiness file, in their order, each with its "Usually answered by" line; a section with no item reads "None.".
6. **Every question is worded as rules 2–2b state**, in the item form:
   - the question in bold;
   - one `Context:` line, with the facts rule 2a names;
   - `See:` the genome sections they rest on;
   - `Recommended:` the Recommended option, with what it gives;
   - `Instead:` one line per other option, with what it gives;
   - `Change:`.

   Each label is in bold and every line is in short sentences. Backticks hold only a name a person types or searches for (a queue, an asset, a file, a package); components and source objects are written plain. A question with no option the build can recommend (a path only the user knows) ends instead on `Until answered:` (what the build does while it stays open) and `Answer:`. A task ends on `Status:`. Each section of questions opens with a `Confirmed:` line.
7. **Build nothing:** no project or install but the scratch project of step 4, no tenant write, no question asked. End by naming the file, how many items each section holds, and how many are needed before the build.

## The readiness file

The header says, in this order:
- when and on what machine facts it was prepared, those facts alone: the host, the packages discovery found, the template feed, the deployed libraries the search found or that it could not run, the source export found. It never names a signed-in account, a user name or a tenant URL, since the file travels with the genome;
- how many items are needed before the build, by section;
- how to answer: fill in an item, or confirm a section, then ask `uipath-planner` to "apply the answers", which writes into the genome what changes it;
- the Contents, with each section's counts.

The sections:
1. **Architecture decisions** (§ The Architecture decisions section). Usually answered by: the engineer, with the architect.
2. **Build setup** — every other selected question, grouped by topic (rule 1). Usually answered by: the engineer.
3. **Existing projects** — one item per component that gets a project of its own, its Rationale opening neither `Retired:` nor `Folded into`: a project of it an earlier build made, to build into. Default: none, a new project. Usually answered by: the engineer.
4. **Systems and applications** — a task per system the automation acts on: each row of Target Applications, each system row of Actors and Systems (never a person, nor an automation that calls this one), each connection of Platform Dependencies. Each task holds:
   - how it is reached: screens, API or connector, database, files, mail;
   - what the build uses it for: exploring screens and checking their targets live, when reachable; the connection a connector's calls are written against; test runs;
   - what to arrange: an instance or endpoint the build may reach, or none; the account of each credential asset the genome names that signs in to it; a connection's identity; network access from the build machine; the machine prerequisites its row names, on the build and robot machines.

   It ends on `Status:`. Usually answered by: each system's owner.
5. **Build environment** — the tasks of the machine that builds:
   - the source export at the path the Source Map records, and the framework migration pack for another framework's source;
   - a Robot that may run the workflows on the build machine, when test runs are wanted;
   - the UiPath CLI signed in to a tenant the build may read;
   - the package feed, with every library the automation consumes;
   - data the build's test runs may change, or none.

   Each ends on `Status:`. Usually answered by: the engineer, with the tenant admin.
6. **Still open in the SDD** — every item of the SDD's Action Required with no answer, under its id and its group's heading, in the SDD's own form. An answer given here is the same item's: it reaches the genome as the SDD's would. Usually answered by: as each item names.

`prepare` run again keeps every change, every `Status:` and every `Confirmed:` line. It drops:
- each item whose question is now answered elsewhere (the genome, by the decided-values table of [configuration-questions-guide.md](configuration-questions-guide.md) rule 5; the SDD; the preferences file), unless it carries a change, which stays as the record of the decision;
- each edit line marked applied.

It draws again a decision whose Recommended option rests on an answer since changed (a settings store that names the template a change removed), opening it with `New since confirmed`, which the `Confirmed:` line no longer covers.

## The Architecture decisions section

The decisions that shape what gets built, each with the build's proposal: the Recommended option, from the preflight and each owning skill's way for its capability. What the genome already shows is named by section where a decision rests on it, never redrawn: its Process Map and Components, Platform Dependencies, the Transactional Shape, Deployment, the Source Map. Four groups, in this order, a group with no decision left out:

1. **Processes and their work items** — for each flow of the Transactional Shape without a `Decided:` line, its split questions ([transactional-execution-guide.md § Split questions](transactional-execution-guide.md)), each `Context:` naming the flow and the facts of its As-is the answer rests on.
2. **Libraries and reusable parts** — the Library layout question, its `Context:` naming the libraries and the source units each is built from, as the Source Map names them.
3. **Technology per capability** — one decision per capability the automation uses, in the order step 4 lists them:
   - `Today:` how the source does it (the application, the client, the protocol), as the genome states it;
   - `Recommended:` the owning skill's way: the activity package, connector or API, by name;
   - `Instead:` each alternative, with when it fits (for mail: Microsoft 365 activities over Graph, the desktop Outlook activities, IMAP and SMTP).

   A migration keeps the source's technology unless an option names a gain the source never had and what it requires (a connection, a licence, an app registration). A choice a Configuration Question already asks is named there, never asked twice.
4. **Other decisions** — Target framework, Settings store, Workflow type, Source fidelity, Log target and, in a refactor, the refactor questions.

**Recorded in.** Each decision has a `Recorded in:` line naming the genome section that states its subject, or `the build` when no section does. `uipath-planner`'s "Apply the answers" writes the answer there. The sections are:
- the flow's `Decided:` line;
- the Target Applications row of the component that uses a capability;
- Deployment's Runtime and machines bullet, or its Logging and retention bullet.

A split option's letter appears only beside its meaning.

**A gap preparing finds in the genome** is a line of the section's closing block, `Edits for uipath-planner`, which is left out when there is none. Such a gap is a requirement of the source's platform written as the target's, a handoff the target runs another way, or a fact the build cannot read. Each line says where the genome states it, what is wrong, and the fact that shows it. `prepare` edits no genome ([SKILL.md](../SKILL.md) Critical Rule 2): "Apply the answers" makes each line, and a build hands any line not yet applied to `uipath-planner` first.

````markdown
# <Process or component>: build readiness

Genome: [`<genome file>`](<relative path>). Prepared <YYYY-MM-DD> by `uipath-genome` `prepare`, on <the machine facts>.

Needed before the build: <n> answers and <n> tasks — <section>: <n>; <section>: <n>. Every other item has a default.

Write an answer after each `Answer:`, `Change:` and `Status:`, or put your name and the date on a section's `Confirmed:` line to accept its defaults. Then ask `uipath-planner` to "apply the answers", and build with `uipath-genome`: it asks nothing this file answers.

## Contents

1. [Architecture decisions](#1-architecture-decisions) — <n> decisions
2. [Build setup](#2-build-setup) — <n> needed, <n> to confirm
3. [Existing projects](#3-existing-projects) — <confirmed | to confirm>
4. [Systems and applications](#4-systems-and-applications) — <n> to arrange
5. [Build environment](#5-build-environment) — <n> to arrange
6. [Still open in the SDD](#6-still-open-in-the-sdd) — <n> items

## 1. Architecture decisions

Usually answered by: the engineer, with the architect.

Each decision carries the build's proposal: confirm it, or change it.

**Confirmed:**

### Processes and their work items

1. **<The split question in plain words>**
   - **Context:** <the flow, and the facts of its As-is the answer rests on>
   - **See:** <the genome sections the context rests on>
   - **Recommended:** <the option, with what it gives and why it fits this genome>
   - **Instead:** <one alternative, with what it gives>
   - **Instead:** <the next alternative, one line each>
   - **Recorded in:** <the flow's `Decided:` line>
   - **Change:**

### Libraries and reusable parts

<n>. **<The Library layout question>**
   - **Context:** <the libraries, and the source units each is built from>
   - **See:** <the genome sections the context rests on>
   - **Recommended:** …
   - **Instead:** <one alternative per line>
   - **Recorded in:** the build
   - **Change:**

### Technology per capability

<n>. **<Capability>: how should the automation <do it>?**
   - **Today:** <how the source does it>
   - **Recommended:** <the owning skill's way>
   - **Instead:** <one alternative per line, with when it fits>
   - **Recorded in:** <the component's Target Applications row>
   - **Change:**

### Other decisions

<n>. **<The question in plain words>**
   - **Context:** <the facts the answer rests on>
   - **See:** <the genome sections the context rests on>
   - **Recommended:** <the option, with what it gives>
   - **Instead:** <one alternative per line>
   - **Recorded in:** <the genome section, or the build>
   - **Change:**

### Edits for `uipath-planner`

Gaps found in the genome while preparing; applying the answers fixes each one. Delete a line you disagree with.

- <where the genome states it>: <what is wrong, and the fact that shows it>

## 2. Build setup

Usually answered by: the engineer.

**Confirmed:**

1. **<The question in plain words>**
   - **Context:** <…>
   - **Recommended:** <…>
   - **Instead:** <one alternative per line>
   - **Change:**

## 3. Existing projects

Usually answered by: the engineer.

**Confirmed:**

1. **<Component>: a project of it an earlier build made**
   - **Default:** none — the build makes a new project
   - **Change:** <its path>

## 4. Systems and applications

Usually answered by: each system's owner.

### <System>

- **Reached through:** <screens | API or connector | database | files | mail>
- **The build uses it for:** <what the build does with it>
- **To arrange:** <an instance or endpoint the build may reach; the account of each credential asset that signs in to it; a connection's identity; network access; machine prerequisites>
- **Status:**

## 5. Build environment

Usually answered by: the engineer, with the tenant admin.

1. **<What to make available>** — <what the build needs it for>
   - **Status:**

## 6. Still open in the SDD

Usually answered by: as each item names.

<each open item of the SDD's Action Required, under its id and its group's heading, as the SDD writes it>
````

## Read Plan

`prepare` reads what the rows of [build-guide.md § Read Plan](build-guide.md) whose phase is "start, before any question" name for the conditions that hold, read as that section says.
