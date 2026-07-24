# Classic MoveFile Source Not Found — de-DE localized canary

Locale-robustness canary for the grep-based playbook routing design: identical scenario to
`classic-movefile-source-not-found`, but every agent-visible .NET framework message in the
fixtures is localized to German (de-DE robot host), as real non-English Windows hosts emit.
Exception class names (`System.IO.FileNotFoundException`) and stack frames stay invariant,
matching real .NET behavior.

What it validates: routing must succeed via language-invariant signals (exception class) and/or
translate-before-grep of the localized message — per SKILL.md's localized-error-text rule.
A failure here means the skill's diagnosis depends on English message text.

CLI-only variant: the project source snapshot is deliberately omitted so the ONLY evidence path runs through the localized runtime fixtures — a source snapshot lets agents shortcut to design-time evidence and never touch the German text (observed in the first validation run).

Grading: identical contract to the English variant (`RESOLUTION.md` — same root cause, same fix).
