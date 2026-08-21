# Classification Details — uipath-feedback

**Classification: Strong**

---

## What the Skill Teaches

Submit structured bug reports or improvement suggestions to UiPath using `uip feedback send`, with auto-captured environment context, area detection, session retrospective, sanitization, and description templating.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | **Area detection from last command or working directory** | **Yes — DETECT** | Fixed lookup table mapping command/signal → area tag |
| 2 | **Environment capture (version, login status, tools)** | **Yes — EXTRACT** | Fixed set of commands: `uip --version`, `uip login status --output json`, `uip tools list` |
| 3 | **Skill-specific troubleshooting capture (per-area rules)** | **Yes — EXTRACT** | Fixed per-area table specifying what to capture and line/entry limits |
| 4 | **Type and priority auto-detection** | **Yes — DETECT** | Fixed signal-to-type and signal-to-priority tables with explicit defaults |
| 5 | **Description body templating** | **Yes — FORMAT-CONVERT** | Fixed section structure with exact header names, field slots, and formatting rules |
| 6 | **Sanitization** | **Yes — VALIDATE/CHECK** | Seven explicit rules: strip secrets, redact PII in paths, redact GUIDs, truncate, exclusions |
| 7 | **Send via `--description-file` pattern** | **Yes — TRANSFORM-PIPELINE** | Write to temp file → invoke CLI with `--description-file` → parse JSON result → report |
| 8 | Session retrospective authoring (5 structured questions) | No | Requires judgment to synthesize session observations into concise answers |

---

## Codifiable Procedures (not yet scripted)

### 1. Area Detection — DETECT

**Source:** `skills/uipath-feedback/SKILL.md` §Workflow → Step 2 → 2a. Detect the area

**What it does:** The skill provides a lookup table mapping the last `uip <verb>` command (or working directory signals) to an area tag used in the report title and Jira labels. Inputs are the last identifiable CLI command or file in the working directory; output is a string from a fixed set (`RPA`, `Flow`, `BPMN`, `Case`, `Agents`, `CodedApps`, `ApiWorkflow`, `DataFabric`, `Solution`, `Test`, `Tasks`, `Admin`, `Governance`, `Platform`). The table covers 13 explicit mappings and one catch-all. Line 45 (table header): "The **area** (which product) becomes the title tag and a Jira label for filtering. Identify it from the last `uip <verb>` the user ran in this conversation."

**Why it's mechanical:** The mapping table is complete and closed; the fallback rule ("anything else → Platform") handles the catch-all with no judgment required.

**Turn savings:** Without a script the agent scans the conversation manually for the last command; a script that accepts the last command string and returns the area tag collapses this to one deterministic call.

---

### 2. Environment and Context Capture — EXTRACT

**Source:** `skills/uipath-feedback/SKILL.md` §Workflow → Step 2 → 2b. Capture environment, 2c. Capture skill-specific troubleshooting, 2d. Capture the failing command

**What it does:** Step 2b prescribes three fixed commands: `uip --version 2>&1`, `uip login status --output json 2>&1`, `uip tools list 2>&1`. From the login status output, only three fields are extracted: `tenantName`, `organizationName`, `baseUrl`. Step 2c maps each area to a specific set of capture commands and size limits (e.g., Flow: `uip maestro flow validate <file> --output json` + `.flow` file first 150 lines + directory max 30 entries). Step 2d captures the last failing command with stderr/stdout truncated to 100 lines. Line 87 (table row): "**Flow** | `uip maestro flow validate <file> --output json`, `.flow` file content, directory listing | `.flow`: first 150 lines; directory: max 30 entries"

**Why it's mechanical:** The commands, the field extraction list, and the size limits are all enumerated in tables with no judgment required.

**Turn savings:** The agent currently runs each capture command as a separate turn and manually enforces line limits; a capture script that accepts the detected area and runs all relevant commands with limit enforcement compresses the entire capture phase to one call.

---

### 3. Type and Priority Auto-detection — DETECT

**Source:** `skills/uipath-feedback/SKILL.md` §Workflow → Step 2 → 2g. Auto-detect type and priority

**What it does:** The skill provides two lookup tables. The type table maps conversation signals to `bug` (default for error messages, crashes, "doesn't work", runtime failures) or `improvement` (feature requests, "would be nice", skill misguidance). The priority table maps signals to `critical` (complete block, data loss, stack trace crash), `normal` (default for working-but-broken cases), or `minor` (cosmetic, low-impact). Both default on ambiguity. Line 128: "**Type** — determine from conversation signals:" followed by the signal table.

**Why it's mechanical:** Both tables have explicit signal keywords and defaults for ambiguity; the classification requires no judgment beyond keyword matching.

**Turn savings:** A detector script that scans the conversation for signals and emits (type, priority) eliminates the need for the agent to reason through the tables each time.

---

### 4. Description Body Templating — FORMAT-CONVERT

**Source:** `skills/uipath-feedback/SKILL.md` §Workflow → Step 3 → Description body

**What it does:** The skill prescribes a fixed description template with mandatory sections (`## What happened`, `## Sample prompts`, `## Error`, `## Environment`, `## Troubleshooting`, `## Session retrospective`), exact header format (`## ` with blank lines before and after), bullet style (`-`), and numbering format. Eight explicit formatting rules govern the output. The environment section has fixed slots: Area, uip version, CLI tools, OS, Tenant. Line 215: "1. Use `## ` (two hashes + space) for EVERY section header. NEVER use numbered lists, letters, or bold text as section separators. 2. Use the EXACT section names from the template above."

**Why it's mechanical:** The template structure, section names, and formatting rules are fixed; building the description body from captured data is a fill-in-the-slots operation.

**Turn savings:** Without a script the agent assembles the description over multiple steps; a templating script that accepts captured fields and emits the formatted body compresses description assembly to one invocation.

---

### 5. Sanitization — VALIDATE/CHECK

**Source:** `skills/uipath-feedback/SKILL.md` §Sanitization Rules

**What it does:** Before any content enters the description or attachments, seven rules apply: (1) strip lines matching secret-keyword patterns, (2) replace home directory prefixes with `~` and usernames in paths with `<USER>`, (3) redact GUIDs in connection/binding fields with `<REDACTED>`, (4) truncate files over 150 lines (keep first 100 + marker + last 30) and cap the full description at 4000 characters, (5) exclude specific files (`~/.uipath/.auth`, `.env`, `.git/config`, env vars with secrets), (6) strip customer data, (7) sanitize sample prompts with the same rules. Line 363: "Apply these rules to ALL content before it is included in the description or attachments."

**Why it's mechanical:** All seven rules specify exact patterns, replacement strings, size limits, and file exclusions with no judgment required.

**Turn savings:** The agent currently applies sanitization manually per piece of content; a sanitize script that accepts raw content and applies all seven rules deterministically eliminates per-turn sanitization reasoning.

---

## Justification for Classification

**Strong** — not Partial, not None.

**Why not Partial:** Seven of eight teaching areas are codifiable. Only the session retrospective (synthesizing session observations into structured answers) requires genuine judgment. Every other step — area detection, environment capture, type/priority classification, description templating, sanitization, and the send pipeline — is a deterministic rule-driven procedure with explicit tables, fixed templates, and stated size limits.

**Why not None:** Five distinct codifiable procedure types exist in the skill: DETECT (area and type/priority tables), EXTRACT (environment capture), FORMAT-CONVERT (description template), VALIDATE/CHECK (sanitization rules), and TRANSFORM-PIPELINE (write-to-tempfile → send → parse → report).

**Evidence locations:**
- Area detection table: `SKILL.md` §Step 2a (lines 45–63)
- Environment capture: `SKILL.md` §Step 2b–2d (lines 73–99)
- Type/priority detection: `SKILL.md` §Step 2g (lines 127–145)
- Description template + formatting rules: `SKILL.md` §Step 3 (lines 179–222)
- Sanitization rules: `SKILL.md` §Sanitization Rules (lines 362–370)
- Send pipeline (--description-file pattern): `SKILL.md` §Step 4 (lines 299–327)
