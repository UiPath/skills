# Finance automation team — UiPath build conventions

1. **Workflow type:** coded C# workflows only; no XAML.
2. **Output folders:** every report is written to the shared drive `\\finance-fs\reports`, never to a local disk.
3. **Logging:** Orchestrator job log only; no log files.
4. **Naming:** projects are named `FIN_<Process>`.
