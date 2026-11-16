# Prepare Guide — the `prepare` verb

`prepare` runs the start of a build and its questions on the machine that will build, as far as the user answers them, and stops before anything is built. It writes the answers and every question still open into a readiness file beside the genome, together with the questions the SDD still holds open, so the people who answer the rest can do so ahead of the build. The questions, their options and the discovery they rest on are the build's own; this guide adds the file.

1. **Start as a build starts:** [build-guide.md](build-guide.md) § Start and the reads of § Read Plan, then [execution-guide.md](execution-guide.md) § 1.1 and its § 1.2, the preflight discovery the options are built from.
2. **Read the answers already given.** That means the SDD beside the genome, and an earlier readiness file, both as the user's files of answers ([configuration-questions-guide.md](configuration-questions-guide.md) rules 4 and 4a). Their genome edits not yet made go to `uipath-planner` first, as at build. A genome with no SDD beside it is read for its open entries and its Configuration Questions directly.
3. **Select every question this build would ask** — the genome, refactor, split and scaffolding questions and the run-level ones ([configuration-questions-guide.md](configuration-questions-guide.md)). Drop each one answered by the request, the decided-values table, the preferences file the genome names, or the SDD (an item answered there), and the Subagents question, which the session that builds answers. An SDD item still open is kept under its id, in Still open in the SDD. A question an answer settles only in part is kept for the rest alone, worded for it: Settings store, when the preferences file places only the constants.
4. **Ask as the build asks, as far as the user wants** ([configuration-questions-guide.md](configuration-questions-guide.md) rules 2–3b), the first question being how to answer. Each answer is written into its item, after `Change:` or `Answer:`, with its source: `(the user, in prepare, <YYYY-MM-DD>)`. A question the user skips, or is not asked, stays open in the file. An answer that settles another question drops it, as at build.
5. **Write the readiness file**, `<slug>-readiness.md` beside the genome (the genome's file name with `-readiness.md` in place of `-genome.md`). A process genome has one, covering its components. It holds the sections of § The readiness file, in their order, each with its "Usually answered by" line; a section with no item reads "None.".
6. **Every question is rendered as an item**, worded and optioned as the build would ask it (rules 2–2b), in the item form:
   - its id and the question in bold, `R<n>.`, numbered through the file and kept on a re-run, a new item taking the next number;
   - at most one `Context:` line, with the facts rule 2a names;
   - `See:` the genome sections they rest on;
   - `Recommended:` the Recommended option, with what it gives;
   - `Instead:` one line per other option, with what it gives;
   - `Change:`.

   Each label is in bold and every line is in short sentences. Backticks hold only a name a person types or searches for (a queue, an asset, a file, a package); components and source objects are written plain. A question with no option the build can recommend (a path only the user knows) ends instead on `Until answered:` (what the build does while it stays open) and `Answer:`. A task ends on `Status:`.
7. **Build nothing:** no project or install but the scratch project of preflight discovery, and no tenant write. End by naming the file, how many items each section holds, and how many are needed before the build. When the answers include genome edits, offer to run `uipath-planner` "Apply the answers" now; when no question is left open, offer to build.

## The readiness file

The header says, in this order:
- when and on what machine facts it was prepared, those facts alone: the host, the packages discovery found, the template feed, the deployed libraries the search found or that it could not run, the source export found. It never names a signed-in account, a user name or a tenant URL, since the file travels with the genome;
- how many items are needed before the build, by section;
- how to answer: fill in an item, `accept` under its `Change:` taking its Recommended option or default, then ask `uipath-planner` to "apply the answers", which writes into the genome what changes it;
- the Contents, with each section's counts.

The sections:
1. **Architecture decisions** (§ The Architecture decisions section). Usually answered by: the engineer, with the architect.
2. **Build setup** — every other selected question, in the build's order. Usually answered by: the engineer.
3. **Systems and applications** — a task per system the automation acts on: each row of Target Applications, each system row of Actors and Systems (never a person, nor an automation that calls this one), each connection of Platform Dependencies. Each task holds:
   - how it is reached: screens, API or connector, database, files, mail;
   - what the build uses it for: exploring screens and checking their targets live, when reachable; the connection a connector's calls are written against; test runs;
   - what to arrange: an instance or endpoint the build may reach, or none; the account of each credential asset the genome names that signs in to it; a connection's identity; network access from the build machine; the machine prerequisites its row names, on the build and robot machines.

   It ends on `Status:`. Usually answered by: each system's owner.
4. **Build environment** — the tasks of the machine that builds that no question asks:
   - a Robot that may run the workflows on the build machine, when test runs are wanted;
   - the UiPath CLI signed in to a tenant the build may read;
   - the package feed, with every library the automation consumes;
   - data the build's test runs may change, or none.

   Each ends on `Status:`. Usually answered by: the engineer, with the tenant admin.
5. **Still open in the SDD** — every item of the SDD's Action Required with no answer, under its id and its group's heading, in the SDD's own form. An answer given here is the same item's: it reaches the genome as the SDD's would. Usually answered by: as each item names.

`prepare` run again keeps every change and every `Status:`. It drops:
- each item whose question is now answered elsewhere (the genome, by the decided-values table of [configuration-questions-guide.md](configuration-questions-guide.md) rule 5; the SDD; the preferences file), unless it carries a change, which stays as the record of the decision;
- each edit line marked applied.

It draws again a decision whose Recommended option rests on an answer since changed (a settings store that names the template a change removed), clearing an `accept` under it: that took the option the change replaced.

## The Architecture decisions section

The build's questions that shape what gets built, each with its Recommended option, in the build's order ([configuration-questions-guide.md](configuration-questions-guide.md)), a group with no question left out:
1. **Refactor** — in a refactor, the refactor questions but the rulings, whose source defects are open decisions the SDD holds.
2. **Processes and their work items** — for each flow of the Transactional Shape without a `Decided:` line, its split questions ([transactional-execution-guide.md § Split questions](transactional-execution-guide.md)), each `Context:` naming the flow and the facts of its As-is the answer rests on.
3. **Libraries and reusable parts** — Source fidelity, Library layout and Library location, the layout's `Context:` naming the libraries and the source units each is built from, as the Source Map names them.
4. **Technology per capability** — one question per capability, its `Today:` line, in place of `Context:`, saying how the source does it (the application, the client, the protocol), as the genome states it.

What the genome already shows is named by section where a decision rests on it, never redrawn: its Process Map and Components, Platform Dependencies, the Transactional Shape, Deployment, the Source Map.

**Recorded in.** Each decision has a `Recorded in:` line naming the genome section that states its subject, or `the build` when no section does. `uipath-planner`'s "Apply the answers" writes the answer there. The sections are the flow's `Decided:` line, and the Target Applications row of the component that uses a capability.

A split option's letter appears only beside its meaning.

**The genome gaps discovery found** ([execution-guide.md](execution-guide.md) § 1.2) are the lines of the section's closing block, `Edits for uipath-planner`, which is left out when there is none. `prepare` edits no genome ([SKILL.md](../SKILL.md) Critical Rule 2): "Apply the answers" makes each line, and a build hands any line not yet applied to `uipath-planner` first.

````markdown
# <Process or component>: build readiness

Genome: [`<genome file>`](<relative path>). Prepared <YYYY-MM-DD> by `uipath-genome` `prepare`, on <the machine facts>.

Needed before the build: <n> answers and <n> tasks — <section>: <n>; <section>: <n>. Every other item has a default.

Write an answer after each `Answer:`, `Change:` and `Status:`. To take an item's Recommended option or default, write `accept` under its `Change:`. An item left blank stays open, and the build asks it. Then ask `uipath-planner` to "apply the answers", and build with `uipath-genome`: it asks nothing this file answers.

## Contents

1. [Architecture decisions](#1-architecture-decisions) — <n> decisions, <n> answered
2. [Build setup](#2-build-setup) — <n> needed, <n> to confirm
3. [Systems and applications](#3-systems-and-applications) — <n> to arrange
4. [Build environment](#4-build-environment) — <n> to arrange
5. [Still open in the SDD](#5-still-open-in-the-sdd) — <n> items

## 1. Architecture decisions

Usually answered by: the engineer, with the architect.

Each decision carries the build's proposal: accept it, or change it.

### Refactor

**R<n>. <The refactor question in plain words>**
- **Context:** <the component, and the facts the answer rests on>
- **Recommended:** <the option, with what it gives>
- **Instead:** <one alternative per line>
- **Recorded in:** the build
- **Change:**

### Processes and their work items

**R<n>. <The split question in plain words>**
- **Context:** <the flow, and the facts of its As-is the answer rests on>
- **See:** <the genome sections the context rests on>
- **Recommended:** <the option, with what it gives and why it fits this genome>
- **Instead:** <one alternative, with what it gives>
- **Instead:** <the next alternative, one line each>
- **Recorded in:** <the flow's `Decided:` line>
- **Change:** <blank, or the answer given while preparing, with its source: (the user, in prepare, YYYY-MM-DD)>

### Libraries and reusable parts

**R<n>. <The Library layout question>**
- **Context:** <the libraries, and the source units each is built from>
- **See:** <the genome sections the context rests on>
- **Recommended:** …
- **Instead:** <one alternative per line>
- **Recorded in:** the build
- **Change:**

### Technology per capability

**R<n>. <Capability>: how should the automation <do it>?**
- **Today:** <how the source does it>
- **Recommended:** <the owning skill's way, or the source's in a migration>
- **Instead:** <one alternative per line, with when it fits>
- **Recorded in:** <the component's Target Applications row>
- **Change:**

### Edits for `uipath-planner`

Gaps found in the genome while preparing; applying the answers fixes each one. Delete a line you disagree with.

- <where the genome states it>: <what is wrong, and the fact that shows it>

## 2. Build setup

Usually answered by: the engineer.

**R<n>. <The question in plain words>**
- **Context:** <…>
- **Recommended:** <…>
- **Instead:** <one alternative per line>
- **Change:**

## 3. Systems and applications

Usually answered by: each system's owner.

**R<n>. <System>**
- **Reached through:** <screens | API or connector | database | files | mail>
- **The build uses it for:** <what the build does with it>
- **To arrange:** <an instance or endpoint the build may reach; the account of each credential asset that signs in to it; a connection's identity; network access; machine prerequisites>
- **Status:**

## 4. Build environment

Usually answered by: the engineer, with the tenant admin.

**R<n>. <What to make available>** — <what the build needs it for>
- **Status:**

## 5. Still open in the SDD

Usually answered by: as each item names.

<each open item of the SDD's Action Required, under its id and its group's heading, as the SDD writes it>
````

## Read Plan

`prepare` reads what the rows of [build-guide.md § Read Plan](build-guide.md) whose phase is "start, before any question" name for the conditions that hold, read as that section says.
