---
confidence: medium
---

# Add Queue Item Failed

## Context

`Add Queue Item` failed while pushing an item into an Orchestrator queue. The failure can be a
client-side validation of the inputs, or an error returned by Orchestrator.

What this looks like:
- "\"Queue name\" may not be null or empty." — the queue name input was not set
- An error about invalid characters in an item-information key — keys may not contain certain
  characters (`.`, `#`, `@`, `:`)
- "An item name from the '{0}' collection is the duplicate of another item name in the '{1}'
  collection" — the same key appears in both the `ItemInformation` and the
  `ItemInformationCollection`
- An Orchestrator error: queue does not exist, permission denied, HTTP error, or a timeout

What can cause it:
- The `QueueName` input is empty or resolved to null from an unset variable/argument
- A queue with that name does not exist in the folder where the job runs
- The robot account lacks permission to create queue items in that folder
- Item-information keys contain reserved characters, or the same key is supplied twice across the two
  collections
- Network/connectivity or session issues between the robot and Orchestrator, causing an HTTP error or
  timeout

What to look for:
- The resolved `QueueName` and the folder the job runs in
- The item-information keys being sent (reserved characters, duplicates)
- The HTTP status / error text returned by Orchestrator, if any
- Whether the queue exists in that folder and the robot account has rights to it

## Investigation

1. Identify the failing `Add Queue Item` and the resolved `QueueName` (from logs/variables).
2. Confirm the queue exists in the Orchestrator folder where the job runs.
3. If a validation error fired, inspect the named inputs: empty queue name, reserved characters in
   keys, or a duplicate key across `ItemInformation` and `ItemInformationCollection`.
4. If Orchestrator returned an error, read the HTTP status / message — distinguish permission denied,
   not found, and timeout.
5. Confirm the robot account is authenticated and has permission to add items in that folder.

## Resolution

- **If the queue name is empty:** set `QueueName` (ensure the upstream variable/argument that feeds it
  is populated).
- **If the queue doesn't exist in the job folder:** create it there, or run the job in the folder
  where the queue is defined.
- **If keys contain reserved characters:** rename the item-information keys to remove `.`, `#`, `@`,
  `:`.
- **If a key is duplicated across the two collections:** remove the duplicate so each key appears
  once.
- **If permission is denied:** grant the robot account permission to create queue items in that
  folder.
- **If it's a network/HTTP/timeout error:** address robot↔Orchestrator connectivity and retry.
