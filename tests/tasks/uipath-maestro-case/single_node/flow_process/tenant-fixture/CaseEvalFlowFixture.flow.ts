import { flow, manual, script, out, types } from "@uipath/maestro-builder-sdk";

export default flow("b764c62f-52f8-4eff-b0c9-544028206d08")
  .schemaVersion("1.9")
  .name("CaseEvalFlowFixture")
  .trigger(manual(), { version: "1.0" })
  .input({ invoiceNumber: types.string })
  .output({ status: types.string })
  .step("acknowledge", script({ code: "return `received-${$vars.start.output.invoiceNumber}`;" }))
  .return({ status: out("acknowledge") })
  .build();
