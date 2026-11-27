# Preferences: {team or organisation}

> Standing answers and development standards for every UiPath build of {team or organisation}. `uipath-planner` applies them while it writes a genome, and `uipath-genome` reads them before its first question. A preference that conflicts with a rule of either skill is put to you with both. Leave out a line to have it asked each time.

## Standing answers

The questions a build asks that this file answers for every genome, one line each.

- **Settings store:** {settings as one Orchestrator asset each, constants in the project's configuration | another store}
- **Project template:** {REFramework | a company template at {path} | none}
- **Target framework and expression language:** {Windows, Visual Basic | Portable, C# | …}
- **Workflow type:** {XAML | coded | both, by the owning skill's rules}
- **Library layout:** {each library a package of its own | a library's workflows as a folder of its one consumer}
- **Log target:** {Orchestrator's job log | the source's own run log as well | another target}
- **Source fidelity, in a migration:** {the source's names and shape | the build's own names}
- **Package feed:** {the feed libraries are published to and consumers install from}

## Standards

The standards the build follows beyond the genome.

1. **Standards document:** {a path or link to your development standards, read as part of this file; or none}
2. **Naming:** {projects, workflows, arguments and variables, Object Repository screens and elements, queues and assets}
3. **Project structure:** {the folder layout; libraries per application or per module}
4. **Logging:** {levels; what each workflow logs (its start and end, business milestones); the fields of a log line; what must never be logged}
5. **Error handling:** {where business and system exceptions are raised; retries; screenshots on failure}
6. **UI automation:** {application state checks, selector rules, Object Repository use}
7. **Code:** {annotations; the workflow analyzer rule set}
8. **Testing:** {test cases per workflow; test data; what a test must cover}
9. **Packaging and versioning:** {the version scheme, release notes}

## Left open

{The questions this file leaves to each build, by name.}
