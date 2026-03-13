# UiPath Plugin for Claude Code

Comprehensive UiPath automation plugin for Claude Code — covering coded workflows, RPA workflows (XAML), environment setup, Orchestrator management, and CLI tooling.

## Quick Start

```bash
# Coded workflow assistant — create, edit, validate, and run coded automations (.cs)
/uipath:uipath-coded-workflows

# RPA workflow architect — generate and edit XAML workflows in UiPath Studio Desktop
/uipath:uipath-rpa-workflows

# Development environment — authentication, Orchestrator, deployment, CLI tools, Integration Service
/uipath:uipath-development
```

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Coded Workflows** | `/uipath:uipath-coded-workflows` | Full coding assistant for creating, editing, validating, and running UiPath coded automation projects (.cs) |
| **RPA Workflows** | `/uipath:uipath-rpa-workflows` | Generate and edit RPA workflows (XAML) using a discovery-first approach with iterative error-driven refinement |
| **Development** | `/uipath:uipath-development` | Environment setup, authentication, Orchestrator management, solution lifecycle, Integration Service, and CLI tooling |

## Coded Workflows

Build UiPath coded automations in C# with automatic validation and activity references.

- **Project Scaffolding**: Create new coded automation projects via `rpa-tool create-project`
- **Workflow Creation**: Build workflows, test cases, and helper classes using templates
- **Validation Loop**: Automatic file validation with `rpa-tool validate` after every create/edit
- **Activity References**: Guides for 20+ UiPath activity packages (Excel, Word, Mail, UI Automation, Azure, AWS, and more)
- **Dependency Management**: Service-to-package mapping ensures correct NuGet dependencies

### Documentation

- **[Operations Guide](skills/uipath-coded-workflows/references/operations-guide.md)** - Step-by-step procedures for all project operations
- **[Coding Guidelines](skills/uipath-coded-workflows/references/coding-guidelines.md)** - Using statements, best practices, and common issues
- **[CodedWorkflow Reference](skills/uipath-coded-workflows/references/codedworkflow-reference.md)** - Base class methods, hooks, and invocation patterns
- **[UI Automation Guide](skills/uipath-coded-workflows/references/ui-automation/ui-automation.md)** - Object Repository, descriptors, and UI interaction
- **[UiPath CLI Guide](skills/uipath-coded-workflows/references/uipcli-guide.md)** - Build, pack, and run commands
- **[Third-Party Packages](skills/uipath-coded-workflows/references/third-party-packages-guide.md)** - Adding and inspecting NuGet dependencies

### Activity References

| Category | Topics |
|----------|--------|
| **Document & Productivity** | [Excel](skills/uipath-coded-workflows/references/excel/excel.md), [Word](skills/uipath-coded-workflows/references/word/word.md), [PowerPoint](skills/uipath-coded-workflows/references/powerpoint/powerpoint.md), [Mail](skills/uipath-coded-workflows/references/mail/mail.md) |
| **Cloud & Integration** | [Office 365](skills/uipath-coded-workflows/references/office365/office365.md), [GSuite](skills/uipath-coded-workflows/references/gsuite/gsuite.md), [Azure](skills/uipath-coded-workflows/references/it-automations/azure/azure.md), [Google Cloud](skills/uipath-coded-workflows/references/it-automations/google-cloud/google-cloud.md), [AWS](skills/uipath-coded-workflows/references/it-automations/amazon-web-services/amazon-web-services.md) |
| **Infrastructure** | [Exchange Server](skills/uipath-coded-workflows/references/it-automations/exchange-server/exchange-server.md), [Active Directory](skills/uipath-coded-workflows/references/it-automations/active-directory/active-directory.md), [Azure AD](skills/uipath-coded-workflows/references/it-automations/azure-active-directory/azure-active-directory.md), [Citrix](skills/uipath-coded-workflows/references/it-automations/citrix/citrix.md), [Hyper-V](skills/uipath-coded-workflows/references/it-automations/hyperv/hyperv.md) |
| **Core** | [System](skills/uipath-coded-workflows/references/system/system.md), [Testing](skills/uipath-coded-workflows/references/testing/testing.md), [UI Automation](skills/uipath-coded-workflows/references/ui-automation/ui-automation.md) |

### Templates

- [Workflow Template](skills/uipath-coded-workflows/assets/codedworkflow-template.md) | [Test Case](skills/uipath-coded-workflows/assets/testcase-template.md) | [Helper Class](skills/uipath-coded-workflows/assets/helper-utility-template.md)
- [JSON Templates](skills/uipath-coded-workflows/assets/json-template.md) | [Project Structure](skills/uipath-coded-workflows/assets/project-structure-examples.md) | [Hooks](skills/uipath-coded-workflows/assets/before-after-hooks-template.md)

## RPA Workflows

Generate and edit RPA workflows (XAML files) in UiPath Studio Desktop using a discovery-first approach with iterative error-driven refinement.

- **Discovery-First Approach**: Understand project structure and existing patterns before generating XAML
- **Example-Driven**: Search and study workflow examples via `uipcli rpa list-workflow-examples` and `uipcli rpa get-workflow-example`
- **Iterative Validation**: Validate after every change with `uipcli rpa get-errors` and fix errors methodically
- **Activity Search**: Find activities with `uipcli rpa find-activities` and get default XAML templates
- **UI Automation**: Capture selectors into the Object Repository with indication tools

### Core Principles

1. **Discovery Before Generation** — Never generate XAML without first understanding project structure
2. **Search Examples Repository** — Always find and study relevant examples before creating workflows
3. **Start Simple, Iterate** — Create minimal working version first, then refine
4. **Validate After Every Change** — Always check with `uipcli rpa get-errors`
5. **Fix Errors Methodically** — Package → Structure → Type → Logic

### Key CLI Commands

```bash
uipcli rpa list-instances --format json           # Find open Studio projects
uipcli rpa find-activities --query "..." --format json  # Search for activities
uipcli rpa list-workflow-examples --tags '["..."]' --format json  # Find examples
uipcli rpa get-workflow-example --key "..."        # Retrieve example XAML
uipcli rpa get-errors --format json                # Validate workflow files
uipcli rpa run-file --file-path "..."              # Run a workflow
```

## Requirements

- UiPath Studio Desktop (2025.x+ for coded workflows)
- .NET 8.0+ (for coded workflows)
- Node.js (for `uipcli` CLI)
- Claude Code CLI

### Setting up uipcli

The `uipcli` CLI is required for both RPA and coded workflow skills. It is temporarily hosted on **GitHub Packages** during development and will be moved to the public npm registry for public release. Until then, you need to set an authentication token before the plugin can install it automatically.

Add `GH_NPM_REGISTRY_TOKEN` to your shell profile so it's available on every session:

```powershell
# PowerShell — add to $PROFILE
$env:GH_NPM_REGISTRY_TOKEN = "ghp_your_token_here"
```

```bash
# Bash / Zsh — add to ~/.bashrc or ~/.zshrc
export GH_NPM_REGISTRY_TOKEN=ghp_your_token_here
```

The plugin handles the rest (registry configuration, installation, and updates) on session start.

## Resources

- [UiPath Documentation](https://docs.uipath.com/)
- [UiPath Community](https://community.uipath.com/)
- [GitHub Issues](https://github.com/UiPath/uipath-claude-plugins/issues)

## License

MIT
