<!--skill-flavor:step-create-solution:start-->
## Step 1: The Open Solution

Studio Web works on one open solution, already scaffolded as the workspace root (`/solution`); never create another. All projects live inside it.
<!--skill-flavor:step-create-solution:end-->

<!--skill-flavor:e2e-create-and-add:start-->
```bash
# 1. The open Studio Web solution is the only solution — nothing to create.
# 2. Add projects (already inside the solution directory)
uip solution projects add ./InvoiceAutomation/Processor --output json
uip solution projects add ./InvoiceAutomation/Reporter --output json
<!--skill-flavor:e2e-create-and-add:end-->

<!--skill-flavor:upload-as-new:start-->
To upload as an unrelated new cloud solution rather than overwriting, replace the `SolutionId` in the local `.uipx` with a fresh GUID and re-run `upload` — removing the field entirely fails `.uipx` validation.
<!--skill-flavor:upload-as-new:end-->

<!--skill-flavor:cheat-create-row:start-->
<!--skill-flavor:cheat-create-row:end-->
