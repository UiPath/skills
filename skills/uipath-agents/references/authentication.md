# UiPath Authentication

Authenticate before running cloud commands. Do not hand-edit auth tokens; run `uip login`. The wrapper resolves the auth env file, injects credentials into forwarded subprocesses, and refreshes access tokens automatically when needed. The Python CLI also loads local `.env` on startup. `uip codedagent` has no auth subcommand; run all auth flows through root-level `uip login`.

## Commands

| Command | Arguments | Purpose |
|---|---|---|
| `uip login` | flags | Establish a session |
| `uip login status` | none | Report login state |
| `uip login tenant list` | none | List tenants |
| `uip login tenant set <name>` | positional `<name>`; not `--tenant` | Switch active tenant |
| `uip logout` | none | Clear the session |

## Rules

- Run `uip login status --output json` once per invocation. It reports `Status`, `Organization`, `Tenant`, and `Expiration Date`. If no specific organization or tenant is requested, trust one `Logged in` result; forwarded cloud commands auto-refresh tokens. There is no `uip login refresh` command. Re-authenticate only after a real `401`.
- If the user supplied environment, organization, and tenant, connect with those exact values. Run or capture `uip login status --output json` if requested or required, then run the matching one-shot command below, including `--authority` for staging or alpha, even if an existing session is `Logged in`; it may target another organization or tenant. Do not ask another auth question when all three values are present.
- Interactive sign-ins belong in the user's terminal. Every `uip login` without `--client-secret` opens a browser and blocks until completion; a shell-tool run may show the user nothing and may time out. Prefer asking the user to run the exact one-shot command themselves; in Claude Code, prefix it with `!` to run it inside the session. If you run it, first tell the user that a browser window will open and the command will wait. Never pass `--no-browser` for human sign-in; it is for automation that opens the printed URL programmatically, and copy/pasting a relayed URL is fragile because line-wrapping or truncation causes an opaque browser-side identity-server error.
- Never run `uip login` without `--tenant`; Claude's Bash tool cannot drive the interactive tenant picker.
- When authentication is needed, the user has not supplied all of environment, organization, and tenant, and status shows they are not logged in, respond with exactly this question and nothing else:

  > What is your UiPath **environment** (cloud / staging / alpha), **organization name**, and **tenant name**?

  Wait for the reply. Then follow the interactive-sign-in rule: give the user the exact one-shot command below to run in their terminal, or, if you run it, first say that a browser window will open. Confirm with `uip login status --output json`.

## Environment and Login Commands

| Environment | Command |
|---|---|
| cloud (default) | `uip login --organization "<ORG>" --tenant "<TENANT>" --output json` |
| staging | `uip login --authority "https://staging.uipath.com/identity_" --organization "<ORG>" --tenant "<TENANT>" --output json` |
| alpha | `uip login --authority "https://alpha.uipath.com/identity_" --organization "<ORG>" --tenant "<TENANT>" --output json` |

For on-premise Automation Suite, run `uip login --authority <identity-url>` pointing at the instance.

## Unattended Service-Principal Login

Run:

```bash
uip login --client-id "<ID>" --client-secret "<SECRET>" --base-url "<URL>" --output json
```

This requires no browser. Pass `env.VAR_NAME` for `--client-id` or `--client-secret` to read an environment variable.

## Unknown Tenant

Run:

```bash
uip login --organization "<ORG>" --output json
uip login tenant list --output json
```

Present the tenants and ask which one to use, then run:

```bash
uip login tenant set "<SELECTED>" --output json
```

## Troubleshooting

| Error | Cause | Solution |
|---|---|---|
| `401 Unauthorized` | Session expired | Re-run the appropriate `uip login` command above |
| `No tenant selected` | Ran `uip login` without `--tenant` or `--interactive` | Re-run with `--organization <org> --tenant <tenant>` |
| `Tenant not found` | Misspelled tenant or insufficient access | Run `uip login tenant list --output json`; names are case-sensitive |
| Browser does not open | SSH/container has no default browser | Use service-principal login with `--client-id` and `--client-secret` |

## Network Configuration

The CLI honors `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`, and `REQUESTS_CA_BUNDLE`.
