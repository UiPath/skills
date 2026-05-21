# `tests/tasks/uipath-platform/` — prompt review

Existing test prompts vs. natural-user rewrites. Methodology in [hitl-prompts-review.html](../../hitl-prompts-review.html) and [CLAUDE.md](../../CLAUDE.md).

## Scope of this folder

`uipath-platform` is the umbrella skill for the `uip` CLI — auth, Orchestrator (folders / jobs / processes / packages / sessions), resource ops (assets / queues / buckets / libraries), Integration Service (connectors / connections / activities / resources), agentic LLM traces + feedback, and platform licensing (tenant allocations, user/group bundles, consumables). The 34 tests in this folder are mostly smoke tests that pose a single read or single mutation in customer voice; the licensing and Integration Service subfolders are richer, multi-step scenarios that often run "offline" (no live tenant) and so layer eval-harness guard-rails ("commands will fail with auth errors — that is expected") on top of the user ask.

## Insider markers seen in this folder

- **"Load the X skill first" preamble** — almost every licensing and IS prompt opens with `Before starting, load the uipath-platform skill and follow its workflow.` or `Use the \`uipath-platform\` skill.` That's a harness affordance — a real customer would never say this.
- **Eval-harness offline guardrails** — `The \`uip\` CLI is available but is NOT connected to a live tenant in this environment. Commands may fail with auth errors — that is expected. Run each command once and move on. Do NOT retry or attempt to login.` and `Use \`--output json\` on every uip command.` are pure test-rig instructions.
- **CLI flag literacy in the prompt** — `use --operation Create`, `Always pass --connection-id ... use a placeholder value like "placeholder-connection-id"`, `--mode summary`, `Do NOT run connections create or connections edit — they open a browser` all teach the agent which flags to reach for instead of testing whether it knows.
- **Connector machine names quoted verbatim** — `"uipath-salesforce-sfdc"` is the connector key, not a friendly name a customer would type ("Salesforce" would be).
- **Synthetic / fixture IDs** — folder key `11111111-2222-3333-4444-555566667777`, tenant id `c0ffee00-0000-0000-0000-000000000001`, trace id `4bf92f3577b34da6a3ce929d0e0e4736`, robot id `f1b2c3d4-0000-0000-0000-000000000001`, env var `$TRACES_SMOKE_PROCESS_KEY`. These are unavoidable for an automated grader but they don't sound like a customer would paste them naked into chat.
- **Skill-rule callbacks** — "refer to the bundle by its friendly name AND its code, per the skill's docs-page resolution rule" and "Resolve product names to codes from the UiPath docs license-codes page before writing the input file" reference internal skill rules.
- **Numbered step-list authoring** — multiple licensing prompts (read_e2e, IS resource_describe / connection_lifecycle) hand the agent a 4–6 step recipe rather than describing the goal.
- **Filename + format dictation** — `save the full output to rules.json`, `details.json`, `consumables.json`, `available.json`, `group-rule.json`, `tenant-allocation.json`, `user-licenses.json`, `spans.json`, `job.json`, `feedback_create.json`, `feedback_get.json`. These are eval-grader contracts, not user requests.
- **Output-format dictation in the body** — `Print a final summary that references at least one bundle code from available.json using the \`<Friendly Name> (<CODE>)\` format`.

## Verdict summary

| Verdict | Count |
|---|---|
| Insider — fixable | 17 |
| Insider — legitimate (CLI/refusal/antipattern coverage) | 7 |
| Mixed | 7 |
| Natural | 3 |

(Total: 34)

## Per-test review

### `integration-service/` (5)

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-platform-is-activity-discovery` | Mixed | Opens with "load the uipath-platform skill," then asks to list non-trigger and trigger activities for Salesforce and summarize activities/triggers/resources. Adds "no live tenant ... commands may fail ... Run each command once and move on. Do NOT retry or attempt to login. Use `--output json` on every uip command." | "I'm trying to figure out what the Salesforce connector can do through UiPath Integration Service. Can you list the actions (non-trigger activities) and the events (triggers) it exposes, and explain how activities, triggers, and resources relate to each other?" |
| `skill-platform-is-connection-lifecycle` | Insider — fixable | "Load the uipath-platform skill," uses connector key `"uipath-salesforce-sfdc"`, dictates "List ... Ping ... Explain ... do NOT run these — they require a browser," and "If connections list returns no connections, use a placeholder like 'placeholder-conn-id' to still run the ping command with correct syntax." | "I want to use the Salesforce connector in Integration Service. Can you find the existing connections for it, recommend a default if there is one, and check its health? If there's no connection set up, tell me what I'd need to do — but please don't try to create or re-auth one now since that needs a browser." |
| `skill-platform-is-connector-discovery` | Mixed | "Load the uipath-platform skill," then asks to search Integration Service connectors for "Google" and "Apify," plus fallback if no native connector. Harness guardrails appended. | "I need to find Integration Service connectors for Google products, and also check whether there's anything for Apify. For each one, if there's no native connector, what's the fallback?" |
| `skill-platform-is-resource-describe` | Insider — legitimate | "Load the uipath-platform skill," then `--operation Create`, `--connection-id` with placeholder, "Always pass --operation on both resources list and resources describe." | _Keep as-is — this test specifically covers `--operation` and `--connection-id` flag discipline on the IS resources commands; naming the flags is the point._ |
| `skill-platform-is-resource-execute` | Insider — fixable | "Walk me through creating a Contact in Salesforce via UiPath Integration Service. Follow the full Integration Service workflow." Plus harness guardrails and "construct a realistic --body with at least LastName (required) and FirstName fields." | "I want to create a Contact in Salesforce through Integration Service. Walk me through the whole flow end-to-end — at minimum the contact should have a last name and a first name." |

### `licensing/` (12)

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-platform-licensing-consumables-daily` | Mixed | "Load the uipath-platform skill," then "Give me a day-by-day consumption breakdown for the period 2026-04-01 through 2026-04-30." Harness guardrails appended. | "Give me a day-by-day license consumption breakdown for April 2026." |
| `skill-platform-licensing-consumables-folders` | Insider — fixable | "Load the uipath-platform skill," then tenant id `c0ffee00-0000-0000-0000-000000000001`. | "Can you show me license consumption broken down by folder for the `c0ffee00-0000-0000-0000-000000000001` tenant?" |
| `skill-platform-licensing-consumables-summary` | Mixed | "Load the uipath-platform skill," then "Give me a summary of license consumption for this account." | "Give me a summary of license consumption for this account." |
| `skill-platform-licensing-groups-rules-details` | Mixed | "Load the uipath-platform skill," then "Who in the 'RPA Developers' group currently holds which license bundle?" | "Who in the 'RPA Developers' group currently holds which license bundle?" |
| `skill-platform-licensing-groups-rules-list` | Insider — fixable | "Load the uipath-platform skill," then "List the group license-allocation rules in this account. Sort them by name in descending order and limit to the first 20 results." | "Show me the group license-allocation rules we have set up — sorted Z to A by name, and just the top 20." |
| `skill-platform-licensing-groups-rules-set` | Insider — fixable | "Configure the group rule for the 'RPA Developers' group so that: every member gets an Automation Developer Named User license (no quota); up to 10 members can also get an Attended Named User license. Save the input JSON file as `group-rule.json` ... then apply it." Plus skill-rule callback "Resolve product names to codes from the UiPath docs license-codes page before writing the input file." | "Set up the license rule for the 'RPA Developers' group so everyone in it automatically gets an Automation Developer Named User license, and up to 10 of them can also get an Attended Named User license." |
| `skill-platform-licensing-read-e2e` | Insider — legitimate | "Use the `uipath-platform` skill. Produce a read-only licensing snapshot ... Do NOT run any command that mutates state — only `get`, `available`, `details`, and `consumables get`." Then a numbered 6-step recipe naming `users licenses available`, `groups rules get`, `groups rules details`, `licenses consumables get --mode summary`, and required `<Friendly Name> (<CODE>)` output format with filenames `available.json` / `rules.json` / `details.json` / `consumables.json`. | _Keep as-is — this is a read-only/no-mutate antipattern-coverage e2e test with strict eval-grader file contracts. The negative-guard wording ("Do NOT run any command that mutates state") and the per-step filenames are part of what's being measured._ |
| `skill-platform-licensing-tenant-allocation-get` | Insider — fixable | "Load the uipath-platform skill," then "Show me the current license unit allocation for tenant `c0ffee00-0000-0000-0000-000000000001`." | "Show me the current license unit allocation on tenant `c0ffee00-0000-0000-0000-000000000001`." |
| `skill-platform-licensing-tenant-allocation-set` | Insider — fixable | "Load the uipath-platform skill," then "Allocate 5 Unattended Robots and 10 Robot Units to tenant `c0ffee00-...`. Save the input JSON file as `tenant-allocation.json` in the current directory, then apply it." | "I need to allocate 5 Unattended Robots and 10 Robot Units to tenant `c0ffee00-0000-0000-0000-000000000001`. Can you do that?" |
| `skill-platform-licensing-users-licenses-available` | Insider — legitimate | "How many Attended Named User seats does this account have available right now? When you reply, refer to the bundle by its friendly name AND its code, per the skill's docs-page resolution rule." Plus harness fallback to resolve the mapping even if the CLI fails. | _Keep as-is — this test exists to measure whether the agent applies the skill's docs-page `<Friendly Name> (<CODE>)` resolution rule even when offline; calling out the rule is the eval target._ |
| `skill-platform-licensing-users-licenses-get` | Insider — legitimate | "What license bundles does user `dan.dinu@uipath.com` currently hold? Tell me each bundle and whether it was assigned directly or inherited from a group. When you reply, refer to each bundle using its friendly name AND its code." | _Keep as-is — same friendly-name-and-code reporting rule is the measurement; the direct-vs-inherited ask is a legitimate user question._ |
| `skill-platform-licensing-users-licenses-set` | Insider — fixable | "Load the uipath-platform skill," then "Assign two licenses to user `dan.dinu@uipath.com`: Attended Named User, Automation Developer Named User. Save the input JSON file as `user-licenses.json` ... then run the assignment command." Plus the docs-page resolution callback. | "Give `dan.dinu@uipath.com` two licenses: Attended Named User and Automation Developer Named User." |

### `orchestrator/` (6)

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-platform-orchestrator-folders-get` | Insider — fixable | "Fetch the metadata for the Orchestrator folder with key `11111111-2222-3333-4444-555566667777` in the current UiPath tenant." | "Pull up the details for the Orchestrator folder with key `11111111-2222-3333-4444-555566667777`." |
| `skill-platform-orchestrator-folders-list` | Natural | "List all Orchestrator folders available in the current UiPath tenant." | _Keep as-is — already natural._ |
| `skill-platform-orchestrator-jobs-list` | Insider — fixable | "List the recently faulted jobs in the Orchestrator folder with key `11111111-2222-3333-4444-555566667777` in the current UiPath tenant." | "Show me the jobs that have faulted recently in the `11111111-2222-3333-4444-555566667777` folder." |
| `skill-platform-orchestrator-packages-list` | Natural | "List the Orchestrator packages available in the current UiPath tenant." | _Keep as-is — already natural._ |
| `skill-platform-orchestrator-processes-list` | Natural | "List the processes published in the `Finance/Accounting` folder of the current UiPath tenant." | _Keep as-is — already natural._ |
| `skill-platform-orchestrator-sessions-unattended-list` | Insider — fixable | "List the unattended robot sessions available in the current UiPath tenant." | "Show me the unattended robot sessions running in the tenant right now." |

### `resources/` (6)

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-platform-resources-assets-get` | Insider — fixable | "Fetch the metadata for the Orchestrator asset named `ApiBaseUrl` in the current UiPath tenant." | "Show me the details for the `ApiBaseUrl` asset." |
| `skill-platform-resources-assets-list` | Insider — fixable | "List the assets defined in the `Shared` folder of the current UiPath tenant." | "What assets do we have in the `Shared` folder?" |
| `skill-platform-resources-buckets-list` | Insider — fixable | "List the storage buckets defined in the `Finance` folder of the current UiPath tenant." | "What storage buckets are set up in the `Finance` folder?" |
| `skill-platform-resources-libraries-list` | Insider — fixable | "List the library packages available in the current UiPath tenant." | "What libraries do we have published in this tenant?" |
| `skill-platform-resources-queue-items-list` | Insider — fixable | "List the queue items in the Orchestrator folder with key `11111111-2222-3333-4444-555566667777` in the current UiPath tenant." | "Show me the queue items in folder `11111111-2222-3333-4444-555566667777`." |
| `skill-platform-resources-queues-list` | Insider — fixable | "List the queues defined in the Orchestrator folder with key `11111111-2222-3333-4444-555566667777` in the current UiPath tenant." | "What queues are set up in folder `11111111-2222-3333-4444-555566667777`?" |

### `traces/` (4)

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-platform-traces-e2e` | Insider — legitimate | "Use the `uipath-platform` skill. Verify that the published agent at process key `$TRACES_SMOKE_PROCESS_KEY` produces LLM trace spans. Save the raw spans output to spans.json. Use `--output json` on all uip commands." | _Keep as-is — uses an env-var fixture and a fixed output filename for grader contract; the "verify spans are produced" framing is a legitimate observability test._ |
| `skill-platform-traces-feedback-e2e` | Insider — legitimate | "Run a feedback round-trip on a real trace: Start a job ... save the result to job.json; Fetch the LLM trace spans ... save to spans.json; Create positive feedback ... save the response to feedback_create.json; Fetch the feedback record back by ID and save to feedback_get.json." | _Keep as-is — e2e round-trip with per-step output filenames the grader needs. The numbered shape is the measurement._ |
| `skill-platform-traces-feedback-smoke` | Mixed | "I want to annotate a trace with positive feedback and then list all feedback for that trace. The trace ID is `4bf92f3577b34da6a3ce929d0e0e4736` and the folder key is `11111111-2222-3333-4444-555566667777`. Use `--output json` on all uip commands." | "I want to leave positive feedback on trace `4bf92f3577b34da6a3ce929d0e0e4736` (folder `11111111-2222-3333-4444-555566667777`), then show me all the feedback that's been left on it." |
| `skill-platform-traces-fetch` | Mixed | "Use the `uipath-platform` skill. I want to inspect the LLM trace spans for a completed job. The job key is `11111111-2222-3333-4444-555566667777`. Fetch them. Use `--output json` on all uip commands." | "I want to look at the LLM trace spans from a job that already finished — the job key is `11111111-2222-3333-4444-555566667777`. Can you pull them up?" |

### root (1)

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-platform-users-import-robot-smoke` | Mixed | "I created a robot account in Identity Service called 'InvoiceRunner' with id `f1b2c3d4-0000-0000-0000-000000000001`. I want to import it into the Orchestrator tenant so I can later assign it to folders. Use `--output json` on all uip commands." | "I just made a robot account in Identity Service called 'InvoiceRunner' (id `f1b2c3d4-0000-0000-0000-000000000001`). I need it imported into Orchestrator so I can assign it to folders later." |

## Notes for the PR description

- **The dominant insider pattern in this folder is the boilerplate preamble plus harness guardrails.** Nearly every Integration Service and licensing test opens with `Before starting, load the uipath-platform skill and follow its workflow.` and ends with the offline-tenant disclaimer + `Use --output json on every uip command.`. Stripping those two stanzas from the customer-voice tests (everything that isn't a legitimately-insider CLI-flag / antipattern / format-contract test) would dramatically improve realism without changing what's measured.
- **The Orchestrator and resources smoke folders are mostly fine.** They're already short, goal-shaped, and rarely name flags. The only consistent slip is the recitation of "in the current UiPath tenant" at the end of every prompt — customers don't say that. Mild rewrites (more conversational tone, drop the "of the current UiPath tenant" tail) are the only fix needed.
- **The legitimately-insider tests cluster cleanly:** `is-resource-describe` (flag coverage for `--operation` / `--connection-id`), `licensing-read-e2e` (no-mutate antipattern + per-step file contract), `users-licenses-available` and `users-licenses-get` (friendly-name-and-code reporting rule), and the two `traces-*-e2e` tests (file-contract round-trips). These four families each measure a specific eval target that needs the insider wording; the smoke equivalents (`traces-feedback-smoke`, `traces-fetch`) don't, and can be humanized.
- **Recurring connector-key slip in IS:** the connector machine name `uipath-salesforce-sfdc` appears in three of five IS prompts. A real customer would say "Salesforce." Worth swapping unless a specific test is explicitly checking that the agent can use the verbatim machine key from a user-supplied identifier.
