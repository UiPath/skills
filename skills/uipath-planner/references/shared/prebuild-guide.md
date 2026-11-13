# Pre-build File Guide — what a person settles before the build

Every genome `author`, `extract` and `edit` write gets a pre-build file beside it: each item the genome leaves to a person — a business decision, material to supply, a configuration value, a build decision, a system or a piece of the build environment to make available — with where the genome raises it and a line for the answer. The engineer fills it in, with the people each section names, before `uipath-genome` builds. The genome stays the specification: the file names each item in a few words and points to the step, question or row that states it in full.

## File

`<slug>-prebuild.md` beside the genome — the genome's file name with `-prebuild.md` in place of `-genome.md`: `invoice-processing-genome.md` → `invoice-processing-prebuild.md`. A process genome has one, covering its components; a component genome inside a process has none of its own.

## Writing Rules

1. **Written after the strict check of every write**, before edits are offered — `author` Step 8, `extract` Step 7, `edit` § Review after every edit — attended or unattended, for a documentation request too. The header states the check's result; each `FAIL` left after the third round is named there, for a `uipath-planner` fix before the build.
2. **Rewritten on every later write, its answers kept.** An item keeps its answer, matched by what it asks (the defect, the question, the object, the system), never by its number. An unanswered item the genome no longer raises leaves the file; an answered one stays as the record of the decision; a new item comes in with an empty answer.
3. **Applied answers are marked.** `edit`'s "Apply the pre-build answers" adds under each answer of sections 1 and 2 `Applied <YYYY-MM-DD>`, or `Not applied: <why>` when the edit cannot make it.
4. **Written for a person filling it in a text editor**, who has read neither the genome nor this skill: plain words; no tables, every item a block of labelled lines as the template lays them out, each answer on its own `Answer:` or `Status:` line; components by their Components names, source objects by the names their author wrote, never by an id or a line. Each item of sections 1 and 2 has a `Where:` line naming its step as `step <N>, <step name>` (the genome section for a point no step holds) and an `Until answered:` line saying what the build does while it stays open.
5. **Every section present**, with the line naming who usually answers it; one with no item reads "None.".
6. **Only what the genome states.** A system's use, access and prerequisites come from its row and the steps that use it, and it gets an account line only for a credential asset the genome names; a fact the genome lacks is asked as an item, never written as one.
7. **Every `*[Inferred]*` mark found by a search.** Before section 1 is written, search every genome file for `[Inferred` (the mark may carry a note: `*[Inferred: …]*`); each hit is an item, or is named in the `Where:` line of the item that covers it.

## Items

| Section | Usually answered by | One item per | Where the genome holds it |
|---|---|---|---|
| 1. Business decisions | the process owner | source defect whose rebuild behaviour is the user's to rule on — options: the source's behaviour, the evident intent; the one built now named | the defect at its step; a process genome's defect index ([extracted-genome-guide.md § Source Defects](extracted-genome-guide.md)) |
| | | detail an evident intent leaves open, with the options the step lists | the step |
| | | `Not covered` or `Unused` object: translate it now, or the build leaves it out | those Source Map rows |
| | | `Resource discrepancies` row: the rebuild follows the source unless the owner rules for the resource | Source Map |
| | | `*[Inferred]*` mark no other item covers, in any section, the Source Map's rows included: confirm it, or say what it should be | the marked line or row |
| 2. Material to supply | whoever holds the source and its documents | object the source calls, or that calls it, that the export does not hold: its export | the unresolved-invocation row |
| | | related resources (PDD, SOP, runbooks), when the extraction never asked for them | the `Related resources` row |
| 3. Configuration values | the environment's owners, with the engineer | Configuration Question, copied whole with its number, kind and default — process questions first, then each component's in Components order | Configuration Questions |
| 4. Build decisions | the engineer | flow of the Transactional Shape: its unit of work and split option; a flow with a `Decided:` line is listed as decided, with no answer | the flow's Unit of work, Alternative units of work and Split options |
| | | component: a project of it an earlier build made, to build into, and its path, or none | Components or Build With |
| 5. Systems | each system's owner | system the automation acts on — each row of Target Applications, each system row of Actors and Systems in a process genome (never a person, nor an automation that calls this one) and each connection of Platform Dependencies: how it is reached (screens, API or connector, database, files, mail); what the build uses it for (screens: exploring them and checking their targets live, when reachable; a connector: the connection its calls are written against; any other: test runs); what to arrange — an instance or endpoint the build may reach, or none; the account of each credential asset that signs in to it; a connection's identity; network access from the build machine; the machine prerequisites its row names, on the build and robot machines | Target Applications; Actors and Systems; Platform Dependencies; the steps that use it |
| 6. Build environment | the engineer, with the tenant admin | the source export at the path the Source Map records, and the framework migration pack (another framework's source); a Robot that may run the workflows on the build machine, when test runs are wanted; the UiPath CLI signed in to a tenant the build may read; the package feed, with every library the automation consumes; data the build's test runs may change, or none; the Orchestrator folder and robot the automation runs under | Source Map; Build With; Platform Dependencies; Deployment |

Items of sections 1 and 3 are grouped under one heading per component, the process genome's own points under the process's name. An authored genome has no Source Map: its section 1 holds its `*[Inferred]*` marks, and section 2 is "None." unless a step names an automation the genome does not hold.

## Where Answers Go

- **Sections 1 and 2 are genome edits.** `edit`'s "Apply the pre-build answers" applies each answered item to the genome, marks it and rewrites this file ([edit-guide.md](../edit/edit-guide.md)). `uipath-genome` builds the genome as written: before it asks anything, it sends back as that edit every answered item of these sections that carries neither mark.
- **Sections 3 to 6 are the build's answers.** `uipath-genome` reads the file beside the genome as the user's file of answers: an answered item is not asked again, an empty one is asked at build, beside the questions the build asks itself. Sections 5 and 6 are also the engineer's list of what to make available before the build starts; their `Status:` lines record it.

## Template

````markdown
# <Process or component>: before the build

Genome: [`<genome file>`](<relative path>) (<component | process>), written <YYYY-MM-DD> by `uipath-planner` `<author | extract | edit>`. Strict check: <passes | <n> failures left: <each>; ask `uipath-planner` to fix them before the build>.

Write each answer after its `Answer:` or `Status:`. Then ask `uipath-planner`: "Apply the pre-build answers"; it writes sections 1 and 2 into the genome. Then build with `uipath-genome`: it reads sections 3 to 6 from this file and asks only what is still empty. Start the requests of sections 5 and 6 first: access takes the longest.

## 1. Business decisions

Usually answered by: the process owner.

### <Component>

1. **<The decision in a few words>**
   - Where: step <N>, <step name>
   - <What the source does, or what the genome builds now.>
   - Options: <option>; <option>
   - Until answered: <what the build does>
   - Answer:

## 2. Material to supply

Usually answered by: whoever holds the source and its documents.

1. **<What to supply>**
   - Where: <where the genome names it>
   - Until supplied: <what the build does>
   - Answer:

## 3. Configuration values

Usually answered by: the environment's owners, with the engineer.

### <Process, or the component>

<N>. **<the question as the genome writes it, whole>**
   - Kind: <setting | constant>
   - Default: <default>
   - Answer:

## 4. Build decisions

Usually answered by: the engineer.

1. **<The flow by its unit of work>: unit of work and split**
   - Options: <the unit and its alternatives; A, B, C as the flow's rows state them> (or: Decided: <option>, <source>)
   - Answer:
2. **<Component>: a project of it an earlier build made**
   - Options: its path; none
   - Answer:

## 5. Systems

Usually answered by: each system's owner.

### <System>

- Reached through: <screens | API or connector | database | files | mail>
- The build uses it for: <what the build does with it>
- To arrange: <an instance or endpoint the build may reach; the account of each credential asset that signs in to it; a connection's identity; network access; machine prerequisites>
- Status:

## 6. Build environment

Usually answered by: the engineer, with the tenant admin.

1. **<What to make available>** — <what the build or the first run needs it for>
   - Status:
````
