<!--skill-flavor:headless-sign-in-1:start-->
- **None**: Ask user to create via `is connections create "<connector-key>"`.
<!--skill-flavor:headless-sign-in-1:end-->

<!--skill-flavor:headless-sign-in-2:start-->
| Fails | Run `is connections edit <id>` to re-authenticate, then ping again. If still fails, ask user to choose another or create new. |
<!--skill-flavor:headless-sign-in-2:end-->

<!--skill-flavor:headless-sign-in-3:start-->
  - Auth error → run `is connections edit <id>` to re-authenticate, then ping again
<!--skill-flavor:headless-sign-in-3:end-->
