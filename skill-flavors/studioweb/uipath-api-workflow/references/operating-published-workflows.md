<!--skill-flavor:published-operations:start-->
After publication, operate and diagnose the API Workflow only through capabilities exposed by Studio Web. Inspect each live lifecycle, run, job, log, trace, trigger, or connection tool schema immediately before invocation and use only schema-declared fields.

- Use read-only embedded `uip is` discovery, including `connections list` / `ping`, only to inspect connector and connection state.
- Do not run embedded or machine-local `uip or`, `uip traces`, `uip is connections edit`, authentication, pack, deploy, or solution commands as operational fallbacks. Host-intercepted `uip solution publish` is only for a separate, explicit request to publish a new active-solution version; it does not operate an existing published workflow.
- Do not infer success from prose. Require the actual Studio Web tool result and, when relevant, the visible run/job state.
- If Studio Web exposes no capability for the requested published operation or diagnostic, report the exact gap and hand off the deeper platform investigation rather than switching environments.
- Preserve explicit consent before any operation that starts a workflow or can create external side effects.
<!--skill-flavor:published-operations:end-->
