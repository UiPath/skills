# Suite Rollup: skill-flow-ixp-routing-listing

**Variant**: `default`
**Rows**: 10 total — 9 passed, 1 failed, 0 errored
**Pass rate**: 90.0%
**Average weighted score**: 0.950

## Criterion stats

| Criterion | Rows | Avg score | Errors |
|---|---|---|---|
| `command_executed` | 10 | 0.900 | 0 |
| `run_command` | 10 | 1.000 | 0 |

## Aggregate metrics — `command_executed` (PASSED)

| metric | value |
|---|---|
| `completion_rate` | 1.000 |
| `count` | 10.000 |
| `max` | 1.000 |
| `mean` | 0.900 |
| `median` | 1.000 |
| `min` | 0.000 |
| `std` | 0.300 |

### Thresholds

| metric | minimum | actual | passed |
|---|---|---|---|
| `mean` | 0.850 | 0.900 | ✓ |

## Aggregate metrics — `run_command` (PASSED)

| metric | value |
|---|---|
| `completion_rate` | 1.000 |
| `count` | 10.000 |
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

### `skill-flow-ixp-routing-listing/r01` — FAILURE
- score: 0.500
- Matched 0/1 required commands (filters: tool_name=Bash, pattern=/(?i)uip\s+maestro\s+flow\s+registry\s+(list\b|(search|list)\b[^\n]*\b(ixp|document|extract))/)
- [task.json](./skill-flow-ixp-routing-listing/r01/00/task.json)

