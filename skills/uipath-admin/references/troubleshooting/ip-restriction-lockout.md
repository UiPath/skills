# IP Restriction Troubleshooting

Diagnostic workflows for IP allowlist and enforcement issues.

## Playbook 9: IP Restriction Lockout

**Symptom:** User or admin locked out of org after enabling IP restriction enforcement. API calls and Portal access fail.

1. Attempt to check enforcement state (may fail if caller is locked out):
   ```bash
   uip admin ip-restriction enforcement get --output json
   ```

2. If command succeeds → caller's IP is in the allowlist. The lockout affects other users/IPs. Skip to step 4.

3. If command fails (403 / network error) → caller IS locked out. Recovery options:
   - **Option A:** Access from an IP that IS in the allowlist (VPN, jump box, office network), then disable enforcement:
     ```bash
     uip admin ip-restriction enforcement disable --output json
     ```
   - **Option B:** Use the UiPath Portal recovery flow (platform-side, no CLI)
   - **No CLI bypass exists** — Rule 32: recovery requires platform-side action or access from an allowed IP

4. Once enforcement is disabled (or accessed from an allowed IP):
   ```bash
   uip admin ip-restriction my-ip --output json
   uip admin ip-restriction ip-ranges list --output json
   ```
   Compare caller's IP against the allowlist entries. Add missing IPs before re-enabling.

5. Before re-enabling enforcement, run the safety pre-flight (Rule 31):
   - Verify caller's IP is covered by an entry in `ip-ranges list`
   - Prompt user with impact statement before `enforcement enable --confirm`

## Playbook 10: Enforcement Not Blocking as Expected

**Symptom:** IP restriction is supposedly enabled but unwanted IPs can still access the org.

1. Verify enforcement is actually enabled:
   ```bash
   uip admin ip-restriction enforcement get --output json
   ```
   If `enabled: false` → enforcement is off; the allowlist is not enforced. Enable with `enforcement enable --confirm`.

2. List all allowlist entries:
   ```bash
   uip admin ip-restriction ip-ranges list --output json
   ```
   Check for overly permissive entries (e.g., `0.0.0.0/0` allows everything).

3. List bypass rules:
   ```bash
   uip admin ip-restriction bypass-rules list --output json
   ```
   Check if a bypass rule's URL regex pattern matches too broadly — bypass rules allow traffic from ANY IP on matching URLs.

4. Common causes:
   - **Enforcement disabled** → simply not turned on
   - **Overly broad CIDR** → a `/8` or `/16` range covering more IPs than intended
   - **Bypass rule too permissive** → regex like `.*` or `/api/.*` bypasses enforcement for all API traffic
   - **Expired entry still active** → entry with past `expires` date was not auto-removed (check if platform auto-cleans)

5. Fix: update or delete the overly permissive entries/rules, then verify with a test request from a blocked IP.
