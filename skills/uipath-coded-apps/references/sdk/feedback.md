# Agent Feedback Reference

Feedback allows you to collect and manage user feedback on AI agent responses, including positive/negative ratings, comments, and categorized feedback. This is useful for monitoring agent quality, identifying areas for improvement, and building datasets for fine-tuning.

## Import

```typescript
import { Feedback } from '@uipath/uipath-typescript/feedback';
```

## Scopes

`Traces.Api` — for both `getAll()` and `getById()`.

## Types to Import

```typescript
import type {
  FeedbackGetResponse,
  FeedbackGetAllOptions,
  FeedbackOptions,
  FeedbackCategory,
} from '@uipath/uipath-typescript/feedback';
```

## Enums

```typescript
import { FeedbackStatus } from '@uipath/uipath-typescript/feedback';
// FeedbackStatus.Pending = 0, Approved = 1, Dismissed = 2
```

## Feedback Service

### getAll(options?: FeedbackGetAllOptions)

Returns `NonPaginatedResponse<FeedbackGetResponse>` or `PaginatedResponse<FeedbackGetResponse>`. As with every list method, this returns one page — see [pagination.md](pagination.md) for cursor-loop retrieval if the source has more rows than the server's default cap.

`FeedbackGetAllOptions` filters: `agentId?`, `agentVersion?`, `status?: FeedbackStatus`, `traceId?`, `spanId?`. Plus `PaginationOptions` (`pageSize`, `cursor`, `jumpToPage`).

### getById(id: string, options: FeedbackOptions)

Returns `Promise<FeedbackGetResponse>`. **`options.folderKey` is required** — get it from a `getAll()` item or wherever the feedback originated.

`FeedbackGetResponse` fields: `id`, `traceId`, `spanId`, `agentId`, `agentVersion?`, `comment?`, `metadata?`, `isPositive`, `feedbackCategories: FeedbackCategory[]`, `folderKey?`, `userEmail?`, `status: FeedbackStatus`, `createdTime`, `updatedTime`.

`FeedbackCategory` fields: `id`, `category`, `createdAt`, `isDefault`, `isPositive`, `isNegative`. Default categories (Output, Agent Error, Agent Plan Execution) are auto-created per tenant.

## Usage Example

```typescript
import { useMemo, useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Feedback, FeedbackStatus } from '@uipath/uipath-typescript/feedback';
import type { FeedbackGetResponse } from '@uipath/uipath-typescript/feedback';

function FeedbackInbox({ agentId }: { agentId: string }) {
  const { sdk } = useAuth();
  const feedback = useMemo(() => new Feedback(sdk), [sdk]);
  const [items, setItems] = useState<FeedbackGetResponse[]>([]);

  useEffect(() => {
    const load = async () => {
      const result = await feedback.getAll({
        agentId,
        status: FeedbackStatus.Pending,
        pageSize: 25,
      });
      setItems(result.items);
    };
    load();
  }, [feedback, agentId]);

  const openDetail = async (item: FeedbackGetResponse) => {
    if (!item.folderKey) return;
    const detail = await feedback.getById(item.id, { folderKey: item.folderKey });
    console.log(detail.comment, detail.feedbackCategories);
  };
}
```
