# Registry workflow: connector object

## 3. Connector (`Intsvc.*`) enrichment

For connector **activity** types (`requiresDiscovery: Yes`, e.g.
`Intsvc.ActivityExecution`), resolve a live connection and object, then enrich.
`Intsvc.EventTrigger` and `Intsvc.WaitForEvent` also require discovery but
resolve their object elsewhere — see
[Integration Service triggers](registry-workflow-bindings.md#integration-service-triggers).

```bash
uip is connections list --all-folders --output json   # pick a connection id + its connector (search all folders)
uip is resources list <connectorKey> --connection-id <id> --output json   # the objects that connector exposes
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <id> --object-name <object> --output json
```

### Picking the object: take it from the table, do not infer it

A connector exposes several objects that perform the same operation, and
`uip is resources describe` cannot rank them. Four Jira objects create an
issue; describe prints `Curated: "Create Issue"` for two of them, because its
summary drops the `curated.isHidden` flag that marks the live one. Ranking on
`Type: curated` or on the display name picks a hidden legacy object instead.

So take the object from this table rather than inferring it. Confirm it with
`uip is resources describe <connectorKey> <object> --connection-id <id>
--operation <Operation.Name>` before authoring, and read `RequestFields` and
`Parameters` from that same call.

| Connector key | Object | Activity | Operation |
| --- | --- | --- | --- |
| `uipath-atlassian-jira` | `curated_create_issue` | Create Issue | `Create` |
| `uipath-atlassian-jira` | `curated_get_issue` | Get Issue | `Retrieve` |
| `uipath-atlassian-jira` | `curated_edit_issue` | Update Issue | `Replace` |
| `uipath-salesforce-slack` | `send_message_to_channel_v2` | Send Message to Channel | `Create` |
| `uipath-microsoft-outlook365` | `send-mail-v2` | Send Email | `Create` |
| `uipath-uipath-dataservice` | `<EntityName>` | Create Entity Record | `Create` |
| `uipath-uipath-dataservice` | `<EntityName>` | Update Entity Record | `Replace` |
| `uipath-uipath-dataservice` | `GetEntityRecordByIdCurated` | Get Entity Record by ID | `List` |
| `uipath-uipath-dataservice` | `DeleteEntityRecordCurated` | Delete Entity Record | `Create` |
| `uipath-uipath-dataservice` | `QueryEntityRecordsCurated` | Query Entity Records | `Create` |
| `uipath-uipath-dataservice` | `UploadFileToRecordField` | Upload File to Record Field | `Create` |
| `uipath-uipath-dataservice` | `DownloadFileFromRecordField` | Download File from Record Field | `List` |
| `uipath-uipath-dataservice` | `DeleteFileFromRecordField` | Delete File from Record Field | `Delete` |
| `uipath-uipath-testmanager` | `TestSet` | Create / Get / Update / Delete Test Set | `Create` / `Retrieve` / `Update` / `Delete` |
| `uipath-uipath-testmanager` | `AssignTestCasesToTestSet` | Assign Test Cases to Test Set | `Create` |
| `uipath-uipath-testmanager` | `GetAssignedTestCasesForTestSet` | Get Assigned Test Cases for Test Set | `List` |
| `uipath-uipath-testmanager` | `ExecuteTestSet` | Execute Test Set | `Create` |
| `uipath-uipath-testmanager` | `TestCase` | Create / Get / Update / Delete Test Case | `Create` / `Retrieve` / `Update` / `Delete` |
| `uipath-uipath-testmanager` | `ExecuteTestCases` | Execute Test Cases | `Create` |
| `uipath-uipath-testmanager` | `TestExecution` | Get / Delete Test Execution | `Retrieve` / `Delete` |
| `uipath-uipath-testmanager` | `GetTestCaseLogsOfTestExecution` | Get Test Case Logs of Test Execution | `List` |
| `uipath-uipath-testmanager` | `TestCaseLog` | Get Test Case Log | `Retrieve` |
| `uipath-uipath-testmanager` | `GetRobotLogs` | Get Robot Logs | `List` |
| `uipath-uipath-testmanager` | `GetAssertions` | Get Assertions | `List` |
| `uipath-uipath-testmanager` | `DownloadAssertion` | Download Assertion | `Retrieve` |
| `uipath-uipath-testmanager` | `GetTestSteps` | Get Test Steps | `List` |
| `uipath-uipath-testmanager` | `GetTestStepLogs` | Get Test Step Logs | `List` |

Operation names are the connector's, not the verb: Get Entity Record is
`List`, Delete Entity Record and Query are `Create`. `describe` rejects the
intuitive name, so do not change them.

`<EntityName>` is the tenant entity's own object: `uip is resources list`
shows one per entity, named after it, with `Custom: yes`. Its `RequestFields`
are the entity's columns, so Create and Update take their body from it.
`CreateEntityRecordCurated` and `UpdateEntityRecordV2` report an empty
`RequestFields`; do not use them.

The file rows take the field as a `fieldName` path parameter. Their `V2`
counterparts expose no field parameter, so do not use them.

`QueryEntityRecordsCurated` reports an empty `RequestFields` until you pass
the entity:

```bash
uip is resources describe <connectorKey> <object> --connection-id <id> \
    --operation Create --field entityName=<EntityName> --output json
```

`RequestFields` then lists `_sortFieldName`. Send it only in the body; as a
query parameter it is ignored. Always set `isAscending`: omitted, the query
sorts ascending, whatever its `DefaultValue` says.

No `uip maestro bpmn` command compiles a filter tree, so write the filter in
`queryExpression` as a CEQL string yourself, even when the request asks for a
FilterBuilder tree and no raw CEQL. CEQL supports `=`, `!=`, `<`, `<=`, `>`,
`>=`, `LIKE`, `NOT LIKE`, `IN`, `NOT IN`, `IS NULL`, `IS NOT NULL`, joined by
`AND` / `OR`; "contains" is `LIKE '%<text>%'`. A tree in `queryExpression`
fails with `400 Error parsing query`.
Put a requested tree in the context `metadata` at
`activityPropertyConfiguration.configuration.essentialConfiguration.savedFilterTrees.queryExpression`,
and say in your summary that the runtime filter is the CEQL string.

```xml
<uipath:input name="entityName" type="string" target="path" value="&lt;EntityName&gt;" />
<uipath:input name="queryExpression" type="string" target="query" value="&lt;field&gt; = &apos;&lt;value&gt;&apos; AND &lt;field&gt; &gt;= &lt;number&gt;" />
<uipath:input name="isAscending" type="boolean" target="query" value="false" />
<uipath:input name="body" type="json" target="body"><![CDATA[{"_sortFieldName":"<field>"}]]></uipath:input>
```

For a Data Fabric operation not listed, drop objects whose display name ends
in `(Preview)` or `(Deprecated)`, then prefer a path starting with `/v2/`.

`send-mail-v2` defaults its `saveAsDraft` query parameter to `true`, which
saves a draft instead of sending. Add a `target="query"` `saveAsDraft` input
set to `false`. Its `body` parameter is `multipart`: keep the message in the
one `target="body"` input and set the context `metadata` input to
`{"inputMetadata":{"type":"multipart","multipart":{"bodyFieldName":"body"}}}`.
Without it the runtime sends the body as JSON.

For a connector or operation not listed, describe every candidate and keep
the ones whose `Operation.Curated` names the activity asked for. Expect more
than one to survive — that is what happens on Jira — and treat the remainder
as undecidable from the CLI: pick one, then say in your summary which object
you used and which others tied. Never pick silently — `validate` and `pack`
accept any object name, so nothing local tells the user you guessed.

The response adds an enrichment block with the live field metadata. Match the
key case-insensitively — the CLI's output formatter has changed key casing
before, and pinning a spelling is what breaks on the next change. Write
the activity's `body` input (`target="body"`) and `context` (`connectorKey`,
`objectName`) from that enrichment — do not hand-author connector schemas. The
connection is referenced through a connection binding, `=bindings.<bindingId>`
(see §4).
