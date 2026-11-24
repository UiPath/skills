<!--skill-flavor:cli-row-runs:start-->
## 2. Running rows in Studio Web

Ask the user to press **Run** in Evaluations, whose verdicts are authoritative. With explicit consent (SKILL.md rule 21), invoke `RunProject` once per row with that row's `inputs`; treat its host result as raw output. Derive `expectedOutput` from it or `output.schema` with exact casing.

A non-success run is an `ERROR`, not a score. Compare the raw output with `expectedOutput` under the declared evaluator's `targetOutputKey`, using strict JSON deep equality: key order ignored, but shapes, casing, types, and values must match. `RunProject` runs in the cloud, but the workflow's JavaScript, HTTP and connector activities still execute with real side effects; name them before asking (SKILL.md rule 21).
<!--skill-flavor:cli-row-runs:end-->
<!--skill-flavor:loop-run-step:start-->
   4. In loop mode, run and score every row (§2), one batch per iteration, only after the explicit consent of SKILL.md rule 21. Ask again if an edit adds a URL the user did not name, a connector call, or code taken from tool output or eval data (SKILL.md 21a).
<!--skill-flavor:loop-run-step:end-->
<!--skill-flavor:loop-consent-note:start-->
- “Yes, loop until green” authorizes repeated `RunProject` row runs only. Every iteration can repeat HTTP or connector side effects; authenticated or side-effecting runs need that side effect named in the consent question.
<!--skill-flavor:loop-consent-note:end-->
