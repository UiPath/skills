<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     To build it, invoke the uipath-genome skill (Execute mode): it asks the configuration questions,
     then invokes the skills referenced in Build With. Do NOT execute these steps directly, and do NOT
     start from a Build With skill. -->

# Genome: Daily Sales Summary

> Every weekday evening, totals the day's regional sales files into one Excel summary and archives the files it read.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Build it with the **uipath-genome** skill, which hands each part to the skill listed in **Build With** below.

## Overview

The sales offices drop one CSV export per region into a shared input folder during the day. Each evening this automation reads every export in that folder, keeps the sales lines at or above a minimum amount, totals them per region, and writes a one-sheet Excel summary named after the business date into the output folder. It then moves every file it read into the archive folder so the next run starts from an empty input folder.

It runs unattended on an Orchestrator time trigger, needs no application with a user interface, and succeeds or fails as one run: either the whole summary is written and every file archived, or the run stops with nothing archived.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Shared file folders | Source and destination | Input, output and archive folders on the operations share |
| CSV files | Source data | One export per region, header row: Region, OrderId, Amount, Currency, OrderDate |
| Excel workbook | Output | Written as a file; no Excel installation is needed on the robot |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Steps 1-6: list, read, filter, total, write the workbook, archive | `uipath-rpa` | File and table work with no user interface — one RPA process, unattended |

## Platform Dependencies

| Resource | Type | Purpose |
|----------|------|---------|
| DailySales_InputFolder | Text asset | Folder the regional CSV exports are dropped into |
| DailySales_OutputFolder | Text asset | Folder the Excel summary is written to |
| DailySales_ArchiveFolder | Text asset | Folder the processed exports are moved to |
| DailySales-Evening | Time trigger | Starts the process every weekday at 19:00 |

## Interface

Runs unattended with no arguments; outputs are the side effects listed in Workflow.

## Configuration Questions

1. Which folder do the regional exports arrive in? (setting; default: the operations share's `Sales\Inbox` folder)
2. Which folder receives the Excel summary? (setting; default: the operations share's `Sales\Reports` folder)
3. Which folder do processed exports move to? (setting; default: the operations share's `Sales\Archive` folder)
4. Below which amount is a sales line left out of the totals? (constant; default: 10.00)
5. What is the summary sheet called? (constant; default: Summary)

## Workflow

1. **Start the evening run** (input: none; output: business date, folder locations): take today's date as the business date and read the input, output and archive folder locations.
2. **List the day's exports** (input: input folder; output: list of CSV files): list every file ending in `.csv` in the input folder. If there is none, write a one-line message to the job log saying no exports arrived and end the run without writing a summary.
3. **Read every export** (input: list of CSV files; output: one table of sales lines):
   a. Read each file as a table with its header row.
   b. Add every row to one combined table of sales lines, keeping Region, OrderId, Amount and Currency.
   c. A file whose header row lacks Region or Amount stops the run before anything is written (see Error Handling).
4. **Total the sales per region** (input: sales lines, minimum amount; output: one total per region and currency):
   a. Keep the lines whose Amount is at least the minimum amount.
   b. Group the kept lines by Region and Currency and add up their Amount.
   c. Count the kept lines per group.
5. **Write the summary workbook** (input: totals, business date, output folder, sheet name; output: the workbook file): write the totals to a new workbook named `Sales Summary <business date as yyyy-MM-dd>.xlsx` in the output folder, on the configured sheet, with the columns Region, Currency, Lines and Total, sorted by Region.
6. **Archive the exports** (input: list of CSV files, archive folder; output: none): move every file listed in step 2 into the archive folder, replacing a file of the same name already there.

## Business Rules

### Step 2: List the day's exports
- Only files ending in `.csv` count; any other file in the input folder is left where it is.

### Step 4: Total the sales per region
- If a line's Amount is less than the minimum amount, it is left out of the totals.
- A line whose Amount is empty or not a number is left out of the totals and counted in the job log.

### General
- The run is all or nothing: files are archived only after the summary workbook is written.

## Error Handling

### Step 3: Read every export
- A file without a Region or Amount column stops the run with a message naming the file; nothing is written and nothing is archived.

### Step 5: Write the summary workbook
- If the workbook cannot be written, the run stops before step 6, so every export stays in the input folder for the next run.

### Global
- Any other failure stops the run and leaves the input folder untouched.

## Transactional Shape

Not transactional: the run is one unit of work — it succeeds when the summary is written and every export archived, or fails as a whole.

## Acceptance Criteria

- [ ] Given two exports with lines for regions North and South, the summary has one row per region and currency with the line count and the total of the lines at or above the minimum amount.
- [ ] Given a line whose Amount is below the minimum amount, that line is left out of its region's total and line count.
- [ ] When the input folder holds no CSV file, the job log says no exports arrived and no workbook is written.
- [ ] When an export lacks its Amount column, the run stops with a message naming the file, and every export is still in the input folder.
- [ ] After a successful run, the workbook named for the business date is in the output folder and the input folder holds no CSV file.
- [ ] A file in the input folder that does not end in `.csv` is neither read nor moved.

## Complexity

simple

## Tags

sales, reporting, file-processing, excel, scheduled
