# Phase 0: Environment Readiness

**Goal:** Ensure Studio Desktop is running, connected, and targeting the correct project before any other operations.

## Step 0.1: Establish Project Root

The `uip rpa` commands use `--project-dir` to target a specific project (defaults to current working directory). **If the current working directory is NOT the UiPath project root, all commands will fail or target the wrong project.**

```bash
# Check if project.json exists in the CWD
ls {cwd}/project.json
```

If the CWD is not the project root:
- Locate the project root by finding `project.json`: `Glob: pattern="**/project.json"`
- **Pass `--project-dir` explicitly** to every `uip rpa` command, or
- Ask the user where their project is located

Store the project root path and use it consistently as `{projectRoot}` throughout all subsequent operations.

## Step 0.2: Verify Studio is Running

```bash
uip rpa list-instances --format json
```

**If no instances are found or Studio is not running:**
```bash
uip rpa start-studio
```

**If Studio is running but the project is not open:**
```bash
uip rpa open-project --project-dir "{projectRoot}"
```

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

When the user needs a brand-new UiPath project (not just a new workflow in an existing project):

```bash
uip rpa new \
  --name "MyAutomation" \
  --location "/path/to/parent/directory" \
  --template-id "BlankTemplate" \
  --expression-language "VisualBasic" \
  --target-framework "Windows" \
  --description "Automates invoice processing" \
  --format json
```

**Note:** `uip rpa new` may return `success: false` but still create the project files (partial success). If it fails, check whether the project directory and `project.json` were created before retrying.

### Parameters

| Parameter | Options | Default | Notes |
|-----------|---------|---------|-------|
| `--name` | Any string | (required) | Project folder name |
| `--location` | Directory path | (current dir) | Parent directory where project folder is created |
| `--template-id` | `BlankTemplate`, `LibraryProcessTemplate`, `TestAutomationProjectTemplate` | `BlankTemplate` | Project template |
| `--expression-language` | `VisualBasic`, `CSharp` | (template default) | Expression syntax for XAML workflows |
| `--target-framework` | `Legacy`, `Windows`, `Portable` | (template default) | .NET target framework |
| `--description` | Any string | (none) | Project description in project.json |

### After Creation

1. Open the project in Studio: `uip rpa open-project --project-dir "/path/to/MyAutomation"`
2. The project root is now `/path/to/parent/directory/MyAutomation/`
3. Proceed to Phase 1 (Discovery) using the new project root
