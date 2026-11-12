# Live healing pass: what to tell the agent and what to ask

The live healing pass checks a finished build against the real application and fixes what the offline build got wrong.

The agent already works read-only outside the runs you allow, never edits the genome while building, and closes only the windows it opened. What it does not know is your system, your data and your limits. This page lists what to tell it, what to ask before the first run, how to question a failure, and what the final report must say.

## 1. Set the scene before it touches the application

Before it builds, the agent asks once whether it can reach the application and how far the healing pass may go. Answer both in full:

> Build `<name>-genome.md`.
> **Live application:** a comparable instance, `<system and environment>`, window `<title or URL>`. I sign in myself; you never type or read a password. Never close `<applications that must stay open>`.
> **Healing pass:** read-only check first. Run only on `<named records>` and only these test cases: `<list>`. Do not touch `<what must stay as it is>`.

A comparable instance is a test or training copy of the target application, not the one the automation will run on in production.

Then add the rules only you know:

- "Fixes for what the rebuild got wrong go into the project. Anything the run needs only on this instance, such as attaching to my session, skipping the sign-out or local test data, goes into a copy of the project. Tell me which is which before you apply each change."
- "Do not change a wait or a timeout without asking me. They are the source's design."
- "Ask before you close an application or answer a security or permission prompt."
- When the build's captures came from another instance: "The captions, menu texts and column headers in the build came from a different instance than this one. Treat them as instance data and check each one on this screen before relying on it."

## 2. Questions to ask before any run

1. "Which instance were the captures taken on, and which one are we healing on?" Captions, tooltips and layouts differ between instances of the same system.
2. "Show me the contract probe for each shape the build repeats: a dialog check and its action, a key press, a table cell read, a list longer than one screen, a tab, a menu path." One probe per shape settles it before hundreds of files depend on it. When the application was reachable during the build, the results are in `applications/<application>.md` in the hand-off folder; otherwise ask for the probes now.
3. "Which tables, menus and lists do the workflows use that the build has no entry for yet?" A missing entry fails only when a case reaches it, so list them up front.
4. "Which steps could the build not exercise live, such as steps that write? List them as unverified." They are the likeliest to fail on first contact, and they are the `run` rows of `live-checks/<project>.md`.
5. "Which accounts and secrets does each case need, and does each one exist on this machine?" A missing one can be skipped silently and fail three steps later.

## 3. When something fails

Ask these in order. Do not accept "probably the data" without the second.

1. "What exactly failed: which activity, in which workflow, with what message? What is on the screen right now?" Look at the live screen, not only the log.
2. "Is this the project or the data? Show me the element the step reads, on screen in this case's state, and when this step last passed." A step that passed before a fix and fails after it is that fix's regression.
3. "Did the step go through a fallback, read nothing while the screen showed something, or pick the wrong entry?" Passing is not healed.
4. "What else uses what you are about to change, and which cases will you re-run?"
5. When the run uses a copy: "Fix it in the project first, then show me the same change in the copy."

A working style that saves time: "Run each case once in debug mode, stop at the first real failure and fix it there. Check the fix with a one-workflow probe instead of re-running the whole case. If the application shows the record is already past the step, cancel and move on."

## 4. Before you trust a green

- "Which run is this verdict from? Show me that run's own start line and status line." A time window can hold the previous case's report.
- "Does this case report a status at all? If not, what rule makes it a pass?"
- "When a case passes, re-run the cases that run after it on the same record: they last ran on a record that case had not moved on yet."
- "A stop is data only if you can show it on screen. Otherwise call it *not shown to be data*."

## 5. What the final report must say

Ask for these, in this form:

- Counts: cases run, passed, stopped, and not run, with the reason.
- Every stop classed as **data** (shown, with the evidence), **account**, or **not shown to be data**.
- A data request: for each chain of cases, the state its record must be in at the start and how to check it.
- Every change the runs made in the application.
- What changed in the project, and what was kept only in the copy.

## Prompts that go wrong

| Prompt | Why it fails | Say instead |
| --- | --- | --- |
| "Make all the tests pass." | The agent bends the project to the data. | "Fix defects of the rebuild; stop and report where the data is the limit." |
| "Speed it up, shorten the waits." | Changes the source's behaviour. | "Speed up the copy only, and ask me before a verdict rests on it." |
| "It's probably a data problem, move on." | Hides defects: stops blamed on data often pass once the project is fixed. | "Show the element on screen in this state, then decide." |
| "Run everything again." | Long runs for one fix. | "Re-run the cases that use what the fix changed, starting with the ones whose stop it addresses." |
