---
confidence: medium
---

# UiPath Extension — Install or Uninstall It

## Context

Machine-level change, **Windows only**: install, upgrade, or uninstall the UiPath extension for a browser (Chrome, Edge, Firefox), Java, or a remote-desktop client with `SetupExtensions.exe` from the Connected installer's extensions component. No job, trace, or project is needed; the machine running this investigation is the anchor.

What this looks like:
- [extension-installation-status.md](./extension-installation-status.md) found the extension not installed or outdated.
- The user asks to install, reinstall, upgrade, or uninstall the UiPath extension.

What can cause it:
- **Extension not installed.** Install it.
- **Extension installed but outdated.** Install it again; the install replaces the old version.
- **Extension no longer wanted, or a clean reinstall is needed.** Uninstall it.

What to look for:
- The extension's entry from [extension-installation-status.md](./extension-installation-status.md), then `status` in the script output.

## Investigation

1. Get the extension's current state: run [extension-installation-status.md](./extension-installation-status.md) through its step 4, unless it already ran in this investigation. `<EXTENSION_NAME>` is the key of the entry (`Chrome`, `Edge`, `Firefox`, ...). Finding "cannot be installed" → go to Resolution; do not run the command.

2. Decide whether the change is per-user, then find the method the script will use. The command comes from `InstallMethods[]` only; the entry's own `InstallCommand` / `UninstallCommand` are not used.

   | Request | Per-user |
   |---|---|
   | Install or uninstall, nothing else asked | No |
   | For the current user only, or without admin rights / without a UAC prompt | Yes; pass `--per-user` in step 4 |

   | Action | Method used |
   |---|---|
   | Install | First `InstallMethods[]` entry |
   | Uninstall | First `InstallMethods[]` entry with `IsInstalled: true` |
   | Per-user, either action | Same, among the entries with `NeedsAdminRights: false` only |
   | The user named a method, or a retry with another method (step 6) | That entry; pass its `Name` as `<METHOD_NAME>` in step 4 |

   That method's `NeedsAdminRights` says whether the change needs admin rights. Per-user and no such method → say that this extension cannot be changed without admin rights; do not run the command.

3. Ask via `AskUserQuestion` before running anything. The question MUST state:
   - the action and the extension (install or uninstall the UiPath extension for `<EXTENSION_NAME>`);
   - per-user: the change applies to the current user only;
   - the change is silent: no installer window, no further confirmation, no message from the installer; the result is reported here;
   - **install only: a running `<EXTENSION_NAME>` browser may be closed without asking — open tabs and unsaved work in it are then lost.** Tell the user to save their work in the browser first. An uninstall does not close the browser; do not mention it there;
   - **only when the method from step 2 has `NeedsAdminRights: true`:** Windows may show a UAC prompt, which the user must accept, unless this session runs elevated. Otherwise do not mention UAC.

   Start each of the last two statements with `WARNING:` and put them first in the question text.

   Do NOT put a command or any switch (`/chrome-enterprise`, `/silent`, ...) in the question or its options; describe the change in words only. Show the exact command only when the user explicitly asks for it.

   Declined, no answer, or `AskUserQuestion` unavailable → do not run the command; go to Resolution.

4. Run the command only on a yes (path relative to the skill root; `<ACTION>` is `install` or `uninstall`; add `--per-user` when step 2 says per-user; `<METHOD_NAME>` only when step 2 says so, otherwise omit it). The last stdout line is one JSON object:

   ```bash
   node scripts/change-extension.mjs <ACTION> <EXTENSION_NAME> <METHOD_NAME> > .local/investigations/raw/change-extension.json
   ```

5. Read `status`:

   | `status` | Exit | Meaning |
   |---|---|---|
   | `installed`, `uninstalled` | 0 | Done and confirmed for `method`: `entry` is what the tool reports for the extension after the command, unfiltered |
   | `change-failed` | 1 | The command ran (`command`, `exitCode`) and failed, or `method` is not in the asked state (`entry`). `logFile` is a file with everything the tool logged during the command, or `null` |
   | `not-allowed` | 1 | Nothing ran. `reason` says why the action cannot be done on this machine |
   | `bad-arguments` | 1 | Nothing ran. Wrong action, extension name, or method name; `extensions` or `methods` lists the valid names |
   | `component-missing`, `connected-missing` | 3 | Nothing ran. Switch to [connected-installer-extensions-component.md](./connected-installer-extensions-component.md) |
   | `status-failed` | 1 | The tool gave no status; quote `error` |
   | `unsupported-os` | 1 | Not Windows |

6. Install ended in `change-failed` → offer another method. Candidates: the `InstallMethods[]` entries with `CanInstall: true` not yet tried, in list order. Ask via `AskUserQuestion` with one option per candidate (its `LocalizedName`, and its `LocalizedDescription` as the description), plus an option to stop; include the step 3 statements for the chosen method. On a choice, re-run step 4 with that entry's `Name` as `<METHOD_NAME>`. No candidates left, or the user stops → go to Resolution.

Run the command at most once per approval and at most once per method. The one exception: the tool never started (see Resolution) → ask again before one retry of the same method. Trying another method goes through the script as in step 6; do NOT run `SetupExtensions.exe` directly, or edit browser policies or the registry. Quote `command` and `exitCode` only on `change-failed` or when the user asks for them.

## Resolution

- **If `installed`:** from `entry`, report the extension, `InstalledVersion`, and the `Name` of the `InstallMethods[]` entry with `IsInstalled: true`. Then act on that method's `LocalizedDescription`:
  - it says the extension must be enabled in the browser → tell the user to open the browser and enable the UiPath extension, and to reply when done;
  - it says the extension is enabled automatically → tell the user to reopen the browser if it was closed; nothing to enable.

  Continue with the playbook that led here, e.g. [browser-communication-failed.md](./browser-communication-failed.md).
- **If `uninstalled`:** report that the extension was removed. Stop.
- **If `change-failed`:** quote `command` and `exitCode`, and state the current `entry.IsInstalled`. Consult `logFile` for the cause: search it for error (`}[E][`) and warning (`}[W][`) lines first, then read the lines around them; do not read the whole file. Quote the lines that show the cause. The log may be missing or hold nothing useful (for example the command ran under another account); then report without it.
  - The method needs admin rights and the log holds no line from the command itself (or `logFile` is `null`) → the tool never started, most often because the UAC prompt was not accepted. Say so, state that nothing was changed, and offer one retry of the same method through the step 3 question.
  - Otherwise, install → offer another method per step 6. Stop when no method is left or the user stops, and list the methods tried with their failures.
- **If `not-allowed`, or the extension cannot be installed:** quote the reason verbatim. Stop.
- **If the user declined:** report the extension's current state and that nothing was changed. Stop.
