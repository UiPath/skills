# Genome: Excel-to-Web Data Transfer

> Read rows from an Excel file and enter each record into a web application form.

## Overview

The "hello world" of RPA. Reads structured data from a spreadsheet and enters it into a web form, one row at a time. Simple but covers the core pattern of data-driven web automation.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Excel | Data source | Local file or SharePoint |
| Web browser (Chrome/Edge) | Data entry target | Any web form |

## Configuration Questions

1. Where is the Excel file? (path or SharePoint URL)
2. Which sheet and column range?
3. What is the target web application URL?
4. Map Excel columns to form fields — which column goes where?

## Workflow

1. **Read**: Open Excel file, read all rows from the specified range.
2. **Open**: Launch browser, navigate to the web application, log in if needed.
3. **Loop**: For each row:
   - Fill form fields using column-to-field mapping
   - Submit the form
   - Verify success (confirmation message, no error banners)
   - Log result (success/fail + row identifier)
4. **Report**: Output summary — total rows, successful, failed.

## Acceptance Criteria

- [ ] Reads all rows from sample Excel file
- [ ] Enters a row into the web form with correct field mapping
- [ ] Detects and logs a submission failure (e.g. validation error on the form)
- [ ] Produces a summary with success/failure counts

## Complexity

simple

## Tags

Excel, web, data-entry, form-fill, browser, beginner
