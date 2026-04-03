<!-- UIPATH-AUTOMATION-GENOME: This file is a build specification for a UiPath automation project.
     Do NOT execute these steps directly. Use the UiPath skills referenced in Build With to create
     the automation project. -->

# Genome: AccuWeather Slack Notification

> Scrape today's weather data for Bucharest from AccuWeather and send it as a Slack message to Dan Munteanu using UI Automation.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Use the skills listed in **Build With** below to create a UiPath automation project that implements this workflow.

## Overview

This automation opens a browser to AccuWeather, navigates to the Bucharest weather page, extracts today's weather data (temperature, conditions, humidity, wind), then switches to the Slack desktop application and sends a formatted message containing that weather data to Dan Munteanu. Both interactions use UI Automation — browser automation for AccuWeather and desktop app automation for Slack.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| AccuWeather (https://www.accuweather.com/) | Data source | Browser-based weather data extraction for Bucharest |
| Slack (desktop app) | Message delivery | UI Automation to send a direct message to Dan Munteanu |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Steps 1-3: Navigate to AccuWeather and extract weather data | `uipath-rpa-workflows` | Browser UI Automation to navigate and scrape structured weather data |
| Steps 4-6: Send Slack message via desktop app | `uipath-rpa-workflows` | Desktop UI Automation to interact with Slack app, find the recipient, and send the message |

## Configuration Questions

Description covers the scope — no additional configuration needed.

## Workflow

1. **Open browser and navigate to AccuWeather Bucharest**
   - Open a browser (or attach to an existing one) and navigate to `https://www.accuweather.com/`
   - Search for "Bucharest" in the AccuWeather search bar and select the Bucharest, Romania result
   - Wait for the current weather page to fully load

2. **Extract today's weather data**
   - Extract the current temperature (°C)
   - Extract the weather condition text (e.g., "Partly Cloudy", "Sunny")
   - Extract the RealFeel® temperature
   - Extract wind speed and direction
   - Extract humidity percentage
   - Store all extracted values in variables for message composition

3. **Compose the weather message**
   - Format the extracted data into a readable message, e.g.:
     ```
     Weather in Bucharest today:
     Temperature: 18°C (RealFeel® 16°C)
     Conditions: Partly Cloudy
     Wind: 15 km/h NW
     Humidity: 62%
     ```

4. **Open Slack and navigate to Dan Munteanu's conversation**
   - Switch to or open the Slack desktop application
   - Use the search or direct message functionality to find Dan Munteanu
   - Open the direct message conversation with Dan Munteanu

5. **Send the weather message**
   - Click the message input field
   - Type or paste the formatted weather message
   - Press Enter or click Send to deliver the message

6. **Confirm delivery**
   - Verify the message appears in the conversation thread
   - Close or minimize the browser if it was opened by the automation

## Business Rules

No explicit business rules — agent applies standard validation patterns.

## Error Handling

Standard error handling — retry on transient failures, log and skip on permanent errors.

## Acceptance Criteria

- [ ] Given the AccuWeather Bucharest page loads, the automation extracts the current temperature as a numeric value with unit (e.g., "18°C")
- [ ] Given the AccuWeather Bucharest page loads, the automation extracts the weather condition text (e.g., "Partly Cloudy")
- [ ] Given extracted weather data, the automation composes a message containing temperature, conditions, RealFeel®, wind, and humidity
- [ ] Given the Slack desktop app is running, the automation navigates to Dan Munteanu's direct message conversation
- [ ] Given a composed weather message and an open DM conversation, the automation sends the message and it appears in the chat thread

## Complexity

Simple

## Tags

weather, accuweather, slack, ui-automation, notification, web-scraping
