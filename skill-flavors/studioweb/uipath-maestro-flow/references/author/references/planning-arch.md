<!-- skill-flavor:plan-output-location:start -->
Generate the plan at `/solution/<FlowProject>/.autopilot/<FlowProject>.uipath.flow.arch.plan.md`. Studio Web has no writable filesystem-backed solution directory or `.uipx`; keep planning material in the reserved `.autopilot/` folder of the current Flow project. The plan may describe sibling projects in the active solution, but it must not be written directly under `/solution` because that mount contains project entities, not arbitrary files.
<!-- skill-flavor:plan-output-location:end -->
