<!--skill-flavor:operation-doc:start-->
**Read the operation's own doc before guessing anything.** The connector library
has a page per operation. Print it:

```bash
uip maestro registry describe uipath.connector.uipath-uipath-dataservice.create-entity-record --output plain
```

That page names the connector *UiPath Data Fabric*, gives the HTTP route
(`POST /v2/{entityName}/CreateEntityRecord`), and prints the exact
`-f entityName=<value>` prepare to run — before any of it has to be inferred.
<!--skill-flavor:operation-doc:end-->
