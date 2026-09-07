# Enforcement Management

Manage the organization-wide IP-restriction enforcement switch (`uip admin ip-restriction enforcement`) and `my-ip` lookup. See [ip-restriction-commands.md](ip-restriction-commands.md) for per-command flags, output codes, and single-command examples.

## Concept

`enforcement` is a per-organization singleton switch:

- **Disabled** (default): platform-default access rules apply; `ip-ranges list` is data only.
- **Enabled**: only networks in `ip-ranges list` can reach the organization.

Toggling is idempotent. Enabling can lock out callers whose IP is not allowlisted, so the CLI requires `--confirm` and performs a `my-ip` pre-flight.

## Workflow: Pre-Flight Before Enabling Enforcement

1. Run:
   ```bash
   uip admin ip-restriction enforcement get --output json
   ```
2. Run:
   ```bash
   uip admin ip-restriction my-ip --output json
   ```
3. Run:
   ```bash
   uip admin ip-restriction ip-ranges list --output json
   ```
   Compare `my-ip`'s `ipAddress` with every entry's `ipNetwork` CIDR. If none covers the caller's IP, add one before enabling; see [ip-range-management.md — Workflow: Add an Entry](ip-range-management.md#add-an-entry-idempotent-on-cidr).

## Workflow: Enable Enforcement

1. Complete the pre-flight.
2. State the impact and obtain explicit confirmation in this turn. Render verbatim:

   ```
   ⚠️ About to enable IP Restriction for this organization.

   Impact:
   • Any caller — Portal session, CLI session, robot, external app, integration —
     whose source IP is not in `ip-ranges list` will be BLOCKED from this org
     starting immediately.
   • If the allowlist is misconfigured, you (and other admins) can be locked out.
     Recovery requires either an in-allowlist IP and `enforcement disable`,
     OR the UiPath Portal recovery flow — there is no CLI bypass.

   Pre-flight summary:
   • Caller IP (from `my-ip`):  <IP>
   • Allowlist entries covering it: <N>  (e.g., <CIDR-1>, <CIDR-2>)

   Proceed?  (yes / no)
   ```

   On `no`, stop. On `yes`, continue. Never replace this prompt with a one-line confirmation.
3. Run:
   ```bash
   uip admin ip-restriction enforcement enable --confirm --output json
   ```
   The CLI runs its own `my-ip` pre-flight and rejects enablement when the caller is not covered. If rejected, do not retry until the allowlist is fixed.
4. Immediately run `enforcement get` and `my-ip` again. Report success only if the caller's IP remains covered. If anything looks wrong, instruct the user to use the recovery flow before access is lost.

## Workflow: Disable Enforcement

Run:

```bash
uip admin ip-restriction enforcement disable --output json
```

Disabling is safe and idempotent, restores platform-default access, requires no `--confirm`, and can recover a near-lockout or bypass the `ip-ranges delete` safety pre-flight.

## Recovery from Lockout

1. Access UiPath from an IP already in the allowlist, such as another VPN or office network, then run `enforcement disable`.
2. If no such IP is available, have the organization owner use the UiPath Portal lockout-recovery flow or contact support. There is no CLI bypass.
