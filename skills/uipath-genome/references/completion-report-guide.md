# Completion Report Guide — the hand-off

Step 3.3 of [execution-guide.md](execution-guide.md). Bare step and section numbers below (§ 2.2, § 3.1, § 3.5) are that guide's.


Execution ends with a hand-off for the engineer who maintains and deploys the build: one folder, `<slug>-handoff/`, beside the solution or project folder (where the Location answer put it), named with the solution's or project's slug ([genome-reading-guide.md § File Naming and Location](genome-reading-guide.md)) — never inside a project, whose package would ship it, nor inside the solution folder. The genome, the built solution or project and this folder are what travels; the working folder (`migration/` in a migration) stays with the build. Its files:

| File | Holds | Written |
|---|---|---|
| `README.md` | the completion report, below, and the index of the folder | its Configuration answers once they exist ([configuration-questions-guide.md](configuration-questions-guide.md) rule 4), the rest last |
| `open-items.md`, `open-items/<project-slug>.md` | what the target environment needs before the first run, with the records to load beside them | at the end, when the environment needs setup ([open-items-guide.md](open-items-guide.md)) |
| `live-checks/<project-slug>.md` | what only the live application can settle, by screen | with each UI target ([ui-target-migration-guide.md § Verifying targets](ui-target-migration-guide.md)) |
| `applications/<application-slug>.md` | how each application is driven: windows and titles, input method, structures, selector verdicts | when a reachable application is explored ([live-application-guide.md § Exploring](live-application-guide.md)) |
| `correspondence/<component>.md` | where the rebuild departs from the source's names and shape, and why | with each component, when the Source fidelity answer keeps it ([source-migration-guide.md § What the executor records](source-migration-guide.md)) |
| `parity/<TestCase>.md`, `checkpoints/<component>.md` | which assertion stands for each source checkpoint | with each test component ([test-execution-guide.md § Result parity](test-execution-guide.md)) |
| `refactor-plan.md` | a refactor's decisions, differences from the source, kept outputs and what is not proven until it runs | once the refactor questions are answered ([refactor-guide.md § Refactor plan](refactor-guide.md)) |
| `integration-check.md` | the independent review of the projects against each other and what became of each finding | after every project is built (§ 3.5) |
| `reports/<project-slug>.md` | each project's group reports: files, validation and link counts, the activity kinds read, what each step's source defects became | at each group's end (§ 2.2 step 4) |

The README is the completion report. It is written for a reader who has this folder and the build but no working folder: in full sentences, with steps and components by the names the genome gives them ([configuration-questions-guide.md](configuration-questions-guide.md) rule 2b), source objects by the names their author wrote, and each decision with its reason, never by a ruling, part or finding number. It states each fact once: the tables stay in their files, and the README counts and links them. The final message to the user is the README's Status section and its path.

````markdown
# <Solution or project>: hand-off

<What the automation does, in two sentences from the genome's Overview; what was built, from which genome and, in a migration, from which source export.>

| | |
|---|---|
| Genome | `<path to the genome file>` (<component | process>) |
| Built | `<path to the solution or project folder>`: <projects, each with its type>; <n> files |
| Source export | `<path>` (<identity>) | none — live capture or placeholders |
| Built with | <skills, and the mandatory reads each performed> |
| Run it | `<the owning skill's run command for the entry point>` |

## Status
- Acceptance criteria: <n>/<total> met (§ Acceptance criteria).
<!--skill-flavor:report-gate:start-->
- Gate: validate + build per project (errors / warnings), libraries packed to <feed>, solution pack dry run <verdict>; runs performed or "compile only — no reachable application"
<!--skill-flavor:report-gate:end-->
- UI targets: <screens>/<elements> (<high/medium/low>), <created>/<reused>/<parametrised>; <n> verified, <n> shape-verified on <instance>, <n> offline-unverified; <n> live checks open (`live-checks/`); <n> placeholders.
- Tests: per test case, `Checkpoints: <source> / <asserted> / <not asserted: reasons> / <added>` (`parity/`).
- Test data and Data Fabric: <n> seed records, <variation files> filled from source rows, <n> credential assets declared; <entity, …> <created and loaded | created | open items> | none.
- Refactor: <the line of refactor-guide.md § Done> | not a refactor.
- Before the first run: <n> setup steps (`open-items.md`).

## Next steps
1. Set up the target environment: `open-items.md`, in order.
2. Check the UI targets on the live application and heal what fails: `live-checks/`, the read-only rows first, then the `run` rows on a test instance.
3. Expect the failures below on the first live run.

## Configuration answers
| Question | Answer |
|---|---|
| <the question in plain words> | <the answer>, "(default)" where no one answered |

## Acceptance criteria
| # | Criterion | Verdict | Where, or what is missing |
|---|---|---|---|

## Decisions
1. <What was decided>: <why>; <what it changed in the build>.

## Differences from the genome
| Step | Genome says | Build does | Why |
|---|---|---|---|

## Rulings still owed
- <The question the user has not answered>: <the default in place>; <what changes if the answer differs>.

## Expected failures on a live run
- <Step or criterion>: <what fails, and why>.

## Data the build's runs changed
- <System or store>: <what changed>; <how to undo it>.

## Files
| File | What it holds |
|---|---|
````

What each section holds:

1. **Decisions:** every choice the build made that the genome leaves open — the split per flow (`Flow <N> (<components>) — option <A|B|C> — <materialised projects and their roles, runners per project>; unit <item> (<the genome's | alternative: reason>); store <one queue per unit: <names> [+ record store: <entity or table>] | in-process | + kept coordination stores: <names>>; template <REFramework <queue|direct> | plain> per consumer project; coordination folded: <what became what>; exits exercised per consumer project: …; as-is was <one sentence>`), the libraries folded into a project, the lead agent's rulings, the user's rulings on source defects, the guards on settings ([configuration-questions-guide.md](configuration-questions-guide.md) rule 8) and the analyzer errors accepted. A ruling that changes what the genome says is offered as a genome edit.
2. **Differences from the genome:** the genome deviations the groups reported, each for a `uipath-planner` edit, with what the build followed ([source-migration-guide.md § Migration preflight](source-migration-guide.md) step 4).
3. **Expected failures on a live run:** the criteria Met (static) that the source's own data or defect fails on a live run (§ 3.1), the placeholder targets, and, as not built, the objects of the Source Map's `Not covered` row — building them is a `uipath-planner` edit (re-extraction), then a new build.
3a. **Rulings still owed:** the questions raised after the configuration answers that the user has not answered, each with the default in place and what changes if the answer differs.
4. **Data the build's runs changed:** each change a run made in a target system or a store, with how to undo it; nothing is undone unasked.
5. **Files:** every file of the folder with what it holds, and the working folder that stays with the build.

A section with nothing to hold reads "None.". The report does not claim results match the source; the parity tables make that comparison possible for whoever holds a source result.
