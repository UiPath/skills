<!--skill-flavor:xsi-unbound-prefix:start-->
- `xsi:type` needs `xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"` on
  `bpmn:definitions`. The `init` scaffold does not declare it. Declare it on
  every file you author, and run `validate`: the sandbox has no `python3`, so
  `validate` is the parse check (see [Validation](#validation)).
<!--skill-flavor:xsi-unbound-prefix:end-->

<!--skill-flavor:wellformed-parse:start-->
The sandbox has no `python3`: do not run a separate XML parse. `validate` is
the parse check, and an `XML_NOT_WELL_FORMED` finding is a source defect to
fix before anything else.
<!--skill-flavor:wellformed-parse:end-->
