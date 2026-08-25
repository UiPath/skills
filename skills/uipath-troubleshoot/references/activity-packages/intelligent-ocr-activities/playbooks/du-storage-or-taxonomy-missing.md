---
confidence: medium
---

# Document Understanding — Storage bucket / taxonomy / folder missing

## Context

A DU activity faults reading or writing a storage location — a taxonomy, a trained model, or validated extraction results held in an Orchestrator storage bucket / folder, or a local directory. The named resource doesn't exist where the activity looked, or the robot can't access it.

What this looks like — verbatim:

- `No such bucket named '<name>'` — the configured storage bucket doesn't exist in the folder/tenant the robot runs in.
- `Couldn't find path <path> in bucket <bucket> associated with '<x>'` — the blob (taxonomy/model) isn't at that path in the bucket.
- `Could not load the <x> from storage bucket <bucket> and path <path>` — a validated-extraction / results blob couldn't be loaded from that bucket+path.
- `The local directory path '<path>' could not be found.` — a configured local directory doesn't exist on the robot host.
- `Could not find Orchestrator Folder '<name>'` — the Orchestrator folder the activity targets (e.g. for Action Center / storage) doesn't exist or isn't visible to the robot.

What can cause it:
- **Bucket / blob / folder doesn't exist** — never created, deleted, or created in a different folder/tenant.
- **Out of scope for the robot** — the bucket/folder exists but the robot account / the folder the process runs in can't see it.
- **Wrong path** — the blob path / local directory configured on the activity is wrong or relative to an unexpected root.
- **Pipeline gap** — an upstream step that should have produced the results blob didn't, so the load can't find it.

What to look for:
- The message names the exact bucket / path / folder — that is the missing resource. These are storage-access failures, not endpoint or tenant-enablement failures.

> **Different cause — do not apply this playbook:**
> - `DUApiException` (HTTP status) → the DU endpoint call → use [du-license-or-endpoint-rejected.md](./du-license-or-endpoint-rejected.md).
> - `Failed to fetch Document Understanding projects list...` / `Couldn't retrieve a tenant key.` → tenant not enabled → use [du-not-enabled-or-tenant-key.md](./du-not-enabled-or-tenant-key.md).

## Investigation

1. **Read the named resource** from the message — bucket, blob path, Orchestrator folder, or local directory.
2. **Confirm it exists** in the tenant/folder the robot runs in (storage bucket / folder list), and that the robot account has read access.
3. **For a results-load failure (`Could not load the ... from storage bucket ...`),** check whether the upstream step that should have written that blob actually ran and completed.
4. **For a local-directory error,** confirm the path exists on the robot host (not just the dev machine).

## Resolution

- **If `No such bucket named '<name>'`:** create / correct the storage bucket in the folder the process runs in, or point the activity at the right bucket; ensure the robot account can access it.
- **If `Couldn't find path ... in bucket ...` / `Could not load the ... from storage bucket ...`:** correct the blob path, upload the missing taxonomy/model, or fix the upstream step that should produce the results blob.
- **If `The local directory path '<path>' could not be found.`:** create / correct the local directory on the robot host (use an absolute path that exists there).
- **If `Could not find Orchestrator Folder '<name>'`:** correct the folder name, or create it / grant the robot account access to it.
