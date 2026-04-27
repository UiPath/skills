# Environment Setup

**Goal:** Ensure Studio Desktop is running, connected, and targeting the correct project before any other operations.

## Step 0.1: Establish Project Root

The `uip rpa` commands use `--project-dir` to target a specific project (defaults to current working directory). **If the current working directory is NOT the UiPath project root, all commands will fail or target the wrong project.**

**Resolution order** (use the first rule that matches):
1. **Explicit path** — The user provided a directory path → use it as-is.
2. **Project name reference** — The user mentioned a project by name → search for a folder with that name containing `project.json`.
3. **Detect from running Studio** — No path or name given → run:
   ```bash
   uip rpa list-instances --output json   ```
   Parse the JSON response. If `Data` is a non-empty array, each entry has a `ProjectDirectory` field. Use it:
   - **One instance** → use its `ProjectDirectory`.
   - **Multiple instances** → pick the best match or ask the user.
4. **Fall back to current working directory** — If `Data` is an empty array.

If the CWD is not the project root:
- Locate the project root by finding `project.json`: `Glob: pattern="**/project.json"`
- **Pass `--project-dir` explicitly** to every `uip rpa` command
- Store the project root path and use it consistently as `{projectRoot}`

## Step 0.2: Verify Studio is Running

```bash
uip rpa list-instances --output json```

**If no instances are found or Studio is not running:**
```bash
uip rpa start-studio
```

**If Studio is running but the project is not open:**
```bash
uip rpa open-project --project-dir "{projectRoot}"```

**If Studio IPC connection fails** (error messages about connection refused, timeout, or pipe not found):
1. Check if Studio Desktop is actually installed on the machine
2. Try `uip rpa start-studio` to launch a fresh instance
3. If Studio is running but IPC fails, the user may need to restart Studio
4. Inform the user and ask them to ensure Studio Desktop is open and responsive

**Note:** If `start-studio` fails with a registry key error, pass `--studio-dir` explicitly pointing to the Studio installation directory.

## Step 0.3: Authentication (If Needed)

Some commands (IS connections, workflow examples, cloud features) require authentication:

```bash
uip login
```

If you encounter auth errors (401, 403, "not authenticated") during any phase, prompt the user to run `uip login` to authenticate against their UiPath Cloud tenant.

## Step 0.4: Creating a New Project

**ALWAYS use `uip rpa create-project`** — never write `project.json`, `project.uiproj`, or other scaffolding files manually.

### For XAML Projects

```bash
uip rpa create-project \
  --name "MyAutomation" \
  --location "/path/to/parent/directory" \
  --template-id "BlankTemplate" \
  --expression-language "VisualBasic" \
  --target-framework "Windows" \
  --description "Automates invoice processing" \
  --studio-dir "<STUDIO_DIR>" \
  --output json
```

**Expression language for XAML projects:** Prefer `VisualBasic` for Windows target framework projects.

**`--studio-dir`:** Pass the Studio installation directory explicitly (e.g. `C:\Program Files\UiPathPlatform\Studio\<version>`) if the CLI fails to resolve it from the registry. Resolve it once per session and reuse for every subsequent `uip rpa` command.

### For Coded Projects

```bash
uip rpa create-project --name "<NAME>" --location "<PARENT_DIR>" --studio-dir "<STUDIO_DIR>" --output json
```

Use `--template-id TestAutomationProjectTemplate` for test projects, or `--template-id LibraryProcessTemplate` for libraries.

#### Parameters

| Parameter | Options | Default | Notes |
|-----------|---------|---------|-------|
| `--name` | Any string | (required) | Project folder name |
| `--location` | Directory path | (current dir) | Parent directory where project folder is created |
| `--template-id` | `BlankTemplate`, `LibraryProcessTemplate`, `TestAutomationProjectTemplate` | `BlankTemplate` | Project template |
| `--expression-language` | `VisualBasic`, `CSharp` | (template default) | Expression syntax for XAML workflows |
| `--target-framework` | `Legacy`, `Windows`, `Portable` | (template default) | .NET target framework |
| `--description` | Any string | (none) | Project description in project.json |

**Note:** `uip rpa create-project` may return `success: false` but still create the project files (partial success). If it fails, check whether the project directory and `project.json` were created before retrying.

### From a NuGet Template Package

Use when the user asks for a domain-specific template, references a specific template package by name, or wants to browse available templates.

**1. Search for available templates:**

```bash
uip rpa search-templates --query "<SEARCH_TERM>" --output json
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
uip rpa create-project \
  --name "MySAPAutomation" \
  --location "/path/to/parent/directory" \
  --template-package-id "<PACKAGE_ID>" \
  --template-package-version "<VERSION>" \
  --studio-dir "<STUDIO_DIR>" \
  --output json
```

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `--template-package-id` | string | (none) | NuGet package ID from `search-templates` results. **Overrides `--template-id` when set** |
| `--template-package-version` | string | (latest) | Omit to use the latest available version |

### After Creation

1. Open the project in Studio: `uip rpa open-project --project-dir "/path/to/MyAutomation"`
2. **Read the scaffolded files** — the command generates starter files. Read them before making changes so you build on valid defaults
3. Proceed with the skill workflow using the new project root
