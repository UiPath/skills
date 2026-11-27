<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     To build it, invoke the uipath-genome skill: it asks the configuration questions,
     then invokes the skills referenced in Build With. Do NOT execute these steps directly, and do NOT
     start from a Build With skill. To change it, invoke the uipath-planner skill. -->

# Genome: ECB FX Rates

> Every weekday morning, sends finance the latest euro foreign exchange reference rates published by the European Central Bank for USD, GBP, CHF and RON, or a notice that they are missing.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Build it with the **uipath-genome** skill, which hands each part to the skill listed in **Build With** below.

## Overview

The finance team needs the European Central Bank's euro foreign exchange reference rates at the start of every working day. Every weekday at 07:00, the automation reads the latest set of reference rates the ECB has published. It keeps the rates for the US dollar, the pound sterling, the Swiss franc and the Romanian leu, and e-mails them to finance as a table.

The ECB publishes each working day's rates at about 16:00 CET, so the 07:00 run sends the most recent set: normally the previous ECB working day's. When that set has not appeared yet, the automation checks again every 30 minutes until 10:00. If the set is still not there, it e-mails finance that the rates are missing.

A time schedule starts the run on weekdays. No person takes part in the run: finance only receives the mail.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| European Central Bank euro foreign exchange reference rates | Input source | The ECB's public daily reference-rates file. Read over HTTPS with no sign-in. It holds one set: the set's date and one rate per currency, each the amount of that currency for one euro. |
| Microsoft Outlook 365 | Output target | Sends both mails from the sender mailbox through an Integration Service connection (Configuration Questions 4 and 5). |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| 1. Start on the weekday schedule | `uipath-maestro-flow` | A scheduled trigger starts the Flow. The whole run is HTTP and connector calls with in-run waits, and nothing needs a robot's machine, so a Flow holds it without occupying a robot for up to three hours. |
| 2. Work out the expected rates date | `uipath-maestro-flow` | A date calculation over a fixed calendar, done as a script step of the Flow. One consumer only, so it is not a separate function. |
| 3. Read the latest ECB rates | `uipath-maestro-flow` | One unauthenticated HTTP read of a public XML file. No catalog connector exists for it and it is not a REST+JSON API, so it is an HTTP step of the Flow. |
| 4. Check whether the expected set is published | `uipath-maestro-flow` | A decision plus a 30-minute delay in the Flow's own loop: a wait inside one run, not coordination between automations. |
| 5. Keep the four currencies | `uipath-maestro-flow` | A deterministic filter, done as a script step of the Flow. |
| 6. Send the rates e-mail | `uipath-maestro-flow` | Outlook 365 connector activity in the Flow, through an Integration Service connection. |
| 7. Send the missing-rates notice | `uipath-maestro-flow` | Same Outlook 365 connector activity, with a different message. |

## Platform Dependencies

### Connections

| Connection | Connector | Signs in as | Used by |
|------------|-----------|-------------|---------|
| FinanceRatesMail | Microsoft Outlook 365 (`uipath-microsoft-outlook365`) | the sender mailbox (Configuration Question 5) | steps 6, 7 |

### Triggers

| Trigger | Starts | Kind | When | Runners |
|---------|--------|------|------|---------|
| EcbFxRatesWeekday | this Flow | Time | Monday to Friday at 07:00 in the time zone of Configuration Question 1 (Configuration Question 2) | 1 |

## Interface

Runs unattended with no arguments; outputs are the side effects listed in Workflow.

## Configuration Questions

1. In which time zone are the 07:00 start and the 10:00 cut-off, and in which time zone is the run date counted? (setting; default: Europe/Berlin — the ECB's own time, CET/CEST)
2. When does the run start, how long does it wait between checks, and at what time does it stop checking and send the missing notice? (setting; default: weekdays at 07:00, every 30 minutes, last check at 10:00)
3. Who receives the rates e-mail and the missing notice? (setting; default: finance@contoso.com)
4. Which email provider sends the mails? (constant; default: Microsoft Outlook 365 through an Integration Service connection)
5. Which mailbox sends the mails, i.e. the account the connection signs in as? (setting; default: none)
6. Which currencies does finance receive, and in what order? (constant; default: USD, GBP, CHF, RON)
7. What is the address of the ECB's daily reference-rates file? (constant; default: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml)
8. What are the subject lines of the two mails? (constant; default: "ECB euro reference rates – {set date}" for the rates e-mail; "ECB euro reference rates missing – {expected date}" for the notice)

## Open Decisions

1. On a run day whose expected set is one finance has already been sent (the day or days after a TARGET closing day, e.g. Easter Monday and the Tuesday after it, 2 January, 2 May, 27 December), what does finance receive? (business outcome; answered by: the process owner; builds now: the same set again, with a line stating that the ECB has published no new rates since the set date; instead: no mail that day; instead: a short note only, saying that no new rates were published) — step 6, Send the rates e-mail
2. When the expected set is published but one of the four currencies is not in it, what does finance receive? (business outcome; answered by: the process owner; builds now: the table with that currency's row reading "not published by the ECB"; instead: treat the set as missing, keep checking until the cut-off, then send the missing notice) — step 5, Keep the four currencies
3. When the ECB file cannot be read at a check (the site does not answer, or the file has no set date), what does the run do? (run behaviour; answered by: the process owner; recommended: count that check as "not yet published" and check again at the next interval; at the cut-off, the missing notice says the file could not be read and gives the last error) — step 3, Read the latest ECB rates
4. When the rates e-mail or the missing notice cannot be sent, what does the run do? (run behaviour; answered by: the process owner; recommended: try the send twice more, one minute apart, then fail the run so it shows as faulted in Orchestrator; no other alert is sent) — steps 6 and 7

## Workflow

1. **Trigger**: the weekday schedule starts the run at 07:00 in the configured time zone (Configuration Questions 1 and 2). The run date is today's date in that time zone.
2. **Work out the expected rates date** (input: run date; output: expected set date, repeat flag):
   a. The expected set date is the latest TARGET working day before the run date. A TARGET working day is a Monday to Friday that is not a TARGET closing day. The TARGET closing days are 1 January, Good Friday, Easter Monday, 1 May, 25 December and 26 December; Good Friday and Easter Monday follow the Western (Gregorian) Easter date of the year.
   b. Also work out the expected set date for the previous weekday, applying item a to that day. When the two dates are the same, the set is one finance already received on that weekday: mark the run as a repeat (Open Decision 1).
   c. Example: run on Tuesday 2026-11-24 → expected 2026-11-23. Run on Monday 2026-11-23 → expected Friday 2026-11-20. Run on Monday 2027-03-29 (Easter Monday) → expected Thursday 2027-03-25, a repeat of Good Friday's run.
3. **Read the latest ECB rates** (input: the ECB file address, Configuration Question 7; output: set date, list of currency and rate):
   a. Download the ECB daily reference-rates file.
   b. Read the set's date and, for each currency in it, the currency's three-letter code and its rate, the amount of that currency for one euro. Keep each rate exactly as the ECB writes it, with no rounding and no change to its decimal places.
   c. If the file cannot be read, or holds no set date, count this check as "not yet published" and record the reason (Open Decision 3) *[Inferred: D3]*.
4. **Check whether the expected set is published** (input: set date, expected set date, current time; output: go to step 5 or step 7):
   a. If the set date is the expected set date or later, the rates are published: continue at step 5.
   b. Otherwise, if waiting 30 minutes from now still falls at or before the 10:00 cut-off, wait 30 minutes and return to step 3. With the defaults, the checks run at 07:00, 07:30, 08:00, 08:30, 09:00, 09:30 and 10:00.
   c. Otherwise, the set is missing: continue at step 7.
5. **Keep the four currencies** (input: list of currency and rate; output: rows of the rates table):
   a. Keep USD, GBP, CHF and RON (Configuration Question 6), in that order, and drop every other currency.
   b. If one of the four is not in the set, its row reads "not published by the ECB" in place of a rate *[Inferred: D2]*.
6. **Send the rates e-mail** (input: rates table rows, set date, repeat flag; output: one mail sent):
   a. Send one mail from the sender mailbox to the recipients (Configuration Questions 3 and 5), subject "ECB euro reference rates – {set date}" (Configuration Question 8), with the set date written as YYYY-MM-DD.
   b. The body opens with one line: "Euro foreign exchange reference rates published by the European Central Bank for {set date} (amount of each currency for 1 EUR)."
   c. Below that line, a table with two columns, "Currency" and "Rate per 1 EUR", and one row per currency from step 5, in order.
   d. Below the table, the line "Source: European Central Bank euro foreign exchange reference rates."
   e. If the run is a repeat (step 2b), add a line above the table: "The ECB has published no new reference rates since {set date} (TARGET closing day)." *[Inferred: D1]*
   f. The run ends.
7. **Send the missing-rates notice** (input: expected set date, last set date found, last read error, check times; output: one mail sent):
   a. Send one mail from the sender mailbox to the same recipients, subject "ECB euro reference rates missing – {expected date}" (Configuration Question 8).
   b. The body says: "The European Central Bank's euro reference rates for {expected date} were not published by {cut-off time} {time zone}. Checked at {check times}. The latest set available is dated {last set date}." When the file could not be read at the last check, it reads "The ECB file could not be read: {last error}." in place of the last sentence *[Inferred: D3]*.
   c. The run ends.

## Business Rules

### Step 2: Work out the expected rates date
- The ECB publishes reference rates only on TARGET working days. A weekday that is a TARGET closing day still gets a run, which expects the set of the TARGET working day before it.
- The run never expects the run date's own set: the ECB publishes it at about 16:00 CET, after the 10:00 cut-off.

### Step 4: Check whether the expected set is published
- If the set date is the expected set date or later, the rates count as published. Otherwise the run keeps checking until the cut-off.
- No check starts after the cut-off. The check at the cut-off is the last one.

### Step 5: Keep the four currencies
- Only USD, GBP, CHF and RON are reported, in that order. A rate is reported as published, with no rounding.

### General
- Each run day sends exactly one mail to finance: either the rates e-mail or the missing-rates notice, never both and never neither (Open Decision 1 may change the repeat-day mail).

## Error Handling

### Step 3: Read the latest ECB rates
- The ECB site does not answer, or the file holds no set date: the check counts as "not yet published", the reason is kept, and the run checks again at the next interval. At the cut-off, the missing notice gives the last reason *[Inferred: D3]*.

### Steps 6 and 7: Send the rates e-mail / Send the missing-rates notice
- The mail cannot be sent: the send is tried twice more, one minute apart. If it still fails, the run fails and shows as faulted in Orchestrator, naming the step *[Inferred: D4]*.

### Global
- Any other failure stops the run, which shows as faulted in Orchestrator with the failing step and its error. No mail is sent for it.

## Transactional Shape

Not transactional: the run is one unit of work.

## Acceptance Criteria

1. Given a run on Tuesday 2026-11-24 and an ECB file dated 2026-11-23, the automation sends at the 07:00 check one mail to finance@contoso.com, with subject "ECB euro reference rates – 2026-11-23" and a table of exactly four rows, USD, GBP, CHF and RON in that order, each rate equal to the ECB file's value character for character.
2. Given a run on Monday 2026-11-23, the expected set date is Friday 2026-11-20, and an ECB file dated 2026-11-20 produces the rates e-mail for 2026-11-20.
3. Given a run on Monday 2027-03-29 (Easter Monday), the expected set date is Thursday 2027-03-25. The rates e-mail for that set carries the line saying the ECB has published no new rates since 2027-03-25.
4. Given a run on Friday 2026-12-25 (a TARGET closing day), the run still takes place and expects the set dated Thursday 2026-12-24.
5. Given an ECB file dated earlier than the expected set date at 07:00 and a file dated the expected set date at 08:00, the automation checks at 07:00, 07:30 and 08:00, and sends the rates e-mail after the 08:00 check, with no missing notice.
6. Given an ECB file that stays dated earlier than the expected set date all morning, the automation checks at 07:00, 07:30, 08:00, 08:30, 09:00, 09:30 and 10:00, then sends one missing notice to finance. The notice names the expected date, the seven check times and the date of the latest set available, and no rates e-mail is sent.
7. Given the ECB site does not answer at any check, the missing notice sent after the 10:00 check says the ECB file could not be read and gives the last error.
8. Given the expected set is published without RON, the rates e-mail lists USD, GBP and CHF with their rates and a RON row reading "not published by the ECB".
9. Given the ECB file lists 30 currencies, the rates e-mail holds only the four configured currencies.
10. When the mail send fails three times, the run ends faulted in Orchestrator, and no second mail is sent for that day.
11. Given the trigger, no run starts on a Saturday or a Sunday.

## Complexity

medium

## Tags

finance, treasury, foreign-exchange, ECB, reference-rates, Microsoft Outlook 365, maestro-flow, scheduled-trigger, integration-service, http
