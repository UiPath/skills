---
name: uipath-feedback
description: "UiPath bug reports and improvement suggestions via `uip feedback send`. Use for 'report issue', 'send feedback', 'file a bug', or the /uipath-feedback command. For investigating an error rather than reporting one→uipath-troubleshoot."
when_to_use: "User says 'this is broken', 'this isn't working', 'report a bug', 'send feedback', 'something is wrong', 'file an issue', 'this crashed', 'wrong result' about a UiPath product, CLI, or skill. Also fires on the /uipath-feedback slash command."
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

# UiPath Feedback

Send structured bug reports or improvement suggestions to UiPath with auto-captured troubleshooting via `uip feedback send`.

> **Design principle: minimum friction.** The agent already knows what went wrong from the conversation. Don't re-ask what you already know. The only mandatory interaction is confirmation before sending; the sole optional one is a single, always-skippable chance (Step 2h) to state Expected vs. Actual in the user's own words.

## Critical Rules

1. **Minimum user interaction.** If the conversation already contains enough context (error, what the user was doing, what went wrong), make the one optional offer in Step 2h, then go straight to confirm and send. Only ask further clarifying questions when you genuinely cannot determine what happened.
2. **Never send without explicit user confirmation.** Always show a preview and wait for "yes".
3. **Never include secrets, tokens, credentials, or customer data.** Sanitize all captured content before sending.
4. **Never include full conversation history.** Summarize relevant context in 2-3 sentences. Sample prompts (Step 2e) are a relevance-filtered selection, capped at 5 — not a transcript, and not a quota to fill.
5. **Use `--output json`** on `uip feedback send` to parse the result programmatically.
6. **If `uip feedback send` fails**, save the report to `./feedback-report.md` so the user does not lose the gathered context.
7. **Omission beats padding.** `## Sample prompts` and `## Session retrospective` (and any bullet within them) are optional. Leave them out entirely when they'd otherwise be filled with generic, obvious, or off-topic content.
8. **The Step 2h offer is opt-in, not required.** It always has a zero-typing skip path, and a skipped answer is a complete, valid input — never re-ask it.

## Workflow

### Step 1 -- Check prerequisites

```bash
uip --version 2>&1
```

| Result | Action |
|---|---|
| Version output | Proceed to Step 2 |
| `uip: command not found` | Tell user to install UiPath CLI. Stop. |
| Other error | Show the error. Stop. |

### Step 2 -- Introspect and capture (silent by default -- optional/fallback interaction only in 2h/2j)

Gather all context automatically. Run these substeps silently.

#### 2a. Detect the area

The **area** (which product) becomes the title tag and a Jira label for filtering. Identify it from the last `uip <verb>` the user ran in this conversation. If no `uip` command is identifiable, fall back to the working directory, then to conversation context. Map command/signal → area:

| Last command / signal | Area |
|---|---|
| `uip rpa …`, or `project.json` + `*.cs`/`*.xaml` | `RPA` |
| `uip maestro flow …`, or `*.flow` file | `Flow` |
| `uip maestro bpmn …`, or `*.bpmn` file | `BPMN` |
| `uip maestro case …`, or `caseplan.json` | `Case` |
| `uip <agent…>`, or `pyproject.toml` with `uipath` / `agent.json` | `Agents` |
| `uip codedapp …`, or `app.config.json` / `action-schema.json` | `CodedApps` |
| `uip api-workflow …` | `ApiWorkflow` |
| `uip df …` | `DataFabric` |
| `uip solution …`, or `*.uipx` | `Solution` |
| `uip tm …` (Test Manager) | `Test` |
| `uip tasks …` | `Tasks` |
| `uip admin …` | `Admin` |
| `uip gov …` | `Governance` |
| anything else (`uip login`, generic Orchestrator / Integration Service / platform) | `Platform` |

If ambiguous, infer from the conversation. Do NOT ask the user -- pick the best match.

**Optional CLI vs Skill marker.** Only when it is *clearly* one or the other, add a second tag so triagers can route the report:
- `CLI` -- a `uip` command crashed, returned wrong output, or lacked a verb/flag.
- `Skill` -- you followed this skill's instructions and they were wrong, misleading, or missing.

Omit it when the cause is mixed or unclear -- don't force a guess.

#### 2b. Capture environment

```bash
uip --version 2>&1
uip login status --output json 2>&1
uip tools list 2>&1
```

From login status, extract only: `tenantName`, `organizationName`, `baseUrl`. Strip everything else.

From tools list, extract tool `name` and `version` from each row.

#### 2c. Capture skill-specific troubleshooting

| Area | What to capture | Limits |
|---|---|---|
| **Flow** | `uip maestro flow validate <file> --output json`, `.flow` file content, directory listing | `.flow`: first 150 lines; directory: max 30 entries |
| **RPA** (`.cs` or `.xaml`) | `project.json` dependencies, `uip rpa validate --output json`, list of workflow files (`.cs` and/or `.xaml`) | File list: max 20 files; `project.json`: dependencies section only; failing workflow: first 150 lines |
| **Agents** | `pyproject.toml`, `bindings.json` (redact connection values), directory listing | `bindings.json`: redact all values; directory: max 30 entries |
| **CodedApps** | `package.json` (name, version, dependencies only), `.uipath/` listing | `package.json`: name + version + dependencies only |
| **Other** (Platform, Solution, Admin, …) | `uip login status --output json` output only | Strip tokens from output |

#### 2d. Capture the failing command

Review the current conversation for the last CLI command that failed. If identifiable, capture:
- The full command
- Its stderr/stdout output (truncated to 100 lines)

If not identifiable, skip this section.

#### 2e. Capture sample prompts

Pick user prompts that **bear on the issue being reported** — not prompts that merely show what the user was trying to do this session. Those are different things: a session has one intent, but a bug can surface incidentally, unrelated to what the user asked for. An agent-discovered issue (found while doing something else, not something the user raised) often has **zero** relevant prompts. That's the normal case, not a gap to fill.

**Relevance test** — apply to every candidate prompt: *would a triager who reads only this prompt and the `## Error` section learn something they didn't already know?* If no, drop it — even if the prompt is substantive and was clearly part of this session's topic.

Selection rules:
- Prefer prompts that describe the failure itself ("this is broken", "wrong result", "why did X happen"), or that state the specific input/configuration that reproduces the issue.
- A prompt stating general session intent ("build a flow that…", "I need to…") qualifies ONLY if it also supplies information the triager needs — e.g., it names the exact data shape or config that triggers the bug. Intent by itself does not pass the relevance test.
- Keep wording **verbatim**. Paraphrasing loses signal. Sanitization Rules apply.
- Skip filler ("ok", "thanks", "try again").
- **5 is a ceiling, not a target.** One genuinely relevant prompt outranks three topical-but-irrelevant ones. Never pad toward 3-5 to look thorough.
- Total length under 1000 characters across all prompts. Truncate any single prompt over 200 chars with `... [truncated]`; keep the most informative portion.
- **Don't requote what Step 2h already placed under `## What happened`.** If the user's Expected/Actual answer (or a conversation statement 2h reused) already quotes this prompt in full or near-verbatim, leave it out here — repeating it adds nothing for a triager who just read it above.
- **If no prompt passes the relevance test, omit the `## Sample prompts` section in Step 3 entirely.** Do not substitute an off-topic-but-substantive prompt just to avoid an empty section.

#### 2f. Session retrospective

Review the full conversation for retrospective signal. This section earns its place only when it tells the triager something the `## Error`, `## Environment`, and `## Troubleshooting` sections don't already cover — it is not a mandatory five-part form.

Apply the same relevance test as Step 2e to each of the five questions below: *would a triager who has already read the rest of the report learn something new from this bullet?* If the honest answer is generic ("outcome matched what was asked", "no friction observed"), obvious from the title, or a restatement of the Error section, **omit that bullet**. Never write a placeholder ("N/A") to keep the list looking complete.

1. **Intent**: What was the user trying to build/edit/fix? Include only if it isn't already obvious from the title and `## What happened`.
2. **Outcome**: Full / Partial / Failed, vs. what was requested. Include only if it adds a reason beyond the label itself — a bare "Full, as expected" is not worth a bullet.
3. **Tool & Skill Gaps**: Specific tools or CLI commands that were called but unhelpful, or that should have existed but didn't. Name them concretely. Omit if nothing concrete was identified.
4. **Friction**: Where the agent got stuck, retried, or misunderstood a UiPath convention, and how many generate-validate-fix cycles it took. Omit entirely if the issue surfaced cleanly with no retries.
5. **Top 3 Improvements**: Specific, actionable skill/tool changes, ranked by impact. **"Up to 3" is a ceiling, not a target.** One well-specified improvement beats three vague ones ("improve error messages", "add better docs"). Leave slots unfilled rather than padding with generic advice.

**If fewer than two bullets clear the relevance test, omit the entire `## Session retrospective` section.** A tight two-bullet retrospective is more credible — and more useful to a triager — than five bullets where three are filler.

#### 2g. Auto-detect type and priority

**Type** -- determine from conversation signals:

| Type | Signals |
|---|---|
| `bug` (default) | Error messages, crashes, "doesn't work", "broken", runtime failures, unexpected behavior |
| `improvement` | "would be nice", "should support", "missing feature", "suggestion", "the skill told me wrong", "no command for X", feature requests |

Default to `bug` when ambiguous.

**Priority** -- determine from conversation signals:

| Priority | Signals |
|---|---|
| `critical` | Blocks user completely, data loss, security issue, CLI crashes with stack trace |
| `normal` (default) | Something is broken or missing but there is a workaround |
| `minor` | Cosmetic, nice-to-have, typos in output, low-impact |

Default to `normal` when ambiguous.

#### 2h. Offer optional Expected/Actual framing

Check whether the conversation already states, in the user's own words, what they expected vs. what actually happened (e.g., "I expected X but got Y", "this should have done A, instead it did B"). If so, use that text directly (sanitized) in `## What happened` at Step 3 — do not ask again.

If it isn't already stated, offer the user one optional chance to add it, via AskUserQuestion, with a `Skip (Recommended)` option on each question that requires no typing:
- **Expected outcome** — "What did you expect to happen? (optional)"
- **What actually happened** — "What actually happened, in your own words? (optional)"

Rules:
- This offer is never mandatory and never blocks the report. If Steps 2a-2g already gave the agent enough to write `## What happened`, sending with both answers skipped is still a complete, valid report.
- If the user answers one or both, quote their words verbatim (sanitized) in `## What happened` under `**Expected:**` / `**Actual:**` labels — only for the ones they actually answered. Add at most one sentence of agent framing, and only if it supplies something their words don't already cover.
- The conversation often states both halves as one compound sentence ("I expected X, but it did Y") rather than two separate answers. Split it at the natural clause boundary between the two labels — don't force an artificial split, and don't duplicate the same clause under both labels.
- If the user skips both, write `## What happened` as an agent-summarized 2-3 sentences, same as if this step didn't exist.
- A `Skip` answer is a preference not to phrase it themselves, not a sign the agent lacks context — it does not trigger 2j's fallback by itself.

#### 2i. Sanitize everything

Apply all rules from the [Sanitization Rules](#sanitization-rules) section below to every piece of captured content before proceeding.

#### 2j. Only if context is insufficient

If the agent genuinely cannot determine what happened (e.g., user typed `/uipath-feedback` with no prior context in the conversation), ask **one** structured question:

> I'll send feedback to UiPath. Please tell me:
> 1. **What were you trying to do?**
> 2. **What happened?**
> 3. **Is this a bug or an improvement suggestion?**

Otherwise, skip directly to Step 3.

### Step 3 -- Build and confirm (mandatory confirmation)

#### Title format

```
[<Area>] short description
```

- `<Area>` -- the area tag from Step 2a: `RPA`, `Flow`, `BPMN`, `Case`, `Agents`, `CodedApps`, `ApiWorkflow`, `DataFabric`, `Solution`, `Platform`, `Tasks`, `Test`, `Admin`, `Governance`.
- Optionally add a `[CLI]` or `[Skill]` tag after the area **only when it is clearly one or the other** (Step 2a): `[<Area>] [CLI] …` or `[<Area>] [Skill] …`.
- Do NOT put the type (Bug/Improvement) in the title -- that is the issuetype, set via `--type`.

Examples: `[RPA] uip rpa run fails when project.json has no dependencies` · `[Flow] [Skill] Flow skill should list IxP models before adding an extraction node`

The CLI derives Jira labels from these leading `[Tag]` segments of the title, so the same tags are both visible in the title and filterable as labels -- no extra flags.

#### Description body

Build the `--description` content. Sections marked *optional* are omitted entirely (header included) when their Step 2 criteria say so — do not leave an empty or placeholder-filled header in their place.

```
## What happened
{If Step 2h captured Expected/Actual: **Expected:** {...} / **Actual:** {...} (only the ones answered), sanitized, plus at most one sentence of agent framing if it adds new information. Otherwise: 2-3 sentence agent summary.}

## Sample prompts
{Optional -- include only if >=1 prompt passed the Step 2e relevance test.}
1. "{prompt 1 -- verbatim, sanitized}"
2. "{prompt 2 -- verbatim, sanitized}"

## Error
{The actual error message or validation output -- if available, otherwise omit this section}

## Environment
- Area: {area}
- uip version: {version}
- CLI tools: {name version, name version, ...}
- OS: {os info}
- Tenant: {tenant} ({org})

## Troubleshooting
- Project type: {detected type}
- Key files: {list of relevant project files found}
- Last failed command: {command + truncated output}

## Session retrospective
{Optional -- include only if >=2 bullets passed the Step 2f relevance test. List only the bullets that passed.}
- **Intent**: {what the user was trying to do}
- **Outcome**: {Full | Partial | Failed -- what was delivered vs requested}
- **Tool & Skill Gaps**: {tools/commands that failed, were missing, or needed workarounds}
- **Friction**: {where the agent got stuck, retried, or misunderstood conventions}
- **Top 3 Improvements**: {up to 3 specific changes -- a ceiling, not a target; 1 concrete item beats 3 padded ones}
```

#### Formatting rules

1. Use `## ` (two hashes + space) for EVERY section header. NEVER use numbered lists, letters, or bold text as section separators.
2. Use the EXACT section names from the template above for any section you include. Do not rename, reword, or add sections. `## Sample prompts` and `## Session retrospective` are optional per Steps 2e/2f — omit the whole section (header included) when their omission criteria are met. Never include a section populated with placeholder or filler content just to match the template.
3. Each `## ` header MUST be preceded by a blank line and followed by a blank line.
4. Use `-` for unordered bullet points.
5. For numbered items within a section body, use `1.`, `2.`, etc. on their own lines. Do not escape the dots.
6. Do NOT escape markdown characters. No `\*`, `\#`, `\-`, `\.`. Write `**bold**`, not `\*\*bold\*\*`.
7. The description MUST be plain markdown. No Jira wiki markup, no HTML, no ADF — the CLI converts this markdown to the tracker's native format (Jira wiki markup) on send, so it renders cleanly.
8. Do NOT include the user's email in the description body. Pass it only via the `--email` flag.
9. When Step 2h captured user-authored Expected/Actual text, present it under `## What happened` as `**Expected:** …` / `**Actual:** …` lines, quoted verbatim (sanitized) — do not paraphrase it into the agent's own words.

#### Example: session-intent report (Sample prompts and partial retrospective apply)

```
## What happened
**Expected:** Validation should point at the nested-loop expression that's wrong.
**Actual:** `uip maestro flow validate` returned a generic "expression error" with no line number or variable name — impossible to locate.

## Sample prompts
1. "Build a flow that iterates over invoice line items and flags duplicates."
2. "Now add a nested loop to compare each item against the prior month's list."
3. "I keep getting 'currentItem is not defined' — which variable should I use inside the nested loop?"

## Error
ExpressionError: Invalid expression at unknown location — currentItem is not defined

## Environment
- Area: Flow
- uip version: 0.1.20
- CLI tools: docsai-tool 0.1.12
- OS: Windows 11 Enterprise 10.0.26100
- Tenant: demo (aro)

## Troubleshooting
- Project type: Flow (.flow)
- Key files: MyProcess.flow
- Last failed command: uip maestro flow validate MyProcess.flow --output json

## Session retrospective
- **Tool & Skill Gaps**: uip maestro flow validate gave no location info for expression errors. No way to inspect available variables inside a loop scope.
- **Friction**: Agent tried 8 generate-validate-fix cycles guessing the correct variable name. The error message never identified which expression failed.
- **Top 3 Improvements**: (1) Include expression location (line/node) in validation errors. (2) Add a CLI command to list variables in scope at a given point.
```

Note what's missing on purpose: `## What happened` quotes the user's own Step 2h answers instead of an agent paraphrase; no `Intent`/`Outcome` retrospective bullets (already covered above); and only 2 of 3 "Improvements" slots filled — a third, vaguer suggestion was dropped rather than included to round out the list.

#### Example: agent-discovered issue (Sample prompts and Session retrospective both omitted)

```
## What happened
While building an unrelated Flow, the agent noticed `uip is connections list --output json` returns `authType: null` for OAuth2 connections instead of the expected string enum, which breaks downstream filtering on that field.

## Error
TypeError: Cannot read properties of null (reading 'toLowerCase') at filterByAuthType (connections.js:42)

## Environment
- Area: Platform
- uip version: 0.1.24
- CLI tools: docsai-tool 0.1.12
- OS: macOS 14.5
- Tenant: demo (aro)

## Troubleshooting
- Project type: N/A -- issue is in `uip is connections list` output, not project files
- Key files: N/A
- Last failed command: uip is connections list --output json
```

Note what's missing on purpose: no `## Sample prompts` — nothing the user said bears on this bug, since the agent found it incidentally. No `## Session retrospective` — there is no friction, tool gap, or improvement here beyond "fix the CLI output," already captured in `## What happened` and `## Error`. The user declined Step 2h (nothing to add in their own words). This is a complete, well-formed report at three sections, not a partial one.

<!--skill-flavor:feedback-description-budget:start-->
Truncate the full description to 4000 characters max. Note if content was truncated.
<!--skill-flavor:feedback-description-budget:end-->

<!--skill-flavor:feedback-prepare-attachments:start-->
#### Prepare attachments

Write sanitized copies of relevant project files to a temp directory:

```bash
mkdir -p "${TMPDIR:-${TMP:-/tmp}}/uip-feedback-attachments"
```

Copy and sanitize files based on the detected area:
- Flow: the `.flow` file
- RPA: `project.json`, the failing workflow file (`.cs` or `.xaml`)
- Agents: `pyproject.toml`, `bindings.json` (redacted)
- CodedApps: `package.json`

Max 10 files, max 10MB each. Skip files that exceed limits.
<!--skill-flavor:feedback-prepare-attachments:end-->

#### Show preview and confirm

Display to the user:

<!--skill-flavor:feedback-preview:start-->
```
**Type:** bug
**Priority:** normal
**Title:** [Flow] [CLI] Expression error in nested loop currentItem
**Description:** (first 3 lines...)
**Attachments:** MyFlow.flow, project.json

Send this to UiPath? (yes/no)
```
<!--skill-flavor:feedback-preview:end-->

The user can adjust type, priority, or title (the title carries the area / optional CLI-or-Skill tag) before confirming. **Never send without explicit "yes".**

### Step 4 -- Send feedback

**Never inline the multi-line description as a `--description "…"` argument.** On Windows PowerShell the native-command argument serializer mangles multi-line values (lines starting with `-` reach the CLI as options → `ValidationError`). Always pass the body through `--description-file`.

1. Write the sanitized description body to a temp file using the **Write tool** (not a shell heredoc — heredocs are bash-only and fail on PowerShell). Use an absolute path in the OS temp dir, e.g. `<temp>/uip-feedback/description.md`.
2. Invoke the CLI with `--description-file` pointing at that file:

<!--skill-flavor:feedback-send-command:start-->
```bash
uip feedback send \
  --type "<bug|improvement>" \
  --title "<TITLE>" \
  --description-file "<TEMP>/uip-feedback/description.md" \
  --priority "<critical|normal|minor>" \
  --attachment <FILE1> <FILE2> \
  --output json
```
<!--skill-flavor:feedback-send-command:end-->

`--description-file` reads the body from disk, so it is immune to shell quoting and works identically on PowerShell, cmd, and bash. (If the CLI predates this flag, pipe the body via stdin instead; do not inline it.)

The title (`--title`) is short and single-line, so passing it inline is safe. Its leading `[Tag]` segments (the area, plus an optional `[CLI]`/`[Skill]` marker) become Jira labels automatically -- no extra flags.

If an email is available from `uip login status`, include `--email "<EMAIL>"`. The CLI places it in the issue's Environment field, never in the description body.

Parse the JSON output. On success, show the user a confirmation with any reference ID returned.

**Diagnose failures correctly.** A `ValidationError` that names an option you did not pass (e.g. it complains about `-` or a bullet line) is a **shell-quoting** failure, not a CLI bug — you inlined a multi-line value. Fix it by using `--description-file`; do not report the CLI as broken and do not retry the same inline invocation.

**Fallback:** Only after `--description-file` genuinely fails (network, auth, real CLI error) save the full feedback to `./feedback-report.md` using the description body and tell the user: _"Could not send automatically. The report is saved to `feedback-report.md`."_

<!--skill-flavor:feedback-cleanup-attachments:start-->
Clean up temp attachments:

```bash
rm -rf "${TMPDIR:-${TMP:-/tmp}}/uip-feedback-attachments"
```
<!--skill-flavor:feedback-cleanup-attachments:end-->

### Step 5 -- Report result

**On success:**
```
Feedback sent successfully.
- Reference: {reference ID from JSON response, if available}
- Type: {bug|improvement}
- Title: {title}
```

**On fallback to file:**
```
Could not send feedback automatically.
- Report saved to: ./feedback-report.md
- You can submit it manually or retry with `/uipath-feedback` later.
```

<!--skill-flavor:feedback-cleanup-note:start-->
Always clean up temp attachments regardless of success or failure.
<!--skill-flavor:feedback-cleanup-note:end-->

## Sanitization Rules

Apply these rules to ALL content before it is included in the description or attachments:

1. **Strip secrets.** Remove lines matching (case-insensitive): `token`, `secret`, `password`, `apiKey`, `credentials`, `authorization`, `Bearer`, `client_secret`, `connection_string`
2. **Redact PII in paths.** Replace home directory prefixes with `~` (e.g., `C:\Users\john.doe\projects\` -> `~/projects/`). Replace usernames in URLs or paths with `<USER>`
3. **Redact GUIDs** in connection/binding fields: replace values with `<REDACTED>`
4. **Truncate long content.** Files over 150 lines: keep first 100 + `... [truncated N lines] ...` + last 30. Full description: max 4000 characters
5. **Never include**: `~/.uipath/.auth`, `.env`, `.git/config`, environment variables containing secrets, full conversation history
6. **Never include customer data.** Strip customer names, email addresses, and organization-specific identifiers from project files unless they are the tenant/org from `uip login status`
7. **Sanitize sample prompts.** Apply rules 1-3 and 6 to every captured prompt before including it under `## Sample prompts`. Replace customer names, email addresses, project codenames, account IDs, ticket IDs, internal URLs, and file paths revealing usernames with `<REDACTED>`. If a prompt cannot be sanitized without losing its signal (the prompt is mostly customer-specific data), drop that prompt and pick another from Step 2e. Never quote a prompt verbatim if it contains a secret, even if the user typed it.
8. **Sanitize Step 2h answers.** Apply rules 1-3 and 6 to the user's Expected/Actual text before quoting it in `## What happened`. If it can't be sanitized without losing its meaning, fall back to the agent's own summary instead of quoting a stripped-down version — don't ask the user to rephrase.

## What NOT to Do

1. **Do not ask questions you already know the answer to.** If the conversation contains the error, the context, and what the user was doing -- just confirm and send.
2. **Do not include raw conversation dumps.** `## What happened` is a 2-3 sentence summary (or the user's own Step 2h answer, quoted). `## Sample prompts` is a relevance-filtered selection per Step 2e — not a transcript.
3. **Do not send without confirmation.** Always preview first.
4. **Do not include secrets, credentials, or PII.** When in doubt, redact.
5. **Do not attach unsanitized files.** Always strip sensitive content before attaching.
6. **Do not retry after user says "no".** Respect the decision. Ask if they want to adjust something or cancel entirely.
7. **Do not modify the user's description without showing them.** The preview is the contract.
8. **Do not send duplicate feedback.** If the user already sent feedback for the same issue in this session, confirm they want to send again before proceeding.
9. **Do not use numbered lists as section headers.** Sections MUST use `## Header` format. Writing `1. What happened  2. Error  3. Environment` produces unreadable Jira issues.
10. **Do not put the user email in the description body.** Pass it only via the `--email` flag. Including it in the description violates sanitization rule #6.
11. **Do not pad Sample Prompts or the Session retrospective to hit a quota.** "3-5 prompts" and "5 retrospective questions" describe ceilings, not targets. Omitting a section, or a bullet within one, is the expected and normal outcome when nothing relevant clears the bar in Step 2e/2f — not a gap to patch with topical-but-irrelevant or generic filler. A report that's shorter because a section had nothing to say is a *better* report, not an incomplete one.
12. **Do not treat Step 2h as mandatory or re-ask it if declined.** It exists so the user can phrase Expected/Actual in their own words when they want to — a skipped answer is a complete, valid input, not a stalled report.
