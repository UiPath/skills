# User Usage & Top-ups

Read per-user license consumption and grant, track or request consumable top-ups for individual users (the "User Licensing Revamp" surface of `uip platform users`).

> For full option details, run `uip platform users usage --help` or `uip platform users top-ups --help`.

---

## When to Use

- Finding who in the organization is eating into their monthly allowance or top-up wallet (`users usage list`)
- Showing one user's consumption per consumable and per service (`users usage get`)
- Granting a user extra consumable units as an admin, and checking the grant job (`users top-ups create`, `users top-ups get`)
- Asking for a top-up for yourself as a regular user (`users top-ups request`)

## Prerequisites

1. Authenticated — verify with `uip login status`; if not, ask the user to run `uip login` (interactive browser flow)
2. `usage list`, `usage get <user>`, `top-ups create` and `top-ups get` are admin-scoped (View/Manage on licensing data). `usage get` with no user and `top-ups request` work for any logged-in user and always act on the logged-in user
3. For `usage get <user>` and `top-ups create <user>`: the user is resolvable from a directory search — name or email prefix must match **exactly one** user
4. For `top-ups create`: the organization holds an active `PLTU` or `AGU` pool, and the recipient holds the `Platform.EligibleForTopUp` entitlement (enforced by the grant job, not prechecked by the CLI)
5. `top-ups request` is feature-gated on the server (`EnableUserTopUp`); when the gate is off the command fails with not-found

---

## Commands

| Command | What it does |
|---------|--------------|
| `uip platform users usage list` | The organization's user-usage table: one row per user with monthly and top-up wallet percent consumed (paginated) |
| `uip platform users usage get <user>` | One user's consumption per consumable, with a per-service breakdown and the top-up wallet (admin) |
| `uip platform users usage get` | The same for the logged-in user (no argument) |
| `uip platform users top-ups create <user> [--wait] [--count <n>]` | Grant a top-up to a user. The source pool is resolved automatically |
| `uip platform users top-ups get <job-id>` | Status of a top-up grant job |
| `uip platform users top-ups request` | Ask for a top-up for yourself. The organization's governance policy decides whether admins are notified or the top-up is granted on the spot |

---

## Consumption Model

Consumption is reported as **percent-of-pool consumed**, never as a price or an absolute count:

- `monthlyPercentConsumed` — the monthly allowance pool.
- `topUpWalletPercentConsumed` (table) / `topUpWallet.monthlyPercentConsumed` (detail) — the top-up wallet.
- A `null` percent means **N/A** (the user has no allowance). That is different from `0` (unused).

### Service names in the per-service breakdown

Each consumable's `services[]` entry has a `service` field (the raw wire value, e.g. `AgentDevelopment`) and a `serviceName` field (its English display name, matching what the web product shows). An unrecognized `service` falls back to the raw value as its `serviceName`, so a new value never breaks the output.

| `service` | `serviceName` | Roughly covers |
|---|---|---|
| `Delegate` | Delegate | Delegate task execution |
| `AgentDevelopment` | Agent Development | Agent Playground runs, agent evals, coded-agent playground |
| `ConversationalAgents` | Conversational Agents | Conversational agent execution and playground |
| `AutopilotForEveryone` | Autopilot for Everyone | Autopilot's semantic copy-paste and natural-language prompt/response actions |
| `Autopilot` | Autopilot | Autopilot execution |
| `Screenplay` | ScreenPlay Development | Agent design in ScreenPlay / UI automation |

The "roughly covers" column is a reading hint, not a stable contract — do not build logic on it.

---

## Step 1: The Organization's User-Usage Table

```bash
uip platform users usage list --output json

# Page, sort, and filter to users holding specific bundles
uip platform users usage list --limit 50 --offset 50 --sort-by email --sort-order asc --license-codes RPADEVPRONU ATTUNU --output json
```

```json
{
  "Result": "Success",
  "Code": "UserUsageList",
  "Data": [
    {
      "userId": "11111111-1111-1111-1111-111111111111",
      "email": "jane.doe@example.com",
      "displayName": "Jane Doe",
      "licenses": ["RPADEVPRONU"],
      "strongestLicense": "RPADEVPRONU",
      "monthlyPercentConsumed": 64,
      "topUpWalletPercentConsumed": 20,
      "topups": 2,
      "status": "TopUp"
    }
  ],
  "Pagination": {"Returned": 1, "Limit": 50, "Offset": 0, "HasMore": false}
}
```

| Field | Meaning |
|-------|---------|
| `status` | `MonthlyLimit` (consuming the monthly allowance), `TopUp` (consuming a top-up wallet) or `PaidUnits` (consuming paid organization units) |
| `topups` | Top-ups granted to the user in the current period |
| `strongestLicense` | The bundle that decides the user's allowance when they hold several |

Flags: `--limit` / `--offset` page through the table; `--sort-by <field>` sorts by any field of the row (e.g. `email`, `displayName`); `--sort-order asc|desc` is case-insensitive here (unlike `groups rules`, which wants `Asc`/`Desc`); `--license-codes <codes...>` is space-separated.

## Step 2: One User's Consumption

```bash
uip platform users usage get --output json                         # the logged-in user (the Preferences "Your usage" view)
uip platform users usage get "jane.doe@example.com" --output json  # a specific user (admin)
```

```json
{
  "Result": "Success",
  "Code": "UserUsage",
  "Data": {
    "userId": "11111111-1111-1111-1111-111111111111",
    "consumables": [
      {
        "entitlement": "AgenticPool",
        "monthlyPercentConsumed": 64,
        "resetsOn": "2026-08-01T00:00:00.000Z",
        "services": [
          {"service": "AgentDevelopment", "serviceName": "Agent Development", "percentOfPool": 40}
        ],
        "topUpWallet": {
          "monthlyPercentConsumed": 20,
          "topups": 2,
          "firstGrantedOn": "2026-07-10T09:00:00.000Z",
          "services": [],
          "topupCountPerMonth": [{"month": "2026-07-01T00:00:00.000Z", "topupCount": 2}]
        }
      }
    ]
  }
}
```

`topUpWallet` is present only when the user has been granted a top-up in the period.

## Step 3: Grant a Top-up (Admin)

```bash
uip platform users top-ups create "jane.doe@example.com" --output json            # start the grant (1 unit)
uip platform users top-ups create "jane.doe@example.com" --wait --output json     # start and wait for the job to finish
uip platform users top-ups create "jane.doe@example.com" --count 5 --output json  # grant 5 units in one call
```

- **The pool is never yours to choose.** The CLI resolves it from the organization's active consumables — `PLTU` first, else `AGU` — the same rule the service applies. There is no `--pool` flag.
- `--count` (1-100, default 1) is how many top-up units are granted in one call. The amount per unit is server-derived from pool + operation, so there is no amount flag.
- Recipient eligibility (`Platform.EligibleForTopUp`) is enforced by the grant job: the job always starts (202) and then fails during execution if the recipient is not eligible. Use `--wait` to see that outcome.

Without `--wait`:

```json
{
  "Result": "Success",
  "Code": "TopUpStarted",
  "Data": {"jobId": "b3f1c2d4-0000-0000-0000-000000000009", "status": "started", "pool": "AGU", "poolPercentConsumed": 42}
}
```

`poolPercentConsumed` reports how consumed the chosen pool already is. It can read over 100 — a pool over its allocation is still a valid source, since a top-up exists to let a user go past quota — and is `null` for an unlimited pool.

With `--wait`: the CLI polls the job until it leaves `started` (2 s interval, 2 min budget) and returns `Code: TopUpCompleted` with `granted: true`, or exits 1 with the rejection reason in `Instructions`.

## Step 4: Check a Grant Job

```bash
uip platform users top-ups get <JOB_ID> --output json
```

```json
{
  "Result": "Success",
  "Code": "TopUpStatus",
  "Data": {"jobId": "b3f1c2d4-0000-0000-0000-000000000009", "status": "completed", "granted": true, "rejectionReason": null}
}
```

`status` is `started` (still processing), `completed` or `failed`. `granted` is `true` only when the service actually granted the top-up.

## Step 5: Request a Top-up for Yourself (Self-Service)

Different from `create`: `request` asks for a top-up for **the logged-in user** and takes no user argument. The License Resource Manager decides the outcome from the organization's governance policy:

```bash
uip platform users top-ups request --output json
```

| Outcome | HTTP | CLI result |
|---------|------|------------|
| `NotificationSent` | 200 | exit 0, `Code: TopUpRequested`, `Data: { userId, outcome, message }`. The admins were notified; nothing is granted and there is no job to poll |
| `AutoGranted` | 200 | exit 0, `Code: TopUpAutoGranted`, `Data: { userId, outcome, message, jobId }`. The policy granted the top-up on the spot; poll `jobId` with Step 4 |
| `NotEligible` | 422 | exit 1, `Message: "Top-up request was not sent (NotEligible)."`, the server's reason in `Instructions` |
| `NoActiveDistribution` | 422 | as above — the organization has no active `PLTU`/`AGU` distribution to top up |
| `AlreadyGranted` | 422 | as above — the user still holds a top-up that is not used up |
| `AllowanceAvailable` | 422 | as above — the user's monthly allowance is not used up yet |

Refusals carry `ErrorCode: invalid_argument`, `Retry: RetryWillNotFix` and the outcome in `Context.errorCode`. **Do not retry in a loop** — a refusal only clears when the user's usage or entitlements change. When the user is out of units and the request is refused, the next step is an admin grant (Step 3), not another request.

---

## Error Conditions

| Error | Cause | Resolution |
|-------|-------|------------|
| `No directory user found matching '<input>'.` | No user with that name/email prefix | Use a more specific or correct prefix |
| `Multiple directory users matched '<input>'.` | Prefix matches more than one user | Use a more specific prefix or the full email |
| `The organization has no active top-up source pool.` | No active `PLTU` or `AGU` pool in the organization | Nothing to grant from; check `uip platform tenants licenses get` / the organization's licenses |
| `Invalid --count '<value>'.` | `--count` outside 1-100 or not an integer | Rejected before any lookup or grant; pass an integer in 1-100 |
| `Top-up <jobId> was not granted.` | The job finished without a grant (e.g. recipient not eligible) | Read `Instructions` for the rejection reason or the terminal status |
| `Top-up <jobId> did not finish (<outcome>).` | `--wait` ran out of its 2 min budget | Check again with `uip platform users top-ups get <job-id>` |
| `Top-up request was not sent (<outcome>).` | The service refused the self-service request (422) | See the outcome table above; an admin can grant with `top-ups create` |
| `Error requesting a top-up.` | The request failed for another reason (gate off → not-found, network, 5xx) | Read `Instructions`; re-run `uip login` if it is an auth error |
| `Error connecting to the License Resource Manager.` | Auth expired or network issue | Re-run `uip login` |
| `Not logged in.` | `usage get` (own) or `top-ups request` without a session | Run `uip login` first |

---

## Gotchas

- **Percent, not count.** Every consumption number is percent-of-pool consumed; `null` is N/A, `0` is unused. Do not sum percents across users.
- **`create` mutates real token balances.** Confirm the recipient before running it against a production organization.
- **`request` is not `create`.** `request` never grants anything itself unless the governance policy auto-grants; `create` is the admin grant. A refused `request` is a signal to use `create`.
- **Own-user commands follow the token.** `usage get` with no argument and `top-ups request` act on the logged-in user (the token's subject); `--organization` changes the organization, never the user.
- **`--sort-order` casing differs** between `users usage list` (`asc`/`desc`, case-insensitive) and `groups rules` (`Asc`/`Desc`, exact).
- **Older CLI builds report refusals generically.** Before the fix in UiPath/cli#4911, every refused request showed as `Error requesting a top-up.` with the raw HTTP 422, and `AutoGranted` was reported as a failure. If you see that, update the CLI.

---

## Related

- [Licensing hub](licensing.md) — concepts, product code table, REST fallback
- [User & Group Licenses](user-licenses-allocations.md) — the bundles that give a user an allowance in the first place
- [Consumables Report](consumables-report.md) — organization-level consumption reporting
- [Full CLI command reference](../uip-commands.md)
