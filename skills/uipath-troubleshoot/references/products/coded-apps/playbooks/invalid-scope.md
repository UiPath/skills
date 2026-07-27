---
confidence: high
---

# invalid_scope in Auth URL

## Context

What this looks like:
- The browser returns from UiPath (or stops on a UiPath error page) with `error=invalid_scope` in the URL
- The failing OAuth `authorize` request carries a `scope=` parameter listing one or more values the server rejects
- Failure happens **before** login completes — the user never reaches the app authenticated (distinct from a post-login `401`, which is [api-401-after-login.md](./api-401-after-login.md))

What can cause it:
- A scope listed in the `uipath.json` `scope` field is **not enabled** on the External Application
- A new SDK service was added to the app (e.g. `new Entities(...)`, `new Tasks(...)`) and its scope was added to `uipath.json` but never registered on the client
- A typo or non-existent scope string in `uipath.json`

What to look for:
- Which requested scope is present in `uipath.json` but absent from the registered scope list
- Which SDK services the app constructs — each maps to a required scope

## Investigation

1. Read the scopes the app requests from `uipath.json`:

   ```bash
   cat uipath.json
   ```

2. Read the scopes registered on the External Application:

   ```bash
   uip admin external-apps get <client-id> --output json \
     --output-filter "scopes"
   ```

3. The rejected scope is one requested in step 1 but missing in step 2. Confirm every service the app uses has its scope registered — grep the source for SDK service construction:

   ```bash
   grep -rnE "new (Assets|Buckets|Queues|Processes|Jobs|Tasks|Entities|MaestroProcesses|Cases|ConversationalAgent)\(" src/
   ```

   Common service → scope mapping (use the most specific scope that covers the calls):

   | SDK service | Scope |
   |-------------|-------|
   | `Assets` | `OR.Assets.Read` (or `OR.Assets`) |
   | `Jobs` / `Processes` | `OR.Jobs` and `OR.Execution` |
   | `Queues` | `OR.Queues.Read` (or `OR.Queues`) |
   | `Tasks` | `OR.Tasks` |
   | `Buckets` | `OR.Buckets` |
   | `Entities` (Data Fabric) | `DataFabric.Schema.Read` + `DataFabric.Data.Read` (+ `DataFabric.Data.Write` for writes) |
   | `MaestroProcesses` / `Cases` | `PIMS` (+ `OR.Execution.Read`) |

## Resolution

> Coded web apps are **non-confidential (public) PKCE clients** — use `--user-scope`, not `--app-scope`. `--user-scope` on `update` **replaces** the registered scopes, so pass the full set (existing from step 2 **plus** the missing scope).

- **If a requested scope is not registered:** add it to the External Application. Ensure the same scope is also present in `uipath.json` `scope` (space-separated):

  ```bash
  uip admin external-apps update <client-id> \
    --user-scope '<existing-scopes>,<missing-scope>' \
    --output json
  ```

- **If `uipath.json` lists a typo / non-existent scope:** correct the `scope` string in `uipath.json` to a valid scope from the mapping above, then restart the dev server.

After registering the scope, clear browser storage and re-authenticate so the new token request includes the corrected scope set.
