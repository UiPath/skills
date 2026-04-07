---
name: uipath-feedback
description: "Send bug reports or improvement suggestions to UiPath via uip feedback send. TRIGGER: 'report issue', 'feedback', 'something is wrong', /uipath-feedback."
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
user-invocable: true
---

# UiPath Feedback

Send structured bug reports or improvement suggestions to UiPath with auto-captured diagnostics via `uip feedback send`.

> **Design principle: minimum friction.** The agent already knows what went wrong from the conversation. Don't re-ask what you already know. The only mandatory interaction is confirmation before sending.

## Critical Rules

1. **Minimum user interaction.** If the conversation already contains enough context (error, what the user was doing, what went wrong), go straight to confirm and send. Only ask clarifying questions when you genuinely cannot determine what happened.
2. **Never send without explicit user confirmation.** Always show a preview and wait for "yes".
3. **Never include secrets, tokens, credentials, or customer data.** Sanitize all captured content before sending.
4. **Never include full conversation history.** Summarize the relevant context in 2-3 sentences.
5. **Use `--output json`** on `uip feedback send` to parse the result programmatically.
6. **If `uip feedback send` fails**, save the report to `./feedback-report.md` so the user does not lose the gathered context.

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

### Step 2 -- Introspect and capture (silent -- no user interaction)

Gather all context automatically. Run these substeps silently.

#### 2a. Detect skill context

Check the current working directory. Stop at first match:

| Check | Skill context |
|---|---|
| `*.flow` file exists | **Flow** |
| `pyproject.toml` with `uipath` dependency | **Agents** |
| `project.json` + `*.cs` and/or `*.xaml` files | **RPA** |
| `package.json` + `.uipath/` directory | **Apps** |
| None of the above | **Platform** |

If ambiguous, infer from the conversation. Do NOT ask the user -- pick the best match.

#### 2b. Capture environment

```bash
uip --version 2>&1
uip login status --output json 2>&1
```

From login status, extract only: `tenantName`, `organizationName`, `baseUrl`. Strip everything else.

#### 2c. Capture skill-specific diagnostics

| Skill context | What to capture | Limits |
|---|---|---|
| **Flow** | `uip flow validate <file> --output json`, `.flow` file content, directory listing | `.flow`: first 150 lines; directory: max 30 entries |
| **RPA** (`.cs` or `.xaml`) | `project.json` dependencies, `uip rpa get-errors --output json --use-studio`, list of workflow files (`.cs` and/or `.xaml`) | File list: max 20 files; `project.json`: dependencies section only; failing workflow: first 150 lines |
| **Agents** | `pyproject.toml`, `bindings.json` (redact connection values), directory listing | `bindings.json`: redact all values; directory: max 30 entries |
| **Apps** | `package.json` (name, version, dependencies only), `.uipath/` listing | `package.json`: name + version + dependencies only |
| **Platform** | `uip login status --output json` output only | Strip tokens from output |

#### 2d. Capture the failing command

Review the current conversation for the last CLI command that failed. If identifiable, capture:
- The full command
- Its stderr/stdout output (truncated to 100 lines)

If not identifiable, skip this section.

#### 2e. Session retrospective

Review the full conversation and produce a structured self-assessment. This is the most valuable part of the feedback -- it gives triagers context no manual bug report can provide.

Answer each question concisely (1-3 sentences each). Reference actual tool names, errors, commands, and files from this session.

1. **Intent**: What was the user trying to build/edit/fix? Was the goal clear from the start?
2. **Outcome**: What was delivered vs. requested? Full / Partial / Failed.
3. **Tool & Skill Gaps**: Which tools or CLI commands were called but unhelpful? Which should have been called but weren't? Any failures or workarounds?
4. **Friction**: Where did the agent get stuck, retry, or misunderstand UiPath conventions? How many generate-validate-fix cycles?
5. **Top 3 Improvements**: What skill/tool changes would have had the biggest impact on this session?

#### 2f. Auto-detect type and priority

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

#### 2g. Sanitize everything

Apply all rules from the [Sanitization Rules](#sanitization-rules) section below to every piece of captured content before proceeding.

#### 2h. Only if context is insufficient

If the agent genuinely cannot determine what happened (e.g., user typed `/uipath-feedback` with no prior context in the conversation), ask **one** structured question:

> I'll send feedback to UiPath. Please tell me:
> 1. **What were you trying to do?**
> 2. **What happened?**
> 3. **Is this a bug or an improvement suggestion?**

Otherwise, skip directly to Step 3.

### Step 3 -- Build and confirm (only user interaction)

#### Title format

```
[Product] short description
```

Product names:

| Skill context | Title prefix |
|---|---|
| Flow | `[Flow]` |
| RPA | `[RPA]` |
| Agents | `[Agents]` |
| Apps | `[Apps]` |
| Platform | `[Platform]` |
| Servo | `[Servo]` |

#### Description body

Build the `--description` content:

```
## What happened
{User's problem -- in their own words or summarized from conversation}

## Error
{The actual error message or validation output -- if available, otherwise omit this section}

## Environment
- Skill context: {detected skill name}
- uip version: {version}
- OS: {os info}
- Tenant: {tenant} ({org})

## Diagnostics
- Project type: {detected type}
- Key files: {list of relevant project files found}
- Last failed command: {command + truncated output}

## Session retrospective
- **Intent**: {what the user was trying to do}
- **Outcome**: {Full | Partial | Failed -- what was delivered vs requested}
- **Tool & Skill Gaps**: {tools/commands that failed, were missing, or needed workarounds}
- **Friction**: {where the agent got stuck, retried, or misunderstood conventions}
- **Top 3 Improvements**: {specific skill/tool changes that would have helped most}
```

Truncate the full description to 4000 characters max. Note if content was truncated.

#### Prepare attachments

Write sanitized copies of relevant project files to a temp directory:

```bash
mkdir -p "${TMPDIR:-${TMP:-/tmp}}/uip-feedback-attachments"
```

Copy and sanitize files based on skill context:
- Flow: the `.flow` file
- RPA: `project.json`, the failing workflow file (`.cs` or `.xaml`)
- Agents: `pyproject.toml`, `bindings.json` (redacted)
- Apps: `package.json`

Max 10 files, max 10MB each. Skip files that exceed limits.

#### Show preview and confirm

Display to the user:

```
**Type:** bug
**Priority:** normal
**Title:** [Flow] Expression error in nested loop currentItem
**Description:** (first 3 lines...)
**Attachments:** MyFlow.flow, project.json

Send this to UiPath? (yes/no)
```

The user can adjust type, priority, or title before confirming. **Never send without explicit "yes".**

### Step 4 -- Send feedback

```bash
uip feedback send \
  --type "<bug|improvement>" \
  --title "<TITLE>" \
  --description "$(cat <<'FEEDBACK_EOF'
<DESCRIPTION_BODY>
FEEDBACK_EOF
)" \
  --priority "<critical|normal|minor>" \
  --attachment <FILE1> <FILE2> \
  --output json
```

If an email is available from `uip login status`, include `--email "<EMAIL>"`.

Parse the JSON output. On success, show the user a confirmation with any reference ID returned.

**Fallback:** If `uip feedback send` fails (network, auth, CLI error), save the full feedback to `./feedback-report.md` using the description body and tell the user: _"Could not send automatically. The report is saved to `feedback-report.md`."_

Clean up temp attachments:

```bash
rm -rf "${TMPDIR:-${TMP:-/tmp}}/uip-feedback-attachments"
```

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

Always clean up temp attachments regardless of success or failure.

## Sanitization Rules

Apply these rules to ALL content before it is included in the description or attachments:

1. **Strip secrets.** Remove lines matching (case-insensitive): `token`, `secret`, `password`, `apiKey`, `credentials`, `authorization`, `Bearer`, `client_secret`, `connection_string`
2. **Redact PII in paths.** Replace home directory prefixes with `~` (e.g., `C:\Users\john.doe\projects\` -> `~/projects/`). Replace usernames in URLs or paths with `<USER>`
3. **Redact GUIDs** in connection/binding fields: replace values with `<REDACTED>`
4. **Truncate long content.** Files over 150 lines: keep first 100 + `... [truncated N lines] ...` + last 30. Full description: max 4000 characters
5. **Never include**: `~/.uipath/.auth`, `.env`, `.git/config`, environment variables containing secrets, full conversation history
6. **Never include customer data.** Strip customer names, email addresses, and organization-specific identifiers from project files unless they are the tenant/org from `uip login status`

## What NOT to Do

1. **Do not ask questions you already know the answer to.** If the conversation contains the error, the context, and what the user was doing -- just confirm and send.
2. **Do not include raw conversation dumps.** Summarize in 2-3 sentences.
3. **Do not send without confirmation.** Always preview first.
4. **Do not include secrets, credentials, or PII.** When in doubt, redact.
5. **Do not attach unsanitized files.** Always strip sensitive content before attaching.
6. **Do not retry after user says "no".** Respect the decision. Ask if they want to adjust something or cancel entirely.
7. **Do not modify the user's description without showing them.** The preview is the contract.
8. **Do not send duplicate feedback.** If the user already sent feedback for the same issue in this session, confirm they want to send again before proceeding.
