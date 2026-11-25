# Content Quality Rules

Standards for documentation quality across all skills and references.

## Writing for AI Agents

This repository's primary audience is AI coding agents, not humans. Write accordingly:

- **Be prescriptive, not descriptive.** Say "Run this command" not "You could run this command."
- **Include exact CLI commands** with all required flags. Agents copy-paste — don't make them guess.
- **Use `--output json`** on any CLI command whose output the agent needs to parse.
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
- Use a placeholder for any example value that carries the shape of a date, an identifier, or personal data — customer content-inspection gates match on shape alone and block the whole published package. Write `--expiration "<EXPIRATION_DATE>"`, never `--expiration "2027-01-15"`; write `<STREET_ADDRESS>` and `<PHONE_NUMBER>`, never a sample address or phone number; mask digit positions as `NNN-NN-NNNN`. State the required format in prose instead: ``--expiration <date>``, ISO 8601 `YYYY-MM-DD`.
- Give each value one placeholder covering the whole value. Never glue a placeholder to a literal fragment: write `--from-date <FROM_TIMESTAMP>`, not `--from-date <FROM_DATE>T00:00:00Z`.
- Validate with `python3 scripts/check-sensitive-content.py` — the `Scan shipped content for customer-blocked data` required check runs it on every PR, and both publish workflows run it on the packed tarball. Block-tier findings (card numbers, SSNs, `MM/DD/YYYY` or `--expiration` dates, phone numbers, street addresses, tokens) fail; warn-tier shapes are annotated on the diff.
- Keep product identifiers the reader needs verbatim — error codes, support-forum thread IDs in URLs, vendor documentation URLs. Those are content, not examples.
- Specify whether a flag is required or optional
- Show expected output when it clarifies behavior
- Group related commands together

Example:
```bash
uip rpa get-errors --file-path "<FILE_PATH>" --project-dir "<PROJECT_DIR>" --output json
```

## Credentials and Authentication

Skill content MUST NOT put a credential into agent context. Applies to `skills/`, `skill-flavors/`, and task prompts under `tests/tasks/`.

1. **Never read the `uip` credentials file.** No step may `cat`, `grep`, `source`, `jq`, open, or decode `~/.uipath/.auth` or any profile's credentials file. It holds a live access token (not revoked by logout) and the refresh token. `uip login which` may return the file's path; never open the file it names.
2. **Session details come from `uip login status --output json`** — base URL, organization, tenant, user id, user email. Never parse them from the credentials file or a decoded JWT.
3. **REST calls go through `uip api`.** CLI makes the call and holds the token. Never extract a bearer token for `curl`, `fetch`, or SDK code.
4. **Never run `uip login refresh` bare or print its output** — it contains `Data.AccessToken`. Never use it as a token source when `uip api` covers the call.
5. **Never ask the user to paste a token, password, or client secret** into the conversation. Send them to `uip login` instead.
6. **Studio Web flavors:** browser bundle does not register `uip api` or `uip login refresh`. Use a command the bundle runs (e.g. `uip solution resources get`) or stop and report the value as unavailable — never fall back to a token.
7. **Mention the credentials file only to forbid it** — e.g. a "never include `~/.uipath/.auth`" list.

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
