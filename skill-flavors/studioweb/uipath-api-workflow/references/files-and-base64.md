<!--skill-flavor:file-inputs-cli:start-->
Files live in Orchestrator blob storage, so a run needs the active Studio Web session. After `uip api-workflow validate Workflow.json --output json` is `Valid`, state the concrete side effects and ask for explicit consent; on approval inspect `/skills/synthetic/proxy-tools-Api/SKILL.md` and the live `RunProject` schema and invoke it with exactly its declared fields. File inputs are supplied through the fields that schema exposes for `JobAttachment` arguments (the host uploads them and passes the reference), and files the workflow returns appear as attachment references in the host result. Report any capability gap with the exact host result.

`uip api-workflow validate` covers these activities offline: it accepts `FileToBase64` / `Base64ToFile` and rejects a task of either type whose script does not call its `$helpers.file.*` function.
<!--skill-flavor:file-inputs-cli:end-->
