# Environment setup

Read this file when: Studio is not running, you need to create a new project, or you need to establish the project root.

## Step 0.1: Establish project root

All `uip rpa` commands default to CWD as the project root. If CWD does not contain `project.json`, pass `--project-dir` explicitly.

```bash
ls {cwd}/project.json
```

If not found, locate it: `Glob: pattern="**/project.json"`. Store the path as `{projectRoot}`.

## Step 0.2: Verify Studio is running

```bash
uip rpa list-instances --format json
```

If no instances found:
```bash
uip rpa start-studio
```

If Studio is running but the project is not open:
```bash
uip rpa open-project --project-dir "{projectRoot}"
```

If `start-studio` fails with a registry key error, pass `--studio-dir` pointing to the Studio installation directory.

## Step 0.3: Authentication

Some commands require authentication (IS connections, workflow examples, cloud features):
```bash
uip login
```

Run this if you encounter 401/403 or "not authenticated" errors.

## Step 0.4: Creating a new project

```bash
uip rpa create-project \
  --name "MyAutomation" \
  --location "/path/to/parent/directory" \
  --template-id "BlankTemplate" \
  --expression-language "VisualBasic" \
  --target-framework "Windows" \
  --description "Automates invoice processing" \
  --format json
```

| Parameter | Required | Default | Options |
|-----------|----------|---------|---------|
| `--name` | Yes | | Project folder name |
| `--location` | No | CWD | Parent directory |
| `--template-id` | No | `BlankTemplate` | `BlankTemplate`, `LibraryProcessTemplate`, `TestAutomationProjectTemplate` |
| `--expression-language` | No | Template default | `VisualBasic`, `CSharp` |
| `--target-framework` | No | Template default | `Legacy`, `Windows`, `Portable` |
| `--description` | No | | Project description |

Note: `create-project` may return `success: false` but still create files (partial success). Check if `project.json` exists before retrying.

After creation:
1. Open the project: `uip rpa open-project --project-dir "/path/to/parent/directory/MyAutomation"`
2. The project root is now `/path/to/parent/directory/MyAutomation/`
