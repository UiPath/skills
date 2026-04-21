---
description: Install a curated Claude Code allowlist for safe `uip` subcommands so the agent is not prompted on every command.
---

# Install UiPath permission allowlist

Help the user add a curated allowlist of safe `uip` subcommands to their Claude Code settings so the agent is not prompted on every command.

**Why this command exists.** Claude Code plugins cannot ship permission rules declaratively — per the [plugins docs](https://code.claude.com/docs/en/plugins.md#ship-default-settings-with-your-plugin), only the `agent` and `subagentStatusLine` keys are honored in a plugin-shipped `settings.json`; any `permissions` block is silently ignored. Without a user-configured allowlist, every `Bash(...)` invocation prompts for approval, and a realistic Flow or RPA build runs 25+ distinct `uip` subcommands.

## Steps

1. **Ask where to install the allowlist** using `AskUserQuestion` with these options:
   - **Project — `.claude/settings.local.json`** (default) — applies only to the current project; conventionally not committed to git.
   - **Project — `.claude/settings.json`** — applies only to the current project; usually committed.
   - **Global — `~/.claude/settings.json`** — applies to every project.
   - **Just print it** — output the JSON only, do not write anything.
   - **Something else** — accept a custom path string.

2. **Read the target file.** If it exists, parse the JSON strictly. If it already contains `permissions.allow` or `permissions.ask`, preserve existing entries and add only the missing ones (deduplicate by exact string). If there is no `permissions` block, add one. If the file parses as invalid JSON, abort with a clear message and ask the user to fix it manually — do not attempt to rewrite.

3. **Show the proposed diff** — print the delta (new entries being added to `allow` and `ask`) before writing. Do not print the full file.

4. **Ask for explicit confirmation** to write. Do not write without a yes.

5. **Write the file** with the merged JSON. Preserve existing formatting (indentation, key order) as much as reasonably possible.

6. **Report** the path written and tell the user the new rules take effect on the next tool call — no restart required.

## Recommended allowlist

Split by risk. `allow` = read-only or local-only commands; `ask` = commands with cloud or filesystem side effects (keep the prompt even if a future `defaultMode` tries to auto-allow).

```jsonc
{
  "permissions": {
    "allow": [
      "Bash(uip --version)",
      "Bash(uip login status)",
      "Bash(uip login status *)",
      "Bash(which uip)",

      "Bash(uip flow registry *)",
      "Bash(uip is *)",
      "Bash(uip or folders *)",

      "Bash(uip flow init *)",
      "Bash(uip flow validate *)",
      "Bash(uip flow tidy *)",
      "Bash(uip flow node *)",
      "Bash(uip flow edge *)",

      "Bash(uip solution new *)",
      "Bash(uip solution project *)",
      "Bash(uip solution resource *)",

      "Bash(uip agent validate *)"
    ],
    "ask": [
      "Bash(uip login)",
      "Bash(uip login --authority *)",
      "Bash(uip flow debug)",
      "Bash(uip flow debug *)",
      "Bash(uip flow pack)",
      "Bash(uip flow pack *)",
      "Bash(uip solution upload)",
      "Bash(uip solution upload *)",
      "Bash(uip solution publish)",
      "Bash(uip solution publish *)",
      "Bash(uip agent init)",
      "Bash(uip agent init *)"
    ]
  }
}
```

## Notes

- Pattern syntax is literal-prefix + `*` wildcard with a space before `*` — see the [Claude Code settings docs](https://code.claude.com/docs/en/settings.md#permissions-configuration).
- `Bash(uip login status *)` matches `uip login status --output json`; `Bash(uip login)` (exact, no wildcard) matches only the bare interactive login so it keeps its prompt.
- If the user has existing `permissions.deny` rules mentioning `uip`, do not remove them — respect explicit denials even if they conflict with the recommended allowlist. Surface the conflict in chat and ask.
- Never modify `~/.claude/settings.json` without explicit consent — that file often contains secrets (tokens, env vars) and should not be edited casually. If the user picks the global option, re-confirm before writing.
- This allowlist intentionally excludes `uip solution upload`, `uip flow debug`, and `uip flow pack / publish` — these produce real cloud side effects (publishing, executing flows) and should keep their prompt per the `uipath-maestro-flow` skill's Critical Rule 9.
