---
confidence: medium
---

# UiPath Extensions Component — Locate It on a Connected Installer Machine

## Context

Machine-level check, **Windows only**: is the component that carries `SetupExtensions.exe` and the UiPath extension files present on a machine where UiPath was installed with the Connected installer (`UiPathPlatform`)? No job, trace, or project is needed; the machine running this investigation is the anchor.

What this looks like:
- The user asks to troubleshoot or check the installation of the UiPath extension for a browser (Chrome, Edge, Firefox) or remote-desktop client.
- A browser playbook reached an "extension missing / not installed" branch and the extension tooling must be found first.

What can cause it:
- **Connected installer not present on the machine.** UiPath was installed another way, or not at all.
- **Browser Extensions component not installed.** The Connected installer is present, but its `BrowserExtensions` (or `DriverExtensions`) component was not selected at install time.
- **Component present.** The extension tooling exists; the fault is in the extension itself or in the browser.

What to look for:
- `status` in the script output: `connected-missing`, `component-missing`, or `ok`.

## Investigation

1. Run the locator (read-only; path relative to the skill root). The last stdout line is one JSON object:

   ```bash
   node scripts/locate-connected-extensions.mjs > .local/investigations/raw/locate-connected-extensions.json
   ```

2. Read `status`:

   | `status` | Exit | Meaning |
   |---|---|---|
   | `ok` | 0 | Component found. `component.directory` holds `SetupExtensions.exe`; `component.version` is the installed version |
   | `component-missing` | 3 | Connected installer present (`updaterAppPath`); no `BrowserExtensions` or `DriverExtensions` folder with `SetupExtensions.exe` next to the Updater folder |
   | `connected-missing` | 3 | No Connected installer, per-user or per-machine |
   | `unsupported-os` | 1 | Not Windows |

Do NOT probe install folders by hand or call the Updater directly. The script's answer is final.

## Resolution

- **If `connected-missing`:** report that UiPath on this machine was not installed through the Connected installer. Stop.
- **If `component-missing`:** report that the Browser Extensions component is not installed. Recommend adding it from the Connected installer's Modify window. Do not install it yourself.
- **If `ok`:** report `component.directory` and `component.version`. The tooling is present; continue with the playbook that led here, e.g. [browser-communication-failed.md](./browser-communication-failed.md).
