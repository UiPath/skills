# Prepare Guide — the `prepare` verb

`prepare` runs the start of a build and its questions on the machine that will build, as far as the user answers them, and stops before anything is built. It writes the answers and every question still open into a readiness file beside the genome, together with the questions the SDD still holds open, so the people who answer the rest can do so ahead of the build. The questions, their options and the discovery they rest on are the build's own ([configuration-questions-guide.md](configuration-questions-guide.md), [execution-guide.md](execution-guide.md) § 1.2).

1. **Start as a build starts:** [build-guide.md](build-guide.md) § Start and the reads of § Read Plan, then [execution-guide.md](execution-guide.md) § 1.1 and its § 1.2, the preflight discovery the options are built from.
2. **Read the answers already given.** That means the SDD beside the genome, and an earlier readiness file, both as the user's files of answers ([configuration-questions-guide.md](configuration-questions-guide.md) rules 4 and 4a). Their genome edits not yet made go to `uipath-planner` first, as at build. A genome with no SDD beside it is read for its open entries and its Configuration Questions directly.
3. **Select every question this build would ask** — the genome, refactor, split and scaffolding questions and the run-level ones ([configuration-questions-guide.md](configuration-questions-guide.md)). Drop each one answered by the request, the decided-values table, the preferences file the genome names, or the SDD (an item answered there), and the Subagents question, which the session that builds answers. An answer that carries a check still to make ("to be checked at build") is kept as a task under Systems and applications, naming its item. An SDD item still open is kept under its id, in Still open in the SDD. A question an answer settles only in part is kept for the rest alone, worded for it: Settings store, when the preferences file places only the constants.
4. **Ask as the build asks, as far as the user wants** ([configuration-questions-guide.md](configuration-questions-guide.md) rules 2–3b), in its order whatever section of the file a question lands in, the first question being how to answer. Each answer is written after its item's `Answer:`, with its source: `b (the user, in prepare, <YYYY-MM-DD>)`. A question the user skips, or is not asked, stays open in the file. An answer that settles another question drops it, as at build.
5. **Write the readiness file**, `<slug>-readiness.md` beside the genome (the genome's file name with `-readiness.md` in place of `-genome.md`). A process genome has one, covering its components. It holds the sections of § The readiness file, in their order, each with its "Usually answered by" line; a section with no item reads "None.".
6. **Every question is rendered as an item**, worded and optioned as the build would ask it (rules 2–2b), in the item form:
   - its id and the question in bold, `R<n>.`, numbered through the file and kept on a re-run, a new item taking the next number;
   - at most one `Context:` line, with the facts rule 2a names;
   - `See:` the genome sections they rest on;
   - `Options:` lettered, one per line, each with what it gives, the Recommended one marked `(recommended)`;
   - `Written into:` the genome section the answer goes to, for an Architecture decision;
   - `Answer:`, which takes an option's letter or the person's own words.

   Each label is in bold and every line is in short sentences. Backticks hold only a name a person types or searches for (a queue, an asset, a file, a package); components and source objects are written plain. A question with no option the build can recommend (a path only the user knows) has `Until answered:` (what the build does while it stays open) in place of its options. A task ends on `Status:`.
7. **Build nothing:** no project or install but the scratch project of preflight discovery, and no tenant write. End by naming the file, how many items each section holds, and how many are needed before the build. When the answers include genome edits, offer to run `uipath-planner` "Apply the answers" now; when no question is left open, offer to build.

## The readiness file

The file travels with the genome: no line of it names a signed-in account, a user name or a tenant URL, and a path under the user's profile is written relative to the genome's folder.

The header says, in this order:
- when and on what machine facts it was prepared, those facts alone: the host, the packages discovery found, the template feed, the deployed libraries the search found or that it could not run, the source export found;
- how many items are needed before the build, by section;
- how to answer: write an option's letter, or your own words, after an item's `Answer:`, then ask `uipath-planner` to "apply the answers", which writes into the genome what changes it;
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

`prepare` run again keeps every answer and every `Status:`. It drops:
- each item whose question is now answered elsewhere (the genome, by the decided-values table of [configuration-questions-guide.md](configuration-questions-guide.md) rule 5; the SDD; the preferences file), unless it carries an answer, which stays as the record of the decision;
- each edit line marked applied.

It draws again a decision whose Recommended option rests on an answer since changed (a settings store that names the template a change removed), clearing an answer that chose the option the change replaced.

## The Architecture decisions section

The build's questions that shape what gets built, each with its Recommended option, in the build's order ([configuration-questions-guide.md](configuration-questions-guide.md)), a group with no question left out:
1. **Refactor** — in a refactor, the refactor questions but the rulings, whose source defects are open decisions the SDD holds.
2. **Processes and their work items** — for each flow of the Transactional Shape without a `Decided:` line, its split questions ([transactional-execution-guide.md § Split questions](transactional-execution-guide.md)), each `Context:` naming the flow and the facts of its As-is the answer rests on.
3. **Libraries and reusable parts** — Source fidelity, Library layout and Library location, the layout's `Context:` naming the libraries and the source units each is built from, as the Source Map names them.
4. **Technology per capability** — one question per independent choice, its `Context:` saying how the source does it today (the application, the client, the protocol), as the genome states it.
5. **Genome gaps to rule on** — each gap discovery found that needs someone to choose, with its options, its `Written into:` the genome section it changes.

What the genome already shows is named by section where a decision rests on it, never redrawn: its Process Map and Components, Platform Dependencies, the Transactional Shape, Deployment, the Source Map.

**Written into.** Each decision has a `Written into:` line naming the genome section that states its subject, or `the build` when no section does. `uipath-planner`'s "Apply the answers" writes the answer there. The sections are the flow's `Decided:` line, and the Target Applications row of the component that uses a capability.

A split option's letter appears only beside its meaning.

**Every other gap discovery found** ([execution-guide.md](execution-guide.md) § 1.2) is a line of the section's closing block, `Edits for uipath-planner`, with its fix; the block is left out when there is none. `prepare` edits no genome ([SKILL.md](../SKILL.md) Critical Rule 2): "Apply the answers" makes each line, and a build hands any line not yet applied to `uipath-planner` first.

````markdown
# <Process or component>: build readiness

Genome: [`<genome file>`](<relative path>). Prepared <YYYY-MM-DD> by `uipath-genome` `prepare`, on <the machine facts>.

Needed before the build: <n> answers and <n> tasks — <section>: <n>; <section>: <n>. Every other item has a default.

Write the letter of the option you choose, or your own words, after each `Answer:`, and the state of each task after its `Status:`. An item left blank stays open, and the build asks it. Then ask `uipath-planner` to "apply the answers", and build with `uipath-genome`: it asks nothing this file answers.

## Contents

1. [Architecture decisions](#1-architecture-decisions) — <n> decisions, <n> answered
2. [Build setup](#2-build-setup) — <n> needed, <n> to confirm
3. [Systems and applications](#3-systems-and-applications) — <n> to arrange
4. [Build environment](#4-build-environment) — <n> to arrange
5. [Still open in the SDD](#5-still-open-in-the-sdd) — <n> items

## 1. Architecture decisions

Usually answered by: the engineer, with the architect.

Each decision carries the build's proposal, marked `(recommended)`.

### Refactor

**R<n>. <The refactor question in plain words>**
- **Context:** <the component, and the facts the answer rests on>
- **Options:**
  - a. <the option, with what it gives> (recommended)
  - b. <another option, with what it gives, one per line>
- **Written into:** the build
- **Answer:**

### Processes and their work items

**R<n>. <The split question in plain words>**
- **Context:** <the flow, and the facts of its As-is the answer rests on>
- **See:** <the genome sections the context rests on>
- **Options:**
  - a. <the option, with what it gives and why it fits this genome> (recommended)
  - b. <one alternative, with what it gives>
  - c. <the next alternative, one line each>
- **Written into:** <the flow's `Decided:` line>
- **Answer:** <blank, or the answer given while preparing, with its source: b (the user, in prepare, YYYY-MM-DD)>

### Libraries and reusable parts

**R<n>. <The Library layout question>**
- **Context:** <the libraries, and the source units each is built from>
- **See:** <the genome sections the context rests on>
- **Options:**
  - a. … (recommended)
  - b. <another option, with what it gives, one per line>
- **Written into:** the build
- **Answer:**

### Technology per capability

**R<n>. <Capability>: how should the automation <do it>?**
- **Context:** <how the source does it today>
- **Options:**
  - a. <the owning skill's way, or the source's in a migration> (recommended)
  - b. <another way, with when it fits, one per line>
- **Written into:** <the component's Target Applications row>
- **Answer:**

### Genome gaps to rule on

**R<n>. <The two statements, or the source's way and the skill's, as a question>**
- **Context:** <where the genome states each, and the fact that shows the gap>
- **Options:**
  - a. <the option, with what it gives> (recommended)
  - b. <another option, with what it gives, one per line>
- **Written into:** <the genome section it changes>
- **Answer:**

### Edits for `uipath-planner`

Gaps found in the genome while preparing, each with its fix; applying the answers makes each one. Delete a line you disagree with.

- <where the genome states it>: <what is wrong, the fact that shows it, and the fix>

## 2. Build setup

Usually answered by: the engineer.

**R<n>. <The question in plain words>**
- **Context:** <…>
- **Options:**
  - a. … (recommended)
  - b. <another option, with what it gives, one per line>
- **Answer:**

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
