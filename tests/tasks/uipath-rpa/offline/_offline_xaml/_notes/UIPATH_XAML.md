# Notes on this setup

This folder is a UiPath process project, as `uip rpa init` creates it: cross-platform
(`"targetFramework": "Portable"`), VB.NET expressions, and one dependency,
`UiPath.System.Activities` 26.8.2. Keep those settings; no other package can be restored here.
`Main.xaml` is the entry point.

The workflow is tested by running it unattended, once per test case, and looking at what the job
shows: whether it completed or faulted (and with which exception), its output arguments, what it
logged and at which level, and the files it wrote. A faulted job returns no output arguments.

This environment has Studio Web Autopilot's constraints: there is no Studio, and `uip` serves only
`uip rpa init` and `uip rpa run`, as the Studio Web host does; `validate`, `build` and the other
`uip rpa` verbs don't exist. `uip rpa run --file-path Main.xaml --input-arguments name=value` (or
`name:=<json>` for a typed value) runs a workflow headlessly and prints its log, then its result.

There is no robot, Orchestrator, network or screen, so UI automation, Orchestrator assets and
queues, and Invoke Process aren't available. Read CSV and Write CSV come with the Excel
package, which this project doesn't have. Don't use Invoke Code.
