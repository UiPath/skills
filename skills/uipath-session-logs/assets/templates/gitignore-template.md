# .gitignore Template

Add this block to your project's `.gitignore` to keep session captures out of the repo.

```gitignore
# UiPath session logs (uipath-session-logs skill)
.uipath-logs/
```

Captured payloads include raw tool inputs and responses, which may contain orchestrator tokens, tenant URLs, personal access tokens, or customer data. They are intended for local debugging and targeted bug reports — never commit them.
