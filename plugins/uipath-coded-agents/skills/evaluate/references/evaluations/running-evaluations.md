# Running Evaluations

This guide covers how to execute your evaluation sets and understand the results.

## Getting Started

### Evaluation Discovery

When you run evaluations, the system will scan for evaluation sets in:

```
evaluations/eval-sets/*.json
```

Example display:

```
AVAILABLE EVALUATIONS
═════════════════════════════════════════════════════════

1. evaluations/eval-sets/happy-path-scenarios.json
   └─ Tests: 3 | Last run: 2 hours ago

2. evaluations/eval-sets/edge-cases.json
   └─ Tests: 5 | Last run: Never

3. evaluations/eval-sets/error-scenarios.json
   └─ Tests: 4 | Last run: 1 day ago
```

### Execution Configuration

Before running, you'll be asked for:

- **Evaluation Set** - Which eval set to run
- **Number of Workers** - Parallel execution (1-8, default: 4)
- **Enable Mocker Cache** - Cache LLM responses for reproducibility (default: False)
- **Report to Studio** - Send results to UiPath Cloud (optional, default: False)

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

## Understanding Results

### Result Format

Each test case produces:

```
Test: calculate_sum
├─ Input: {"num1": 5, "num2": 3}
├─ Expected Output: {"result": 8}
├─ Actual Output: {"result": 8}
├─ ExactMatchEvaluator: PASS (1.0) - Output exactly matches expected
├─ JsonSimilarityEvaluator: PASS (1.0) - JSON structure identical
└─ Execution Time: 125ms
```

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

## Detailed Results

### Results Display

Results include:

- **Numeric Scores** - 0.0-1.0 range for each test and evaluator
- **Detailed Justification** - Why each evaluator gave that score
- **Execution Metrics** - Test execution time and performance data
- **Complete Traces** - Full execution history including function calls and state changes

### Example Detailed Result

```json
{
  "testId": "test-1-basic",
  "testName": "Basic addition test",
  "status": "PASSED",
  "input": {
    "num1": 5,
    "num2": 3
  },
  "expectedOutput": {
    "result": 8
  },
  "actualOutput": {
    "result": 8
  },
  "evaluationResults": [
    {
      "evaluatorId": "ExactMatchEvaluator",
      "score": 1.0,
      "status": "PASSED",
      "justification": "Output exactly matches expected value",
      "executionTime": 45
    },
    {
      "evaluatorId": "JsonSimilarityEvaluator",
      "score": 1.0,
      "status": "PASSED",
      "justification": "JSON structure and values are identical",
      "executionTime": 52
    }
  ],
  "totalExecutionTime": 125,
  "agentExecutionTrace": {
    "steps": [
      {
        "type": "tool_call",
        "toolName": "calculator",
        "arguments": {"a": 5, "b": 3},
        "result": 8
      }
    ]
  }
}
```

## Pass vs Fail

### Determining Overall Test Status

A test passes if:

- All required evaluators produce their expected scores
- Output matches criteria for pass-fail evaluators (ExactMatch, Contains)
- Similarity scores are above your acceptance threshold

A test fails if:

- Any evaluator criteria are not met
- Output doesn't match for ExactMatch or Contains evaluators
- Similarity scores are below acceptable thresholds

### Example Breakdown

```
RESULTS SUMMARY
═════════════════════════════════════════════════════════

Total Tests: 5
Passed: 4 (80%)
Failed: 1 (20%)

FAILED TESTS
─────────────────────────────────────────────────────────

Test: test-2-edge-case (Edge case with zero)
Input: {"num1": 0, "num2": 5}
Expected: {"result": 5}
Actual: {"result": "5"}
├─ ExactMatchEvaluator: FAIL (0.0)
│  └─ Reason: Expected number but got string
└─ Suggestion: Ensure output type matches schema

PASSED TESTS
─────────────────────────────────────────────────────────

Test: test-1-basic → PASS (1.0)
Test: test-3-large → PASS (1.0)
Test: test-4-negative → PASS (1.0)
Test: test-5-decimal → PASS (1.0)
```

## Analyzing Results

### For Each Failing/Warning Test

The system shows:

1. **Input/Output Pairs**
   - Exact inputs used
   - Expected vs actual results

2. **Evaluator Scores and Justification**
   - Score from each evaluator
   - Explanation of the score
   - Why it passed or failed

3. **Execution Traces**
   - Full execution history
   - Function calls made
   - State changes during execution
   - Timing information

4. **Suggestions for Fixes**
   - Identified issues
   - Recommended changes
   - Best practices for similar cases

### Example Detailed Analysis

```
FAILING TEST ANALYSIS
═════════════════════════════════════════════════════════

Test ID: test-3-invalid-type
Test Name: Invalid input type handling
Status: FAILED

Input Provided:
{
  "value": "not-a-number"  // Should have been numeric
}

Expected Output:
{
  "error": "Invalid input type"
}

Actual Output:
{
  "result": null,
  "error": null
}

Evaluation Results:
─────────────────────────────────────────────────────────

1. ExactMatchEvaluator (Score: 0.0 - FAILED)
   Justification: Expected error message was not returned

2. JsonSimilarityEvaluator (Score: 0.3 - FAILED)
   Justification: 30% similarity. Has 'error' field but value differs.

Execution Trace:
─────────────────────────────────────────────────────────

1. [0ms] Function called: validate_input
   Arguments: {"value": "not-a-number"}
   Result: {"valid": false, "error": "Not numeric"}

2. [5ms] Function called: process_value
   Arguments: {"value": "not-a-number"}
   Result: null
   Note: Process function called despite validation failure

3. [8ms] Return result
   Final Output: {"result": null, "error": null}

Recommendations:
─────────────────────────────────────────────────────────

✓ Check validation logic in validate_input function
✓ Return error when validation fails instead of processing
✓ Ensure error handling is consistent across all paths
✓ Consider adding type checking at entry point
```

## Follow-up Actions

After running evaluations, you can:

### Create More Evaluations

Add additional evaluation sets for:
- Different scenarios
- New test cases
- Additional edge cases

### Fix Issues

I can help:
- Modify agent code to fix failing tests
- Update evaluation criteria if needed
- Improve error handling

### Re-run Evaluations

Execute with different configurations:
- Different number of workers
- Different evaluation sets
- With/without mocking

### View Details

Examine detailed information:
- Individual test results
- Execution traces
- Performance metrics
- Failure analysis

### Export Results

Save results for:
- External analysis
- CI/CD integration
- Performance tracking
- Trend analysis

### Compare Runs

Track improvements:
- Compare current run with previous runs
- View score trends over time
- Identify regressions
- Monitor performance changes

## Integration with UiPath Cloud

Results can be:

- **Reported to UiPath Cloud** - for monitoring and analytics
- **Integrated with CI/CD pipelines** - for automated testing
- **Compared with previous runs** - for trend tracking
- **Used for performance tracking** - across versions

Set `--report` flag to send results to your UiPath Cloud account:

```bash
uv run uipath eval <entrypoint> <eval-file> \
  --report \
  --workers 4
```

## Performance Optimization

### Using Parallel Workers

Run tests in parallel for faster execution:

```bash
uv run uipath eval <entrypoint> <eval-file> \
  --workers 8
```

**Worker count recommendations:**
- `1` - Sequential, useful for debugging
- `4` - Default, good balance
- `8` - Maximum, for large evaluation sets

### Caching LLM Responses

For evaluators using LLMs (LLMJudge, Trajectory), enable mocker cache:

```bash
uv run uipath eval <entrypoint> <eval-file> \
  --mocker-cache
```

Benefits:
- Faster execution on re-runs
- Reproducible results
- Lower API costs
- Useful for CI/CD pipelines

## Troubleshooting

### Test Passes but Score Seems Wrong

- Check evaluator configuration
- Review evaluation criteria
- Verify expected output format
- Look at justification in detailed results

### All Tests Fail

- Verify agent is working correctly
- Check evaluation set references correct agent
- Ensure evaluator files exist and are valid
- Review agent input/output schemas

### Performance Issues

- Reduce number of workers if hitting rate limits
- Enable mocker cache for LLM evaluators
- Run subset of tests first to debug
- Check for slow external API calls

### LLM Evaluator Issues

- Verify API credentials are configured
- Check model name is valid
- Review prompt template syntax
- Enable cache to reduce API calls

## Best Practices

✅ **Do:**
- Run evaluations regularly during development
- Start with small evaluation sets, expand gradually
- Use multiple evaluators for comprehensive validation
- Cache LLM responses in CI/CD pipelines
- Review detailed traces for failing tests
- Track score trends over time

❌ **Don't:**
- Run with too many workers without testing first
- Skip detailed result analysis for failures
- Ignore justification messages from evaluators
- Set unrealistic expectations too early
- Run expensive LLM evaluators without caching

## Next Steps

- [Creating Evaluations](creating-evaluations.md) - Create more test cases
- [Evaluators Guide](evaluators.md) - Learn about evaluator types
- [Evaluation Sets](evaluation-sets.md) - Structure evaluation set files
- [Best Practices](best-practices.md) - Tips for effective testing
