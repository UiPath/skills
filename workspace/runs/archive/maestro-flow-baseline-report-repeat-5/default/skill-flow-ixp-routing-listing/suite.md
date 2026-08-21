# Suite Rollup: skill-flow-ixp-routing-listing

**Variant**: `default`
**Rows**: 50 total — 46 passed, 4 failed, 0 errored
**Pass rate**: 92.0%
**Average weighted score**: 0.960

## Criterion stats

| Criterion | Rows | Avg score | Errors |
|---|---|---|---|
| `command_executed` | 50 | 0.920 | 0 |
| `run_command` | 50 | 1.000 | 0 |

## Aggregate metrics — `command_executed` (PASSED)

| metric | value |
|---|---|
| `completion_rate` | 1.000 |
| `count` | 50.000 |
| `max` | 1.000 |
| `mean` | 0.920 |
| `median` | 1.000 |
| `min` | 0.000 |
| `std` | 0.271 |

### Thresholds

| metric | minimum | actual | passed |
|---|---|---|---|
| `mean` | 0.850 | 0.920 | ✓ |

## Aggregate metrics — `run_command` (PASSED)

| metric | value |
|---|---|
| `completion_rate` | 1.000 |
| `count` | 50.000 |
| `max` | 1.000 |
| `mean` | 1.000 |
| `median` | 1.000 |
| `min` | 1.000 |
| `std` | 0.000 |

### Thresholds

| metric | minimum | actual | passed |
|---|---|---|---|
| `mean` | 0.850 | 1.000 | ✓ |

**Suite gate**: PASSED

## Failed/errored samples (up to 20)

### `skill-flow-ixp-routing-listing/r05` — FAILURE
- score: 0.500
- Matched 0/1 required commands (filters: tool_name=Bash, pattern=/(?i)uip\s+maestro\s+flow\s+registry\s+(list\b|(search|list)\b[^\n]*\b(ixp|document|extract))/)
- [task.json](./skill-flow-ixp-routing-listing/r05/01/task.json)

### `skill-flow-ixp-routing-listing/r05` — FAILURE
- score: 0.500
- Matched 0/1 required commands (filters: tool_name=Bash, pattern=/(?i)uip\s+maestro\s+flow\s+registry\s+(list\b|(search|list)\b[^\n]*\b(ixp|document|extract))/)
- [task.json](./skill-flow-ixp-routing-listing/r05/02/task.json)

### `skill-flow-ixp-routing-listing/r01` — FAILURE
- score: 0.500
- Matched 0/1 required commands (filters: tool_name=Bash, pattern=/(?i)uip\s+maestro\s+flow\s+registry\s+(list\b|(search|list)\b[^\n]*\b(ixp|document|extract))/)
- [task.json](./skill-flow-ixp-routing-listing/r01/04/task.json)

### `skill-flow-ixp-routing-listing/r05` — FAILURE
- score: 0.500
- Matched 0/1 required commands (filters: tool_name=Bash, pattern=/(?i)uip\s+maestro\s+flow\s+registry\s+(list\b|(search|list)\b[^\n]*\b(ixp|document|extract))/)
- [task.json](./skill-flow-ixp-routing-listing/r05/04/task.json)

