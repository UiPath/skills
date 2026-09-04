<!--skill-flavor:t01-preconditions:start-->
   - **For the `case` plugin (T01)**: `uip maestro case init "<ProjectName>"` (Step 6.0, CLI) creates the project in the open Studio Web solution at `/solution/<ProjectName>/` and seeds its scaffold. T01 then writes `caseplan.json` there (§ Write caseplan.json) and any of the 5 boilerplate files Studio Web did not seed (§ Scaffold). See [plugins/case/impl-json.md](plugins/case/impl-json.md). Pre-scaffold check: `/solution/<ProjectName>/` exists and `caseplan.json` is not yet authored.
<!--skill-flavor:t01-preconditions:end-->

<!--skill-flavor:bash-usage:start-->
**Bash is still used for**: UUID v4 generation only (`node -e "console.log(crypto.randomUUID())"` for `operate.json.projectId` and `entry-points.json` `uniqueId`; subprocess MUST NOT `require('fs')`, `require('child_process')`, or use any redirection operator), `uip maestro case init` (project creation in the open Studio Web solution) / `uip solution upload`, `uip maestro case validate`, `uip maestro case debug`, `uip maestro case registry` discovery, and read-only metadata fetches (`uip maestro case tasks describe`, `is resources describe`, `is triggers describe`). Never for file mutation.
<!--skill-flavor:bash-usage:end-->
