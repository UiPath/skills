# UiPath Coded Workflows Assistant

Full coding assistant for creating, editing, managing, and running UiPath coded automation projects with AI-powered assistance in Claude Code.

## Quick Start

### Access the Skill

The UiPath Coded Workflows plugin provides a single comprehensive skill for all coded workflow operations:

```bash
# Full coding assistant for UiPath coded automations
/uipath-coded-workflows:uipath-coded-workflows
```

## Features

- **Project Scaffolding**: Create new UiPath coded automation projects via `rpa-tool create-project`
- **Workflow Creation**: Build coded workflows, test cases, and helper classes using templates
- **Validation Loop**: Automatic file validation with `rpa-tool validate` after every create/edit
- **Activity References**: Comprehensive guides for 20+ UiPath activity packages (Excel, Word, Mail, UI Automation, Azure, AWS, and more)
- **Dependency Management**: Service-to-package mapping ensures correct NuGet dependencies in `project.json`

## Skill Overview

| Skill | Description | Purpose |
|-------|-------------|---------|
| `/uipath-coded-workflows:uipath-coded-workflows` | Full coding assistant for UiPath coded automations | Create, edit, validate, build, and run coded workflow projects |

## Documentation Structure

### Operations & Guidelines
- **[Operations Guide](skills/uipath-coded-workflows/references/operations-guide.md)** - Step-by-step procedures for all project operations
- **[Coding Guidelines](skills/uipath-coded-workflows/references/coding-guidelines.md)** - Using statements, best practices, and common issues
- **[CodedWorkflow Reference](skills/uipath-coded-workflows/references/codedworkflow-reference.md)** - Base class methods, hooks, and invocation patterns
- **[UI Automation Guide](skills/uipath-coded-workflows/references/ui-automation/ui-automation.md)** - Object Repository, descriptors, and UI interaction
- **[UiPath CLI Guide](skills/uipath-coded-workflows/references/uipcli-guide.md)** - Build, pack, and run commands
- **[Third-Party Packages](skills/uipath-coded-workflows/references/third-party-packages-guide.md)** - Adding and inspecting NuGet dependencies

### Document & Productivity Activities
- **[Excel](skills/uipath-coded-workflows/references/excel/excel.md)** - Spreadsheet automation
- **[Word](skills/uipath-coded-workflows/references/word/word.md)** - Document processing
- **[PowerPoint](skills/uipath-coded-workflows/references/powerpoint/powerpoint.md)** - Presentation automation
- **[Mail](skills/uipath-coded-workflows/references/mail/mail.md)** - Email automation (SMTP/IMAP/POP3)
- **[Office 365](skills/uipath-coded-workflows/references/office365/office365.md)** - Microsoft Graph API integration
- **[GSuite](skills/uipath-coded-workflows/references/gsuite/gsuite.md)** - Google Workspace integration

### Cloud & Infrastructure Activities
- **[Azure](skills/uipath-coded-workflows/references/azure/azure.md)** - Azure services automation
- **[Google Cloud](skills/uipath-coded-workflows/references/google-cloud/google-cloud.md)** - GCP services automation
- **[Amazon Web Services](skills/uipath-coded-workflows/references/amazon-web-services/amazon-web-services.md)** - AWS services automation
- **[Exchange Server](skills/uipath-coded-workflows/references/exchange-server/exchange-server.md)** - On-premise Exchange
- **[Active Directory](skills/uipath-coded-workflows/references/active-directory/active-directory.md)** - AD domain services
- **[Azure AD](skills/uipath-coded-workflows/references/azure-active-directory/azure-active-directory.md)** - Azure Active Directory
- **[Citrix](skills/uipath-coded-workflows/references/citrix/citrix.md)** - Citrix virtual desktop automation
- **[Hyper-V](skills/uipath-coded-workflows/references/hyperv/hyperv.md)** - Hyper-V management

### Core Activities
- **[System](skills/uipath-coded-workflows/references/system/system.md)** - Orchestrator queues, assets, and storage
- **[Testing](skills/uipath-coded-workflows/references/testing/testing.md)** - Test assertions and verification
- **[UI Automation](skills/uipath-coded-workflows/references/ui-automation/ui-automation.md)** - Desktop and web UI interaction

### Templates
- **[Workflow Template](skills/uipath-coded-workflows/assets/codedworkflow-template.md)** - Coded workflow scaffold
- **[Test Case Template](skills/uipath-coded-workflows/assets/testcase-template.md)** - Test case scaffold
- **[Helper Class Template](skills/uipath-coded-workflows/assets/helper-utility-template.md)** - Coded source file scaffold
- **[JSON Templates](skills/uipath-coded-workflows/assets/json-template.md)** - project.json, .cs.json, and project.uiproj
- **[Project Structure Examples](skills/uipath-coded-workflows/assets/project-structure-examples.md)** - Reference project layouts
- **[Before/After Hooks](skills/uipath-coded-workflows/assets/before-after-hooks-template.md)** - Hook patterns

## Example Workflow

A typical coded workflow development workflow:

1. **Resolve project** - Detect or create a UiPath coded automation project
2. **Discover patterns** - Read existing `.cs` files to learn project conventions
3. **Create files** - Add workflows, test cases, or helper classes using templates
4. **Update project.json** - Add dependencies, entry points, and file info as needed
5. **Validate** - Run the validation loop until all files compile cleanly
6. **Run** - Execute the workflow with `rpa-tool run-file`

## Project Structure

When you create a UiPath coded automation project, it generates:

```
ProjectName/
├── project.json              # Project configuration (dependencies, entry points)
├── project.uiproj            # Project descriptor (Name, ProjectType, MainFile)
├── Main.cs                   # Main entry point workflow
├── Main.cs.json              # Metadata for Main.cs
├── [OtherWorkflow].cs        # Additional workflow/test case files
├── [OtherWorkflow].cs.json   # Metadata for each workflow/test case
├── [HelperClass].cs          # Coded Source File (plain C#, no metadata)
├── .codedworkflows/          # Auto-generated connection factories
├── .objects/                 # Object Repository metadata
└── .settings/                # IDE design settings
```

## Requirements

- UiPath Studio 2025.x+
- .NET 8.0+
- `rpa-tool` CLI (bundled with UiPath Studio)
- Claude Code CLI

## Getting Started

1. **Open your project** in UiPath Studio or point to a project directory
2. **Invoke the skill** with `/uipath-coded-workflows:uipath-coded-workflows`
   - The assistant auto-detects your project via `rpa-tool list-instances`
3. **Describe what you need** - new workflow, test case, helper class, or edits
4. **Review generated code** - the assistant validates all files automatically
5. **Run your workflow** with the provided `rpa-tool run-file` command

## Common Issues

### "rpa-tool" not found

Ensure UiPath Studio is installed and `rpa-tool` is available in your PATH. It ships with UiPath Studio 2025.x+.

### Validation errors after file creation

The assistant runs an automatic validation loop (up to 5 retries). If errors persist:
- Check that required NuGet packages are listed in `project.json` `dependencies`
- Verify namespace matches the sanitized project name
- Ensure `using` statements match the packages available in the project

### Missing service properties (CS0103)

Each `CodedWorkflow` service (e.g., `excel`, `system`, `uiAutomation`) requires its corresponding NuGet package in `project.json`. See the Service-to-Package mapping in the skill documentation.

### Project detection fails

If `rpa-tool list-instances` returns an empty array, either:
- Open the project in UiPath Studio first, or
- Provide the project directory path explicitly

## Learning Resources

- **[UiPath Documentation](https://docs.uipath.com/)** - Official UiPath documentation
- **[UiPath Platform](https://www.uipath.com/)** - Main UiPath website
- **[UiPath Community](https://community.uipath.com/)** - Community forum

## Support

- **GitHub Issues**: https://github.com/UiPath/uipath-claude-plugins/issues
- **Documentation**: https://docs.uipath.com/
- **Community**: https://community.uipath.com/

## License

MIT License - See project LICENSE file for details
