---
confidence: high
---

# If — Wrong Branch Taken at Runtime (Whitespace / Case / Null in Condition)

## Context

An `If` activity (`System.Activities.Statements.If`) runs without error but takes the **wrong branch** —
the `Then` path runs when `Else` was expected, or vice versa — so the job completes **Successful** while
producing the wrong outcome (records routed to the wrong queue, an approval skipped, a check silently
bypassed). This is a **silent logic fault**: there is usually no exception and no faulted job, so there
is no error string to grep — route from the *symptom* ("job succeeded but the result is wrong / every
item goes down the same branch"), not an error code.

A related **runtime fault** variant: the Condition itself throws `System.NullReferenceException`
("Object reference not set to an instance of an object") when it dereferences an uninitialized
variable — that one DOES fault the job.

What this looks like:
- Job/run **Successful** but the branch outcome is wrong — e.g. every record takes the `Else` path even
  when the data should match the `Then` condition.
- No exception in most cases; the only evidence is the branch actually executed vs the branch expected
  (visible in `Log Message` output, downstream side effects, or output arguments).
- Variant: `System.NullReferenceException` raised **inside the `If.Condition`** — the job faults, stack
  points at the `If` condition expression.

What can cause it:
- **String comparison is case-sensitive.** VB `=` / `.Equals` on strings is case-sensitive by default
  (`Option Compare Binary`); `"APPROVED" = "Approved"` is `False`. The upstream system returns a
  different case than the literal in the Condition, so the match silently fails.
- **Leading/trailing whitespace.** The compared value carries hidden spaces/tabs/newlines
  (`"Success "` vs `"Success"`), from a UI scrape, Excel cell, API field, or CSV — the equality is
  `False` even though the values look identical.
- **Wrong-type / loose comparison.** Comparing a number formatted as text (`"010"` vs `"10"`), a
  trimmed vs untrimmed date string, or relying on `Object` equality (reference, not value).
- **Null in the Condition (fault variant).** The variable/argument the Condition reads was never
  initialized (or an upstream activity returned null), so member access inside the Condition throws
  `NullReferenceException`.

What to look for:
- The **actual runtime value** of the variable the Condition compares (from `Log Message` lines,
  output arguments, or upstream activity results) versus the **literal in the Condition** — compare
  them character-for-character for case and trailing whitespace.
- Whether the Condition uses `.Trim()` / case-normalization at all.
- For the fault variant: an exception message `Object reference not set…` whose stack points at the
  `If` condition.

## Investigation

1. **Establish which branch ran and what was expected.** For an Orchestrator job, read `uip or jobs
   logs` / `jobs get` — look for `Log Message` output naming the compared value and the branch outcome;
   for local execution, list `%localappdata%\UiPath\logs\` and open the log for the run date.
2. Locate the `If` in source (ask for the project directory if not provided). Read the exact
   `Condition` expression and the literal(s) it compares against.
3. **Compare the logged/actual value against the Condition literal character-for-character** — check
   for case differences (`APPROVED` vs `Approved`) and leading/trailing whitespace (`"Success "`). A
   value that "looks right" but fails the match is the tell.
4. Confirm the Condition does no normalization (no `.Trim()`, no case-insensitive compare) — an
   exact-match comparison against messy upstream data is the root cause.
5. **Fault variant:** if the job faulted with `NullReferenceException` at the `If` condition, trace the
   variable back to its (missing) initialization — see
   [null-reference-exception.md](./null-reference-exception.md).

The root cause is WHY the comparison mismatched (case, whitespace, type, or null) — not merely "the
wrong branch ran." A confirmed finding names the exact value-vs-literal difference.

## Resolution

- **Case mismatch:** compare case-insensitively — VB
  `value.Trim().Equals("approved", StringComparison.OrdinalIgnoreCase)` or `value.Trim().ToLower() =
  "approved"`. Normalize both sides the same way.
- **Whitespace:** `.Trim()` the value before comparing (`value.Trim() = "Success"`); trim upstream data
  at the point it is read if multiple checks depend on it.
- **Combined (recommended default):** `value.Trim().ToLower() = "success"` handles both case and
  whitespace in one expression.
- **Wrong-type / formatted-number:** compare as the correct type — parse numbers/dates
  (`CInt(value) = 10`, `DateTime.Parse(value) > cutoff`) instead of string-comparing formatted text.
- **Null in the Condition (fault variant):** guard with a short-circuit before dereferencing —
  `value IsNot Nothing AndAlso value.Trim().ToLower() = "success"` (`AndAlso` stops before the null
  deref). Ensure the variable is initialized / the upstream activity produced a value.
- **Do not mask it with `ContinueOnError`:** setting `ContinueOnError = True` hides the mismatch and
  makes the wrong-branch behavior harder to diagnose. Fix the comparison instead; wrap genuinely
  volatile checks (UI state, external calls) in a `Try Catch`
  (`System.Activities.Statements.TryCatch`) so real runtime errors surface rather than being swallowed.
