<!--skill-flavor:host-availability-extra:start-->
> **Not available in Studio Web.** The `uip vss deploy` command family (`deploy`, `status`, `resume`, `cancel`, `seed`) is not in the Studio Web CLI. Do not try to deploy from this host, and do not work around it with REST calls to the Vertical Solutions service. Tell the user to deploy from a terminal on their own machine: install the `uip` CLI (`curl -fsSL https://download.uipath.com/uipath-cli/install.sh | bash` on macOS/Linux; `irm https://download.uipath.com/uipath-cli/install.ps1 | iex` in Windows PowerShell), run `uip login`, then run `uip vss deploy`, which asks every question itself. Answer questions about the steps and the access below from this skill, but do not run them here.
<!--skill-flavor:host-availability-extra:end-->

<!--skill-flavor:cli-ready:start-->
- In Studio Web, stop here: `uip vss deploy` is not in this host's CLI, and the host injects authentication, so there is no `uip login` step to run. Give the user the terminal instructions from the note at the top of this skill.
<!--skill-flavor:cli-ready:end-->
