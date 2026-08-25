---
confidence: medium
---

# Invoke Code Failed

## Context

`Invoke Code` failed either to compile the supplied snippet or while running it. The activity
compiles the code (C#/VB) before execution, so failures split into compile-time and run-time.

What this looks like:
- A compilation error listing the offending line(s) in the snippet
- "No compiled code to run" — there was no successfully compiled code to execute
- An error that the language is not supported in the current runtime
- A run-time exception thrown by the snippet itself (e.g. a null reference, an index out of range, an
  external call failing)

What can cause it:
- Syntax errors in the snippet, or references to types/namespaces not imported in the project
- An argument referenced in the snippet whose name/type/direction does not match the `Arguments`
  defined on the activity
- A language selected that the current runtime/project does not support
- Missing assembly/namespace imports for the APIs the snippet uses
- The snippet compiles but throws at run time because of the data it operates on or an external
  dependency it calls

What to look for:
- The full compiler error text and the line it points to
- The `Arguments` defined on the activity vs the identifiers used in the snippet
- The project's imported namespaces/references vs what the snippet needs
- Whether the failure is at compile time (before any logic runs) or at run time (a thrown exception)

## Investigation

1. Read the error: distinguish a compilation failure ("No compiled code to run" / compiler errors)
   from a run-time exception thrown by the snippet.
2. For compilation errors, locate the line the compiler names and the missing type/namespace or
   syntax problem.
3. Compare the snippet's referenced identifiers against the activity's `Arguments` (name, type,
   direction) and against the project's imports/references.
4. For run-time exceptions, identify which statement threw and what input/data it was operating on.
5. Confirm the selected language is supported by the project/runtime.

## Resolution

- **If there are syntax/type errors:** fix the snippet syntax and add the required namespace
  imports / assembly references in the project.
- **If arguments don't match:** align the activity's `Arguments` with the identifiers, types, and
  directions used in the snippet.
- **If the language is unsupported:** switch to a language the runtime supports, or update the
  project/runtime so the chosen language is available.
- **If the snippet throws at run time:** fix the logic or guard the input/dependency it failed on,
  the same as you would for any runtime exception in workflow code.
