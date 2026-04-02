---
name: uipath-report-issue
description: "Report a skill issue with auto-captured context. TRIGGER when: user says 'report issue', 'report bug', 'something is wrong', 'file a bug', 'this isn't working', 'skill bug', or invokes /report-issue. DO NOT TRIGGER when: user is asking a question, requesting help, or describing expected behavior."
metadata:
  allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

# UiPath Skill Issue Reporter

Files a structured GitHub Issue on [UiPath/skills](https://github.com/UiPath/skills) with auto-captured diagnostics. Works with all UiPath skills.

> **Design goal: 2 user interactions.** Ask → Confirm → Filed. The agent handles detection, capture, and formatting silently.

## Workflow

### Step 1 — Check `gh` CLI

```bash
gh auth status 2>&1
```

| Result | Action |
|---|---|
| `Logged in to github.com` | Proceed |
| `gh: command not found` | Tell user: **"Install GitHub CLI first: `brew install gh` (macOS) or https://cli.github.com — then `gh auth login`."** Stop. |
| Auth error | Tell user: **"Run `gh auth login` to authenticate with GitHub."** Stop. |

### Step 2 — Gather user input (interaction 1 of 2)

Ask the user **one structured question**:

> I'll file a bug report on GitHub. Please tell me:
> 1. **What were you trying to do?** (e.g., "create a flow with a Jira connector")
> 2. **What happened?** (e.g., "validate failed with 'missing targetPort'")
> 3. **What error did you see?** (paste the error message if you have it)

If the user's response is vague (e.g., "it broke"), follow up **once** with: "Can you paste the error message or describe which step failed?"

Also determine the **issue type** from the user's description:

| Type | Signals | Label |
|---|---|---|
| **Wrong instructions** | "skill told me to do X but it was wrong", "the JSON example is broken" | `skill-content` |
| **Missing CLI command** | "there's no command for X", "CLI doesn't support Y" | `cli-gap` |
| **Expression/runtime error** | "expression failed", "Jint error", "script node crashed" | `expression-error` |
| **Bug** (default) | Everything else | `bug` |

### Step 3 — Auto-detect and capture (silent — no user interaction)

#### 3a. Detect skill context

Check the current working directory. Stop at first match:

1. `*.flow` exists → **Flow**
2. `pyproject.toml` with `uipath` dependency → **Agents**
3. `project.json` + `*.cs` files → **Coded Workflows**
4. `project.json` + `*.xaml` files → **RPA Workflows**
5. `package.json` + `.uipath/` directory → **Apps**
6. None of the above → **Platform**

If ambiguous, infer from the user's description. Do NOT ask — pick the best match.

#### 3b. Capture environment

```bash
uip --version 2>&1
uip login status --output json 2>&1
uname -s -r
```

Extract from login status: `tenantName`, `organizationName`, `baseUrl` only. **Strip tokens, secrets, keys.**

#### 3c. Capture skill-specific diagnostics

| Skill | Capture |
|---|---|
| **Flow** | `uip flow validate <file> --output json`, `.flow` file content (first 150 lines), project directory listing |
| **Coded Workflows** | `project.json` dependencies section, `uip rpa validate` output, list of `.cs` files |
| **RPA Workflows** | `project.json` dependencies section, `uip rpa get-errors` output, list of `.xaml` files |
| **Agents** | `pyproject.toml`, `bindings.json` (redact connection values), directory listing |
| **Apps** | `package.json` (name, version, dependencies only), `.uipath/` listing |
| **Platform** | `uip login status` output only |

#### 3d. Capture the failing command

Look in the current conversation for the last CLI command that failed. If identifiable, include:
- The full command
- Its stderr/stdout output

If not identifiable, skip this section.

#### 3e. Sanitize everything

Before including any content in the issue:

1. **Remove lines** containing: `token`, `secret`, `password`, `apiKey`, `credentials`, `authorization`, `Bearer`
2. **Redact GUIDs** in `bindings_v2.json` connection fields → `<REDACTED>`
3. **Truncate** files over 150 lines: first 100 + `... [truncated N lines] ...` + last 30
4. **Never include**: `~/.uipath/.auth`, `.env` files, environment variables with secrets

### Step 4 — Build and confirm (interaction 2 of 2)

#### Title format

```
[Product] type: short description
```

**Product names** (user-friendly, not package names):

| Skill detected | Title prefix |
|---|---|
| uipath-maestro-flow | `[Flow]` |
| uipath-coded-workflows | `[Coded Workflows]` |
| uipath-rpa-workflows | `[RPA Workflows]` |
| uipath-coded-agents | `[Agents]` |
| uipath-coded-apps | `[Apps]` |
| uipath-platform | `[Platform]` |
| uipath-servo | `[Servo]` |

**Type in title:**

| Label | Title example |
|---|---|
| `skill-content` | `[Flow] skill-content: wrong JSON example for subflow variables` |
| `cli-gap` | `[Flow] cli-gap: no command to remove nodes` |
| `expression-error` | `[Flow] expression-error: $vars.loop.currentItem undefined in nested loop` |
| `bug` | `[RPA Workflows] bug: validate passes but Studio rejects generated XAML` |

#### Issue body template

```markdown
## What happened

{User's description — in their own words, lightly edited for clarity}

## Error

```
{The actual error message or validation output — if available}
```

## Environment

| | |
|---|---|
| **Skill** | {skill name} |
| **uip** | {version} |
| **OS** | {os} |
| **Tenant** | {tenant} ({org}) |

## Context

<details>
<summary>Project structure</summary>

```
{directory listing}
```

</details>

<details>
<summary>Relevant files</summary>

```json
{sanitized file content — .flow, project.json, pyproject.toml, etc.}
```

</details>

<details>
<summary>Last command</summary>

```bash
{the command that failed}
```

```
{its stderr/stdout}
```

</details>
```

> **Keep it short.** The issue should be scannable in 30 seconds. The description and error tell the story. If the triager needs more, they'll ask on the issue.

#### Show the user a preview

Display:
1. **Title**: the formatted title
2. **Error captured**: yes/no and a one-liner
3. **Files included**: list of file names that will be attached (not content)
4. **Ask**: "File this issue on UiPath/skills? (yes/no)"

> **NEVER file without explicit confirmation.**

### Step 5 — File the issue

```bash
gh issue create --repo UiPath/skills \
  --title "{TITLE}" \
  --label "{TYPE_LABEL},{SKILL_LABEL}" \
  --body "$(cat <<'ISSUE_EOF'
{ISSUE_BODY}
ISSUE_EOF
)"
```

If labels don't exist, file without labels — `gh` will warn but succeed.

Show the user the **issue URL** after creation.

**Fallback:** If `gh issue create` fails (network, permissions), save the report to `./issue-report.md` and tell the user: "Couldn't file automatically. The report is saved to `issue-report.md` — you can paste it into a GitHub Issue manually."

## Labels

| Label | Color | Description |
|---|---|---|
| `bug` | `#d73a4a` | Something isn't working |
| `skill-content` | `#0075ca` | Wrong or missing skill instructions |
| `cli-gap` | `#e4e669` | Missing CLI command or option |
| `expression-error` | `#f9d0c4` | Jint expression or runtime issue |
| `uipath-maestro-flow` | `#1d76db` | Flow skill |
| `uipath-coded-workflows` | `#1d76db` | Coded Workflows skill |
| `uipath-rpa-workflows` | `#1d76db` | RPA Workflows skill |
| `uipath-coded-agents` | `#1d76db` | Agents skill |
| `uipath-coded-apps` | `#1d76db` | Apps skill |
| `uipath-platform` | `#1d76db` | Platform skill |
| `uipath-servo` | `#1d76db` | Servo skill |

## Rules

- **2 user interactions max** — ask what happened, confirm before filing. Everything else is silent.
- **Never file without confirmation**
- **Never include secrets, tokens, credentials, or customer data**
- **Never include full conversation history** — the error and context are enough
- **Never auto-assign or set milestone** — let maintainers triage
- **If `gh` fails**, save to local file as fallback
