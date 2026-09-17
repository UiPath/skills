<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     Do NOT execute these steps directly. Use the UiPath skills referenced in Build With to create
     the automation project. -->

# Genome: Artemis 2 Mission Monitor

> Polls NASA data sources every few minutes during the live Artemis 2 mission and sends email alerts on milestone transitions, status changes, and anomalies.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Use the skills listed in **Build With** below to create a UiPath automation project that implements this workflow.

## Overview

This automation monitors the live Artemis 2 mission by polling NASA's public APIs and status feeds at short intervals, detecting when the mission transitions between key milestones (trans-lunar injection, lunar flyby, return trajectory, reentry, splashdown) or when anomalies and schedule changes are reported. When a change is detected, it composes a concise status email and sends it to a configured recipient list.

The automation maintains a lightweight state file tracking the last known mission phase and timestamp so it can distinguish new events from already-reported ones. It runs unattended on an Orchestrator time trigger every 3-5 minutes for the duration of the active mission.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| NASA Open APIs / Spaceflight News API | Data source | Public REST APIs for mission status, events, and news articles |
| NASA Artemis mission status page | Fallback data source | Web scrape fallback when API data lags behind the official page |
| SMTP / Email service | Notification channel | Sends alert emails on milestone changes and anomalies |
| Local JSON state file | State persistence | Last known milestone, last poll timestamp, reported event IDs |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Steps 2, 3, 5-10: load state, poll APIs, detect changes, compose and send email, update state, log | `uipath-rpa` | Pure REST calls, JSON parsing, and file I/O — coded (C#) workflows inside the RPA project, no UI |
| Step 4: scrape NASA mission status page (fallback) | `uipath-rpa` | Browser UI automation with selectors — a XAML workflow in the same project, invoked from the coded entry point |

## Platform Dependencies

| Resource | Type | Purpose |
|----------|------|---------|
| ArtemisMonitor-Schedule | Time trigger | Fires the process every 3 minutes |
| SMTP credentials | Credential asset | Authenticates the outgoing mail server when a custom SMTP server is configured |

## Interface

- **Inputs:** none (unattended, scheduled); reads the local state file
- **Outputs:** alert emails to the configured recipients; updated state file; one summary log line per run
- **Side effects:** files written under `unsent/` when email delivery fails

## Configuration Questions

1. Which email address(es) should receive mission alerts? (default: none — must be provided)
2. Which mail server sends the alerts? (default: Orchestrator's mail configuration; alternative: custom SMTP host with credential asset)
3. How far back should the first poll look for events, to avoid flooding the inbox on first run? (default: 1 hour)
4. Should the state file persist across Orchestrator restarts? (default: yes — avoids duplicate notifications)
5. Which email format? (default: HTML with mission phase icons; alternative: plain text)

## Workflow

1. **Trigger**: Orchestrator time trigger fires every 3 minutes.
2. **Load state** (input: state file; output: last phase, last poll timestamp, reported event IDs): read the local JSON state file. If it does not exist (first run), initialize defaults and set the last poll timestamp to the configured lookback (default 1 hour ago).
3. **Poll NASA APIs** (input: last poll timestamp; output: current phase, list of events with ID, description, timestamp):
   a. Query the Spaceflight News API articles and events filtered to "Artemis II" and newer than the last poll timestamp
   b. Query the NASA Open API for Artemis-related updates
   c. Collect mission phase, event descriptions, and timestamps from both responses
4. **Fallback scrape** (conditional; input: age of last successful API result; output: scraped phase text): if both APIs returned no new data and the last successful API result is older than 15 minutes, open the NASA Artemis mission status page and read the current phase text. Guards against API lag during critical moments.
5. **Detect changes** (input: current phase and events, stored phase; output: change type):
   a. **Milestone transition** — phase differs from the stored phase
   b. **Status update** — new event or article while the phase is unchanged
   c. **Anomaly/delay** — any event text contains an anomaly keyword (see Business Rules)
6. **Filter duplicates**: drop events whose IDs already appear in the reported-events list.
7. **Compose email** (input: change type, phase, events; output: subject and body): subject names the change type and current phase; body carries the timestamp, change summary, and a link to NASA's live mission page. Milestone transitions include the previous and new phase names.
8. **Send email**: deliver to the configured recipient list via the configured mail server.
9. **Update state**: write the new phase, current timestamp, and newly reported event IDs to the state file.
10. **Log**: write one summary line to the job log (phase, change type, email sent yes/no).

## Business Rules

### Step 5: Detect changes
- Milestone phases are ordered: Launch → Trans-Lunar Injection → Outbound Coast → Lunar Flyby → Return Coast → Reentry → Splashdown → Recovery. A transition is valid only when the new phase is later in the sequence, or is an anomaly override.
- Anomaly keywords trigger a notification regardless of phase change: "anomaly", "delay", "hold", "abort", "contingency", "scrub", "off-nominal".
- A detected phase outside the known sequence is reported as an anomaly with the raw phase text.

### Step 4: Fallback scrape
- Activates only after 15+ minutes without new API data. If the scraped phase equals the stored phase, no action is taken.

### Step 6: Filter duplicates
- A reported event ID is never re-sent. The reported-events list is capped at 500 entries, oldest evicted first.

### Step 8: Send email
- At most one email per 5-minute window, except anomaly alerts, which bypass the rate limit.

## Error Handling

### Step 3: Poll NASA APIs
- Non-200 status or 30-second timeout: log the error and continue to the next data source. If every source fails, log a warning and exit without sending. No in-run retry — the next scheduled run is the retry.

### Step 4: Fallback scrape
- Element not found or page structure changed: log the error with the failing target and continue without scrape data.

### Step 2: Load state
- State file is not valid JSON: rename it to `state-corrupt-{timestamp}.json`, initialize a fresh state, log a warning. The next poll treats current events as new (one-time duplicate notification accepted).

### Step 8: Send email
- Delivery failure: log recipient, subject, and error; write the unsent body to the `unsent/` folder. Mark the event IDs as reported anyway so the next run does not retry.

## Acceptance Criteria

- [ ] Given the Spaceflight News API returns a new Artemis II event not present in the state file, the automation sends an email containing the event description and timestamp to the configured recipients.
- [ ] Given the mission phase changes from "Trans-Lunar Injection" to "Lunar Flyby" between two consecutive polls, the email subject includes "Milestone: Lunar Flyby" and the body shows the phase transition.
- [ ] Given an event description containing "anomaly", the automation sends an email immediately regardless of the 5-minute rate limit.
- [ ] Given both APIs return no new data for 15+ minutes, the automation reads the NASA mission status page and uses the scraped phase for change detection.
- [ ] Given no state file exists, the automation initializes state and polls events from the configured lookback without crashing.
- [ ] Given a state file with invalid JSON, the automation renames it, initializes fresh state, and logs a warning.
- [ ] Given an event ID reported in a previous run, no duplicate email is sent for that event.
- [ ] Given the mail server rejects the email, the automation writes the unsent body to `unsent/` and logs the failure details.
- [ ] Given an API returns HTTP 500, the automation logs the error and continues to the next data source without failing the job.

## Complexity

medium

## Tags

nasa, artemis, space, mission-monitoring, email-alerts, api-polling, scheduled, notifications
