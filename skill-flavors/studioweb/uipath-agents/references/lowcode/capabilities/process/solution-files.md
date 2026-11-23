<!--skill-flavor:rest-fallback-auth:start-->
> **In Studio Web, Steps 2–3 do not run.** They call Orchestrator through `uip api`, which is not in this host's CLI. Get the values from `uip solution resources get` instead — see [process.md § Discovery](process.md#discovery). If it cannot supply a value, stop and tell the user which value is missing. Never read credentials or call the API another way.
<!--skill-flavor:rest-fallback-auth:end-->

<!--skill-flavor:releases-query:start-->
In Studio Web this query does not run (see the note above); `uip solution resources get` returns these fields.
<!--skill-flavor:releases-query:end-->

<!--skill-flavor:entry-points-query:start-->
In Studio Web this call does not run (see the note above); `uip solution resources get` returns these fields.
<!--skill-flavor:entry-points-query:end-->
