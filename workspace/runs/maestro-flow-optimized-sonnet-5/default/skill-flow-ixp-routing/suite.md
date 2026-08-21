# Suite Rollup: skill-flow-ixp-routing

**Variant**: `default`
**Rows**: 5 total — 4 passed, 1 failed, 0 errored
**Pass rate**: 80.0%
**Average weighted score**: 0.800

## Criterion stats

| Criterion | Rows | Avg score | Errors |
|---|---|---|---|
| `command_executed` | 5 | 0.800 | 0 |
| `run_command` | 5 | 0.800 | 0 |

## Aggregate metrics — `command_executed` (FAILED)

| metric | value |
|---|---|
| `completion_rate` | 1.000 |
| `count` | 5.000 |
| `max` | 1.000 |
| `mean` | 0.800 |
| `median` | 1.000 |
| `min` | 0.000 |
| `std` | 0.400 |

### Thresholds

| metric | minimum | actual | passed |
|---|---|---|---|
| `mean` | 0.850 | 0.800 | ✗ |

## Aggregate metrics — `run_command` (FAILED)

| metric | value |
|---|---|
| `completion_rate` | 1.000 |
| `count` | 5.000 |
| `max` | 1.000 |
| `mean` | 0.800 |
| `median` | 1.000 |
| `min` | 0.000 |
| `std` | 0.400 |

### Thresholds

| metric | minimum | actual | passed |
|---|---|---|---|
| `mean` | 0.850 | 0.800 | ✗ |

**Suite gate**: FAILED

## Failed/errored samples (up to 20)

### `skill-flow-ixp-routing/receipts` — FAILURE
- score: 0.000
- Matched 0/1 required commands (filters: tool_name=Bash, pattern=/(?i)uip\s+maestro\s+flow\s+registry\s+(list\b|(search|list|get)\b[^\n]*\b(ixp|document|extract))/)
- Command: grep -rqE "\"type\"[[:space:]]*:[[:space:]]*\"(uipath\.ixp|core\.logic\.mock)" --include="*.flow" .
Exit code: 1 (expected: 0)
Stdout: (empty)
Stderr: (empty)
- [task.json](./skill-flow-ixp-routing/receipts/00/task.json)

