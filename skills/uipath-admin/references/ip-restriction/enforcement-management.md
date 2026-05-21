# Enforcement Management

Multi-step workflows for the org-wide IP-restriction enforcement switch (`uip admin ip-restriction enforcement`) and the `my-ip` lookup that supports it. For per-command flag tables, output codes, and single-command examples, see [ip-restriction-commands.md](ip-restriction-commands.md).

## Concept

`enforcement` is a singleton switch per organization:

- **Disabled** (default) — platform default access rules apply; `ip-ranges list` is just data, no enforcement.
- **Enabled** — only IP networks in `ip-ranges list` can reach this org. Everything else is blocked.

Toggling the switch is **idempotent** on both sides — flipping twice is a safe no-op.

**Lockout risk is real.** Enabling enforcement with the caller's IP outside the allowlist locks the caller out (and possibly the whole org). The CLI has two safety rails:

1. `enforcement enable` runs a `my-ip` pre-flight and **rejects** the call if the caller's IP is not covered by any entry in `ip-ranges list`.
2. `--confirm` is required to acknowledge the lockout risk.

## Workflow: Pre-Flight Before Enabling Enforcement

Before flipping `enforcement enable`, confirm the caller's IP is in the allowlist. The CLI runs the same check server-side and will reject otherwise — front-loading it lets you fix the allowlist explicitly instead of guessing from a rejected call.

1. Check current state:
   ```bash
   uip admin ip-restriction enforcement get --output json
   ```
2. Look up the caller's public IP:
   ```bash
   uip admin ip-restriction my-ip --output json
   ```
3. List allowlist entries and verify the IP is covered:
   ```bash
   uip admin ip-restriction ip-ranges list --output json
   ```
   Compare `my-ip`'s `ipAddress` against each entry's `ipNetwork` CIDR. If no entry covers your IP, add one before enabling — see [ip-range-management.md — Workflow: Add an Entry](ip-range-management.md#workflow-add-an-entry-idempotent-on-cidr).

## Workflow: Enable Enforcement

1. Run the pre-flight above.
2. **State the impact and prompt for an explicit confirmation.** Do not run `enforcement enable` until the user has acknowledged the impact in this turn. Render verbatim:

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

   On "no" → stop. On "yes" → run the command. **Never substitute the prompt with a one-line "are you sure".** The full impact statement is required because of the lockout severity.

3. Enable:
   ```bash
   uip admin ip-restriction enforcement enable --confirm --output json
   ```

The CLI runs its own `my-ip` pre-flight and rejects the call if the caller is not covered. If rejected, do NOT retry until the allowlist is fixed.

4. **Post-state check.** Re-run `enforcement get` and `my-ip` immediately after. If the caller's IP is still covered, report success. If something looks off, instruct the user to use the recovery flow before they lose access.

## Workflow: Disable Enforcement

Safe and idempotent — restores platform default access:

```bash
uip admin ip-restriction enforcement disable --output json
```

No `--confirm` required. Use to recover from a near-lockout, or to bypass the `ip-ranges delete` safety pre-flight.

## Recovery from Lockout

If `enforcement enable` succeeded but a subsequent change locked the caller out:

1. Access UiPath from an IP already in the allowlist (e.g., a different VPN or office network), then run `enforcement disable`.
2. If no such IP is available, the org owner must use the UiPath Portal lockout-recovery flow or contact support — there is no CLI bypass.
