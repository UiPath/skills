<!--skill-flavor:headless-sign-in-1:start-->
- **Token / auth inner message:** re-authenticate the connection (`uip is connections edit <connection-id>` or the UI). If `invalid_grant` / revoked / scope errors, re-authorize the app in the external service first. If `user is no longer a member of the organization`, the connection's owning identity must be replaced.
<!--skill-flavor:headless-sign-in-1:end-->
