# Agent Feedback Reference

Feedback allows you to collect and manage user feedback on AI agent responses, including positive/negative ratings, comments, and categorized feedback. This is useful for monitoring agent quality, identifying areas for improvement, and building datasets for fine-tuning.

## Import

```typescript
import { Feedback } from '@uipath/uipath-typescript/feedback';
```

## Scopes

`Traces.Api` — for **every** method (reads, writes, and category management).

## Types to Import

```typescript
import type {
  FeedbackGetResponse,
  FeedbackResponse,
  FeedbackGetAllOptions,
  FeedbackOptions,
  FeedbackSubmitOptions,
  FeedbackUpdateOptions,
  FeedbackGetCategoriesOptions,
  FeedbackCreateCategoryOptions,
  FeedbackDeleteCategoryOptions,
  FeedbackCategory,
  FeedbackCategoryInput,
  FeedbackCategoryResponse,
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

### submit(traceId: string, isPositive: boolean, options: FeedbackSubmitOptions)

Returns `Promise<FeedbackResponse>`. Creates a new feedback entry against an agent trace. `isPositive` is the thumbs-up/down. **`options.folderKey` is required.** Other `FeedbackSubmitOptions` fields (all optional): `agentId`, `agentVersion`, `comment`, `metadata` (string), `spanId`, `spanType`, `categories: FeedbackCategoryInput[]`.

### updateById(id: string, isPositive: boolean, options: FeedbackUpdateOptions)

Returns `Promise<FeedbackResponse>`. Updates an existing feedback entry. **`options.folderKey` is required.** Optional fields: `comment`, `metadata`, `categories: FeedbackCategoryInput[]`.

### deleteById(id: string, options: FeedbackOptions)

Returns `Promise<void>`. **`options.folderKey` is required.**

### getCategories(options?: FeedbackGetCategoriesOptions)

Returns `NonPaginatedResponse<FeedbackCategoryResponse>` or `PaginatedResponse<FeedbackCategoryResponse>`. Lists feedback categories (default + custom). `FeedbackCategoryResponse` fields: `id`, `category`, `createdTime`, `isDefault`, `isPositive`, `isNegative`.

### createCategory(category: string, options?: FeedbackCreateCategoryOptions)

Returns `Promise<FeedbackCategoryResponse>`. Creates a custom category. `FeedbackCreateCategoryOptions`: `isPositive?` (defaults `true`), `isNegative?` (defaults `true`) — set the flags to scope the category to one rating direction.

### deleteCategory(id: string, options?: FeedbackDeleteCategoryOptions)

Returns `Promise<void>`. Deletes a custom category. Default tenant categories cannot be removed.

## Usage Example — Feedback Inbox

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

## Usage Example — Submitting & Managing Feedback

```typescript
import { Feedback } from '@uipath/uipath-typescript/feedback';

const feedback = new Feedback(sdk);

// Submit thumbs-up on an agent trace
const created = await feedback.submit(traceId, true, {
  folderKey,                      // required
  agentId,
  comment: 'Accurate and well-structured answer',
  categories: [{ category: 'Output', isPositive: true }],
});

// Flip it to thumbs-down and edit the comment
await feedback.updateById(created.id, false, {
  folderKey,
  comment: 'On second read, the figures were wrong',
});

// Manage categories
const categories = await feedback.getCategories({ pageSize: 50 });
const custom = await feedback.createCategory('Tone', { isNegative: true, isPositive: false });
await feedback.deleteCategory(custom.id);

// Remove the entry
await feedback.deleteById(created.id, { folderKey });
```
