# Test Report Generation Guide

Generate persona-tailored test reports from UiPath Test Manager.

## Prerequisites

- Authenticated session
- Test Manager project key
- Test Manager test set key

## Workflow

1. **Fetch test executions from the test set**, using `status`, `execution-type`, and `execution-finished-interval` as needed.
2. **Ask for the report persona:** "Who is this report for?" Personas include `QA Engineer`, `Release Manager`, and `Developer`.
3. **Ask for the output directory:** "Which folder should the report be saved in? (or use the current directory.)" Use a supplied absolute or relative path as-is; otherwise use `.`. Verify it exists before writing. If it does not, ask whether to create it or choose another path; do not create directories silently.
4. **Include in every report:** every execution's status; counts of already-fetched test case logs by result (`none`, `passed`, `failed`, `restricted`), tallied from those logs; and frequently failing test cases.
5. **Add persona-specific content:**
   - **QA Engineer:** List regressions (previously passing tests that now fail). Ask whether further details are needed and follow [Analyse More](#analyse-more).
   - **Developer:** Include the failing assertion message for each test case log. Ask whether further details are needed and follow [Analyse More](#analyse-more).
   - **Release Manager:** Provide an overall summary and go/no-go decision support: success rate, blocker count, and risk assessment.
   - **Other:** Ask for the persona and report purpose.
6. **Validate before saving:** confirm the required sections below and step 7, adding missing sections. Each must be a real `##` or `###` markdown heading, not prose; write "None" beneath headings without content.

   | Persona | Required headings |
   |---|---|
   | All personas | `## Summary`; `## Test Set` (name and key); `## Results Breakdown` (passed / failed / none / restricted counts); `## Frequently Failing Test Cases` |
   | QA Engineer | Plus `## Regressions` |
   | Developer | Plus `## Failed Assertions` (assertion message per failing test case log) |
   | Release Manager | Plus `## Go / No-Go` (success rate, blocker count, risk assessment) |

   Add a persona-appropriate extra section when the data warrants it. Never omit a required heading.
7. **Ask whether further details are needed** and follow [Analyse More](#analyse-more).
8. **Save the report** with all fetched data.

## Output Format

Use `test-report-<PERSONA>-<YYYY-MM-DD>.md`, with `<PERSONA>` `qa`, `dev`, or `release` (use `custom` otherwise) and `<YYYY-MM-DD>` today's date. Ask:

- "Where should the repory be saved? (default: current directory)"
- "What should the report be named? (default: `<DEFAULT_FILENAME>`)"

Write to `<OUTPUT_DIR>/<FILENAME>`. Create the directories if not present.

## Analyse More

When the user asks for further details:

1. **Explore** — run `uip tm <resource> --help` to confirm the right subcommand and flags.
2. **Execute** — run the command with IDs from the previous response, always with `--output json`.
3. **Validate** — if `items` is empty or the command errors, diagnose before retrying; make at most 3 attempts.
4. **Repeat** — if the user asks for deeper detail, identify the next command and repeat.

<!-- | User asks about | Command |
|---|---|
| Regression history for a test case | `uip tm testcases list-result-history --project-key <KEY> --test-case-id <ID>` |
| Failing assertions for a test case log | `uip tm testcaselog list-assertions --project-key <KEY> --test-case-log-id <ID>` |
| Attachments for an execution | `uip tm attachment download --execution-id <ID>` | -->

Stop when the user is satisfied, the response has no more data, or 3 retries have failed.

## Anti-patterns

- **Do NOT generate a report without asking for the persona** — raw test logs are noise for a release manager, while a tester receiving only pass/fail counts lacks needed detail.
- **Do NOT fabricate test results** — report only API-returned data. If executions are empty, tell the user there are no results for the selected filters.
- **Do NOT build `--output-filter` aggregate expressions to compute counts** — a malformed filter aborts the command, and under Critical Rule 10 that stops the whole report for totals tallyable from the test case logs already fetched.
