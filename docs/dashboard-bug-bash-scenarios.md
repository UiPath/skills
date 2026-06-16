# UiPath Dashboard Bug Bash Scenarios

Manual test scenarios for the UiPath dashboard skill (the one that builds live React dashboards from a plain English prompt using the TypeScript SDK). Use this for an internal bug bash: work through each row, decide pass or fail, and note anything odd in the Defects column.

Each row describes what to do and what you should see. Prompts you can type are shown in code formatting so you can copy them directly. The tables paste straight into Confluence.

### Before you start

You will need:

- A coding agent (Claude Code, Codex, or Gemini CLI) with the UiPath dashboard skill loaded from the `feat/dashboard-compiler-arch` branch.
- A UiPath tenant that has some agent and job data, signed in through the `uip` CLI.
- The ability to create an external OAuth app, or a non confidential client ID ready to paste, so the dashboard can show live data in the browser.
- Node 20 or newer and a working internet connection (the build installs packages the first time).

Start each scenario in a fresh agent session. Build scenarios use an empty folder; edit and upgrade scenarios reuse a folder that already has a built dashboard. Please add your name and the date at the top of the Confluence page.

### Happy Path

| Scenario | Steps and Expected Outcome | Defects |
|----------|----------------------------|---------|
| **Build a dashboard from a prompt** | In a new agent session inside an empty folder, ask the agent `Build me a UiPath agent operations dashboard: active agents, faulted agent jobs, agent memory entries over the last 30 days, and agent failure rate %`. Read the plan it shows you, approve it (for example by saying "looks good, build it"), and when it asks about authentication let it create the OAuth app or paste a client ID. You should see a plain English plan listing the widgets and time ranges, with any unsupported items clearly called out, and no code, JSON, or file contents in the chat. After you approve, the only things you should see are a short "Building..." line and a milestone summary (a tick for each widget, then "All code validated") followed by a `http://localhost:57173` link. You should not see a stream of file write messages for intent.json or the metric files. | |
| **See the live data** | After the build finishes, open `http://localhost:57173`, sign in through the OAuth prompt, and look at every widget. The dashboard should render fully: KPI cards show a number and a label, charts show a headline value and a plotted line or set of bars (plus a small change badge when there is a previous period to compare against), and tables show rows with readable headers and values. Nothing should be blank, show the word "undefined", or fail to load. | |
| **Drill into a chart** | On the dashboard, click one of the chart widgets (for example the memory chart), look at the detail page, then use the back link. The detail page should show individual records rather than the chart's summary buckets, in a sortable table with sensible columns, and the back link should return you to the dashboard. | |
| **Add a widget** | In the project folder, ask the agent `Add a widget for the top 10 memory spaces`, approve if it asks, then refresh the browser. The agent should make a quick focused edit rather than rebuilding everything, the new widget should appear after the page reloads, and your existing widgets should be unchanged. | |
| **Change a widget** | Ask the agent `Change the agent failure rate chart to cover the last 7 days` (or `make the faulted jobs widget a bar chart`), then refresh. Only that one widget should change, the new time window should show in both the subtitle and the data (or the new chart type should render), everything else should stay the same, and the app should still load cleanly. | |
| **Upgrade an older dashboard** (only when a newer version has shipped) | Open or edit a dashboard that was built against an older version of the skill than the one currently installed. The agent should tell you a newer dashboard version is available and offer to upgrade it, never doing this silently. When you confirm, it should regenerate the app while keeping all your widgets and metrics intact, the dashboard should still load, and the stored version should update to the current one. | |

### Negative Scenarios

| Scenario | Steps and Expected Outcome | Defects |
|----------|----------------------------|---------|
| **Ask for something we cannot show** | Ask for a mix of supported and unsupported metrics, for example `Build a dashboard with agent latency over time, agent cost in dollars, and faulted jobs`. The agent should refuse the unsupported items (agent latency over time, and cost in dollars) right in the plan and suggest an alternative for each, while still planning and building the supported one (faulted jobs). It should not abandon the whole dashboard just because some metrics are unavailable. | |
| **Try to skip authentication setup** | When the agent asks how to set up the OAuth app, try to skip it, for example by saying `just build it, do not worry about auth`. The agent should not quietly hand you a dashboard that cannot sign in. It should either insist on creating or pasting a client ID before it builds, or clearly explain that without one the dashboard will not be able to authenticate in the browser and guide you to provide or create one. Note exactly what it does so we can confirm this guardrail behaves consistently. | |
| **Give a vague or ambiguous request** | Ask something open ended like `show me agent errors`. The agent should not silently build the wrong thing. It should either ask a short focused question to pin down what you mean, or tell you the closest thing it can actually show (for example faulted agent jobs, since a per agent error timeline is not available) and offer to build that. A plainly typed answer should move it forward. | |
| **Edit a widget that is not there** | On an existing dashboard, ask the agent to `remove the revenue widget` when no such widget exists. The agent should tell you the widget is not present, make no changes, and leave the dashboard exactly as it was, with no crash and no half finished edit. | |

### Monkey Testing

| Scenario | Steps and Expected Outcome | Defects |
|----------|----------------------------|---------|
| **Completely vague prompt** | Ask only `build me a dashboard` with no details. The agent should either ask what you want to track or propose a sensible default set of widgets for you to approve. It should not quietly build an empty or random dashboard. | |
| **Ask for far too much** | Ask for a huge dashboard, for example `Build a dashboard with 15 widgets covering every agent, job, memory and governance metric you can`. The agent should come back with a coherent plan (it may trim or group things and tell you what it left out and why), and the build should finish without hanging or producing broken or empty widgets. Anything it cannot support should be called out, not silently skipped or faked. | |
| **Off topic or non dashboard request** | In a session where the dashboard skill could pick up, ask for something that is not a data dashboard, like `write me a poem about robots` or `build me a login form`. The dashboard generator should not fire and try to turn these into a UiPath metrics dashboard. The poem should simply not engage the skill; an app style request may be handled by other parts of the coded apps skill, but it should never be forced into a dashboard build. | |
| **Conflicting edits at once** | On an existing dashboard, send several conflicting edits in one message, for example `add a faulted jobs widget, then remove it, then change all charts to bar charts`. The agent should handle the edits together and end in a sensible final state, with no leftover or duplicate widget, no broken layout, and no dead drill into links, and the app should still load. | |

### Logging a defect

In the Defects column, write what you did, what you expected, and what actually happened, along with any error text or a screenshot link, and mark the row Pass, Fail, or Partial. If something fails, please keep the generated intent.json file, the metrics folder, and the .dashboard/state.json file from that run so we can reproduce it quickly.
