# uipath-a2a-agents — eval task suite

Regression tasks for the `uipath-a2a-agents` skill (Agent Gateway remote A2A agents). Two kinds:

- **Live e2e** (`e2e-remote-agent`) runs the real CLI against the shared test tenant. It writes `report.json` (`{"slug", "folder_path"}`), and the `post_run` hook `_setup/cleanup_a2a_agent.py` deletes that agent (`remote-a2a-agent delete --yes`). Remote A2A agents are off on Automation Suite, so the Automation Suite ETE run skips it (the skip is in coder_eval_uipath's `ete_unsupported.py`, merged with this suite).
- **Mocked smoke tasks** replay the agent against a manifest-driven `uip` CLI mock: no live UiPath tenant, no network. Each response file is a real CLI envelope captured from `uip agenthub remote-a2a-agent` against a test tenant, with ids, names, URLs and tenant values replaced by the mock values (`Shared` / `0f0f0f0f-0000-4000-8000-0000000000f1`, `https://agent.example.com`, `mock.user@example.com`, connection ids `7a1b2c3d-…aa` (OAuth) and `…bb` (Personal Access Token)).

## Layout

```
tests/tasks/uipath-a2a-agents/
├── README.md
├── _shared/mock_template/mocks/
│   ├── uip                            # mock dispatcher (the MCP suite's, plus match_all and after rules)
│   └── responses/                     # responses every task shares: help_*.txt, *_print_schema.json, or_folders_list.json
├── _setup/cleanup_a2a_agent.py        # e2e post_run cleanup
├── e2e-remote-agent/                  # live
├── not-supported-as/                  # mocked
├── diagnose-502-non-oauth/            # mocked
├── create-card-url/                   # mocked
├── create-oauth-connection/           # mocked
├── create-pat-only/                   # mocked
├── create-apikey-asset/               # mocked
├── update-headers-masked/             # mocked
├── user-connection-set-other/         # mocked
├── relay-on/                          # mocked
└── delete-confirm/                    # mocked
    ├── task.yaml
    ├── check_<name>.py                # grades mocks/.calls.jsonl
    └── fixtures/mocks/responses/
        ├── manifest.json              # rule dispatch → response file
        └── *.json                     # captured responses for this scenario
```

Each task copies `_shared/mock_template` first and its own `fixtures` second, so a task's file replaces a shared one of the same name.

The mock here also takes `"match_all": [<substring>, ...]`: the rule matches when every substring is in the command, in any order. Flags arrive in any order, so this is how a manifest tells `update --dry-run` from `create --dry-run`.

A rule may also take `"after": [<substring>, ...]`: it matches only once an earlier call that succeeded, and was not a `--dry-run`, `--help` or `--print-schema` call, carried every substring. That is how `get` and `list` answer the state after the agent's change (headers set, Relay on, the agent deleted, Jane's connection set) and the starting state until then.

The connection rows of `is connections list` carry the same `ByoaConnection` value, so nothing in them gives away a connection's auth type, which the CLI cannot show.

## Running

From the repo root (one-time `make install` in `tests/` first):

```bash
cd tests
.venv/bin/coder-eval run tasks/uipath-a2a-agents/create-card-url/task.yaml -e experiments/default.yaml -v
```

A passing run scores 1.0. `mocks/.calls.jsonl` in the run artifact shows which rule answered each command.

## Coverage

Rule numbers reference the SKILL.md Critical Rules (1-10).

| Scenario | Tier | Rules | Key assertion |
|---|---|---|---|
| `create-card-url` | smoke (mock) | 1, 2, 4 | one successful `create --slug vendor-agent --agent-card-url <card URL>` without a connection, and a successful create or `update` that sent `X-API-Key=%ASSETS/VendorKey%` exactly. The mock answers a create from a card URL with an asset-backed header with the CLI's real 403, so the header lands with `update --header`. |
| `create-apikey-asset` | smoke (mock) | 1, 4 | as above with `Authorization=%ASSETS/VendorToken%`; any write that sends `Authorization=Bearer %ASSETS/VendorToken%` fails. |
| `create-oauth-connection` | smoke (mock) | 1, 3 | a successful `create --agent-card-url https://agent.example.com/api/a2a/agentCard/v1.0 --connection-id <OAuth id>`; no write sends the PAT connection; no `--agent-card-json`. `is connections list` cannot show the types; the simulated user names them when asked. |
| `create-pat-only` | smoke (mock) | 3 | no write sends the PAT connection; LLM judge: the answer says it cannot work and offers an asset-backed `--header`. |
| `update-headers-masked` | smoke (mock) | 1, 6 | a successful `update vendor-agent` sends `X-Api-Key=****` (as stored) with `X-Region=us`, and one sets the description; every update that sends headers keeps `X-Api-Key=****`; none re-sends the card (`--agent-card-json`). The mock answers `X-Region=****` with the CLI's real refusal. |
| `user-connection-set-other` | smoke (mock) | 5, 8, Per-User Connections | `remote-a2a-agent-user-connections set --agent foundry-agent` for Jane (`--user-email` / `--user-id`) and her connection (`--connection-id` / `--connection-name`) after a `--dry-run`; never `--me`; no `update --connection-id`. |
| `relay-on` | smoke (mock) | 1, Relay | the last Relay change on `vendor-agent` is `update --use-relay`; no create or delete. |
| `delete-confirm` | smoke (mock) | 1, 9 | exactly one `delete vendor-agent --yes`; LLM judge: the agent named the agent and got the simulated user's yes before it. The mock answers a delete without `--yes`, `--dry-run` included, with the CLI's real `confirmation_required`. |
| `not-supported-as` | smoke (mock) | 10, Automation Suite | every call that reaches the service answers the CLI's `not_supported`; at most two real creates, no `uip login`, no MCP server instead; LLM judge: the answer says remote A2A agents aren't available on the connected environment. |
| `diagnose-502-non-oauth` | smoke (mock) | 3, Troubleshooting | after the user's 502 with a PAT connection: at most one more create with it, no update setting it; either nothing registered, or `vendor-agent` registered with `Authorization=%ASSETS/VendorToken%`; LLM judge: the answer names the non-OAuth connection as the cause. |
| `e2e-remote-agent` | e2e (live) | 1, 2, Registering an Agent | from `--agent-card-json`: `get` shows the card's `url`, the new description and the name, with no headers, connection or Relay. |
