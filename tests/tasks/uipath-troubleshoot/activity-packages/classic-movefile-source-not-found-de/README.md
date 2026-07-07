# Classic MoveFile Source Not Found — de-DE localized canary

Locale-robustness canary for the signature-index routing design: identical scenario to
`classic-movefile-source-not-found`, but every agent-visible .NET framework message in the
fixtures is localized to German (de-DE robot host), as real non-English Windows hosts emit.
Exception class names (`System.IO.FileNotFoundException`) and stack frames stay invariant,
matching real .NET behavior.

What it validates: routing must succeed via language-invariant signals (exception class) and/or
translate-before-grep of the localized message — per SKILL.md's localized-error-text rule.
A failure here means the skill's diagnosis depends on English message text.

Grading: identical contract to the English variant (`RESOLUTION.md` — same root cause, same fix).
