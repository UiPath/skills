# Preferences file: an example

A preferences file holds your team's standing answers and development standards: naming, project structure, which activities to use, logging, error handling, what the hand-off looks like. Its shape is the planner's `preferences-template.md`: standing answers, one line per build question it answers; standards, the rules every build follows beyond the genome; and the questions it leaves open. More in [Working with UiPath genomes](../working-with-uipath-genome.md#before-you-start).

Give it once. `uipath-planner` asks for it when it writes or extracts a genome, applies it there and names it on the genome's `Preferences:` line; `uipath-genome` reads it before its first question:

- A question it answers is not asked; the completion report records the answer as "(from the answers file)".
- A standard it states is followed by every part of the build.
- A preference that conflicts with a rule of either skill comes back to you as a question, with both statements.

## The example

- [migration-preferences.md](migration-preferences.md): preferences for migrating existing automations to UiPath.
- [handoff-template/](handoff-template/README.md): the HTML hand-off page its Standards 8 asks for. It is a standalone sample with placeholder data, plus how a build fills it.

Copy both, then change what does not fit your practice.
