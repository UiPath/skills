# validation

## Purpose
Catch dashboard errors BEFORE the user is told to open `http://localhost:5173`. A Build session must not declare success until the generated code type-checks AND every SDK method the generated query hooks call actually exists in the introspected manifest.

User feedback: "my preview was generated but there was errors, skill should validate there should be no errors. Also whatever APIs that are getting used in dashboard should be validated so that runtime does not break."

## When to run
After Generate, before Preview hands the user a URL.

## Two validation passes

### Pass 1 — Static type check
Run `npx tsc --noEmit` in the project root. Capture stderr. If non-zero exit:
1. Parse the errors. Group by file. Cap at 5 most-relevant errors for user display.
2. Surface a friendly summary:
   ```
   ⚠ Found <N> type errors in the generated dashboard. Fixing automatically...
     - <Widget>: <human-readable reason>
     - ...
   ```
3. **Self-heal common cases** before re-running:
   - Missing import → add it.
   - Wrong field name on SDK row → cross-reference the introspected `.d.ts` for the actual field name; correct.
   - `jobError` rendered raw → wrap with `formatJobError()`.
   - `dueDate` referenced (Tasks have no `dueDate` — see `service-semantics.md` § Tasks) → switch to `taskSlaDetail.status` via `taskSlaStatusOf()`.
4. Re-run tsc. Up to 3 iterations. If still failing, halt and surface to user with: *"I hit a type error I can't fix automatically: <error>. Want me to retry, skip the failing widget, or pause for you to look?"*

### Pass 2 — API existence check
For each generated query hook in `src/lib/queries/*.ts`:
1. Parse the file (regex is enough): find every call of the form `new <ClassName>(sdk).<methodName>(...)` or `<sdkInstance>.<className>.<methodName>(...)`.
2. For each `(className, methodName)` pair:
   - Look up the class in `<project>/.dashboard/sdk-manifest.json` `services[].exports.classes[]`.
   - Look up the method in that service's `methods[]` filtered by `class === className`.
   - If either is missing → that query hook calls a non-existent API. Surface: *"<Widget> calls <ClassName>.<methodName>(), which doesn't exist in the installed SDK (v<sdkVersion>). Did you mean <closest match by edit-distance>? Or skip this widget?"*
3. **Validate parameter shape against the manifest** (best-effort):
   - Method signature in manifest is `paramsRaw` like `"options?: JobGetAllOptions"`.
   - Generated call passes a literal — e.g., `{filter: "...", pageSize: 1000}`.
   - Cross-reference the param type's interface definition (in the manifest's `interfaces[]`) when available.
   - On detected mismatch, surface clearly. We don't auto-fix because parameter shape is too easy to get wrong; the user / agent should review.

## Pass 3 — Dev-server smoke (optional, lightweight)
Once tsc passes:
1. `npm run dev` in the background; capture the first 5 seconds of output.
2. Look for resolution errors (`Could not resolve "..."`), missing dep errors (`Cannot find module ...`), parse errors.
3. If any → halt and surface; usually a missing import the type-check didn't catch (unusual but happens with subpath exports).
4. If clean → leave the dev server running, proceed to user-facing summary.

## Failure surface — friendly UX

When validation fails, the user sees ONE summary:
```
⚠ I built the dashboard but found <N> issues during validation. Fixing now...

  ✓ Active Agents — OK
  ✓ Invocation Volume — OK
  ⚠ Trace Spans — references conversational-agent.Spans.getRecent() which
                  doesn't exist in SDK 1.3.2. The SDK has Exchanges.getAll()
                  with similar data — switch to that?
  ✗ Top Agents Table — type error: row.errorRate (number) not assignable to
                       string. Fixed automatically.

Reply 'switch trace widget to Exchanges' or 'remove the trace widget' to continue.
```

The user makes a decision; the agent applies it; we re-validate; we don't claim success until everything passes.

## Anti-patterns

- **Telling the user the dashboard is ready when tsc has errors.** Banned. Validation gate is non-skippable.
- **Surfacing raw tsc output.** Translate to friendly messages with widget names — "Active Agents widget" not "src/dashboard/widgets/ActiveAgentsKPI.tsx:34:12".
- **Failing without a recovery offer.** Every validation failure ends with "want me to skip / switch / pause?" — never "build failed, goodbye."
- **Skipping API validation because tsc passed.** Tsc only catches what types declare. The SDK's manifest reveals what actually exists; runtime breakage often comes from method-name typos that happen to type-check against `unknown`.
- **Running validation BEFORE the plan was approved.** Order is: Plan → Approval → Generate → Validate. Validating an unapproved plan is wasted work.
