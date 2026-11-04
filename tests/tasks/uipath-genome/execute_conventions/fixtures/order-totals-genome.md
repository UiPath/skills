<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     To build it, invoke the uipath-genome skill (Execute mode): it asks the configuration questions,
     then invokes the skills referenced in Build With. Do NOT execute these steps directly, and do NOT
     start from a Build With skill. -->

# Genome: Order Totals

> Totals the day's order export and writes a one-line summary file for the finance team.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Build it with the **uipath-genome** skill, which hands each part to the skill listed in **Build With** below.

## Overview

Reads the day's order export, a CSV file with one order per row, adds up the order amounts and writes a summary text file with the order count and the total. Finance reads the summary each morning. It runs unattended once a day with no input and touches no user interface.

## Target Applications

No user interface: the run reads and writes files only.

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Steps 1–3 | `uipath-rpa` | File reading, a sum and a file write in one unattended project |

## Platform Dependencies

No Orchestrator or Integration Service resources required.

## Interface

Runs unattended with no arguments; outputs are the side effects listed in Workflow.

## Configuration Questions

1. Which folder holds the day's order export? (setting; default: `C:\Orders\Inbox`)
2. Where is the summary file written? (setting; default: `C:\Reports`)
3. Which folder are processed exports moved to? (setting; not in the export — left empty)

## Workflow

1. **Read the export** — read `orders.csv` from the folder in Configuration Question 1, with a header row, columns `OrderId`, `Amount`.
2. **Total the orders** — add up `Amount` over the rows and count them. **Source defect:** the loop stops one row early: its bound is the row count minus one, so the last order is never added or counted. Evident intent: total every row — the step's log text reads `Totalled all {count} orders`.
3. **Write the summary and archive** — write `summary.txt` (`Orders: {count}; Total: {total}`) to the folder in Configuration Question 2, then move `orders.csv` into the folder in Configuration Question 3; an empty archive folder moves the file to the drive root.

## Business Rules

None beyond the steps.

## Error Handling

### Global

A missing export fails the run with the source's message `Order export not found`.

## Transactional Shape

Not transactional: one file per run, read and summed once.

## Acceptance Criteria

1. Given an export of three orders of 10, 20 and 30, `summary.txt` reads `Orders: 3; Total: 60`.
2. After the run, `orders.csv` is in the archive folder and no longer in the inbox.
3. A missing export ends the job faulted with `Order export not found`.

## Complexity

simple

## Tags

finance, csv, file-processing

## Source Map

| Row | Source artifact | Notes |
|-----|-----------------|-------|
| Source framework | Acme Workflow Engine 4.2 | Scheduled job definition |
| Source export | `./export/order-totals` — job `OrderTotals` 1.3 | Not present on this machine |
| Inventory | 1 job, 3 steps, 1 script step (the total loop), 1 log line | — |
| Not covered | none | — |
| Inferred | none | — |
| Verification | the total loop script | Defect at step 2 confirmed in the script source |

### Steps

| Step | Source objects | Data sets | Captures | Notes |
|------|----------------|-----------|----------|-------|
| 1 | `ReadOrders` (s1) | none | 0 | — |
| 2 | `TotalLoop` (s2) | none | 0 | loop bound `rows.length - 1` |
| 3 | `WriteSummary` (s3) | none | 0 | — |
