import { flow, manual, script, out, types } from "@uipath/maestro-builder-sdk";

export default flow("e30434b7-0396-4025-8c4b-e26ce3df9e91")
  .schemaVersion("1.9")
  .name("PermitDesk")
  .input({ permit: types.file })
  .output({ summary: types.string })
  .trigger(manual(), { version: "1.0" })
  .step("logReceipt", script({ code: `return "Permit received";` }))
  .return({ summary: out("logReceipt") })
  .build();
