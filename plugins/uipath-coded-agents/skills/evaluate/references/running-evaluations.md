# Running Evaluations

This guide covers how to execute your evaluation sets and understand the results.

## Running Evaluations

### Command

```bash
uv run uipath eval <entrypoint> <eval-file> \
  --workers 4 \
  --no-report \
  --output-file eval-results.json
```

**Parameters:**
- `<entrypoint>` - Agent entry point name from `entry-points.json`
- `<eval-file>` - Path to evaluation set file
- `--workers` - Number of parallel workers (1-8)
- `--no-report` - Don't report to UiPath Cloud
- `--output-file` - Save results to JSON file
- `--mocker-cache` - Cache LLM responses for reproducibility

### Evaluation Discovery

The system scans for evaluation sets in:

```
evaluations/eval-sets/*.json
```

## Understanding Results

### Numeric Scores

All evaluators return scores:

- **1.0** - Perfect pass (evaluator criteria fully met)
- **0.5-0.9** - Partial success (similarity-based evaluators show partial match)
- **0.0** - Complete failure (evaluator criteria not met)

### Score Interpretation

**For ExactMatchEvaluator & ContainsEvaluator:**
- 1.0 - Requirement met
- 0.0 - Requirement not met

**For Similarity-Based Evaluators (JSON, LLM Judge, Trajectory):**
- 1.0 - Perfect match
- 0.9-0.5 - Good match with minor differences
- 0.4-0.1 - Weak match with significant differences
- 0.0 - No match

### Example Detailed Result

```json
{
  "testId": "test-1-basic",
  "testName": "Basic addition test",
  "status": "PASSED",
  "input": { "num1": 5, "num2": 3 },
  "expectedOutput": { "result": 8 },
  "actualOutput": { "result": 8 },
  "evaluationResults": [
    {
      "evaluatorId": "ExactMatchEvaluator",
      "score": 1.0,
      "status": "PASSED",
      "justification": "Output exactly matches expected value"
    }
  ]
}
```

## Pass vs Fail

A test passes if:
- All required evaluators produce their expected scores
- Output matches criteria for pass-fail evaluators (ExactMatch, Contains)
- Similarity scores are above your acceptance threshold

A test fails if:
- Any evaluator criteria are not met
- Similarity scores are below acceptable thresholds

## Performance Optimization

### Using Parallel Workers

```bash
uv run uipath eval <entrypoint> <eval-file> --workers 8
```

**Worker count recommendations:**
- `1` - Sequential, useful for debugging
- `4` - Default, good balance
- `8` - Maximum, for large evaluation sets

### Caching LLM Responses

For evaluators using LLMs (LLMJudge, Trajectory), enable mocker cache:

```bash
uv run uipath eval <entrypoint> <eval-file> --mocker-cache
```

Benefits: Faster re-runs, reproducible results, lower API costs.

## Integration with UiPath Cloud

```bash
uv run uipath eval <entrypoint> <eval-file> --report --workers 4
```

## Troubleshooting

### All Tests Fail
- Verify agent is working correctly with `uipath run`
- Check evaluation set references correct agent
- Ensure evaluator files exist and are valid
- Review agent input/output schemas

### Performance Issues
- Reduce number of workers if hitting rate limits
- Enable mocker cache for LLM evaluators
- Run subset of tests first to debug

### LLM Evaluator Issues
- Verify API credentials are configured
- Check model name is valid
- Enable cache to reduce API calls

