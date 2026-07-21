# Runtime Exceptions Playbooks

**Investigation guide:** [investigation_guide.md](./investigation_guide.md) — scope check, data correlation rules, local log paths, and source code analysis for runtime exception investigations

| Issue | Confidence | Description | Playbook |
|-------|:---:|-------------|----------|
| Null Reference Exception | Medium | `System.NullReferenceException` in workflow code — uninitialized variable, null activity output, missing data, or unguarded conditional path | [null-reference-exception.md](./playbooks/null-reference-exception.md) |
| Argument Null Exception | Medium | `System.ArgumentNullException` in workflow code — null value passed to activity or method that requires non-null | [argument-null-exception.md](./playbooks/argument-null-exception.md) |
| If — Condition Compiler / Expression Error (Design-Time) | High | `Compiler error(s) encountered processing expression` / `Option Strict On disallows implicit conversions` — Studio Error List error on an `If` whose Condition is not a Boolean or compares mismatched types | [if-condition-compiler-error.md](./playbooks/if-condition-compiler-error.md) |
| If — Wrong Branch Taken at Runtime | High | `If` runs the wrong branch (job Successful, wrong result) from case/whitespace/type mismatch in the Condition — or `NullReferenceException` thrown inside the Condition | [if-wrong-branch.md](./playbooks/if-wrong-branch.md) |
