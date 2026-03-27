# Content Quality Rules

Standards for documentation quality across all skills and references.

## Writing for AI Agents

This repository's primary audience is AI coding agents, not humans. Write accordingly:

- **Be prescriptive, not descriptive.** Say "Run this command" not "You could run this command."
- **Include exact CLI commands** with all required flags. Agents copy-paste — don't make them guess.
- **Use `--format json`** on any CLI command whose output the agent needs to parse.
- **Specify error handling.** Tell the agent what to do when a command fails, not just the happy path.
- **Number your rules.** Agents follow numbered lists more reliably than prose.
- **Include anti-patterns.** "What NOT to do" sections prevent the most common and expensive mistakes.

## Markdown Standards

- Use ATX-style headers (`#`, `##`, `###`) — not underline style
- Use fenced code blocks with language identifiers: ` ```bash `, ` ```yaml `, ` ```csharp `, ` ```json `
- Use tables for structured data (CLI flags, option mappings, package versions)
- Use `>` blockquotes for important warnings and notes
- Use bullet lists for unordered items, numbered lists for sequential steps or prioritized rules
- Heading hierarchy must not skip levels (no `##` followed by `####`)

## CLI Command Documentation

- Show the full command with all required flags
- Use `<PLACEHOLDER>` for user-provided values (angle brackets, UPPER_SNAKE_CASE)
- Specify whether a flag is required or optional
- Show expected output when it clarifies behavior
- Group related commands together

Example:
```bash
uip rpa validate --file-path "<FILE_PATH>" --project-dir "<PROJECT_DIR>" --format json
```

## Cross-Platform Awareness

- Shell commands must use Unix syntax (`/dev/null`, forward slashes, `rm`/`ls`/`cp`)
- Never use Windows-specific commands (`del`, `dir`, `copy`, `nul`) in skill documentation
- Escape backslashes in file paths when showing them in code: `C:\\path\\file.txt`
- When a tool is platform-specific, state the requirement upfront (e.g., "Windows only")

## What NOT to Include

- No marketing language or promotional content
- No version-specific information that will become stale (link to latest docs instead)
- No duplicate content — if the information exists in another reference file, link to it
- No auto-generated content without review (e.g., raw CLI `--help` output)
- No images or binary files (use text-based formats: ASCII diagrams, markdown tables, mermaid)
