---
confidence: medium
---

# Queue Items Failing

## Context

Queue items are transitioning to Failed status. Multiple distinct error types may be present across items. Successful items may still be processing normally.

What can cause it:
- Input data issues — failed items have different SpecificContent from successful ones
- Failures clustering around a specific time window or machine
- Performer process was recently updated and introduced a regression
- Asset, permission, or configuration issue affecting only certain data paths

What to look for:
- Compare input data (SpecificContent) between failed and successful items to identify data-driven failures
- Check if failures cluster around a specific time window or machine
- Check if the performer process was recently updated

## Investigation

1. Get ALL failed queue items (paginate if >100) — do NOT stop at the first page
2. Categorize failures by error type — there may be MULTIPLE distinct failure modes
3. After identifying a failure mode, count how many items it explains. If the count does not match the total number of failed items, there are additional failure modes — keep investigating until every failed item is accounted for
4. Get 2-3 successful queue items for comparison
5. Compare input data between failed and successful items

A confirmed hypothesis is only a complete root cause if it accounts for ALL failed items. If it explains only a subset (e.g., 156 of 160), the remaining items have a different root cause — classify the finding as partial and continue investigating.

When source code is available, trace the full execution path for EACH error category, not just the first one found. Different queue item data can trigger different code paths and different failures.

## Resolution

- Fix input data at source (dispatcher process or upstream system)
- Fix the performer process if a regression was introduced
- Restore asset/permission/configuration if that was the cause
