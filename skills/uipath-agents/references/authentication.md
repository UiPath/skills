# UiPath Authentication

Authenticate before running cloud commands. Do not hand-edit auth tokens — use `uip login`. The wrapper resolves the auth env file and injects credentials into forwarded subprocesses, and refreshes the access token automatically when needed; the Python CLI also loads local `.env` on startup. The `uip codedagent` wrapper does not expose an auth subcommand; all auth flows go through `uip login` at the CLI root.

## Command Surface

| Command | Argument style | Purpose |
|---------|----------------|---------|
| `uip login` | flags | Establish a session |
| `uip login status` | none | Report current login state |
| `uip login tenant list` | none | List tenants for the current session |
| `uip login tenant set <name>` | positional `<name>` (not `--tenant`) | Switch the active tenant |
| `uip logout` | none | Clear the session |

## Quick Reference

```bash
# Status (includes "Expiration Date") — the wrapper auto-refreshes tokens before forwarding cloud commands
uip login status --output json

# Production cloud (one-shot browser sign-in, org/tenant pre-selected — see Critical Rules for who runs it)
uip login --organization "<ORG>" --tenant "<TENANT>" --output json

# Staging
uip login --authority "https://staging.uipath.com/identity_" --organization "<ORG>" --tenant "<TENANT>" --output json

# Alpha
uip login --authority "https://alpha.uipath.com/identity_" --organization "<ORG>" --tenant "<TENANT>" --output json

# Service principal (unattended)
uip login --client-id "<ID>" --client-secret "<SECRET>" --base-url "<URL>" --output json
```

## Critical Rules

- **`uip login status --output json` once per invocation.** Reports `Status`, `Organization`, `Tenant`, `Expiration Date`. When the user has not asked to connect to a specific org/tenant, trust one `Logged in` result — the wrapper auto-refreshes tokens on forwarded cloud calls. No `uip login refresh` subcommand exists. Re-auth only on a real `401`.
- **If the user supplied environment + organization + tenant, connect with those exact values.** First run/capture `uip login status --output json` if requested or required, then use the matching one-shot command from the Quick Reference (`uip login --organization "<ORG>" --tenant "<TENANT>" --output json`, plus `--authority` for staging/alpha) — see the next rule for who runs it. Do this even if the status check reports an existing `Logged in` session, because the active session may point at a different org/tenant. Do not ask another auth question when all three values are already present.
- **Interactive sign-ins belong in the user's own terminal.** Every `uip login` without `--client-secret` is a browser sign-in: it blocks until the person completes it, and run from your shell tool it shows them nothing while your tool's timeout can kill it mid-wait. Prefer asking the user to run the one-shot command themselves (in Claude Code, prefix it with `!` so it runs inside the session); if you do run it, first tell the user a browser window is about to open and the command will wait for them. **Never pass `--no-browser` for a human sign-in** — that flag is for automation that opens the printed URL programmatically; relaying the URL by copy/paste is fragile (a line-wrapped or truncated copy is rejected by the identity server with an opaque browser-side error).
- **NEVER run `uip login` without `--tenant`.** The interactive tenant picker cannot be driven from Claude's Bash tool.
- **When auth is needed and the user did not supply all values, ask one question, then stop.** If the status check shows the user is not logged in and any of environment / organization / tenant is missing, your entire response must be exactly this question — no headers, no bullets, no next-steps:

  > What is your UiPath **environment** (cloud / staging / alpha), **organization name**, and **tenant name**?

  Wait for the reply, then follow the interactive-sign-ins rule above: give the user the exact one-shot command from the Quick Reference to run in their own terminal (or, if you run it, first tell them a browser window is about to open), and confirm with `uip login status --output json`.

## Environment → Authority Mapping

| User says | Flag to use |
|-----------|-------------|
| cloud (default) | no `--authority` flag |
| staging | `--authority "https://staging.uipath.com/identity_"` |
| alpha | `--authority "https://alpha.uipath.com/identity_"` |

For on-premise Automation Suite, use `--authority <identity-url>` pointing at your instance.

## Unattended (Service Principal)

```bash
uip login --client-id "<ID>" --client-secret "<SECRET>" --base-url "<URL>" --output json
```

Works without a browser. Values for `--client-id` and `--client-secret` can be passed as `env.VAR_NAME` to read from an environment variable.

## If the User Doesn't Know Their Tenant

```bash
uip login --organization "<ORG>" --output json
uip login tenant list --output json
# Present tenants, ask which one:
uip login tenant set "<SELECTED>" --output json
```

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Session expired | Re-run the appropriate `uip login` command from the Quick Reference |
| `No tenant selected` | Ran `uip login` without `--tenant` or `--interactive` | Re-run with `--organization <org> --tenant <tenant>` |
| `Tenant not found` | Tenant name misspelled or user lacks access | Run `uip login tenant list --output json` to see exact names (case-sensitive) |
| Browser does not open | Running under SSH/container without a default browser | Use service-principal flow (`--client-id`, `--client-secret`) |

## Network Configuration

The CLI honours `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`, and `REQUESTS_CA_BUNDLE`.
