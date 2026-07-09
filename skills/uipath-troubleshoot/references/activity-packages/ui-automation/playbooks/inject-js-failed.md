---
confidence: medium
---

# Inject Js Script — Script Missing or Execution Failed

## Context

An `Inject Js Script` activity (`NInjectJsScript`) either had no script to run or the JavaScript failed when executed in the browser.

What this looks like:
- `Required argument 'Script code' was not provided.` — the `Script code` input was empty/whitespace at runtime.
- A runtime error surfacing the browser/JavaScript engine's own message — the script was sent to the page but threw or could not run.

What can cause it:
- The `Script code` input is empty — often a variable/expression an earlier step should have populated.
- `Script code` is meant to be a path to a `.js` file: when the path can be read, its contents run; when it cannot be read, the value itself is sent to the page as script text and fails as invalid JavaScript. A wrong/missing path therefore surfaces as a JavaScript error, not a "file not found".
- The JavaScript itself throws (references a missing element/global, syntax error, async assumptions about page state).
- The activity runs against a target that is not a live web page/DOM, so there is no JavaScript context to execute in.
- The script's return value cannot be serialized back from the page.

What to look for:
- Confirm the faulting activity is `Inject Js Script`.
- Read the `Script code` input: inline script vs file path vs variable, and what it evaluates to.
- Confirm the activity targets a web page (a `Use Browser` context or a web element).

## Investigation

1. From the failed job, capture whether the message is the missing-`Script code` argument or a JavaScript/browser execution error, plus the activity + workflow.
2. Read `Script code`. If empty, trace the upstream step that should produce it. If it is a file path, confirm the path resolves on the robot — an unreadable path is run as literal script and fails.
3. If the script is present, read the browser/engine error: it usually names the offending line, missing reference, or syntax issue.
4. Confirm the target is a web page with a DOM (the activity needs a browser/JavaScript context).
5. Check whether the script depends on page state that may not be ready when it runs.

## Resolution

- **Empty `Script code`:** fix the upstream step that should produce it (or supply the script directly when it is static).
- **File-path script that didn't load:** correct the `.js` path so it resolves on the robot, or inline the script.
- **JavaScript error:** fix the script — guard for elements/globals it assumes exist, correct syntax, and account for page-load timing (wait for the element/state before injecting).
- **Non-web target / no DOM:** run the activity against a web page inside a `Use Browser` context; `Inject Js Script` needs a JavaScript context.
- **Unserializable return:** return a serializable value (string/number/plain object) from the script.
