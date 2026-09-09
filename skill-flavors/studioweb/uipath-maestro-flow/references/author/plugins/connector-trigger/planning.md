<!--skill-flavor:ct-debug-impact:start-->
> **Debug impact:** Only `polling` triggers can be debugged. `webhooks` triggers cannot be tested via `uip flow debug` — publish (`uip solution publish --location "<FolderPathOrKey>"`) and fire a real event. Flag this in the plan if the trigger uses webhook mode.
<!--skill-flavor:ct-debug-impact:end-->
