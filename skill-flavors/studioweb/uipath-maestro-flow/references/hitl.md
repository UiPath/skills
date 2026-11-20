<!--skill-flavor:field-variable-sdk-upgrade:start-->
  — tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:field-variable-sdk-upgrade:end-->

<!--skill-flavor:field-type-sdk-upgrade:start-->
  so tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:field-type-sdk-upgrade:end-->

<!--skill-flavor:field-settings-sdk-upgrade:start-->
  so tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:field-settings-sdk-upgrade:end-->

<!--skill-flavor:action-schema-sdk-upgrade:start-->
so tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:action-schema-sdk-upgrade:end-->

<!--skill-flavor:inso-app-uip-floor:start-->
  If the run fails with `170004 Invalid input for the HITL task`, tell the
  user Studio Web's packager dropped the in-solution app's folder, and do not
  retry the run.
<!--skill-flavor:inso-app-uip-floor:end-->

<!--skill-flavor:app-sibling-register:start-->
  The app project must already be in the open solution. Do not run
  `uip solution resources refresh`: it fails in Studio Web. The
<!--skill-flavor:app-sibling-register:end-->

<!--skill-flavor:inso-app-sdk-upgrade:start-->
  so tell the user: Studio Web owns the SDK copy.
<!--skill-flavor:inso-app-sdk-upgrade:end-->

<!--skill-flavor:hitl-live-debug:start-->
Debug suspends at the task until a person completes it, so the reply ends in `TimedOut` with no instance id. Do not re-run or search with `uip tasks list`; tell the user the run waits for the task in Action Center.
<!--skill-flavor:hitl-live-debug:end-->
