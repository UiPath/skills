---
confidence: high
---

# Deploy Fails: `routing name must be unique`

## Context

What this looks like:
- `uip codedapp deploy` returns HTTP 400 with `routing name must be unique`
- A fresh deployment fails while claiming its requested path
- An upgrade of an existing app fails even though it requests the route that app already uses

What can cause it:
- **The requested route is already owned by a different coded-app deployment.** This is a real fresh-create collision.
- **An existing-app upgrade resubmitted its unchanged `routingName`, and server uniqueness validation treated it as a conflicting new assignment.** The app already owns the route; creating another app is not a valid workaround.
- **A previous publish or deploy attempt had an indeterminate result, so remote state may already have changed even though the client reported failure.** Timeouts, connection loss, interruption, HTTP 5xx, and nonzero exits after a write begins do not prove that the service rejected it.

What to look for:
- Whether the intended operation was an explicit fresh create or an upgrade
- The exact organization, tenant, folder, deployment identifier, system name, route, current version, and candidate package version
- Which remote deployment currently owns the route
- Whether the candidate version is published, deployed, or active after the failed attempt
- Whether the failed command completed with a definitive HTTP 400 before any other write, or ended ambiguously after a remote write may have started

## Investigation

1. Capture the original command output and stop. Do **not** rerun `publish` or `deploy` while diagnosing the first result.

2. Record the intended operation (`create` or `upgrade`) and its exact target tuple: organization, tenant, folder, app/deployment identifier, system name, routing name, current version, candidate version, and package identity. If any part is unknown, the operation is not safely retryable.

3. Inspect the local deploy hint, if present:

   ```bash
   cat .uipath/app.config.json
   ```

   Use `appUrl` and `systemName` only to locate the expected deployment. This file is not authoritative and cannot establish current remote state.

4. In the target tenant's Apps deployment inventory, re-read the deployment that owns the requested route and the intended app's current state. Capture the exact deployment identifier, system name, route, active version, and candidate package/deploy version. This remote read is mandatory after a timeout, connection loss, interruption, HTTP 5xx, or any other result where a write may have reached the service.

5. Classify the evidence:
   - **Fresh-create collision:** no existing deployment is the intended upgrade target, and a different deployment owns the requested route.
   - **Existing-app upgrade defect:** the intended existing deployment owns the requested route, its identity matches the upgrade target, and the HTTP 400 occurred when that unchanged route was submitted during the upgrade.
   - **Indeterminate prior write:** the remote version or package state changed, or cannot be proven unchanged, after an interrupted or ambiguous publish/deploy attempt.
   - **Insufficient evidence:** no route owner or exact deployment/version state can be established. Stop; do not infer safety from `.uipath/app.config.json` or from the CLI's exit code alone.

## Resolution

- **If the requested route is already owned by a different coded-app deployment:** do not retry the same create and do not generate a random route. Confirm which app is supposed to own the human-facing route. The owner must select an intentionally approved unused route or resolve the existing ownership through the supported Apps administration path before a new create is attempted.

- **If an existing-app upgrade resubmitted its unchanged `routingName`, and server uniqueness validation treated it as a conflicting new assignment:** use a supported in-place upgrade path bound to the exact existing deployment that does not reassign or change its route. If the available deployment client cannot perform that operation, stop and report the client/server defect; do not simulate an upgrade by creating a second app, omitting the desired route on a fresh deployment, issuing raw REST requests, or deleting and recreating the app.

- **If a previous publish or deploy attempt had an indeterminate result, so remote state may already have changed even though the client reported failure:** reconcile the authoritative remote package and deployment state first. If the candidate is already active, verify it rather than redeploying. If it is published but not deployed, prepare a new operation bound to the exact reconciled deployment and versions. If state cannot be proven, stop and escalate; never resume or blindly repeat the original write.

For every branch, preserve the existing deployment identifier, system name, and route unless an owner explicitly chooses a different route for a genuinely new app. A successful command exit is not sufficient: re-read the deployment and verify the expected version and unchanged route.
