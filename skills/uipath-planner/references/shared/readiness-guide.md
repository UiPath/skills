# Readiness Guide — the technical readiness that precedes a build

Every genome `author`, `extract` and `edit` write gets a readiness file beside it: everything a person settles before `uipath-genome` builds — the architecture decisions the build proposes, once it has prepared; the systems, existing projects and build environment to make available; the build's own setup questions; the customer's preferences; material to supply; configuration values; business decisions. Each item says what happens if nobody answers it. Most carry a default — the build's proposal, a question's default, what the genome builds now — which a reviewer confirms or changes; an item with none is needed before the build, and the header counts those first. The engineer fills it in with the people each section names. The genome stays the specification and the picture of what gets built — its Process Map and Components, Platform Dependencies, Transactional Shape and Deployment, and the Source Map's Today view of what the rebuild replaces: the file names each item in a few words and points to the step, question, row or section that states it in full, never redraws it. The platform resources the build declares and hands over for the target environment are the genome's Platform Dependencies and Deployment; the file counts them and asks nothing about them.

## File

`<slug>-readiness.md` beside the genome — the genome's file name with `-readiness.md` in place of `-genome.md`: `invoice-processing-genome.md` → `invoice-processing-readiness.md`. A process genome has one, covering its components; a component genome inside a process has none of its own.

## Writing Rules

1. **Written after the strict check of every write**, before edits are offered — `author` Step 8, `extract` Step 7, `edit` § Review after every edit — attended or unattended, for a documentation request too. The header states the check's result — each `FAIL` left after the third round named there, for a `uipath-planner` fix before the build — what gets built and handed over, and how many items are needed before the build, by section; the Contents under it link every section with its counts.
2. **Rewritten on every later write, its answers kept.** An item keeps its answer or change, and a section its `Confirmed:` line, matched by what it asks (the defect, the question, the object, the system, the topic), never by its number. An item the genome no longer raises leaves the file, unless it carries an answer or a change, which stays as the record of the decision; a new item comes in blank, and under a filled `Confirmed:` line it opens with `New since confirmed`, which that line does not cover. Architecture decisions and Build setup are `uipath-genome`'s: a rewrite keeps them as they stand.
3. **Applied answers are marked.** `edit`'s "Apply the readiness answers" adds under each item it writes into the genome — an answer or a change of Material to supply, Business decisions or Architecture decisions, and a confirmed recommendation that differs from what the genome builds now — `Applied <YYYY-MM-DD>`, or `Not applied: <why>` when the edit cannot make it.
4. **Written for a person filling it in a text editor**, who has read neither the genome nor this skill: plain words; no tables, every item a block of labelled lines as the template lays them out; components by their Components names, source objects by the names their author wrote, never by an id or a line. Each item of Material to supply and Business decisions has a `Where:` line naming its step as `step <N>, <step name>` (the genome section for a point no step holds).
5. **Every item says what a blank costs**, in one of three forms:
   - **A default:** the item states it — `Recommended:` for the option the build or this guide recommends, `Default:` for a question's default, `Builds now:` for what the genome builds today, `Reading:` for an inferred point — with `Instead:` for each other option, and ends on `Change:`. A filled `Change:` is the item's answer.
   - **Needed:** an item with no default the build can run with — without its answer the build stops or asks, or builds a placeholder or an empty setting the run stops on — ends on `Answer:`, after an `Until answered:` line saying which.
   - **A task:** something to arrange — access, an account, an install — ends on `Status:`.
6. **Confirmed in one line.** Each section with defaults opens with a `Confirmed:` line — in Configuration values and Business decisions each component heading does instead: a name and date there accept, for every item under it with no change, its Recommended option, otherwise its default, what it builds now or its reading. A blank confirms nothing: the reviewer reads the defaults and corrects what is wrong.
7. **Every section present, in the template's order**, with the line naming who usually answers it; one with no item reads "None.".
8. **Only what the genome states.** A system's use, access and prerequisites come from its row and the steps that use it, and it gets an account line only for a credential asset the genome names; a fact the genome lacks is asked as an item, never written as one.
9. **Every `*[Inferred]*` mark found by a search.** Before Business decisions is written, search every genome file for `[Inferred` (the mark may carry a note: `*[Inferred: …]*`); each hit is an item, or is named in the `Where:` line of the item that covers it.

## Items

The sections, in the file's order:

| Section | Usually answered by | One item per | Where the genome holds it |
|---|---|---|---|
| 1. Architecture decisions | the engineer, with the customer's architect | written by `uipath-genome`'s `prepare`: each decision that shapes what gets built — the split of each flow, the library layout, the technology for each capability (mail, documents, spreadsheets, applications, connectors), the framework and the other build-wide choices — with the build's Recommended option and the genome section that records the answer; until then the section names that step and points to the genome's picture of what gets built and what it replaces | the Transactional Shape; the Source Map's Today view; Target Applications or Actors and Systems; Deployment |
| 2. Systems and applications | each system's owner | task per system the automation acts on — each row of Target Applications, each system row of Actors and Systems in a process genome (never a person, nor an automation that calls this one) and each connection of Platform Dependencies: how it is reached (screens, API or connector, database, files, mail); what the build uses it for (screens: exploring them and checking their targets live, when reachable; a connector: the connection its calls are written against; any other: test runs); what to arrange — an instance or endpoint the build may reach, or none; the account of each credential asset that signs in to it; a connection's identity; network access from the build machine; the machine prerequisites its row names, on the build and robot machines | Target Applications; Actors and Systems; Platform Dependencies; the steps that use it |
| 3. Existing projects | the engineer | component: a project of it an earlier build made, to build into; default: none, a new project | Components or Build With |
| 4. Build environment | the engineer, with the tenant admin | task: the source export at the path the Source Map records, and the framework migration pack (another framework's source); a Robot that may run the workflows on the build machine, when test runs are wanted; the UiPath CLI signed in to a tenant the build may read; the package feed, with every library the automation consumes; data the build's test runs may change, or none | Source Map; Build With; Platform Dependencies |
| 5. Build setup | the engineer | written by the same `prepare`, on the machine that builds: each remaining question that build would ask — where, with which packages, what it may reach | — |
| 6. Preferences | the customer's delivery lead or centre of excellence | each topic of the template's Preferences, every genome alike: the customer's standards document, naming, project structure, logging, error handling, UI automation, code, testing, packaging and versioning — the standards the build follows beyond the genome; default: the building skills' own practice | — |
| 7. Material to supply | whoever holds the source and its documents | needed: object the source calls, or that calls it, that the export does not hold: its export | the unresolved-invocation row |
| | | related resources (PDD, SOP, runbooks), when the extraction never asked for them; default: none | the `Related resources` row |
| 8. Configuration values | the environment's owners, with the engineer | Configuration Question, copied whole with its number, kind and default — process questions first, then each component's in Components order; a default the build cannot run with ("not in the export", none) makes it needed | Configuration Questions |
| 9. Business decisions | the process owner | source defect with no `User ruling` that the next row does not take — its evident intent marked `*[Inferred]*` or shown only by the step's purpose, or its ruling open — options: the source's behaviour, the evident intent; `Builds now:` the one the genome builds, as the defect index's Rebuild follows cell, or else the step, states it | the defect at its step; a process genome's defect index ([extracted-genome-guide.md § Source Defects](extracted-genome-guide.md)) |
| | | source defect with no `User ruling` whose rebuild follows an evident intent the source states (no `*[Inferred]*`, more than the step's purpose), as the Rebuild follows cell or the step says: one line in the section's closing block, Defects the rebuild fixes, with its component, step and what the rebuild does; the block's one `Change:` names any the rebuild should keep as the source does | the defect at its step; the defect index |
| | | detail an evident intent leaves open, with the options the step lists; `Builds now:` the option the genome builds | the step |
| | | `Not covered` or `Unused` object: `Builds now:` left out; `Instead:` translate it now | those Source Map rows |
| | | `Resource discrepancies` row: `Builds now:` the source; `Instead:` the resource, when the owner rules for it | Source Map |
| | | `*[Inferred]*` mark no other item covers, in any section, the Source Map's rows included, as `Reading:` | the marked line or row |

**Business decisions are ordered by what a wrong default costs**, so the owner reads the few that matter first. None is needed before the build: the genome builds each as it stands until the owner changes it. Each item goes to one tier, then, inside its tier, under one heading per component and in step order:

1. **Business outcomes:** what is written to a system of record, what is sent and to whom, which item is worked, skipped, charged or paid, an amount. `Builds now:` is the source's behaviour, no option is recommended — the owner rules — and an `Affects:` line names the outcome.
2. **How a run behaves:** how it counts, retries, recovers, stops, logs or reports, never its outcome. The evident intent is `Recommended:` — a run that counts, retries and recovers as it was meant to — and a `Builds now:` line shows the source's behaviour when the genome builds that until the owner confirms.
3. **The genome's readings:** an `*[Inferred]*` point with no outcome of its own — a purpose, a caller, a name, a format — as `Reading:`. A point only the live application shows — a screen label, a window title, a control's position — is listed under the tier's closing line "Checked against the application at build", one line each, with no `Change:`.

The same kind of point at several steps — one defect repeated, one reading applied throughout — is one item whose `Where:` names every step. The tiers' item counts open the section.

Items of Business decisions and Configuration values are grouped under one heading per component, the process genome's own points under the process's name. An authored genome has no Source Map: its Business decisions hold its `*[Inferred]*` marks, and Material to supply is "None." unless a step names an automation the genome does not hold.

## Where Answers Go

- **Material to supply and Business decisions are genome edits**, and so is each Architecture decision whose `Recorded in:` line names a genome section. `edit`'s "Apply the readiness answers" writes into the genome each answer, change and confirmed recommendation that alters it, marks the item and rewrites this file ([edit-guide.md](../edit/edit-guide.md)). `uipath-genome` builds the genome as written: before it asks anything, it sends back as that edit every answered or changed item of Material to supply and Business decisions, and every confirmed recommendation there, that carries neither mark and changes what the genome builds; one that keeps it is followed as it stands. An Architecture decision the build follows as an answer, recorded in the genome or not.
- **Every other section is the build's answers.** `uipath-genome` reads the file beside the genome as the user's file of answers: an item with an answer or a change, and an item under a filled `Confirmed:` line, is not asked again; any other item is asked at build. A preference no question asks is a rule the build follows, and one that conflicts with a rule of the building skills is put to the user with both. Systems and applications and Build environment are also the engineer's list of what to make available before the build starts; their `Status:` lines record it.

## Template

````markdown
# <Process or component>: technical readiness

Genome: [`<genome file>`](<relative path>) (<component | process>), written <YYYY-MM-DD> by `uipath-planner` `<author | extract | edit>`. Strict check: <passes | <n> failures left: <each>; ask `uipath-planner` to fix them before the build>.

What gets built: <each project and its type>, as the genome's Process Map and Components show it. Handed over for the target environment, as the genome's Platform Dependencies and Deployment describe them: <n> queues, <n> assets, <n> credentials, <n> storage buckets, <n> connections, <n> triggers, <the folders and robots Deployment names>.

Needed before the build: <n> answers and <n> tasks — <section>: <n>; <section>: <n>. Every other item has a default.

## Contents

1. [Architecture decisions](#1-architecture-decisions) — <not prepared | <n> decisions, <confirmed | to confirm>>
2. [Systems and applications](#2-systems-and-applications) — <n> to arrange
3. [Existing projects](#3-existing-projects) — <confirmed | to confirm>
4. [Build environment](#4-build-environment) — <n> to arrange
5. [Build setup](#5-build-setup) — <not prepared | <n> needed, <n> to confirm>
6. [Preferences](#6-preferences) — <confirmed | to confirm>
7. [Material to supply](#7-material-to-supply) — <n> needed
8. [Configuration values](#8-configuration-values) — <n> needed, <n> to confirm
9. [Business decisions](#9-business-decisions) — <n> business outcomes, <n> run behaviours, <n> readings

Write an answer after each `Answer:` and `Status:`. Read each section's defaults, write a change under any that is wrong, then your name and the date on its `Confirmed:` line. Then:
1. On the machine that will build, ask `uipath-genome` to "prepare the build". It writes Architecture decisions and Build setup.
2. Ask `uipath-planner`: "Apply the readiness answers". It writes into the genome what the answers change.
3. Build with `uipath-genome`: it asks nothing this file answers or confirms.

Start the requests of Systems and applications and Build environment first: access takes the longest.

## 1. Architecture decisions

Usually answered by: the engineer, with the customer's architect.

Not prepared yet: on the machine that will build, ask `uipath-genome` to "prepare the build". What gets built is the genome's Process Map and Components; what it replaces, the Source Map's Today view; its Transactional Shape holds <n> flows, whose split `prepare` proposes.

## 2. Systems and applications

Usually answered by: each system's owner.

### <System>

- Reached through: <screens | API or connector | database | files | mail>
- The build uses it for: <what the build does with it>
- To arrange: <an instance or endpoint the build may reach; the account of each credential asset that signs in to it; a connection's identity; network access; machine prerequisites>
- Status:

## 3. Existing projects

Usually answered by: the engineer.

Confirmed:

1. **<Component>: a project of it an earlier build made**
   - Default: none — the build makes a new project
   - Change: <its path>

## 4. Build environment

Usually answered by: the engineer, with the tenant admin.

1. **<What to make available>** — <what the build needs it for>
   - Status:

## 5. Build setup

Usually answered by: the engineer.

Not prepared yet: on the machine that will build, ask `uipath-genome` to "prepare the build".

## 6. Preferences

Usually answered by: the customer's delivery lead or centre of excellence.

The standards the build follows beyond the genome; each defaults to the building skills' own practice. A standards document named in item 1 is read as preferences; the items below then hold only what it leaves out.

Confirmed:

1. **Standards document**: a path or link to the customer's development standards; default: none.
   - Change:
2. **Naming**: projects, workflows, arguments and variables, Object Repository screens and elements, queues and assets.
   - Change:
3. **Project structure**: the template projects start from (REFramework, a company template), libraries per application or per module, the folder layout.
   - Change:
4. **Logging**: levels, what each workflow logs (its start and end, business milestones), the fields of a log line, what must never be logged.
   - Change:
5. **Error handling**: where business and system exceptions are raised, retries, screenshots on failure.
   - Change:
6. **UI automation**: application state checks, selector rules, Object Repository use.
   - Change:
7. **Code**: XAML or coded workflows, expression language, annotations, the workflow analyzer rule set.
   - Change:
8. **Testing**: test cases per workflow, test data, what a test must cover.
   - Change:
9. **Packaging and versioning**: the version scheme, release notes, the feed each package goes to.
   - Change:

## 7. Material to supply

Usually answered by: whoever holds the source and its documents.

1. **<What to supply>**
   - Where: <where the genome names it>
   - Until answered: <what the build does — a placeholder, a stop>
   - Answer:

## 8. Configuration values

Usually answered by: the environment's owners, with the engineer.

### <Process, or the component>

Confirmed:

<N>. **<the question as the genome writes it, whole>**
   - Kind: <setting | constant>
   - Default: <default>
   - Change:

<N>. **<a question whose default the build cannot run with>**
   - Kind: <setting | constant>
   - Until answered: <built as an empty setting the run stops on>
   - Answer:

## 9. Business decisions

Usually answered by: the process owner.

<n> business outcomes, <n> run behaviours, <n> readings. None stops the build: each is built as written until you change it. Start with the business outcomes: each changes what the automation does for the business. Under each component, write a change under any item that is wrong, then your name and the date on its `Confirmed:` line.

### 9a. Business outcomes

#### <Component>

Confirmed:

1. **<The decision in a few words>**
   - Where: step <N>, <step name>
   - Builds now: <what the source does, which the rebuild keeps until you rule>
   - Affects: <the business outcome — what is written, sent, to whom, for which item>
   - Instead: <the other option, with what it gives>
   - Change:

### 9b. How a run behaves

#### <Component>

Confirmed:

1. **<The point in a few words>**
   - Where: step <N>, <step name>; step <N>, <step name>
   - Recommended: <the evident intent, in words — "retries every failure three times", never only "the evident intent">
   - Builds now: <the source's behaviour, when the genome builds it until you confirm>
   - Change:

### 9c. The genome's readings

#### <Component>

Confirmed:

1. **<The reading in a few words>**
   - Where: step <N>, <step name>
   - Reading: <what the genome takes it to be, and why it is inferred>
   - Change:

Checked against the application at build:
- <step <N>, <step name>: the reading — a label, a window title, a position>

### Defects the rebuild fixes

The source states what each was meant to do, and the rebuild does that. Name any the rebuild should keep as the source does.

- <Component>, step <N>, <step name>: <the defect in a few words> — the rebuild <what it does instead>
- Change:
````
