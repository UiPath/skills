# Genome Questions Guide

Content rules for a genome's Configuration Questions and Open Decisions sections and for the `*[Inferred]*` mark, however the genome is produced. The sections' place among the others, their stubs and the rules every section follows: [genome-format-guide.md](genome-format-guide.md).

## Configuration Questions

Format: `N. {Question}? ({setting | constant}; default: {value})` — every question names its kind (below) before its default. A question keeps its number, since business rules, the SDD and answers cite it (`CQ3`): a new question goes at the end, and one the genome no longer needs stays as `N. Withdrawn: {why}.`

**Authored genomes** ask every value the description gives or leaves open: paths, URLs, addresses, server names, credential and queue names, thresholds, column names, and the application choice itself ("Which email provider? (constant; default: Outlook)"). A business value the description does not give (a limit, an amount) reads `default: none`, and its question is needed: no value is invented for it.

**Extracted genomes ask only what the source leaves open.** The source is the ground truth and a migration keeps its rules, so a value the source fixes has one right answer; asked, it can only be answered with its default. A value is open when it is:

1. **Bound to the environment** the rebuild runs in:
   - hosts and URLs, paths, shares and folders, mailboxes, recipients and senders, domains, system and client entries;
   - the browser, credential, asset, queue, bucket and Data Fabric entity names, schedules;
   - the language model an AI step uses (the tenant decides which models exist);
   - the reach of a clean-up that acts beyond what the run set up (every window of the session, every certificate of the user, every mapped drive).

   Default: the source's value.
2. **Missing from the export** — a value the build needs that the export does not hold:
   - a setting the source reads from a configuration file, table or vault left out of the export;
   - a caption the source picks only by its key;
   - the starting content of a state file the source reads before it first writes it (a last-used number).

   Default: the key name and "not in the export".
3. **A choice the source never faced** — the target platform offers a way the source had no counterpart for: an Integration Service connection beside the source's token. Default: the source's way. The run's log is the exception: its default is the job's log in Orchestrator, keeping the source's own run log the option ([extract-guide.md](../extract/extract-guide.md) Step 4, evidence policy). The mirror case is open too: the target lacks the source's way, as for an inbound endpoint that took the caller's own token where the target authenticates every caller itself. Default: the target's way, named.
4. **Read from the source's own configuration store** — a key the source reads from a config table, or from a properties file or workbook the export holds outside the project's own files, whatever it carries (a host, a timeout, a poll interval, a limit, a flag). The source's owners change it without a release, so the rebuild keeps it changeable. Default: the source's value. A configuration file among the project's own files ships in its package and changes only with a release: its keys are facts unless item 1 makes one open. A key that only names another resource is a fact (below); the same value written only in the code is a fact.

Every other value is a fact, written once where its reader looks:

- a value typed, posted, compared or checked, and a limit, length or format, in the Workflow substep or Business Rule that uses it;
- a wait, timeout, poll interval or attempt count in its step or that step's Error Handling;
- the item retry and consecutive-failure counts in the Transactional Shape's outcomes ([transactional-shape-guide.md](transactional-shape-guide.md) rule 4);
- a switch a start argument sets in Interface;
- the application and a machine prerequisite (Excel installed) in Target Applications, the application's own, never software only the source platform used to reach it;
- a file the project ships in the step that uses it and the Source Map.

Changing a fact is a genome edit, not a configuration answer.

**A setting depends on the environment.** Every Orchestrator connection the automation is deployed to is its own environment — dev, UAT, prod — and the build is often made on another machine and tenant than the one it runs on. Mark each Configuration Question as:

- a *setting* when its answer differs between environments (hosts and URLs, mailboxes and recipients, shares and paths, credential, queue, bucket, asset and Data Fabric entity names, schedules, language models) or must change without a new version (a key the source reads from its configuration store, item 4 above);
- a *constant* when it is the same in every environment and a change to it is a change to the automation (thresholds, limits, retry counts, message texts).

The kind is written in the question's parenthesis, before the default: `(setting; default: …)` or `(constant; default: …)`. A question that asks each environment's value gives a default per environment: `(setting; default: Test in test, Live in production)`; an environment with no default reads `none`, and the question is needed for it. A configuration key is not by itself one setting: several keys that always carry the same value (one recipient list repeated per notification type) are one setting, and a key whose value only names another resource (a vault alias, a table name fixed by the setup) is a fact. A source's own configuration store (a config table, a properties file, a workbook) is not a Platform Dependency of the rebuild: its keys become questions or facts, and where the rebuild's settings and constants live is decided by execution's configuration questions.

Both modes: when the open values run to dozens (a configuration table or procedure), group them by theme into one question per theme and name every key inside its question, before the question mark, so the list stays readable and the build can still map each key: `4. Which folders does the run use — the drive letter (row 5) and the in-process, processed and invalid folders (rows 6–8)? (setting; default: not in the export)`. A grouped question holds values of one kind; a theme whose values are settings and constants is two questions. When an empty value would change the flow instead of failing (an end time that compares as reached, a list matched by containment), the question says so — "required: empty ends the run" — so the build guards it. Questions the build asks itself are not written into the genome: the scaffolding choices (project location, target framework, expression language, installed package versions), and the split questions (unit, split, store, template, triggers and runners) when the Transactional Shape is not the stub.

## Open Decisions

Every point the genome leaves to a person, one numbered entry each, in the file that owns it: a component's point in its component genome, a point spanning components in the process genome. The interview asks them ([interview-guide.md](../interview/interview-guide.md)), an SDD lists them for the people who answer them when there is one ([sdd-from-genome-guide.md](sdd-from-genome-guide.md)), and the build reads the same list. Format: `N. {The decision as a question}? ({tier}; answered by: {role}; {Builds now | Recommended | Reading | Until answered}: {…}; instead: {an option}) — {step <N>, <step name>, or the section}`, one `instead:` per other option, and `Builds now:` after `Recommended:` when the genome builds something other than the recommendation.

Tiers, in the order the owner reads them, by what a wrong default costs:
1. **business outcome** — what is written to a system of record, what the business is sent and who receives it, which item is worked, skipped, charged or paid, an amount. No option is recommended: the owner rules, and `Builds now:` stands until then. An inferred point that decides an outcome is this tier too, with `Reading:` beside its options.
2. **run behaviour** — how a run counts, retries, recovers, stops, logs or reports: the reason, message or comment it records for an item, a failure notice and what it carries, never its outcome. `Recommended:` the evident intent, in words ("retries every failure three times").
3. **reading** — an inferred point with no outcome of its own: a purpose, a caller, a name, a format. `Reading:` what the genome takes it to be, and why it is inferred.
4. **material** — an object or file the build needs that nobody has supplied: an automation the source calls that the export does not hold, a file from outside the export whose content a step rests on (a template it fills, a workbook whose sheets and columns it reads). `Until answered:` what the build does without it — a placeholder, a stop.

**Answerer roles.** Every entry names one in its `answered by:`; an SDD item, an interview question and the closing counts take it from there:
- `the process owner` — business outcomes, rules, exceptions, scope: the business outcome and run behaviour tiers;
- `whoever knows the process` — how a step is done today: the reading tier;
- `whoever holds the source` — an object or file the build needs: the material tier;
- `the system's owner` — access route, accounts, test instance;
- `the environment's owners` — hosts, mailboxes, folders, schedules per environment;
- `the delivery lead or the centre of excellence` — organisation standards, the preferences file.

A tier's role holds unless the point is another owner's (a system's owner, the environment's owners). A Configuration Question is the environment's owners' when it is a setting, and the process owner's when it is a constant.

Only what nothing else answers is an entry. A point the source, an agreed SDD, the request, the preferences file or the tenant settles is a fact, written where it acts. A point a flow's split options settle (a unique reference, a lock) is the split question's, asked at build, never an entry of its own. The platform the automation is delivered on (Automation Cloud, Automation Suite, standalone) is the planner's product gate and the deployment's, never an entry or a line of the genome ([process-genome-sections-guide.md § Deployment (process)](process-genome-sections-guide.md)). Every other point is classed before it is written:
- a safe default (a retry count, a timeout, a format the target fixes) is the genome's own value, a fact or a Configuration Question's default;
- one whose reading changes what is built or a business outcome is an entry with its default (`builds now:`, `recommended:`, `reading:`);
- one with no reading and no safe default is an entry with `until answered:`, or a Configuration Question whose default the build cannot run with.

Each of these is an entry:

- every `*[Inferred]*` point;
- every source defect with no `User ruling`, except one whose rebuild follows an intent the source states and that changes no business outcome ([extracted-genome-guide.md § Source Defects](extracted-genome-guide.md));
- a detail an evident intent leaves open, with the options the step lists;
- each `Not covered` or `Unused` object of the Source Map, a business outcome since it decides what is built (`Builds now:` left out; `instead:` translate it now) and each `Resource discrepancies` row (`Builds now:` the source; `instead:` the resource);
- material.

A value a Configuration Question asks is that question, never an entry. Points one answer settles — one defect repeated, one reading applied throughout — are one entry whose location names every place; two points on one line that one answer does not settle are two entries, each with its mark.

Every open entry is named where the genome states its point: a marked line (`*[Inferred: D3]*`), a defect's `(ruling open: D3)`, a defect index row or a Source Map row (`(D3)`), or, for a process genome's entry, a component's `process D3`. An entry nothing in the genome names is no question about it, and is not written.

An entry is never removed, so its number stays the one every SDD and answer cites (`D3`), and a new entry goes at the end:
- **decided**, once the genome states the answer: `N. {Question}? (decided {YYYY-MM-DD}: {the answer})`;
- **withdrawn**, once the genome no longer raises it: `N. {Question}? (withdrawn: {why})`.

## Ambiguity Marker

When intent is unclear from the source:

- write the best interpretation;
- append `*[Inferred: D<n>]*` to that line, naming the Open Decisions entry that asks it — `process D<n>`, in a component genome, for an entry of the process genome, `CQ<n>` when a Configuration Question asks the value;
- in an extracted genome, record the uncertainty in the Source Map.

Never leave a section empty because the source is ambiguous. Wherever a genome content rule says a line or a value is `*[Inferred]*`, the mark takes this form. A confirmed reading loses its marker, and its entry reads decided ("Remove the inferred flags" confirms every reading).

## Preferences Question

`author` and `extract` ask it once, before writing, skipped when the request names a file or says none: "Do you have a preferences file: your team's standing answers and development standards for UiPath builds? A path, or none." When each verb asks it, and where it goes when no question is asked: that verb's guide. A file named is applied as [genome-format-guide.md § Design Links](genome-format-guide.md) states.
