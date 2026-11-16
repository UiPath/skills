# Open Questions Guide — the questions an SDD puts to people

Every SDD the planner writes opens with every question still open about what gets built, in `## Action Required — SME Review Items`. Whoever answers reads the questions first and the design below them. The genome holds the same questions for agents: its Configuration Questions and its Open Decisions ([genome-format-guide.md](genome-format-guide.md)). This section is their rendering for people.

Who writes it:
- `design` writes it from its own gaps, before a genome exists ([sdd-writing-guide.md](../design/sdd-writing-guide.md) Step 1.5).
- Once the genome exists, every write (`author`, `extract`, `edit`) writes it again from the genome, on the design path too ([sdd-from-genome-guide.md](sdd-from-genome-guide.md)).

The build's own questions are `uipath-genome`'s: the split, the libraries, the technology for each capability, scaffolding, existing projects and the build environment. Its `prepare` writes them into a readiness file beside the genome, with this section's items that are still open.

## Writing Rules

1. **Written from the genome after its strict check, on every write, its answers kept.**
   - An item keeps its answer, and a heading its `Confirmed:` line. Each is matched by its id (`D3`, `CQ2`, under its component's heading), or by what it asks when the id no longer fits.
   - An item the answers made into a genome edit leaves the section on the rewrite after that edit; the genome's decided entry keeps the record. One the edit could not make stays, marked `Not applied: <why>`.
   - A configuration value's answer stays as it is: it is the build's answer.
   - A new item comes in blank. Under a filled `Confirmed:` line it opens with `New since confirmed`, which that line does not cover.
2. **Written for a person filling it in a text editor**, who has read neither the genome nor this skill:
   - plain words, and no tables;
   - every item is its id and the question in bold, then labelled lines as the template lays them out, each label in bold;
   - one `Context:` line per item, and one option per `Instead:` line;
   - every line in short sentences;
   - a pointer to the step on a `Where:` line of its own, as `step <N>, <step name>`, or the SDD section for a point no step holds;
   - components by their Components names, and source objects by the names their author wrote, in plain text, never by an id or a line;
   - backticks only for a name a person types or searches for (a queue, an asset, a file, a package).
3. **Every item says what a blank costs**, in one of two forms:
   - **A default.** The item states it: `Builds now:` for what the genome builds, `Recommended:` for the option the genome's entry recommends, `Default:` for a question's default, `Reading:` for an inferred point. Then `Instead:` for each other option, ending on `Change:`. A filled `Change:` is the item's answer.
   - **Needed.** An item with no default the build can run with ends on `Answer:`, after an `Until answered:` line. That line says whether the build stops, asks, builds a placeholder, or builds an empty setting the run stops on.
4. **Answered by** names the role on every item, from the genome entry's `answered by:` (for a Configuration Question, the section's role), so one person's items can be picked out.
5. **Confirmed in one line.** Each component heading in Business decisions and in Configuration values opens with a `Confirmed:` line. A name and date there accept, for every item under it with no change, its Recommended option, otherwise its default, what it builds now, or its reading. A blank confirms nothing: the reviewer reads the defaults and corrects what is wrong.
6. **Only what the genome states.** An item's context comes from its step, its entry and the sections that use it. A fact the genome lacks is asked as an item, never written as one.
7. **Marked where the design states it.** The SDD section that holds an item's subject carries `[SME REVIEW]` for an answer only the business can give, or `[DEFAULT]` for a default applied, with the note after the bracket naming the item (`[SME REVIEW] D3: refund approval when the approver is absent`), as [sdd-writing-guide.md](../design/sdd-writing-guide.md) § Gap Markers states.

## Items

| Group | One item per | Usually answered by |
|---|---|---|
| Business decisions | open Open Decisions entry of the first three tiers, under one heading per tier, then per component (the process genome's own entries under the process's name), in step order | the process owner |
| Material to supply | open entry of the material tier | whoever holds the source and its documents |
| Configuration values | Configuration Question not withdrawn, copied whole with its number, kind and default: process questions first, then each component's in Components order, never a component's line pointing to a process question. A default the build cannot run with ("not in the export", none) makes it needed | the environment's owners, with the engineer |
| Preferences | the preferences file, only when the genome names none ([genome-format-guide.md § Design Links](genome-format-guide.md)): default none, the building skills' own practice | the delivery lead or the centre of excellence |

Business decisions close with two lists that ask nothing one item at a time:
- **Checked against the application at build:** each reading entry that only the live application shows (a screen label, a window title, a control's position), one line each, with no `Change:`.
- **Defects the rebuild fixes:** each defect that has no entry because its rebuild follows an intent the source states and changes no business outcome ([extracted-genome-guide.md § Source Defects](extracted-genome-guide.md)). One line each, with its component, step and what the rebuild does. The block's one `Change:` names any the rebuild should keep as the source does.

**A process genome's items** sit only in the solution overview's Action Required, under one heading per component, the process genome's own under the process's name. Each keeps its own genome file's id: ids repeat across components and are never renumbered into one series, so an item is named by its component and id (`LARA.Library D1`, `process D1`). A per-project SDD has no Action Required section, and its body's markers name the item with its component.

The section opens with its counts: needed before the build, by group and by role. An item that ends on `Answer:` counts as needed, including one the build covers with a placeholder until then. A group or tier with no item is left out of the section.

## Where Answers Go

- **Business decisions, Material to supply and Preferences are genome edits.** `edit`'s "Apply the answers" writes into the genome each answer, change, and confirmed recommendation that alters what it builds ([edit-guide.md](../edit/edit-guide.md)). The entry then reads decided, and the step and the SDD follow. A confirmed default that keeps what the genome builds decides the entry as it stands.
  - On the design path, an item taken from the SDD's own design is a design change first ([sdd-writing-guide.md](../design/sdd-writing-guide.md) § Keeping the Genome Current).
- **A point an answer opens** (a clash the new behaviour can meet, a value it needs) is a new entry, added at the end with its default and marked where the genome states it. On the design path it is a new SDD item, after the SDD's last id. It comes into Action Required under `New since confirmed`.
- **Configuration values are the build's answers.** `uipath-genome` reads this section as the user's file of answers, so an answered or confirmed question is not asked again.
- **Before the build asks anything,** `uipath-genome` sends back as that edit every answered item of the genome-edit groups not yet applied.

## Template

````markdown
## Action Required — SME Review Items

<n> questions are open. Needed before the build: <n> — <group>: <n>; <group>: <n>. Every other item has a default the build uses until someone changes it. By role: the process owner <n>; the environment's owners <n>; whoever holds the source <n>.

How to answer:
1. Write your answer under an item's `Change:` or `Answer:`, or put your name and the date on a `Confirmed:` line to accept every default under it.
2. Or ask `uipath-planner` to interview you on them: "Interview me on the open questions", adding a role to be asked only that person's. It first asks how you want to answer: every item, only what needs a decision, or the defaults.
3. Then ask it to "Apply the answers". It writes them into the genome and this document.

### Business decisions

<n> business outcomes, <n> run behaviours, <n> readings. None stops the build: each is built as written until you change it. Start with the business outcomes, because each one changes what the automation does for the business.

#### Business outcomes

##### <Component>

**Confirmed:**

**D<n>. <The decision as a question>**
- **Context:** <the facts the decision rests on>
- **Where:** step <N>, <step name>
- **Builds now:** <what the genome builds until you rule>
- **Affects:** <the business outcome: what is written, sent, to whom, for which item>
- **Instead:** <the other option, with what it gives>
- **Answered by:** the process owner
- **Change:**

#### How a run behaves

##### <Component>

**Confirmed:**

**D<n>. <The point as a question>**
- **Context:** <…>
- **Where:** step <N>, <step name>
- **Recommended:** <the evident intent, in words: "retries every failure three times">
- **Builds now:** <the source's behaviour, when the genome builds it until you confirm>
- **Answered by:** the process owner
- **Change:**

#### The genome's readings

##### <Component>

**Confirmed:**

**D<n>. <The reading as a question>**
- **Where:** step <N>, <step name>
- **Reading:** <what the genome takes it to be, and why it is inferred>
- **Answered by:** whoever knows the process
- **Change:**

Checked against the application at build:
- <step <N>, <step name>: the reading — a label, a window title, a position>

#### Defects the rebuild fixes

The source states what each was meant to do, and the rebuild does that. Name any the rebuild should keep as the source does.

- <Component>, step <N>, <step name>: <the defect in a few words>. The rebuild <what it does instead>.
- **Change:**

### Material to supply

**D<n>. <What to supply>**
- **Where:** step <N>, <step name>
- **Until answered:** <what the build does: a placeholder, a stop>
- **Answered by:** whoever holds the source
- **Answer:**

### Configuration values

#### <Process, or the component>

**Confirmed:**

**CQ<n>. <The question as the genome writes it, whole>**
- **Kind:** <setting | constant>
- **Default:** <default>
- **Answered by:** the environment's owners
- **Change:**

**CQ<n>. <A question whose default the build cannot run with>**
- **Kind:** <setting | constant>
- **Until answered:** <built as an empty setting the run stops on>
- **Answered by:** the environment's owners
- **Answer:**

### Preferences

<only when the genome names no preferences file; otherwise this group is left out>

**Which preferences file should the build follow?**
- **Context:** <the development standards and standing answers the build follows beyond the genome: naming, project structure, logging, error handling, UI automation, code, testing, packaging>
- **Default:** none: the building skills' own practice
- **Answered by:** the delivery lead or the centre of excellence
- **Change:** <a path or link; start one from `preferences-template.md`, which `uipath-planner` ships>
````
