<!-- skill-flavor:diagnostic-workflow:start -->
Use the following Studio Web diagnostic ladder:

1. **Run result:** capture state, message, project display name, trace/log excerpt, instance ID, and trace ID.
2. **Incidents:** when an incident operation is advertised, fetch incidents for the returned run/instance and inspect the specific incident.
3. **Runtime variables:** inspect only through an advertised project or browser CLI capability.
4. **Flow correlation:** read the current `.flow` from `/solution/<project>/` and map the faulting element to its node, edges, variables, and definition.
5. **Deployed asset:** use an advertised asset/BPMN operation when the executed version may differ from the open file.
6. **Traces:** use only when earlier evidence is insufficient; traces are verbose and may contain sensitive values.

Use the exact command prefix and required identifiers shown by the current session. Never run login/config, infer `.uipx` state, or fabricate an unavailable incident/instance command. If a step is unsupported, skip it explicitly and continue with the remaining evidence.
<!-- skill-flavor:diagnostic-workflow:end -->
