---
confidence: medium
---

# Custom Connector Publishing and Lifecycle

## Context

Use when local changes are absent after publishing, publish fails or remains incomplete,
the connector is not visible to consumers, an equal-version publish is rejected, a development
to production promotion breaks connector references, or ownership/version identity is unclear.

Required anchors: source connector key and version, target environment/org/tenant, import
response/revision, publish ID/status/version, published connector key, connection ID and consumer
package/reference, timestamp, and the first environment where identities diverge.

### What can cause it

- Local changes were validated but never imported, so publish promoted an older imported revision.
- The publish job failed, remained non-terminal, reused an existing version, or has not completed normal propagation.
- The source, imported, published, or consumer connector key/version identities diverged.
- Environment promotion did not rewrite connector references or connection bindings for the target environment.
- The consumer cached older generated metadata or references a different connector version.
- Ownership transfer or access policy prevents the intended author from publishing or managing the connector.

## Investigation

1. **Build the lifecycle chain:** local files → validation → import → imported revision →
   publish job → published catalog version/key → consumer discovery/cache → connection/binding.
2. **Confirm local validation:**

   ```bash
   uip is connectors builder inspect --output json
   uip is connectors builder validate --output json
   ```

3. **Confirm import preceded publish.** Publishing promotes what is already imported; it does
   not upload unimported local edits.
4. **Check publish status by its returned publish ID** and retain terminal failure details.
   A new connector can use its seeded initial version; republishing requires a higher version
   than the currently published one.
5. **Compare content and identity.** Verify source connector key/version, target imported key,
   published key/version, and the key/version referenced by the workflow/solution and connection.
6. **For “published but not visible,”** require terminal publish success first, then allow the
   normal catalog propagation interval and refresh consumer discovery. Repeatedly republishing
   during propagation creates ambiguous evidence.
7. **For environment promotion,** determine whether import preserved or generated connector
   identity and whether the deployment mechanism rewrote connector and connection bindings.
   A production connection cannot satisfy a package that still references an unrelated
   development connector key.
8. **For ownership transfer,** separate access/ownership policy from a technical publish
   failure. Capture current owner, target owner, connector identity, and supported transfer
   path; never work around ownership by copying secrets.

### Diagnosis

| Evidence | Diagnosis |
|---|---|
| Local changed after last successful import | Stale imported revision |
| Import is current; publish ID failed | Publish-job failure |
| Server rejects equal/older version | Version monotonicity violation |
| Publish succeeded but catalog delay has not elapsed | Propagation, not yet a defect |
| Published key/version differs from consumer reference | Promotion/identity mismatch |
| Catalog is correct but connection binds old identity | Connection/binding drift |
| User cannot publish/manage a connector they do not own | Ownership/access lifecycle |

## Resolution

Quote one confirmed cause verbatim from **What can cause it**, then correct only
that lifecycle branch. If evidence does not isolate one cause, stop at the missing
discriminator.

Diagnosis is read-only. Obtain explicit approval before importing, publishing,
transferring ownership, recreating a connection, or rebinding a consumer.

- Validate, import the intended local revision, then publish that imported revision and retain
  the publish ID.
- Bump the connector version for republish; do not reuse or lower an existing published version.
- After terminal success, wait for normal propagation and refresh the consumer before escalating.
- Preserve/rewrite connector references and connection bindings through the supported
  promotion mechanism. Recreate/rebind connections when connector identity changed.
- Use the supported ownership-transfer process; do not clone credentials or silently create an
  unrelated connector identity as a substitute.

### Verification

Compare a known changed field across local, imported, published, and consumer-visible versions.
Execute one operation through the target environment's connection. For promotion, prove the
consumer package and connection both reference the target published connector key.

### Escalation Bundle

Include anchors, validation/import/publish responses, publish ID and status history, local and
published version/key, target consumer reference and binding, UTC timeline, visibility checks,
and current/target owner for ownership cases.
