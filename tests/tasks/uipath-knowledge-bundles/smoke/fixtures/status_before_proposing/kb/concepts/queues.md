# Queues

A queue holds work items. A failed item is retried up to the
queue's `MaxRetries`, and only for application exceptions — a business
exception is never retried.
