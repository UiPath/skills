# Test Report Generation Guide

Detailed instructions for generating persona-tailored test reports from UiPath Test Manager.

## Prerequisites

- Authenticated session
- A Test Manager project key
- A Test Manager test set key

---

## Workflow

1. **Fetch test executions from the test set**
   - Use options like `status`, `execution-type`, `execution-finished-interval` to filter results as needed

2. **Determine the report persona**
   - Ask the user: "Who is this report for?"
   - Example personas: `QA Engineer`, `Release Manager`, or `Developer`

3. **Determine the output directory**
   - Ask the user: "Which folder should the report be saved in? (or use the current directory.)"
   - If the user provides a path, use it as-is (absolute or relative).
   - If the user presses Enter or provides no path, use `.` (current working directory).
   - Verify the directory exists before writing. If it does not exist, ask the user whether to create it or choose a different path. Do not create directories silently.

4. **Include common metrics in all reports**
   - Status of each test execution
   - Count of test case logs per execution with result: `none`, `passed`, `failed`, `restricted` — derive these counts by tallying the test case logs already fetched in step 1
   - List of frequently failing test cases

5. **Add persona-specific content**
   
   **For QA Engineer reports:**
   - List regressions (previously passing tests that now fail). Ask if further details are needed → follow [Analyse More](#analyse-more).
   
   **For Developer reports:**
   - Include the failing assertion message for each test case log. Ask if further details are needed → follow [Analyse More](#analyse-more).
   
   **For Release Manager reports:**
   - Provide an overall summary with go/no-go decision support (success rate, blocker count, risk assessment)

   **Other:**
   - Ask for persona and what purpose is this report for.
  
6. **Validate the report before saving**
   - Check that all required sections for the persona (steps 4–5, 7) are present. Add any missing sections before writing the file.

   Every section below is a real markdown heading (`##` or `###`), not a
   sentence folded into prose. Reports without them are incomplete:

   | Persona | Required headings |
   |---|---|
   | All personas | `## Summary` · `## Test Set` (name and key) · `## Results Breakdown` (counts for passed / failed / none / restricted) · `## Frequently Failing Test Cases` (step 4 requires this metric in every report) |
   | QA Engineer | plus `## Regressions` |
   | Developer | plus `## Failed Assertions` (assertion message per failing test case log) |
   | Release Manager | plus `## Go / No-Go` (success rate, blocker count, risk assessment) |

   Add a persona-appropriate extra section when the data warrants it, but
   never drop a required one; write "None" under a heading that has no
   content rather than omitting the heading.

7. **Ask if further details are needed**
   - Follow [Analyse More](#analyse-more).
  
8. **Save the report**
   - Save the report with all the fetched data.


### Output Format

The default filename is `test-report-<PERSONA>-<YYYY-MM-DD>.md`, where `<PERSONA>` is `qa`, `dev`, or `release` (use `custom` for any other persona) and `<YYYY-MM-DD>` is today's date.

Ask the user: 
- "Where should the repory be saved? (default: current directory)"
- "What should the report be named? (default: `<DEFAULT_FILENAME>`)"

Write the report to `<OUTPUT_DIR>/<FILENAME>`. Create the directories if not present

Examples:
- `./test-report-release-2026-04-13.md` (current directory, release manager, default name)
- `/home/user/reports/my-report.md` (absolute path, user-provided name)

---

## Analyse More

When the user asks for further details, use this loop:

1. **Explore** — run `uip tm <resource> --help` to confirm the right subcommand and its flags
2. **Execute** — run the command using IDs from the previous response, always with `--output json`
3. **Validate** — if `items` is empty or the command errors, diagnose before retrying (max 3 attempts)
4. **Repeat** — if the user asks for deeper detail, identify the next command and repeat

<!-- | User asks about | Command |
|---|---|
| Regression history for a test case | `uip tm testcases list-result-history --project-key <KEY> --test-case-id <ID>` |
| Failing assertions for a test case log | `uip tm testcaselog list-assertions --project-key <KEY> --test-case-log-id <ID>` |
| Attachments for an execution | `uip tm attachment download --execution-id <ID>` | -->

Stop when: the user is satisfied, the response has no more data, or 3 retries have failed.

---

## Anti-patterns

- **Do NOT generate a report without asking for the persona** — a release manager receiving raw test logs is noise; a tester receiving only a pass/fail count is missing the detail they need.
- **Do NOT fabricate test results** — only report data returned by the API. If executions are empty, tell the user there are no results for the selected filters.
- **Do NOT build `--output-filter` aggregate expressions to compute counts** — a malformed filter aborts the command, and under Critical Rule 10 that stops the whole report for totals you can tally from the test case logs already fetched.
