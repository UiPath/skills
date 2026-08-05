<!-- skill-flavor:instance-lifecycle:start -->
Intervene in a Flow instance only through a lifecycle capability advertised in the current Studio Web session. Authentication is inherited; never run `uip login`.

- Read the advertised project ProxyTool skill before invoking a host lifecycle action.
- If using a browser CLI instance command, use the exact live prefix and options from `--help`, including any required instance or folder key returned by the run.
- Diagnose a fault before retrying and confirm any destructive cancel operation not already requested by the user.
- If pause, resume, cancel, or retry is not exposed, report the missing capability instead of substituting desktop commands.
<!-- skill-flavor:instance-lifecycle:end -->
