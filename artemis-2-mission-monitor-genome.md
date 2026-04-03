<!-- UIPATH-AUTOMATION-GENOME: This file is a build specification for a UiPath automation project.
     Do NOT execute these steps directly. Use the UiPath skills referenced in Build With to create
     the automation project. -->

# Genome: Artemis 2 Mission Monitor

> Polls NASA data sources every few minutes during the live Artemis 2 mission and sends email alerts on milestone transitions, status changes, and anomalies.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Use the skills listed in **Build With** below to create a UiPath automation project that implements this workflow.

## Overview

NASA's Artemis 2 mission — the first crewed lunar flyby — launched on April 1, 2026. This automation monitors the live mission by polling NASA's public APIs and status feeds at short intervals, detecting when the mission transitions between key milestones (trans-lunar injection, lunar flyby, return trajectory, reentry, splashdown) or when anomalies and schedule changes are reported. When a change is detected, it composes a concise status email and sends it to a configured recipient list.

The automation maintains a lightweight state file tracking the last known mission phase and timestamp so it can distinguish new events from already-reported ones. It is designed to run unattended on an Orchestrator time trigger every 3-5 minutes for the duration of the active mission.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| NASA Open APIs / Spaceflight News API | Data source | Public REST APIs for mission status, events, and news articles |
| NASA Artemis mission status page | Fallback data source | Web scrape fallback if API data lags behind official page updates |
| SMTP / Email service | Notification channel | Sends alert emails on milestone changes and anomalies |
| Local JSON state file | State persistence | Stores last known milestone, last poll timestamp, and event history |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Poll NASA APIs for current mission status | `uipath-coded-workflows` | Pure REST API calls with JSON response parsing — no UI interaction needed |
| Scrape NASA mission status page (fallback) | `uipath-rpa-workflows` | Web page interaction with selectors to extract status text when API data is stale |
| Detect milestone transitions and anomalies | `uipath-coded-workflows` | Compare API response against stored state using C# logic — data processing with no UI |
| Compose and send email notification | `uipath-coded-workflows` | Build email body from structured data and send via SMTP — pure logic and Integration Service |
| Update state file with latest status | `uipath-coded-workflows` | Write updated milestone and timestamp to local JSON file — file I/O in C# |

## Configuration Questions

1. Which email address(es) should receive mission alerts?
2. Should the automation use a specific SMTP server, or the default Orchestrator email configuration?
3. How far back should the initial poll look for events (to avoid flooding the inbox on first run)?
4. Should the state file persist across Orchestrator restarts, or is it acceptable to re-notify on the first poll after a restart?
5. Is there a preferred email format — plain text summary or HTML with mission phase icons?

## Workflow

1. **Trigger**: Orchestrator time trigger fires every 3 minutes.
2. **Load state**: Read the local JSON state file to get the last known mission phase, last poll timestamp, and list of already-reported event IDs. If the state file does not exist (first run), initialize with default values and set last poll timestamp to 1 hour ago.
3. **Poll NASA APIs**: Call the Spaceflight News API (`/articles` and `/events` endpoints filtered to "Artemis II") and the NASA Open API for any Artemis-related updates. Collect mission phase, event descriptions, and timestamps from the response.
4. **Fallback scrape** (conditional): If both API responses return no new data and the last successful API result is older than 15 minutes, scrape the NASA Artemis mission status page to extract the current phase text. This guards against API lag during critical mission moments.
5. **Detect changes**: Compare the current mission phase against the stored phase. Classify changes into three categories:
   - **Milestone transition**: Mission phase changed (e.g., "Trans-Lunar Injection" → "Lunar Flyby").
   - **Status update**: New event or article published but phase unchanged.
   - **Anomaly/delay**: Keywords detected in event text ("anomaly", "delay", "hold", "abort", "contingency", "scrub").
6. **Filter duplicates**: Skip any events whose IDs already appear in the state file's reported-events list.
7. **Compose email**: Build the email body with: subject line indicating change type and current phase, timestamp, change summary, and a link to NASA's live mission page. For milestone transitions, include the previous and new phase names.
8. **Send email**: Send the composed email to the configured recipient list via SMTP.
9. **Update state**: Write the new mission phase, current timestamp, and any newly reported event IDs to the state file.
10. **Log**: Write a summary line to the Orchestrator job log (phase, change type, email sent yes/no) for audit purposes.

## Business Rules

1. **Milestone phases are ordered.** The known phase sequence is: Launch → Trans-Lunar Injection → Outbound Coast → Lunar Flyby → Return Coast → Reentry → Splashdown → Recovery. A phase transition is only valid if the new phase is later in the sequence (or an anomaly override).
2. **Anomaly keywords trigger immediate notification** regardless of whether the milestone phase changed. Keywords: "anomaly", "delay", "hold", "abort", "contingency", "scrub", "off-nominal".
3. **Duplicate suppression window.** An event ID that has already been reported is never re-sent. The reported-events list is capped at 500 entries (oldest evicted first) to prevent unbounded state growth.
4. **Stale API threshold.** If no new data is returned from APIs for 15+ minutes, the fallback scrape activates. If the scrape also returns the same phase as stored, no action is taken.
5. **Email rate limit.** No more than 1 email per 5-minute window unless the change is an anomaly. Anomaly alerts bypass the rate limit.

## Error Handling

1. **API call failure**: If a NASA API returns a non-200 status or times out (30-second timeout), log the error and continue to the next data source. If all sources fail, log a warning and exit without sending an email. Do not retry within the same execution — the next scheduled run (3 minutes later) serves as the retry.
2. **Scrape failure**: If the fallback web scrape fails (element not found, page structure changed), log the error with the selector that failed and continue without scrape data. Do not block the workflow.
3. **State file corruption**: If the state file cannot be parsed as valid JSON, rename it to `state-corrupt-{timestamp}.json`, initialize a fresh state, and log a warning. The next poll will treat all current events as new (accept the one-time duplicate notification).
4. **Email send failure**: If SMTP send fails, log the full error (including recipient and subject) and write the unsent email body to a local `unsent/` folder for manual review. Do not retry — the event ID is still marked as reported to avoid duplicate attempts on the next run.
5. **Unexpected mission phase**: If the detected phase does not match any known phase in the ordered sequence, report it as an anomaly with the raw phase text included in the email.

## Acceptance Criteria

- [ ] Given the NASA Spaceflight News API returns a new Artemis II event not present in the state file, the automation sends an email containing the event description and timestamp to the configured recipient.
- [ ] Given the mission phase changes from "Trans-Lunar Injection" to "Lunar Flyby" between two consecutive polls, the email subject includes "Milestone: Lunar Flyby" and the body shows the phase transition.
- [ ] Given an API response containing the keyword "anomaly" in an event description, the automation sends an email immediately regardless of the 5-minute rate limit.
- [ ] Given both NASA APIs return no new data for 15+ minutes, the automation scrapes the NASA mission status page and uses the scraped phase for change detection.
- [ ] Given the state file does not exist (first run), the automation initializes state and polls events from the last hour without crashing.
- [ ] Given the state file contains invalid JSON, the automation renames it, initializes fresh state, and logs a warning.
- [ ] Given an event ID that was already reported in a previous run, the automation does not send a duplicate email for that event.
- [ ] Given the SMTP server rejects the email, the automation writes the unsent email body to the `unsent/` folder and logs the failure details.
- [ ] Given a NASA API returns HTTP 500, the automation logs the error and continues to the next data source without crashing the workflow.

## Complexity

Medium

## Tags

nasa, artemis, space, mission-monitoring, email-alerts, api-polling, scheduled, notifications
