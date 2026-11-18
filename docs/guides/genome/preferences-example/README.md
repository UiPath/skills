# Build preferences: an example

A preferences file holds the answers you give every build the same way and the rules of your own practice: naming, project layout, which activities to use, how to configure and log, and what the hand-off looks like. It expands step 3 of [Working with UiPath genomes](../working-with-uipath-genome.md#3--build). Name it in the build request:

> Build `<name>-genome.md` with the preferences in `migration-preferences.md`.

The build reads it as your answers file:

- A question it answers is not asked; the completion report records the answer as "(from the answers file)".
- A rule it states that no question asks is recorded the same way, and every part of the build follows it.
- A rule that conflicts with a rule of the skill comes back to you as a question, with both statements. The build never settles it on its own.

## The example

- [migration-preferences.md](migration-preferences.md): preferences for migrating existing automations to UiPath.
- [handoff-template/](handoff-template/README.md): the HTML hand-off page that § 8 of the preferences asks for. It is a standalone sample with placeholder data, plus how a build fills it.

Copy both, then change what does not fit your practice.
