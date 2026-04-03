<!-- UIPATH-AUTOMATION-GENOME: This file is a build specification for a UiPath automation project.
     Do NOT execute these steps directly. Use the UiPath skills referenced in Build With to create
     the automation project. -->

# Genome: Web Form Data Entry from Excel

> Reads records from an Excel spreadsheet and fills out a web form for each record, submitting them one at a time and capturing the final result.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Use the skills listed in **Build With** below to create a UiPath automation project that implements this workflow.

## Overview

This automation reads structured data from an Excel spreadsheet and enters each record into a web-based form. For every row in the spreadsheet, the automation populates all form fields (first name, last name, company name, role, address, email, and phone number), submits the form, and moves to the next record. After all records have been submitted, it captures the confirmation message or score displayed by the website and returns it as an output.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Excel | Data source | Spreadsheet containing the records to be entered into the web form |
| Web browser (Chrome) | UI interaction | Navigates to the target website and fills out the form fields |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Read records from Excel | `uipath-rpa-workflows` | Excel reading via workbook activities |
| Open website, fill forms, submit, capture result | `uipath-rpa-workflows` | Browser UI interaction with typing, clicking, and reading elements |

## Configuration Questions

Description covers the scope -- no additional configuration needed.

## Workflow

1. **Read input data from Excel spreadsheet** (input: file path to spreadsheet; output: table of records with columns First Name, Last Name, Company Name, Role in Company, Address, Email, Phone Number):
   a. Open the configured Excel file
   b. Read all rows from the first sheet, treating the first row as column headers
   c. Log the total number of records loaded

2. **Open the target website in a browser**:
   a. Navigate to the target web form URL (source project used: `https://rpachallenge.com`)
   b. If the browser is already open to the correct page, attach to the existing session rather than opening a new one

3. **Start the challenge**:
   a. Click the "Start" button on the page to begin the timed form-filling session

4. **Fill and submit the form for each record** (input: one row of data; output: submitted form):
   a. For each record in the data table, populate the following form fields from the corresponding columns:
      - First Name
      - Last Name
      - Company Name
      - Role in Company
      - Address
      - Email
      - Phone Number
   b. Click the "Submit" button to submit the completed form
   c. Log progress (current row number out of total)
   d. Repeat for every record in the data table

5. **Capture the final result** (output: score/confirmation text):
   a. After all records have been submitted, read the confirmation message displayed on the page
   b. Return the captured result text as the automation output

## Business Rules

No explicit business rules -- agent applies standard validation patterns.

## Error Handling

Standard error handling -- retry on transient failures, log and skip on permanent errors.

## Acceptance Criteria

- [ ] Given an Excel file with multiple records, all records are entered into the web form and submitted successfully
- [ ] Given a record with values for all seven fields (first name, last name, company name, role, address, email, phone number), each field is populated in the correct form input before submission
- [ ] Given all records have been submitted, the confirmation message or score is captured and returned as output
- [ ] Given an empty Excel file (headers only, no data rows), the automation completes without error and returns whatever result the website displays

## Complexity

simple

## Tags

web-automation, excel, form-filling, browser, data-entry
