<!--skill-flavor:flow-project-location:start-->
1. **Locate the canonical `.flow` file in the Studio Web workspace/VFS.** List the projects exposed under `/solution`, identify the host-generated Flow project, and edit the `.flow` entrypoint inside that project directory. Treat the host-exposed tree as authoritative. `uip maestro flow validate <PATH>.flow` checks the file supplied to it, so also confirm that the chosen path belongs to the host-generated project.
<!--skill-flavor:flow-project-location:end-->
