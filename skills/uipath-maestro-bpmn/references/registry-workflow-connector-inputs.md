# Registry workflow: connector inputs

## Body shape: hand-authored files need ONE `target="body"` input

This holds for every `Intsvc.*` type whose `inputTarget` is `body` —
`ActivityExecution`, `AsyncExecution`, `SyncAgentExecution`,
`AsyncAgentExecution`, `SyncWorkflowExecution`, `AsyncWorkflowExecution`. Each
declares `inputPattern: separateInputs`, which reads as an instruction to add
one `uipath:input` per request field. **The runtime does not consume that
shape:** several `target="body"` inputs do not merge — each claims to
be the entire body, the last one wins, and the provider receives that single
value as a bare scalar. Integration Service answers `500 Internal failure`, or
the provider reports the other fields missing (Slack:
`missing required field: channel`). Measured on live Alpha against both the
Atlassian Jira and Slack connectors.

So when you hand-author the XML, emit exactly one `target="body"` input holding
the complete request object as JSON element content, nested the way the
provider's API nests it:

```xml
<uipath:input name="body" type="json" target="body"><![CDATA[{"fields":{"project":{"key":"=vars.Var_TargetProject"},"issuetype":{"id":"=vars.Var_IssueTypeId"},"summary":"=js:'Created from Maestro at ' + vars.Var_RunLabel}}]]></uipath:input>
```

Take every body field name from the operation's `RequestFields` in
`uip is resources describe`, never from the provider's public API docs. A
curated operation frequently renames the provider's fields, so a name copied
from the vendor's REST reference is accepted by `validate` and by `pack` and
then silently omitted from the request. What comes back names neither the
field nor the cause: the provider validates the body it actually received and
complains about whatever is now missing or empty downstream of your field.
This is the same trap as taking `operation` from the catalogue's per-activity
`Name` — the described contract wins over the provider's own vocabulary, and
`describe` is the only place that contract is written down.

`=vars.<id>` and `=js:` resolve inside that CDATA, so build the body from
variables rather than literals. In an XML *attribute* a `=js:` expression must
escape the XML metacharacters — `&amp;&amp;` for `&&`, and `&lt;` for `<` — or
the file is not well-formed; `>` needs no escaping in an attribute value, and
inside CDATA nothing does.

This single-input form **is** the canonical shape, and it round-trips. Studio
Web's own design schema for this type sets `isSplitInputs: false` with one
`jsonBody` at `target="body"`
(`origin/develop:src/services/serialization/design-schema/intsvc.activityExecution.beta.design-schema.json`),
and the canvas's round-trip fixture for a Jira `curated_create_issue` node is
exactly one nested `target="body"` CDATA asserted parse→serialize identical
(`origin/develop:src/services/serialization/xml-serialization.test.ts:706`).
The serializer *preserves* separate inputs if a file already has them rather
than merging, but it never generates them. Copy that fixture's body shape, not
its context inputs: being a parse→serialize identity test, it faithfully
preserves an `operation="CreateIssue"` that the next section corrects.

The outlier is the CLI manifest: `Intsvc.ActivityExecution` still declares
`inputPattern: separateInputs` with `inputTarget: body`, and its `InputNotes`
still tell authors to add one `uipath:input` per request field. That contradicts
both the canvas and the runtime, so treat the manifest's InputNotes as stale
here rather than as the contract.

`target="bodyField"` is **not** an option here. It is the target of a merged
*arguments* payload on specific types — `JobArguments` on the `Orchestrator.*`
job and process starts, `HitlTaskArguments` on `Actions.HITL`, `args` on
`BPMN.ScriptTask` — and no `Intsvc.*` type uses it. Read `inputTarget` from the
manifest per type; it is not a property of `inputPattern`. Five of the fourteen
`mergedBody` types use `body` (`Orchestrator.CreateQueueItem`,
`Orchestrator.CreateAndWaitForQueueItem`, `A2A.AgentExecution`,
`Maestro.CaseRulesEvaluator`, `Maestro.CaseManagerGuardrails`), so inferring
`bodyField` from the pattern gets the target wrong on a third of them.

**Local validation will not catch a wrong target or a wrong input name here.**
`validateInputs` short-circuits for this type: `usesCanvasOwnedDynamicPayload`
(`project-validator.ts:1602`) is true for anything `isDynamic` or for an
`Intsvc.*` type requiring discovery, and it returns after
`validateDynamicDirectInputs`, which checks only that each input has a `name`
and that `type="json"` payloads parse. No allow-list, no `target` check, no
count check — so several `target="body"` inputs, a `bodyField` input, and an
unrecognized input name all pass `validate` and `pack`. The failure is a
runtime one. This is why a clean `validate` is not evidence the body shape is
right.

Nest a dotted `RequestFields` name yourself: `fields.project.key` becomes
`{"fields":{"project":{"key": …}}}`. A literal `"fields.project.key"` key is
sent as-is, and the provider never sees `fields.project`.

Take `operation` from the `Operation.Name` reported by
`uip is resources describe` (for example `Create`); `path` and `objectName`
come from the same described object. The template's `DiscoveryNotes` say "set
operation from Name", which reads as the catalogue's per-activity `Name`
(`CreateIssue`) — a value that can never resolve: `METHOD_TO_OPERATION`
(`integrationservice-sdk/src/dap/validation/rules.ts:74`) defines a closed
six-name lexicon — List, Retrieve, Create, Update, Delete, Replace — and the
reverse map accepts only those plus raw HTTP verbs, which is also exactly what
`uip is resources run` exposes as subcommands. `--operation` takes the same
value, so pass `--operation Create`.

## Set every required `RequestFields` entry

Put every `RequestFields` entry marked `Required: true` in the body under its
described name. List them from the describe `--output json` result with
`jq '.Data | with_entries(.key |= ascii_downcase) | .requestfields
| map(with_entries(.key |= ascii_downcase) | select(.required) | .name)'`;
never filter `RequestFields` by the names you expect. A missing Slack
`messageToSend` faults with `invalid_blocks`. Describe for Jira
`curated_create_issue` omits `fields.summary`; set it there anyway.

## Required `Parameters` are separate from the body — emit every one

`uip is resources describe` reports `Parameters` alongside `RequestFields`.
Each parameter is its own input, targeted by its `Type` (`query`, `path`, or
`file`) — never folded into the body. Emit an input for every parameter marked
`Required: true`, using its `DefaultValue` when the request has no better
value:

```xml
<uipath:input target="query" name="send_as" type="string" value="bot" />
```

Omitting one is accepted by local validation and by `pack`, then fails only at
runtime with `400` and `Value for required parameter '<name>' not found`. A
`Parameters` list can be empty (Jira's `curated_create_issue`) or carry a
required entry (Slack's `send_message_to_channel_v2` requires `send_as`), so
check it per activity rather than assuming.

## A `Reference` entry takes a looked-up value, never the display name

A `Parameters` or `RequestFields` entry that carries `Reference` takes the
`LookupValue` field of the row whose `LookupNames` match the user's value. Slack
`ConversationsInfo_GET` parameter `conversationsInfoId` carries
`{"ObjectName": "curated_channels", "LookupNames": ["name", "id"], "LookupValue": "id"}`:
the value is the channel id (`C0123ABCDEF`), not `<channel-name>`. A name
passes `validate` and faults at runtime (`channel_not_found`).

List `Reference.ObjectName` itself, not a sibling object such as
`conversations`, on the connection the node binds:

```bash
uip is resources run list uipath-salesforce-slack "curated_channels?types=public_channel,private_channel" --connection-id <id> --output json
```

- A nonzero exit or a `Result` other than `Success` is a lookup failure, not an
  empty result.
- Match keys inside `Data` case-insensitively (`items`, `Pagination`,
  `HasMore`, `NextPageToken`).
- While `HasMore` is true, re-run with `--query "nextPage=<NextPageToken>"`.
  `pageToken=`, `page=`, and `name=` are ignored and return page 1 again. Stop
  at the first match, or when a page adds no rows you have not already seen.

No match on that connection: repeat on every other `Enabled` connection from
`uip is connections list <connector-key> --all-folders --output json` and bind
the one that holds it. The `IsDefault` connection can reach a workspace
without the value. No connection holds it, or a lookup fails: stop and report
that field. Never write the display name in its place.
