<!--skill-flavor:step-create-solution:start-->
## Step 1: The Open Solution

Studio Web works on one open solution, already scaffolded as the workspace root (`/solution`); never create another. All projects live inside it.
<!--skill-flavor:step-create-solution:end-->

<!--skill-flavor:tenant-df-rpa:start-->
RPA (XAML) workflows use strongly-typed DataService activities. `uip rpa` has no entity commands in Studio Web: choosing the entity in the activity's Entity property in the designer, with Entity Scope `Tenant`, installs it into the project, and Data manager → Entities lists it. Studio Web builds the generated types into the package when it publishes the solution; the deployed process reads the tenant entity.
<!--skill-flavor:tenant-df-rpa:end-->

<!--skill-flavor:e2e-lead-in:start-->
Add two projects to the open solution, sync resources, and verify:
<!--skill-flavor:e2e-lead-in:end-->

<!--skill-flavor:e2e-create-and-add:start-->
```bash
# Projects are created with `uip <family> init <Name>` and registered
# automatically; resources stay in sync in the host (`resources refresh`
# is Node-CLI-only). Verify from /solution:
<!--skill-flavor:e2e-create-and-add:end-->

<!--skill-flavor:upload-as-new:start-->
<!--skill-flavor:upload-as-new:end-->

<!--skill-flavor:cheat-create-row:start-->
<!--skill-flavor:cheat-create-row:end-->
