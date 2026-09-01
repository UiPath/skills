# Running Evaluations

Run evaluation sets and interpret their results.

## Run Evaluations

Run an evaluation set:

```bash
uip codedagent eval <entrypoint> <eval-file> \
  --no-report \
  --output-file eval-results.json
```

`<entrypoint>` is the agent entry point name from `entry-points.json`; `<eval-file>` is the evaluation-set path. The system discovers sets in `evaluations/eval-sets/*.json`.

Supported options:

- `--workers`: Parallel workers; default `1`.
- `--eval-ids`: Python/JSON-style case-ID list, such as `'["test-1-basic", "test-3-edge-case"]'`; default `[]` (all cases).
- `--no-report`: Do not report to UiPath Cloud.
- `--output-file`: Save results to a JSON file.
- `--enable-mocker-cache`: Cache LLM responses for reproducibility.

Run a subset while debugging:

```bash
uip codedagent eval <entrypoint> <eval-file> --no-report --eval-ids '["test-1-basic"]'
```

## Interpret Results

Evaluators return numeric scores:

- `1.0`: Perfect pass; all criteria are met.
- `0.5-0.9`: Partial success; common for similarity-based evaluators.
- `0.0`: Complete failure; criteria are not met.

For `ExactMatchEvaluator` and `ContainsEvaluator`, `1.0` means the requirement is met and `0.0` means it is not. For similarity-based evaluators (`JSON`, `LLM Judge`, and `Trajectory`):

- `1.0`: Perfect match.
- `0.9-0.5`: Good match with minor differences.
- `0.4-0.1`: Weak match with significant differences.
- `0.0`: No match.

A test passes only when all required evaluators produce their expected scores, pass-fail outputs satisfy their criteria, and similarity scores exceed the acceptance threshold. It fails when any criterion is unmet or a similarity score is below the acceptable threshold.

Detailed results contain fields such as:

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

## Optimize Performance

Run with parallel workers when dependencies and rate limits support concurrency:

```bash
uip codedagent eval <entrypoint> <eval-file> --workers 4
```

- Use `1` for sequential execution, debugging, or rate-limit-sensitive evaluators.
- Use `4` as a practical balance for larger sets.
- Use higher values only when the agent, evaluators, and external services safely support concurrency.

For `LLMJudge` and `Trajectory`, run with mocker cache:

```bash
uip codedagent eval <entrypoint> <eval-file> --enable-mocker-cache
```

Caching makes reruns faster and more reproducible and reduces API costs.

## Report to UiPath Cloud

Authenticate, set `UIPATH_PROJECT_ID` in `.env`, and obtain it by pushing the agent to Studio Web with `uip codedagent push`. Report results to Studio Web:

```bash
uip codedagent eval <entrypoint> <eval-file> --report --workers 4
```

Run local-only evaluation:

```bash
uip codedagent eval <entrypoint> <eval-file> --no-report
```

## Troubleshoot

### All Tests Fail

- Verify the agent with `uip codedagent run`.
- Check that the evaluation set references the correct agent.
- Ensure evaluator files exist and are valid.
- Review agent input and output schemas.

### Performance Issues

- Reduce workers when hitting rate limits.
- Enable mocker cache for LLM evaluators.
- Run a subset of tests first to debug.

### LLM Evaluator Issues

- Verify API credentials.
- Check that the model name is valid.
- Enable cache to reduce API calls.
