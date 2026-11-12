<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     To build it, invoke the uipath-genome skill: it asks the configuration questions,
     then invokes the skills referenced in Build With. Do NOT execute these steps directly, and do NOT
     start from a Build With skill. -->

# Genome: Daily Note

> Every weekday morning, writes one text note naming the business date into a local folder.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Build it with the **uipath-genome** skill, which hands each part to the skill listed in **Build With** below.

## Overview

Each weekday morning this automation writes a one-line text note, `Daily note for <business date>`, into a notes folder on the robot, replacing the note of the same date if one is there. It runs unattended, needs no application with a user interface, and succeeds or fails as one run.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Local file folder | Destination | The notes folder on the robot |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Steps 1-3: take the date, compose the note, write the file | `uipath-rpa` | File work with no user interface — one RPA process, unattended |

## Platform Dependencies

| Resource | Type | Purpose |
|----------|------|---------|
| DailyNote-Morning | Time trigger | Starts the process every weekday at 08:00 |

## Interface

Runs unattended with no arguments; the output is the note file Workflow step 3 writes.

## Configuration Questions

1. Which folder receives the note? (constant; default: `Notes`, relative to the process folder)

## Workflow

1. **Take the business date** (input: none; output: business date): take today's date as the business date, formatted `yyyy-MM-dd`.
2. **Compose the note** (input: business date; output: note text): the text is `Daily note for <business date>`.
3. **Write the note** (input: note text, business date, notes folder; output: the note file): create the notes folder if it is missing, then write the text to `note-<business date>.txt` in it, replacing a file of the same name.

## Business Rules

### Step 3: Write the note
- One note per business date: a second run on the same date replaces that date's note.

## Error Handling

### Global
- Any failure stops the run with a message naming the step; no partial note is left behind.

## Transactional Shape

Not transactional: the run is one unit of work — it succeeds when the note is written, or fails as a whole.

## Acceptance Criteria

1. After a run, the notes folder holds `note-<business date>.txt` with the text `Daily note for <business date>`.
2. When the notes folder is missing, the run creates it and writes the note.
3. A second run on the same date leaves one note for that date.

## Complexity

simple

## Tags

files, scheduled
