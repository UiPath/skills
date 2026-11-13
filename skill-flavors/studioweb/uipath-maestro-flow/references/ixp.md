<!--skill-flavor:ixp-list-commands:start-->
```bash
uip maestro flow registry pull --force
uip maestro flow registry search 'uipath.ixp' -f 'type:startsWith=uipath.ixp' --output json
```
<!--skill-flavor:ixp-list-commands:end-->

<!--skill-flavor:ixp-no-login:start-->
- **You are already signed in.** Studio Web signs you in to the tenant of the user, so the search shows the tenant IxP nodes.
<!--skill-flavor:ixp-no-login:end-->

<!--skill-flavor:ixp-no-model:start-->
If the registry has no suitable published extractor, report the missing model and stop. Do not hand off to `uipath-ixp` and add no Extract document node unless the user named it. Only when the user asked for a placeholder or a validate-only topology, put `mock()` in the extraction position, complete and validate the surrounding flow, and report the placeholder as the capability gap.
<!--skill-flavor:ixp-no-model:end-->
