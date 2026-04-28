---
description: Install a curated Claude Code allowlist for safe `uip` subcommands so the agent is not prompted on every command.
---

# Install UiPath permission allowlist

Help the user add a curated allowlist of safe `uip` subcommands to their Claude Code settings so the agent is not prompted on every command.

**Why this command exists.** Claude Code plugins cannot ship permission rules declaratively — per the [plugins docs](https://code.claude.com/docs/en/plugins.md#ship-default-settings-with-your-plugin), only the `agent` and `subagentStatusLine` keys are honored in a plugin-shipped `settings.json`; any `permissions` block is silently ignored. Without a user-configured allowlist, every `Bash(...)` invocation prompts for approval, and a realistic Flow or RPA build runs 25+ distinct `uip` subcommands.

## Steps

1. **Ask which variant to install** using `AskUserQuestion`:
   - **Full — with safety rails** (default, recommended) — writes both `allow` and `ask`. Cloud-side-effect commands (`debug` / `upload` / `publish` / `pack` / `login`) still prompt, even under `defaultMode: bypassPermissions` or `--dangerously-skip-permissions`. Prevents accidental prod publishes in YOLO mode.
   - **Allow-only — no safety rails** — writes only the `allow` block. Power users who explicitly want zero prompts under `--dangerously-skip-permissions` pick this. Accept that a stray `uip solution publish` will execute without confirmation.

2. **Ask where to install the allowlist** using a second `AskUserQuestion`:
   - **Project — `.claude/settings.local.json`** (default) — applies only to the current project; conventionally not committed to git.
   - **Project — `.claude/settings.json`** — applies only to the current project; usually committed.
   - **Global — `~/.claude/settings.json`** — applies to every project.
   - **Just print it** — output the JSON only, do not write anything.
   - **Something else** — accept a custom path string.

3. **Read the target file.** If it exists, parse the JSON strictly. If it already contains `permissions.allow` or `permissions.ask`, preserve existing entries and add only the missing ones (deduplicate by exact string). If there is no `permissions` block, add one. If the file parses as invalid JSON, abort with a clear message and ask the user to fix it manually — do not attempt to rewrite.

   - If the user chose **allow-only** in step 1 and the target file already has relevant `ask` entries from a prior run, **do not remove them** — leave existing `ask` rules intact. Only the `write` side is skipped; pre-existing safety rails the user already opted into stay put.

4. **Show the proposed diff** — print the delta (new entries being added to `allow`, and to `ask` if included) before writing. Do not print the full file.

5. **Ask for explicit confirmation** to write. Do not write without a yes.

6. **Write the file** with the merged JSON. Preserve existing formatting (indentation, key order) as much as reasonably possible.

7. **Report** the path written, which variant was installed (full vs allow-only), and tell the user the new rules take effect on the next tool call — no restart required.

## Recommended allowlist

Split by risk. `allow` = read-only or local-only commands; `ask` = commands with cloud or filesystem side effects (keep the prompt even if a future `defaultMode` tries to auto-allow).

```jsonc
{
  "permissions": {
    "allow": [
      // binary + auth status (read-only)
      "Bash(uip --version)",
      "Bash(uip login status)",
      "Bash(uip login status *)",
      "Bash(which uip)",

      // discovery — registry + Integration Service + Orchestrator list ops (all read-only)
      "Bash(uip maestro flow registry *)",
      "Bash(uip is *)",               // Integration Service (connections, connectors, resources, triggers)
      "Bash(uip or folders *)",       // Orchestrator folders

      // local-only flow / solution / agent scaffolding
      "Bash(uip maestro flow init *)",
      "Bash(uip maestro flow validate *)",
      "Bash(uip maestro flow tidy *)",
      "Bash(uip maestro flow node *)",
      "Bash(uip maestro flow edge *)",
      "Bash(uip solution new *)",
      "Bash(uip solution project *)",
      "Bash(uip solution resource *)",
      "Bash(uip agent init)",
      "Bash(uip agent init *)",
      "Bash(uip agent validate *)",

      // RPA skill — build, get-errors, find-activities, create-project, inspect-package, etc.
      // All local; no cloud side effects (publish goes through `uip solution upload/publish`).
      "Bash(uip rpa *)"
    ],
    "ask": [
      "Bash(uip login)",
      "Bash(uip login --authority *)",
      "Bash(uip maestro flow debug)",
      "Bash(uip maestro flow debug *)",
      "Bash(uip maestro flow pack)",
      "Bash(uip maestro flow pack *)",
      "Bash(uip solution upload)",
      "Bash(uip solution upload *)",
      "Bash(uip solution publish)",
      "Bash(uip solution publish *)"
    ]
  }
}
```

## Notes

- Pattern syntax is literal-prefix + `*` wildcard with a space before `*` — see the [Claude Code settings docs](https://code.claude.com/docs/en/settings.md#permissions-configuration).
- `Bash(uip login status *)` matches `uip login status --output json`; `Bash(uip login)` (exact, no wildcard) matches only the bare interactive login so it keeps its prompt.
- Rule precedence in Claude Code is `deny > ask > allow`, and rules are evaluated **before** `defaultMode` / `--dangerously-skip-permissions`. So the `ask` list in the full variant still forces a prompt under YOLO mode — that is the point of it, and it is the difference between the two variants offered in step 1.
- If the user has existing `permissions.deny` rules mentioning `uip`, do not remove them — respect explicit denials even if they conflict with the recommended allowlist. Surface the conflict in chat and ask.
- Never modify `~/.claude/settings.json` without explicit consent — that file often contains secrets (tokens, env vars) and should not be edited casually. If the user picks the global option, re-confirm before writing.
- The full variant's `ask` block intentionally guards `uip solution upload`, `uip maestro flow debug`, `uip maestro flow pack`, `uip solution publish`, and `uip login` — these produce real cloud side effects (publishing, executing flows, tenant auth). The `uipath-maestro-flow` skill's rules explicitly require user consent before cloud-executing a flow.
- `uip agent init` is in `allow` (scaffolding — same as `uip maestro flow init`). It does not publish to the cloud; it creates local agent project files.
- `uip rpa *` covers the full RPA subcommand tree (`build`, `get-errors`, `create-project`, `find-activities`, `inspect-package`, `focus-activity`, etc.). None of these publish to the cloud — RPA deployment flows through `uip solution upload` / `publish` (already guarded in `ask`).
