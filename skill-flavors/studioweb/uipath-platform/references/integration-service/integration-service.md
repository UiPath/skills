<!--skill-flavor:headless-sign-in-1:start-->
| Ping returns non-enabled | Run `is connections edit <id>` to re-authenticate, then ping again. If still fails, ask user to choose another connection or create new. |
<!--skill-flavor:headless-sign-in-1:end-->

<!--skill-flavor:headless-sign-in-2:start-->
| Execute fails with 403 (scope) | Connection is Enabled but lacks optional scopes for this activity. Re-authorize with broader scopes via `is connections edit <id>`. See [connections.md](connections.md). |
<!--skill-flavor:headless-sign-in-2:end-->
