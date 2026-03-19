# Claude Plugin Marketplace

This repository contains a Claude Code plugin marketplace with configuration and management files.

## Managing Marketplaces

### Adding a Marketplace

To add a marketplace, use the `claude plugin marketplace add` command:

```bash
claude plugin marketplace add ./
```

This adds the current directory as a marketplace, making all plugins in it available for installation.

### Removing a Marketplace

To remove a marketplace, use the `claude plugin marketplace remove` command:

```bash
claude plugin marketplace remove uipath-marketplace
```

Replace `uipath-marketplace` with the name of the marketplace you want to remove.

## Managing Plugins

### Installing a Plugin

To install a plugin from a marketplace, use the `claude plugin install` command:

```bash
claude plugin install <plugin-name>@uipath-marketplace
```

Example:
```bash
claude plugin install uipath-coded-agents@uipath-marketplace
```

### Uninstalling a Plugin

To uninstall a plugin, use the `claude plugin uninstall` command:

```bash
claude plugin uninstall <plugin-name>
```

Example:
```bash
claude plugin uninstall uipath-coded-agents
```

## Plugins in This Marketplace

| Plugin | Description | Version |
|--------|-------------|---------|
| [**uipath-coded-agents**](./uipath-coded-agents/README.md) | Create, run, and evaluate UiPath coded agents with AI-powered assistance | 0.0.1 |
| [**uipath**](./uipath/README.md) | UiPath plugin for Claude Code — custom skills, agents, hooks, and MCP servers for UiPath workflows, UI automation, and UI testing | 0.0.8 |

## Project Structure

For a complete overview of the plugin marketplace structure and individual plugin structures, see the [Claude Code Plugin Documentation](https://code.claude.com/docs/en/plugins).

This marketplace contains:

- **`.claude-plugin/`** - Plugin configuration directory
  - `marketplace.json` - Marketplace definition listing all available plugins
- **`uipath-coded-agents/`** - UiPath coded agents plugin
- **`uipath/`** - UiPath workflows, UI automation, and UI testing plugin
- **README.md** - This file

## Getting Help

For comprehensive information about Claude plugins and how to develop them, see:
- **[Claude Code Plugins Documentation](https://code.claude.com/docs/en/plugins)** - Complete plugin development guide including project structure, SKILL.md format, plugin manifest, hooks, and more

For help with Claude plugin commands in your terminal:

```bash
claude plugin --help
claude plugin marketplace --help
```

For plugin-specific documentation, see the README files in individual plugin directories (`uipath-coded-agents/`, `uipath/`)
