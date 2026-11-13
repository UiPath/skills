---
confidence: medium
---

# UiPath Extension — Check Its Installation Status

## Context

Machine-level check, **Windows only**: is the UiPath extension for a browser (Chrome, Edge, Firefox), Java, or a remote-desktop client (Citrix, RDP, VMware, Amazon WorkSpaces) installed on this machine, in which version, by which install method, and can it be installed? The answer comes from `SetupExtensions.exe` in the Connected installer's extensions component. No job, trace, or project is needed; the machine running this investigation is the anchor.

What this looks like:
- The user asks to troubleshoot or check the installation of the UiPath extension for a browser or remote-desktop client.
- A browser playbook reached an "extension missing / not installed" branch.

What can cause it:
- **Extension not installed.** `IsInstalled: false`, `CanInstallExtension: true`.
- **Extension installed but outdated.** `IsInstalled: true`, `CanBeUpgraded: true`.
- **Extension cannot be installed on this machine.** `CanInstallExtension: false`; `InstallDisabledReason` says why (target browser or client absent, machine role mismatch).
- **Extension installed and current.** `IsInstalled: true`, `CanBeUpgraded: false`. The fault is elsewhere: extension disabled in the browser, not allowed in incognito, native messaging blocked, browser↔package version skew.
- **Extensions component not available.** The tool that reports the status is not on the machine.

What to look for:
- `status` in the script output, then the entry under `extensions` for the extension the user named.

## Investigation

1. Read the status (read-only; path relative to the skill root). `<EXTENSION_NAME>` is one of `Chrome`, `Edge`, `Firefox`, `Java`, `CitrixClient`, `RdpClient`, `VMwareClient`, `AmazonWorkspacesClient`, among others. No extension named by the user → omit the argument; the output then holds every extension. The last stdout line is one JSON object:

   ```bash
   node scripts/read-extensions-status.mjs <EXTENSION_NAME> > .local/investigations/raw/read-extensions-status.json
   ```

2. Read `status`:

   | `status` | Exit | Meaning | Next |
   |---|---|---|---|
   | `ok` | 0 | `extensions` holds the entry as the tool reports it, unfiltered | Step 3 |
   | `bad-arguments` | 1 | Unknown extension name; `extensions` lists the valid names | Re-run step 1 with a valid name |
   | `component-missing`, `connected-missing` | 3 | The extensions component was not located | Switch to [connected-installer-extensions-component.md](./connected-installer-extensions-component.md), starting from its Investigation step 2 with this output. Come back to step 1 once that playbook reports the component present |
   | `status-failed` | 1 | The tool ran but gave no status | Quote `error`; stop |
   | `unsupported-os` | 1 | Not Windows | Report; stop |

3. Read the entry. No extension named → report every entry with `IsInstalled: true`, plus `Chrome` and `Edge`. Fields that matter:

   | Field | Meaning |
   |---|---|
   | `IsInstalled`, `InstalledVersion`, `CanBeUpgraded` | Current state |
   | `CanInstallExtension`, `InstallDisabledReason` | Whether an install is possible, and why not |
   | `InstallMethods[]` | Every way the extension can be installed: `Name`, `LocalizedDescription`, `IsInstalled`, `NeedsAdminRights`, `InstallCommand`, `UninstallCommand`. The entries with `IsInstalled: true` are the methods in place. An install or uninstall runs a method's command |
   | `InstallCommand`, `UninstallCommand`, `NeedsAdminRights` (entry level) | Not used; ignore |
   | `Warnings[]` | Notices to pass on (`Title`, `Text`), for example Group Policy |

4. Classify the entry, first match wins:

   | Entry | Finding |
   |---|---|
   | `IsInstalled: false`, `CanInstallExtension: false` | Cannot be installed on this machine |
   | `IsInstalled: false`, `CanInstallExtension: true` | Not installed |
   | `IsInstalled: true`, `CanBeUpgraded: true` | Installed but outdated |
   | `IsInstalled: true`, `CanBeUpgraded: false` | Installed and current |

Do NOT run `SetupExtensions.exe` directly, read browser profile folders, or query the registry: the script's answer is final.

## Resolution

Report the finding with its evidence: `IsInstalled`, `InstalledVersion`, and the `Name` of each installed method. Quote `Warnings` verbatim when present (for example a Group Policy notice): a policy on the machine can override what the installer set. Do not list commands or the other methods unless asked. This playbook changes nothing on the machine; any change goes through [extension-install-uninstall.md](./extension-install-uninstall.md), which asks first.

- **If not installed:** state that the UiPath extension for `<EXTENSION_NAME>` is not installed and that it can be installed on this machine. Continue with [extension-install-uninstall.md](./extension-install-uninstall.md) from its step 2 to offer the install.
- **If installed but outdated:** state the installed version and that a newer one is available from the extensions component. Continue with [extension-install-uninstall.md](./extension-install-uninstall.md) from its step 2 to offer the upgrade.
- **If it cannot be installed:** quote `InstallDisabledReason` verbatim. Stop.
- **If installed and current:** the installation is not the fault. Continue with the playbook that led here, e.g. [browser-communication-failed.md](./browser-communication-failed.md).
