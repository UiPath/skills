import { dynamicExtract, flow, input, manual, types } from "@uipath/maestro-builder-sdk";

export default flow("df38c5d0-6ee9-44ee-af6c-e996897c01cf")
  .schemaVersion("1.9")
  .name("InvoiceReader")
  .openTails()
  .trigger(manual(), { version: "1.0" })
  .input({ invoice: { type: types.file, description: "The invoice document to extract" } })
  .step("extractInvoice1", dynamicExtract({ fileRef: input("invoice"), schema: {"prompt":"Extract the invoice header fields exactly as they appear on the page.","outputSchema":{"type":"object","additionalProperties":false,"required":["Invoice"],"properties":{"Invoice":{"type":["object","null"],"description":"The invoice header, which appears once per document.","additionalProperties":false,"required":["Invoice Number","Invoice Date","Vendor Name","Total"],"x-uipath-field-group-id":"7096e6d3-9cfc-483b-9085-56fc5720279b","properties":{"Invoice Number":{"$ref":"#/$defs/ft-exact-text","description":"The invoice number as printed, without a leading # or the word 'Invoice'.","x-uipath-field-id":"9fbb50a5-5b7a-442b-bc48-4d528c82e200"},"Invoice Date":{"$ref":"#/$defs/ft-inferred-text","description":"The date the invoice was issued, not the due date.","x-uipath-field-id":"9ad17b9e-17ce-4410-a4d8-2d19bec3f25d"},"Vendor Name":{"$ref":"#/$defs/ft-inferred-text","description":"The company that issued the invoice, from the letterhead or the remit-to block.","x-uipath-field-id":"d246a961-e9bc-452a-9ff5-f86178bb535c"},"Total":{"$ref":"#/$defs/ft-monetary-quantity","description":"The amount payable including tax, usually the last line of the summary block.","x-uipath-field-id":"059158da-1564-4680-a208-ce02de660518"}}}},"$defs":{"ft-exact-text":{"title":"Exact Text","type":["string","null"],"format":"verbatim"},"ft-inferred-text":{"title":"Inferred Text","type":["string","null"]},"ft-date":{"title":"Date","type":["string","null"],"format":"date"},"ft-number":{"title":"Number","type":["string","null"],"format":"decimal"},"ft-monetary-quantity":{"title":"Monetary Quantity","type":["string","null"],"format":"monetary"},"ft-boolean":{"title":"Boolean","type":["boolean","null"]}}},"config":{"extraction_method":"external_llm","model":{"family":"gemini","version":"gemini_2_5_flash"},"execution_mode":"standard","pre-processing":"none","attribution":"word_ids","model_config":{"temperature":null,"top_p":null,"seed":null,"frequency_penalty":null,"prompt_override":null}}} }), { version: "1.0.0", label: "Extract Invoice" })
  .layout({
    nodes: {
      start: { position: { x: 256, y: 144 } },
      extractInvoice1: { position: { x: 0, y: 0 } },
    },
  })
  .build();
