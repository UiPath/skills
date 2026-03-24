# File Sync Guide

Push and pull coded app source code between your local development environment and UiPath Studio Web.

## Overview

File sync lets you develop coded web apps locally with your preferred tools and IDE, then push the build output to Studio Web for collaboration, testing, and integration. You can also pull existing Studio Web projects to work on locally.

| Command | Direction | Description |
|---------|-----------|-------------|
| `uip codedapp push` | Local → Studio Web | Upload local build output to a Studio Web project |
| `uip codedapp pull` | Studio Web → Local | Download project files from Studio Web to local |

## Prerequisites

- **Authentication**: Run `uip login` before push/pull
- **Project ID**: Required for both commands. Can be:
  - Auto-created during `push` (first time only)
  - Set as `UIPATH_PROJECT_ID` in `.env`
  - Passed as the first argument

## Push Workflow

### First-Time Push (Auto-Create Project)

When no `UIPATH_PROJECT_ID` exists, `push` offers to create a new Coded App project:

```bash
# 1. Build your app
npm run build

# 2. Push (will prompt to create project)
uip codedapp push
```

Interactive flow:
```
? No project ID found. Create a new Coded App project? (Y/n)
? Enter a name for the new Coded App: my-webapp
✔ Created coded app project "my-webapp" with ID: abc-123-def
  Saved UIPATH_PROJECT_ID to .env
```

The project ID is automatically saved to `.env` for future pushes.

### Subsequent Pushes

Once `UIPATH_PROJECT_ID` is in `.env`, pushes are one-command:

```bash
npm run build
uip codedapp push
```

### Push Options

```bash
# Push with explicit project ID (overrides .env)
uip codedapp push abc-123-def

# Push a custom build directory (default: dist)
uip codedapp push --buildDir build

# Skip importing referenced resources
uip codedapp push --ignoreResources
```

### What Gets Pushed

The command uploads the contents of the build directory (default: `dist/`) to Studio Web. This includes:
- HTML, CSS, JavaScript files
- Static assets (images, fonts, etc.)
- Any other files in the build output

The `--ignoreResources` flag skips importing referenced resources (connections, assets) that may be declared in the app.

## Pull Workflow

### Basic Pull

```bash
# Pull using project ID from .env
uip codedapp pull

# Pull with explicit project ID
uip codedapp pull abc-123-def
```

### Pull to a Specific Directory

```bash
uip codedapp pull --targetDir ./my-app
```

### Handling File Conflicts

By default, `pull` prompts before overwriting existing local files:

```bash
# Overwrite without prompting
uip codedapp pull --overwrite
```

## Common Workflows

### Local Development with Studio Web Sync

```bash
# 1. Auth once
uip login

# 2. Initial push (creates project)
npm run build
uip codedapp push

# 3. Development loop
#    - Edit source code locally
#    - Build
#    - Push changes
npm run build
uip codedapp push
```

### Pulling an Existing Project

```bash
# 1. Auth
uip login

# 2. Pull the project (get project ID from Studio Web URL)
uip codedapp pull <project-id> --targetDir ./my-app

# 3. Install dependencies
cd my-app
npm install
```

### Team Collaboration

```bash
# Developer A pushes changes
npm run build
uip codedapp push

# Developer B pulls latest
uip codedapp pull --overwrite
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `UIPATH_PROJECT_ID` | Studio Web project ID (auto-saved on first push) |
| `UIPATH_ACCESS_TOKEN` | Authentication token |
| `UIPATH_URL` | UiPath Cloud base URL |
| `UIPATH_ORGANIZATION_ID` | Organization ID |
| `UIPATH_TENANT_ID` | Tenant ID |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Not authenticated` | Run `uip login` |
| `Project not found` | Verify the project ID exists in Studio Web |
| `dist/ directory not found` | Run `npm run build` before pushing |
| File conflict on pull | Use `--overwrite` to force, or manually resolve |
| `UIPATH_PROJECT_ID` not saved | Check `.env` file permissions; set it manually |
