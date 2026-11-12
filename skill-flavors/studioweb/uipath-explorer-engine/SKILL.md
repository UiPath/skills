<!--skill-flavor:explorer-engine-availability:start-->
- **`--help` succeeds** → continue.
- **`unknown command` or `UnavailableInHost`** → Studio Web's built-in `uip` does not ship `uip explorer-engine`. Tell the user to run the analysis from a local terminal with a prerelease `uip` build (`preview` / `dev` channel), and stop. Do not reach the Explorer Engine API another way.
- **Not logged in** → tell the user to sign in to Studio Web again, then stop.
<!--skill-flavor:explorer-engine-availability:end-->
