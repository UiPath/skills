---
confidence: high
---

# Attachment Not Found After Job Retention

## Context

What this looks like:
- "Attachment not found" or 404 on file access
- Files disappear after some time but process initially worked

What can cause it:
- Attachments are linked to the job that created them. Job retention policy deletes the job and orphans the attachment

## Investigation

1. Check the job retention policy for the folder
2. Verify the job that created the attachment still exists

## Resolution

- Redesign the process so downstream jobs download files directly from the source (e.g., Data Fabric, storage bucket) instead of passing file references as job arguments
- Alternatively, increase job retention period (delays the issue but does not fix it)
