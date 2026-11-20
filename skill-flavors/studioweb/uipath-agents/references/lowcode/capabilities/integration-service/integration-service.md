<!--skill-flavor:headless-sign-in-1:start-->
Present connections to the user. Recommend the default enabled one but let the user confirm. When the task names something in the connected system (a Jira project, a Slack channel), the connection must be able to see it; Step 6, "Fields that load after a selection", says how to check. Note the connection `Id`, `FolderKey`, `Name`. If the `--all-folders` list is empty, no connection exists: prompt the user to create one via `uip is connections create "<connector-key>"` — never generate a placeholder or random `Id`.
<!--skill-flavor:headless-sign-in-1:end-->

<!--skill-flavor:is-solution-files-refresh:start-->
3. Add the connection to the solution: `uip solution resources add --source remote --kind Connection --cloud-key <ConnectionId> --output json`. Do not run `uip solution resources refresh`: it fails in Studio Web (see [critical-rules.md](../../critical-rules/critical-rules.md) Anti-pattern 7).
<!--skill-flavor:is-solution-files-refresh:end-->

<!--skill-flavor:is-connection-definition-refresh:start-->
**Declared with `resources add`:** Do not create these files manually. After `uip agent refresh` and `uip agent validate`, run `uip solution resources add --source remote --kind Connection --cloud-key <ConnectionId> --output json`; Studio Web writes the connection resource. `uip solution resources refresh` fails here.
<!--skill-flavor:is-connection-definition-refresh:end-->

<!--skill-flavor:is-step8-refresh:start-->
### Step 8 — Refresh, validate, and add the connection to the solution

```bash
# Refresh — regenerates entry-points.json and bindings_v2.json.
uip agent refresh "<AGENT_NAME>" --output json

# Validate — read-only check.
uip agent validate "<AGENT_NAME>" --output json

# Declare the connection in the open solution. `uip solution resources refresh`
# fails in Studio Web, so add it yourself with the connection `Id` from Step 3.
uip solution resources add --source remote --kind Connection --cloud-key <ConnectionId> --output json

# Confirm the solution now lists the connection.
uip solution resources list --source local --output json
```

Add every other tenant resource the agent uses (memory spaces, indexes) the same way; see [critical-rules.md](../../critical-rules/critical-rules.md) Anti-pattern 7.
<!--skill-flavor:is-step8-refresh:end-->
