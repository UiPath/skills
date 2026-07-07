# Invoke VBA EntryMethodName - de-DE localized canary (translate-forcing)

Locale-robustness canary #2: unlike the classic-movefile canary, this scenario's playbook
(`invoke-vba-entry-method-name.md`) is routable ONLY by message signatures ("Cannot run the
macro" / "Sub or Function not defined") - there is no language-invariant exception class or
error code for it in the signature index. The fixtures' only exception class (COMException)
is indexed for an unrelated Word playbook whose preconditions do not fit.

All Office/VBA error messages in the fixtures are localized to authentic de-DE wording.
Routing therefore succeeds only via the skill's translate-before-grep rule: read the German
message, translate to canonical English, grep the index. CLI-only (no source snapshot), so
the localized runtime evidence cannot be bypassed.

Grading: identical contract to the English variant (same root cause, same fix).
