<!-- skill-flavor:diagnostic-contract:start -->
Diagnose a failed Studio Web Flow run from the host result outward:

1. Start with the terminal status, error, trace/log excerpt, instance ID, and trace ID returned by `RunProject` or the live run command.
2. Read `/skills/synthetic/proxy-tools-Flow/SKILL.md` when advertised and use only its listed diagnostic operations through `ProxyTool`.
3. If the live browser bundle exposes incident, variable, asset, job, or trace commands, inspect them in the order **incident → variables → deployed asset/Flow correlation → traces**.
4. Correlate faulting element IDs with the `.flow` under `/solution/<project>/` and apply the smallest authoring fix.
5. Obtain consent before re-running a Flow with side effects.

Authentication is inherited; never run `uip login`. Do not assume legacy `uip maestro flow` commands, a folder key, or a project proxy exists unless the current session exposes it. If deeper diagnostics are unavailable, report the evidence collected and the missing capability.
<!-- skill-flavor:diagnostic-contract:end -->
