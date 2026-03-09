# UiPath RPA Workflows

Generate and edit RPA workflows (XAML files) in UiPath Studio Desktop using a discovery-first approach with iterative error-driven refinement.

## Quick Start

```bash
# Full RPA workflow architect — create, edit, and validate XAML workflows
/uipath-rpa-workflows:uipath-rpa-workflows
```

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **RPA Workflow Architect** | `/uipath-rpa-workflows:uipath-rpa-workflows` | Generate and edit RPA workflows using discovery-first approach with error-driven refinement |

## Features

- **Discovery-First Approach**: Understand project structure and existing patterns before generating XAML
- **Example-Driven**: Search and study workflow examples via `uipcli rpa list-workflow-examples` and `uipcli rpa get-workflow-example`
- **Iterative Validation**: Validate after every change with `uipcli rpa get-errors` and fix errors methodically
- **Activity Search**: Find activities with `uipcli rpa find-activities` and get default XAML templates
- **UI Automation**: Capture selectors into the Object Repository with indication tools
- **Comprehensive References**: Activity guides for Excel, Word, PowerPoint, Mail, GSuite, Document Understanding, UI Automation, and more

## Core Principles

1. **Discovery Before Generation** — Never generate XAML without first understanding project structure
2. **Search Examples Repository** — Always find and study relevant examples before creating workflows
3. **Start Simple, Iterate** — Create minimal working version first, then refine
4. **Validate After Every Change** — Always check with `uipcli rpa get-errors`
5. **Fix Errors Methodically** — Package → Structure → Type → Logic

## Key CLI Commands

```bash
uipcli rpa list-instances --format json           # Find open Studio projects
uipcli rpa find-activities --query "..." --format json  # Search for activities
uipcli rpa list-workflow-examples --tags '["..."]' --format json  # Find examples
uipcli rpa get-workflow-example --key "..."        # Retrieve example XAML
uipcli rpa get-errors --format json                # Validate workflow files
uipcli rpa run-file --file-path "..."              # Run a workflow
uipcli rpa new --name "..."                        # Create new project
```

## Requirements

- UiPath Studio Desktop
- Node.js (for `uipcli` CLI)
- Claude Code CLI

## Resources

- [UiPath Documentation](https://docs.uipath.com/)
- [UiPath Community](https://community.uipath.com/)
- [GitHub Issues](https://github.com/UiPath/skills/issues)

## License

MIT
