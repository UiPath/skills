# HTTP Request Node — Planning

## Node Type

`core.action.http`

## When to Use

Use an HTTP Request node to call a REST API where no pre-built connector exists, or for quick prototyping.

### Selection Heuristics

| Situation | Use HTTP? |
| --- | --- |
| No connector exists for the service | Yes |
| Quick prototyping against any REST API | Yes |
| Connector exists and covers the use case | No — use [Connector Activity](../connector/planning.md) |
| Connector exists but lacks the specific endpoint | Maybe — use HTTP within the connector (handles auth) |
| Target system has no API (desktop app) | No — use [RPA Workflow](../rpa/planning.md) |

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `default`, `branch-{id}` (dynamic per branch) |

**Dynamic ports:** Each entry in `branches` creates a `branch-{item.id}` output port. If no branch condition matches, flow goes to `default`.

## Output Variables

- `$vars.{nodeId}.output` — `{ body, statusCode, headers }`
- `$vars.{nodeId}.error` — error details if the call fails

## Key Inputs

| Input | Required | Description |
| --- | --- | --- |
| `method` | Yes | GET, POST, PUT, PATCH, DELETE |
| `url` | Yes | Target URL or `=js:` expression |
| `headers` | No | Key-value pairs |
| `body` | No | Request body string |
| `contentType` | No | Default `application/json` |
| `timeout` | No | ISO 8601 duration (default `PT15M`) |
| `retryCount` | No | Retries on failure (default 0) |
| `branches` | No | Response routing conditions |
| `authenticationType` | No | `manual` or from a connector connection |

## Planning Annotation

In the architectural plan, note the HTTP method and URL pattern. Use `<PLACEHOLDER>` for values that Phase 2 must resolve.
