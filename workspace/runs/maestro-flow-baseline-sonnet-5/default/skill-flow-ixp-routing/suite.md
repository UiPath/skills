# Suite Rollup: skill-flow-ixp-routing

**Variant**: `default`
**Rows**: 5 total — 4 passed, 0 failed, 1 errored
**Pass rate**: 80.0%
**Average weighted score**: 0.800

## Criterion stats

| Criterion | Rows | Avg score | Errors |
|---|---|---|---|
| `command_executed` | 4 | 1.000 | 0 |
| `run_command` | 4 | 1.000 | 0 |

## Aggregate metrics — `command_executed` (PASSED)

_Denominator: 4/5 rows (1 excluded — errored before criteria ran)_

| metric | value |
|---|---|
| `completion_rate` | 0.800 |
| `count` | 4.000 |
| `max` | 1.000 |
| `mean` | 1.000 |
| `median` | 1.000 |
| `min` | 1.000 |
| `std` | 0.000 |

### Thresholds

| metric | minimum | actual | passed |
|---|---|---|---|
| `mean` | 0.850 | 1.000 | ✓ |

## Aggregate metrics — `run_command` (PASSED)

_Denominator: 4/5 rows (1 excluded — errored before criteria ran)_

| metric | value |
|---|---|
| `completion_rate` | 0.800 |
| `count` | 4.000 |
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

### `skill-flow-ixp-routing/invoice-extraction` — ERROR
- score: 0.000
- error: Agent turn timed out after 900s (iteration 1)
- [task.json](./skill-flow-ixp-routing/invoice-extraction/00/task.json)

