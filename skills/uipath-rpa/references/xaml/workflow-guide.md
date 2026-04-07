# XAML Workflow Guide

Discovery-first approach with iterative error-driven refinement for generating and editing XAML workflows. Always understand before acting, start simple, and validate continuously.

## Core Principles

1. **Activity Docs Are the Source of Truth** — Installed packages may ship structured documentation at `{projectRoot}/.local/docs/packages/{PackageId}/`. When present, these docs contain source-accurate properties, types, defaults, enum values, conditional property groups, and working XAML examples. Always check for them first.
2. **Know Before You Write** — Never generate XAML blind. Understand the project structure, packages, expression language, and existing patterns.
3. **Use What You Know, Skip What You Don't Need** — If you already know the package ID and activity class name, go directly to its doc file. Be efficient: the discovery steps are a priority ladder, not a mandatory checklist.
4. **Start Minimal, Iterate to Correct** — Build one activity at a time. Write the smallest working XAML, validate with `uip rpa get-errors --use-studio`, fix what breaks, repeat.
5. **Validate After Every Change** — Never assume an edit succeeded. Always confirm with `uip rpa get-errors --use-studio`.
6. **Fix Errors by Category** — Triage in order: Package → Structure → Type → Activity Properties → Logic.

---

## Core Workflow: Classify Request

| Request Type | Trigger Words | Action |
|--------------|---------------|--------|
| **CREATE** | "generate", "create", "make", "build", "new" | Discovery → Generate |
| **EDIT** | "update", "change", "fix", "modify", "add to" | Discovery → Edit |

If unclear which file to edit, **ask the user** rather than guessing.

---

## Phase 1: Discovery

**Goal:** Understand project context, leverage installed activity documentation, study existing patterns, identify reusable components, and discover activities before writing any XAML.

### Step 1.1: Project Structure

```
Glob: pattern="**/*.xaml" path="{projectRoot}"       → list all XAML workflow files
Read: file_path="{projectRoot}/project.json"          → read the project definition
```

Analyze:
- Where should new workflows be placed? (folder conventions)
- What naming pattern is used?
- What similar workflows already exist?
- VB or C# syntax? (check `expressionLanguage` in `project.json`)
- What packages are already installed?
- Are there existing connections, credentials, or objects to reuse?

### Step 1.2: Discover Activity Documentation (Primary Source)

**This is the most important discovery step.** Installed activity packages ship structured markdown at `{projectRoot}/.local/docs/packages/{PackageId}/`.

**Availability:** Docs exist only for **installed packages** and typically only for **newer package versions**. When the package is not installed, install it first. When docs are missing, update to the latest version.

#### Filesystem Structure

```
{projectRoot}/.local/docs/packages/
+-- {PackageId}/
    +-- overview.md
    +-- activities/
    |   +-- {ActivitySimpleClassName}.md
    +-- coded/                             # Ignore for XAML workflows
```

#### Activity Doc Template

Every `activities/{ActivityName}.md` follows: Header → Metadata → Properties (Input, Output, Conditional groups, Common) → Valid Configurations → Enum Reference → XAML Examples → Notes.

#### Decision Table

| Situation | Action |
|-----------|--------|
| **Know package + activity name** | `Read: file_path="{projectRoot}/.local/docs/packages/{PackageId}/activities/{ActivityName}.md"` |
| **Know package, not activity** | `Read` the `overview.md`, then read the identified activity doc |
| **Don't know package** | `Glob` with `**/*.md` in `{projectRoot}/.local/docs/packages/`. `.local/` is gitignored — use `Glob` + `Read`, not `Grep` |
| **Docs exist but activity undocumented** | Use other docs as structural reference, fall back to `get-default-activity-xaml` |
| **No docs for package** | Update the package first — this often adds docs. If still none, fall back to Steps 1.4-1.7 |
| **Package not installed** | Install it first — both docs and `get-default-activity-xaml` require it |
| **No `.local/docs/` at all** | Use fallback flow starting at Step 1.3 |

### Step 1.3: Search Current Project

Search existing workflows for reusable patterns and conventions.

```
Glob: pattern="**/*pattern*.xaml" path="{projectRoot}"
Grep: pattern="ActivityName|pattern" path="{projectRoot}"
Read: file_path="{projectRoot}/ExistingWorkflow.xaml"
```

- **Mature project**: Prioritize local patterns.
- **Greenfield project**: Skip this step.

### Step 1.4: Discover Activities (When Needed)

Use when you need to find which activity implements a user-described action:

```bash
uip rpa find-activities --query "send mail" --limit 10 --output json --use-studio
```

- Results are **global** — not limited to installed packages
- If a useful activity is in an uninstalled package, install it immediately
- Tags can narrow results further

### Step 1.5: Disambiguate Approach and Provider

#### Approach-level (API vs UI Automation vs Connector)

- **Auto-select** when the user stated the approach or only one is viable
- **Prompt** when multiple approaches are viable and user hasn't indicated preference
- **Do NOT install packages until approach is confirmed**

#### Provider-level (within an approach)

**Auto-select** when: user specified provider, only one package matches, project already has the package installed, project defines a matching connection, or workflow already uses activities from one package.

**Prompt only as last resort** — present top 2-4 choices with recommendations.

### Step 1.6: Resolve Activity Properties (Fallback)

Use `uip rpa get-default-activity-xaml --use-studio` when activity docs are insufficient:

```bash
# Non-dynamic activity:
uip rpa get-default-activity-xaml --activity-class-name "<FULLY_QUALIFIED_CLASS>" --output json --use-studio

# Dynamic activity (connector-backed):
uip rpa get-default-activity-xaml --activity-type-id "<TYPE_ID>" --connection-id "<CONN_ID>" --output json --use-studio
```

For JIT custom types: `Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"`. See [jit-custom-types-schema.md](jit-custom-types-schema.md).

### Step 1.7: Search Examples Repository

Use when activity docs, `find-activities`, and `get-default-activity-xaml` don't provide enough context:

```bash
uip rpa list-workflow-examples --tags web --limit 10 --output json --use-studio
uip rpa get-workflow-example --key "<BLOB_PATH>" --use-studio
```

**Complete tag list:** `adobe-sign`, `asana`, `box`, `concur`, `confluence`, `database`, `document-understanding`, `docusign`, `dropbox`, `email-generic`, `excel`, `excel-online`, `freshbooks`, `freshdesk`, `github`, `gmail`, `google-calendar`, `google-docs`, `google-drive`, `google-sheets`, `gsuite`, `hubspot`, `intacct`, `jira`, `mailchimp`, `marketo`, `microsoft-365`, `onedrive`, `outlook`, `outlook-calendar`, `pdf`, `powerpoint`, `productivity`, `quickbooks`, `salesforce`, `servicenow`, `sharepoint`, `shopify`, `slack`, `smartsheet`, `stripe`, `teams`, `testing`, `trello`, `web`, `webex`, `word`, `workday`, `zendesk`, `zoom`

### Step 1.8: Get Current Context (As Needed)

```
Read: file_path="{projectRoot}/project.json"
Glob: pattern="**/*" path="{projectRoot}/.objects/"
Bash: uip is connections list --output json
```

### Step 1.9: Discover Connector Capabilities (For IS/Connector Workflows)

See [../connector-capabilities.md](../connector-capabilities.md) for the full procedure.

---

## Phase 2: Generate or Edit

### UI Automation — Target Configuration Gate

Before writing any XAML with UI activities, every UI element target must be configured through the `uia-configure-target` skill flow. See [uia-configure-target-workflows.md](../uia-configure-target-workflows.md).

Do NOT manually call low-level `uip rpa uia` CLI commands outside of the skill flow. Do NOT launch the target application before running `uia-configure-target`.

### For CREATE Requests

**Strategy:** Generate minimal working version, one activity at a time, validate frequently.

Use the `Write` tool to create a new `.xaml` file. Refer to [xaml-basics-and-rules.md](xaml-basics-and-rules.md) for the complete XAML file anatomy template.

```
Write: file_path="{projectRoot}/Workflows/DescriptiveName.xaml"
       content=<valid XAML content>
```

**File path inference:** Use folder conventions from project structure, create descriptive filenames, ensure `.xaml` extension.

### For EDIT Requests

**Strategy:** Always read current content before editing.

```
Read: file_path="{projectRoot}/WorkflowToEdit.xaml"
Edit: file_path=... old_string=<exact text> new_string=<modified text>
```

**Critical:** `old_string` must match exactly and be unique. Include surrounding context if needed.

---

## Phase 3: Validate & Fix Loop

Repeats until 0-error state or errors cannot be resolved automatically.

### Step 3.1: Check for Errors

```bash
uip rpa get-errors --file-path "Workflows/MyWorkflow.xaml" --output json --use-studio
```

`--file-path` must be **relative to the project directory**. Use `--skip-validation` only for quick cached-error checks.

### Step 3.2: Categorize and Fix

**Fix order:** Package → Structure → Type → Activity Properties → Logic.

1. **Package Errors** — Install/update the package. After install, activity docs become available.
2. **Structural Errors** — Fix XML structure. Cross-check against [xaml-basics-and-rules.md](xaml-basics-and-rules.md).
3. **Type Errors** — Check activity doc for correct types and enum values. For JIT types: [jit-custom-types-schema.md](jit-custom-types-schema.md).
4. **Activity Properties Errors** — Read activity doc for properties, conditional groups, valid configurations. Fallback: `get-default-activity-xaml`. Watch for OverloadGroup conflicts.
5. **Logic Errors** — Verify expression syntax matches project language. For UI automation: use `--command StartDebugging`. See [uia-debug-workflow.md](../uia-debug-workflow.md).

**When stuck:** Defer to user for minor config details. If failing to resolve an activity, consider InvokeCode as a last resort.

For detailed procedures, see [../validation-guide.md](../validation-guide.md).

---

## Phase 4: Response

1. **File path** of created/edited workflow
2. **Brief description** of what the workflow does
3. **Key activities** and logic implemented
4. **Packages installed** (if any)
5. **Limitations** or notes
6. **Suggested next steps** (testing, parameterization)
7. **Encourage user to review and customize** (fill placeholders, set up connections)

---

## Anti-Patterns

- Generate large, complex workflows in one go
- Manually craft UI selectors outside of `uia-configure-target` skill flow
- Assume a create/edit succeeded without validating
- Stop the iteration loop before correctly rendering all activities
- Guess properties, types, or configurations without checking docs
- Use incorrect keys with `uip rpa get-workflow-example` (always from list results)
- Pass absolute paths to `--file-path` in `get-errors` (must be relative)
- Ask user to choose provider without checking project signals first
- Retry failing CLI commands in a loop without diagnosing root cause
- Skip Phase 0 (Studio readiness)
- Use connector activities without checking connection existence
- Ignore activity doc conditional property groups (OverloadGroup conflicts cause validation errors)
- Generate full XAML from scratch without using `get-default-activity-xaml` as a starting point
