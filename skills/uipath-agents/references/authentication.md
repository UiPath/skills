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

# Production cloud (one-shot, non-interactive)
uip login --organization "<ORG>" --tenant "<TENANT>" --output json

# Staging
uip login --authority "https://staging.uipath.com/identity_" --organization "<ORG>" --tenant "<TENANT>" --output json

# Alpha
uip login --authority "https://alpha.uipath.com/identity_" --organization "<ORG>" --tenant "<TENANT>" --output json

# Service principal (unattended)
uip login --client-id "<ID>" --client-secret "<SECRET>" --base-url "<URL>" --output json
```

## Critical Rules

- **`uip login status --output json` once per invocation.** Reports `Status`, `Organization`, `Tenant`, `Expiration Date`. After one `Logged in`, trust the wrapper — it auto-refreshes tokens on forwarded cloud calls. No `uip login refresh` subcommand exists. Re-auth only on a real `401`.
- **NEVER run `uip login` without `--tenant`.** The interactive tenant picker cannot be driven from Claude's Bash tool.
- **When auth is needed, ask one question, then stop.** If the status check shows the user is not logged in, your entire response must be exactly this question — no headers, no bullets, no next-steps:

  > What is your UiPath **environment** (cloud / staging / alpha), **organization name**, and **tenant name**?

  Wait for the reply, then run the matching command from the Quick Reference.

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
