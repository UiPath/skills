---
confidence: medium
---

# Queue Operation Failed (Add/Get Queue Item)

## Context

`Add Queue Item` failed while pushing an item into an Orchestrator queue, or `Get Queue Item`
(`GetQueueItem`) failed while reading from one. The shared branches cover `QueueName` resolution and
errors returned by Orchestrator. Item-information validation applies only to `Add Queue Item`.

What this looks like:
- "\"Queue name\" may not be null or empty." — the queue name input was not set
- `NoSuchQueue does not exist. Error code: 1002` (often inside an HTTP 404
  `OrchestratorHttpException`) — the resolved queue name was unavailable in the job folder
- For `Add Queue Item`, an error about invalid characters in an item-information key — keys may not
  contain certain characters (`.`, `#`, `@`, `:`)
- For `Add Queue Item`, "An item name from the '{0}' collection is the duplicate of another item name
  in the '{1}' collection" — the same key appears in both `ItemInformation` and
  `ItemInformationCollection`
- An Orchestrator error: queue does not exist, permission denied, HTTP error, or a timeout

What can cause it:
- The `QueueName` input is empty or resolved to null from an unset variable/argument
- A queue with that name does not exist in the folder where the job runs
- The robot account lacks the queue permission required by the operation in that folder
- For `Add Queue Item`, item-information keys contain reserved characters, or the same key is supplied
  twice across the two collections
- Network/connectivity or session issues between the robot and Orchestrator, causing an HTTP error or
  timeout

What to look for:
- The resolved `QueueName` and the folder the job runs in
- For `Add Queue Item`, the item-information keys being sent (reserved characters, duplicates)
- The HTTP status / error text returned by Orchestrator, if any
- Whether the queue exists in that folder and the robot account has rights to the required operation

## Investigation

1. Identify the failing `Add Queue Item` or `Get Queue Item` / `GetQueueItem` and the resolved
   `QueueName` from the correlated job record, logs, or traces.
2. Confirm the queue exists in the exact Orchestrator folder where the job runs. Try the documented
   exact-name lookup first and preserve its response:
   ```
   uip or queues list --folder-key <folder-key> --name "<queue-name>" --output json \
     | tee .local/investigations/raw/triage-queue-exact.json
   ```
   If that request returns `Result=Failure` / `HTTP 400: Invalid OData query options`, it is a failed
   query, not proof that the queue is absent. Preserve it, then retry once without the backend name
   filter and filter the small response client-side:
   ```
   uip or queues list --folder-key <folder-key> --output json \
     --output-filter "[?Name=='<queue-name>'].{Key:Key,Name:Name}" \
     | tee .local/investigations/raw/triage-queue-folder-fallback.json
   ```
   An empty successful fallback supports current absence only after the folder key is verified. For
   incidents older than 24 hours, current absence cannot distinguish never-created from deleted-since;
   the correlated runtime 404 establishes only that the name was unavailable then.
3. If a validation error fired, inspect the empty queue name and — for Add only — reserved characters
   or duplicate keys across `ItemInformation` and `ItemInformationCollection`.
4. If Orchestrator returned an error, read the HTTP status / message — distinguish permission denied,
   not found, and timeout.
5. Confirm the robot account is authenticated and has the queue permission required by that operation
   in the folder.
6. When runtime evidence proves the queue name was unavailable but does not explain why that name was
   used, check the working-directory source boundary from `SKILL.md` §5: inspect the named workflow and
   `project.json` if present. If source is unavailable, leave wrong name, deleted/missing queue, and
   wrong execution folder as explicit conditional branches; do not pick one from the activity display
   name or a suggestive suffix.

## Resolution

- **If the queue name is empty:** set `QueueName` (ensure the upstream variable/argument that feeds it
  is populated).
- **If the queue name is wrong in source/configuration:** correct the activity's `QueueName` (or the
  upstream variable/config value feeding it), then republish through the normal project lifecycle.
- **If the intended queue is missing or was deleted:** create/recreate it in the job folder with the
  intended schema and settings.
- **If the intended queue exists in another folder:** run/deploy the process in that folder, or define
  the intended queue in the current job folder.
- **If evidence cannot choose among those three branches:** lead with the source/configuration check
  that discriminates them, then present all three as conditional fixes. Do not create a queue merely
  because a not-found response occurred.
- **If keys contain reserved characters:** rename the Add item's information keys to remove `.`, `#`,
  `@`, `:`.
- **If a key is duplicated across the two collections:** remove the duplicate so each Add item key
  appears once.
- **If permission is denied:** grant the robot account the least queue permission required by the
  failing Add/Get operation in that folder.
- **If it's a network/HTTP/timeout error:** address robot↔Orchestrator connectivity and retry.
