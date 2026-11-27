# Open Questions Guide — the questions an SDD puts to people

Every SDD the planner writes holds every question still open about what gets built, in `## Action Required — SME Review Items`, where the template places it: before the design, so whoever answers reads the questions first, or last, with its count in the overview, so the design reads first. The genome holds the same questions for agents: its Configuration Questions and its Open Decisions ([genome-questions-guide.md](genome-questions-guide.md)). This section is their rendering for people.

Who writes it:
- `design` writes it from its own gaps, before a genome exists ([sdd-writing-guide.md](../design/sdd-writing-guide.md) Step 3).
- Once the genome exists, it is written from the genome: in the agreed SDD, by `author` on the design path; in an SDD written from the genome, when there is one ([sdd-from-genome-guide.md](sdd-from-genome-guide.md)). A genome with no SDD holds its questions in its Open Decisions and Configuration Questions alone.

The build's own questions are `uipath-genome`'s: the split, the libraries, the technology for each capability, scaffolding and the build environment. Its `prepare` writes them into a readiness file beside the genome, with this section's items that are still open.

## Writing Rules

1. **Written from the genome on every write, its answers kept**; the strict check run after the write verifies its fingerprint.
   - An item keeps its answer, matched by its id (`D3`, `CQ2`, under its component's heading), or by what it asks when the id no longer fits.
   - An item leaves the section on the rewrite once its entry reads decided, whether the answer changed the genome or kept what it builds; the decided entry keeps the record. One the edit could not make stays, marked `Not applied: <why>`.
   - A configuration value's answer stays as it is: it is the build's answer.
   - A new item comes in blank.
2. **Written for a person filling it in a text editor**, who has read neither the genome nor this skill:
   - plain words, and no tables;
   - every item is its id and the question in bold, then labelled lines as the template lays them out, each label in bold;
   - at most one `Context:` line per item;
   - every line in short sentences;
   - a pointer to the step on a `See:` line of its own, as `step <N>, <step name>`, or the SDD section for a point no step holds;
   - components by their Components names, and source objects by the names their author wrote, in plain text, never by an id or a line;
   - backticks only for a name a person types or searches for (a queue, an asset, a file, a package).
3. **Every item says what a blank costs**, in one of three forms:
   - **A choice.** Its options are lettered under `Options:`, one per line, each with what it gives: the one the genome builds until someone answers marked `(built now)`, the one its entry recommends `(recommended)`, both on one option when they are the same. A reading is a choice whose `(built now)` option is the genome's reading, and whose last option is "something else, in your words".
   - **A value.** `Default:` the value the build uses until someone answers.
   - **Needed.** An item with no option or value the build can run with has an `Until answered:` line instead, saying whether the build stops, asks, builds a placeholder, or builds an empty setting the run stops on.
4. **One answer line names who answers**, `Answer (by <role>):`, the role from the genome entry's `answered by:`, or, for a Configuration Question and the Preferences item, the role [genome-questions-guide.md § Open Decisions](genome-questions-guide.md) gives it, so one person's items can be picked out. An answer is an option's letter, a value, `default` for a value item's default, or the person's own words; a blank stays open.
5. **Only what the genome states.** An item's context comes from its step, its entry and the sections that use it. A fact the genome lacks is asked as an item, never written as one.
6. **Marked where the design states it.** The SDD section that holds an item's subject carries `[SME REVIEW]` for an answer only the business can give, or `[DEFAULT]` for a default applied, as [sdd-writing-guide.md](../design/sdd-writing-guide.md) § Gap Markers states. The note after the bracket names the item (`[SME REVIEW] D3: refund approval when the approver is absent`). The note is the id and a few words, never the item's options or an answer line: an item is answered in Action Required alone, so its letters mean one thing.

## Items

| Group | One item per |
|---|---|
| Business decisions | open Open Decisions entry of the first three tiers, except a Build Assumption's (the list below), under one heading per tier, then per component (the process genome's own entries under the process's name), in step order |
| Material to supply | open entry of the material tier |
| Configuration values | Configuration Question not withdrawn, copied whole with its number, kind and default: process questions first, then each component's in Components order, never a component's line pointing to a process question. A default the build cannot run with ("not in the export", none) makes it needed. A question with a default per environment lists each environment's; `default` takes each, and an environment whose default is `none` makes it needed |
| Preferences | the preferences file, only when the genome names none ([genome-format-guide.md § Design Links](genome-format-guide.md)): default none, the building skills' own practice. A "none" the request or the user's reply gave is its answer, written with who gave it |

Who answers each group's items: Writing Rule 4.

Business decisions close with two lists that ask nothing one item at a time and are not counted as items:
- **Checked against the application at build:** each reading entry that only the live application shows (a screen label, a window title, a control's position), one line each, with no answer line.
- **Confirmed by the build:** each open entry carried from an SDD Build Assumption (its `— SDD Build Assumption A<n>` trailer): what the build confirms, the skill that confirms it, and what the build does if it does not hold, one line each, with no answer line. A build skill answers it, never a person, and the build marks it decided.
- **Defects the rebuild fixes:** each defect that has no entry because its rebuild follows an intent the source states and changes no business outcome ([extracted-genome-guide.md § Source Defects](extracted-genome-guide.md)). One line each, with its component, step and what the rebuild does. The block's one answer line names any the rebuild should keep as the source does. A defect named there takes its ruling and leaves the list; the block has no entry, so it stays, with its answer, while the genome fixes such a defect.

**A process genome's items** sit only in the solution overview's Action Required, under one heading per component, the process genome's own under the process's name. Each keeps its own genome file's id: ids repeat across components and are never renumbered into one series, so an item is named by its component and id (`Portal.Library D1`, `process D1`). A per-project SDD has no Action Required section, and its body's markers name the item with its component.

The section opens with its counts: needed before the build, by group and by role. An item with an `Until answered:` line counts as needed, including one the build covers with a placeholder until then. A group or tier with no item is left out of the section.

## Where Answers Go

- **Business decisions, Material to supply and Preferences are genome edits.** `edit`'s "Apply the answers" writes into the genome each answer that alters what it builds, a recommended option chosen included ([edit-guide.md](../edit/edit-guide.md)). The entry then reads decided, and the step and the SDD follow. An answer that keeps what the genome builds decides the entry as it stands.
  - On the design path, an item taken from the SDD's own design is a design change first ([sdd-writing-guide.md](../design/sdd-writing-guide.md) § Keeping the Genome Current).
- **A point an answer opens** (a clash the new behaviour can meet, a value it needs) is a new entry, added at the end with its default and marked where the genome states it. On the design path it is a new SDD item, after the SDD's last id.
- **Configuration values are the build's answers.** `uipath-genome` reads this section as the user's file of answers, so an answered question is not asked again.
- **Before the build asks anything,** `uipath-genome` offers to send back as that edit every answered item of the genome-edit groups not yet applied, and builds nothing past them until it is made.

## Template

````markdown
## Action Required — SME Review Items

<n> questions are open. Needed before the build: <n> — <group>: <n>; <group>: <n>. Every other item has a default the build uses until someone changes it. By role: the process owner <n>; the environment's owners <n>; whoever holds the source <n>. The build's own questions (the split, the libraries, the technology, the setup) are not here: they are asked when the build is prepared or starts.

How to answer:
1. After an item's `Answer`, write the letter of the option you choose, a value, `default` to keep a value's default, or your own words. An item left blank stays open.
2. Or ask `uipath-planner` to interview you on them: "Interview me on the open questions", adding a role to be asked only that person's. It first asks how you want to answer: every item, only what needs a decision, or the defaults.
3. Then ask it to "Apply the answers". It writes them into the genome and this document.

### Business decisions

<n> business outcomes, <n> run behaviours, <n> readings. None stops the build: each is built as marked `(built now)` until you answer. Start with the business outcomes, because each one changes what the automation does for the business.

#### Business outcomes

##### <Component>

**D<n>. <The decision as a question>**
- **Context:** <the facts the decision rests on, and the business outcome it changes: what is written, sent, to whom, for which item>
- **See:** step <N>, <step name>
- **Options:**
  - a. <what the genome builds now, with what it gives> (built now)
  - b. <the other option, with what it gives>
- **Answer (by the process owner):**

#### How a run behaves

##### <Component>

**D<n>. <The point as a question>**
- **Context:** <…>
- **See:** step <N>, <step name>
- **Options:**
  - a. <the evident intent, in words: "retries every failure three times"> (recommended)
  - b. <the source's behaviour> (built now)
- **Answer (by the process owner):**

#### The genome's readings

##### <Component>

**D<n>. <The reading as a question>**
- **Context:** <why the genome had to infer it>
- **See:** step <N>, <step name>
- **Options:**
  - a. <what the genome takes it to be> (built now)
  - b. something else, in your words
- **Answer (by whoever knows the process):**

Checked against the application at build:
- <step <N>, <step name>: the reading — a label, a window title, a position>

Confirmed by the build:
- <A<n>: can <the capability>? — <skill>; if not, <what the build does instead>>

#### Defects the rebuild fixes

The source states what each was meant to do, and the rebuild does that. Name any the rebuild should keep as the source does.

- <Component>, step <N>, <step name>: <the defect in a few words>. The rebuild <what it does instead>.
- **Answer (by the process owner):**

### Material to supply

**D<n>. <What to supply>**
- **See:** step <N>, <step name>
- **Until answered:** <what the build does: a placeholder, a stop>
- **Answer (by whoever holds the source):**

### Configuration values

#### <Process, or the component>

**CQ<n>. <The question as the genome writes it, whole>**
- **Kind:** <setting | constant>
- **Default:** <default>
- **Answer (by <the environment's owners | the process owner>):**

**CQ<n>. <A question whose default the build cannot run with>**
- **Kind:** <setting | constant>
- **Until answered:** <built as an empty setting the run stops on>
- **Answer (by <the environment's owners | the process owner>):**

### Preferences <only when the genome names no preferences file; with one named, this heading and its item are not written>

**Which preferences file should the build follow?**
- **Context:** <the development standards and standing answers the build follows beyond the genome: naming, project structure, logging, error handling, UI automation, code, testing, packaging>
- **Default:** none: the building skills' own practice
- **Answer (by the delivery lead or the centre of excellence):** <a path or link; start one from `preferences-template.md`, which `uipath-planner` ships>
````
