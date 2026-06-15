# Environment Setup

**Goal:** Resolve the project root before any other operations.

## Studio Desktop vs headless Studio

`uip rpa` runs against a **headless Studio** by default (codename Helm — ships as the `UiPath.Studio.Helm.{Platform}` NuGet package, auto-launched the first time a command needs it). **Studio Desktop is not required** for the standard authoring loop — `init`, `run`, `debug start`, `validate`, `build`, `activities find`, `packages install`, the `uia` group (indication, capture, interaction), etc. all work headless.

Studio Desktop is only required for two interactive UI tools:
- `uip rpa files diff` — opens an interactive diff window in Studio's UI.
- `uip rpa focus-activity` — selects an activity in Studio's active workflow designer.

For these two, see [§ Edge case: requiring Studio Desktop](#edge-case-requiring-studio-desktop) below.

> **Coded UI automation caveat.** One non-interactive task also needs Studio Desktop: regenerating `ObjectRepository.cs` — the `Descriptors.*` class consumed by coded `uiAutomation.*` workflows. `uip rpa build` alone does NOT produce it; Studio Desktop reconciles the coded workflow against the Object Repository to generate it. A headless flow can author and validate coded UIA, but populating `Descriptors.*` requires a Studio Desktop pass. See [ui-automation-guide.md](ui-automation-guide.md) § Finding Descriptors.

> **First call is slow.** On a cold NuGet cache, the very first `uip rpa` invocation triggers a silent `dotnet restore` of the headless Studio package and may sit near-silent for 30–90 seconds (longer behind a slow feed). A heartbeat line every 15s confirms it's still working. The default shell timeout covers this; bump `timeoutSeconds` only behind a slow feed.

## Step 0.1: Establish Project Root

The `uip rpa` commands use `--project-dir` to target a specific project (defaults to current working directory). **If the current working directory is NOT the UiPath project root, all commands will fail or target the wrong project.**

**Resolution order** (use the first rule that matches):
1. **Explicit path** — The user provided a directory path → use it as-is.
2. **Project name reference** — The user mentioned a project by name → search for a folder with that name containing `project.json`.
3. **Fall back to current working directory** — If neither is given.

If the CWD is not the project root:
- Locate the project root by finding `project.json`: `Glob: pattern="**/project.json"`
- **Pass `--project-dir` explicitly** to every `uip rpa` command
- Store the project root path and use it consistently as `{projectRoot}`

## Step 0.2: Authentication (If Needed)

Some commands (IS connections, workflow examples, cloud features) require authentication:

```bash
uip login
```

If you encounter auth errors (401, 403, "not authenticated") during any phase, prompt the user to run `uip login` to authenticate against their UiPath Cloud tenant.

## Step 0.3: Creating a New Project

**ALWAYS use `uip rpa init`** — never write `project.json`, `project.uiproj`, or other scaffolding files manually.

**`init` always scaffolds XAML.** Regardless of flags, the templates produce XAML files: `BlankTemplate` → `Main.xaml`, `TestAutomationProjectTemplate` → `TestCase.xaml`, `LibraryProcessTemplate` → XAML library workflows. There is no flag that flips the scaffolding to coded.

**`--expression-language` is independent of coded vs XAML.** It controls VB vs C# syntax inside XAML activity expressions — not whether the project has `.cs` workflow files. Coded workflows (`.cs` with `[Workflow]` / `[TestCase]`) work fine in both `VisualBasic` and `CSharp` projects.

**To work in coded mode**, scaffold the project (always XAML), then add `.cs` workflow files following [coded/operations-guide.md § Add a Workflow File](coded/operations-guide.md#add-a-workflow-file-to-existing-project) and update `entryPoints` in `project.json`. The scaffolded `Main.xaml` / `TestCase.xaml` can stay alongside your `.cs` files — `.xaml` and `.cs` workflows coexist freely.

**First, decide which template to use** — see [§ Template selection](#template-selection) below **before** running any `init` command. Defaulting to `--template-id BlankTemplate` is correct only when the user did not name a template or domain pattern.

### For XAML Projects (default for new projects)

```bash
uip rpa init \
  --name "MyAutomation" \
  --location "/path/to/parent/directory" \
  --template-id "BlankTemplate" \
  --expression-language <VisualBasic|CSharp> \
  --target-framework <Windows|Portable> \
  --description "Automates invoice processing" \
  --output json
```

**Decide `--target-framework` and `--expression-language` before running — never omit them.** Both are immutable after creation; omitting `--target-framework` silently produces a **Windows** project. The placeholder shows the two new-project options (`Windows`, `Portable`). Windows - Legacy is a last resort (explicit ask or hard .NET 4.6.1 need) and is created/authored in **Legacy mode**, not via this command. Choose from runtime / host-OS signals per SKILL.md Common Rule 2a.

**Expression language:** Default `VisualBasic`. Use `CSharp` only when the user explicitly asks for C# expressions inside XAML activities.

**`--studio-dir`:** Optional. Headless Studio does not need it. Pass it only when you have explicitly forced Studio Desktop (`UIPATH_RPA_TOOL_USE_STUDIO=1`, or invoking `diff`/`focus-activity`) and Studio's auto-detection from the registry fails.

### For Coded Projects (only when the user explicitly requested coded)

Run the **same** `init` command as for an XAML project (above) — there is no separate coded form. After it scaffolds, add `.cs` workflow files per [coded/operations-guide.md § Add a Workflow File](coded/operations-guide.md#add-a-workflow-file-to-existing-project) and update `entryPoints` in `project.json`. The scaffolded `Main.xaml` / `TestCase.xaml` can stay — remove it only if the user explicitly asks for a coded-only project.

#### Parameters

| Parameter | Options | Default | Notes |
|-----------|---------|---------|-------|
| `--name` | Any string | (required) | Project folder name |
| `--location` | Directory path | (current dir) | Parent directory where project folder is created |
| `--template-id` | `BlankTemplate`, `LibraryProcessTemplate`, `TestAutomationProjectTemplate` | `BlankTemplate` | Project template |
| `--expression-language` | `VisualBasic`, `CSharp` | none — set explicitly | Expression syntax for XAML workflows. Immutable after creation |
| `--target-framework` | `Windows`, `Portable` (Cross-platform), `Legacy` (Windows - Legacy) | none — set explicitly (omitting → Windows) | .NET target framework. Immutable after creation. `Legacy` is a last resort for new projects (explicit ask or hard .NET 4.6.1 need only). Decide per Rule 2a |
| `--description` | Any string | (none) | Project description in project.json |

**Note:** `uip rpa init` may return `success: false` but still create the project files (partial success). If it fails, check whether the project directory and `project.json` were created before retrying.

### Template selection

Before running `init`, decide which template to use.

**1. Trigger keywords**

| User says... | Action |
|---|---|
| "REFramework", "ERP template", "SAP template", "based on X template", or any specific template name | Run `uip rpa templates search --query "<term>" --output json` (see § "Search and select" below) |
| "library", "library project" | Use `--template-id LibraryProcessTemplate` (built-in, no search) |
| "test project", "test automation" | Use `--template-id TestAutomationProjectTemplate` (built-in, no search) |
| Nothing template-related | Use `--template-id BlankTemplate` (default) |

**2. Search and select**

Run `uip rpa templates search --query "<term>" --output json`. Apply this rule against `Data[*]`, top-down:

- **User named a specific non-Official template** (e.g. "Enhanced REFramework", "Lite ReFrameWork", a specific package name) AND a `Marketplace` item's `title` or `packageId` substring-matches the user's specific qualifier ("Enhanced", "Lite", etc.) → ask the user (treat Official + that Marketplace item as candidates). Do NOT auto-pick.
- **Exactly one item with `source == "Official"`** AND user did not name a non-Official template → pick it. No user prompt.
- **Multiple `Official` items** → present candidates (`packageId`, `version`, `title`, `description`) and ask the user.
- **Zero `Official` items, ≥1 `Marketplace` item** → present and ask. Never silently pick a Marketplace template.
- **No results** → tell the user, then create with `--template-id BlankTemplate`.

**3. Create from package**

For Official/Marketplace templates, pass `--template-package-id` (and optionally `--template-package-version` — omit for latest) to `init`. When `--template-package-id` is set, `--template-id` is ignored.

### From a NuGet Template Package

Use when the user asks for a domain-specific template, references a specific template package by name, or wants to browse available templates.

**1. Search for available templates:**

```bash
uip rpa templates search --query "<SEARCH_TERM>" --output json
```

Does not require a project to be open. Returns a JSON array of `TemplateSearchResult` objects:

```json
[
  {
    "packageId": "UiPath.Template.SAPExample",
    "version": "2.0.0",
    "title": "SAP Automation Template",
    "description": "Pre-configured project for SAP GUI automation",
    "authors": "UiPath",
    "source": "https://feed.example.com/v3/index.json",
    "tags": ["SAP", "ERP"]
  }
]
```

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `--query` | string | (none) | Filter by name or description. Omit to list all |
| `--limit` | integer | 20 | Maximum results |
| `--include-prerelease` | flag | false | Include prerelease versions |

**2. Create from the chosen template:**

```bash
uip rpa init \
  --name "MySAPAutomation" \
  --location "/path/to/parent/directory" \
  --template-package-id "<PACKAGE_ID>" \
  --template-package-version "<VERSION>" \
  --target-framework <Windows|Portable> \
  --expression-language <VisualBasic|CSharp> \
  --output json
```

Pass `--target-framework` and `--expression-language` here too (Rule 2a) — a template package does not exempt you from the explicit-framework decision.

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `--template-package-id` | string | (none) | NuGet package ID from `templates search` results. **Overrides `--template-id` when set** |
| `--template-package-version` | string | (latest) | Omit to use the latest available version |

### After Creation

1. Open the project in Studio: `uip rpa project open --project-dir "/path/to/MyAutomation"`
2. **Read the scaffolded files** — the command generates starter files. Read them before making changes so you build on valid defaults
3. Proceed with the skill workflow using the new project root

> **Batch the post-`init` prerequisites.** Step 2 here, the analyzer-rules list (SKILL.md Rule 3), `packages install` for known-needed packages, and the first `activities find` all depend only on the project existing — emit them as parallel tool calls in one message, not one per turn. They share the warmed Studio host. See SKILL.md § Call Batching.

## Edge case: requiring Studio Desktop

Two `uip rpa` commands need a running Studio Desktop instance — they have UI side effects that Helm cannot render:

| Command | Why it needs Studio |
|---------|---------------------|
| `uip rpa files diff` | Opens an interactive diff window in Studio's UI; finishes when the user closes the window. |
| `uip rpa focus-activity` | Selects/highlights an activity in Studio's active workflow designer. |

When (and only when) you need to run one of these, ensure Studio Desktop is up:

```bash
uip rpa instances list --output json   # hidden diagnostic — confirms a Studio Desktop instance is running
uip rpa studio start --project-dir "{projectRoot}" --output json   # launches Studio Desktop if none is running
```

If `studio start` cannot resolve Studio's install directory from the registry, pass `--studio-dir` pointing to the Studio installation root.

You can also force Studio Desktop for any other command by setting `UIPATH_RPA_TOOL_USE_STUDIO=1`, but this is not needed for the standard authoring loop and gives up the headless benefits.
