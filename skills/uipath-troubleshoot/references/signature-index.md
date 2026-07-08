# Signature Index

Routing entry point. **Grep this file — never read it whole.** Grep with each extracted signal: leaf exception class, full FQN, error code, verbatim message fragment, resource key. Signature values are verbatim — use fixed-string search (`grep -F "<signal>" references/signature-index.md`; a shorter fragment beats a guessed-case variant). Check every hit's `note` column and the Disambiguations list before choosing; honor exclusions.

The signature table is generated from playbook frontmatter — edit playbooks, then run `python3 scripts/build-signature-index.py --write-index`. The sections after the generated block are hand-maintained.

## Signature → playbook

<!-- BEGIN GENERATED SIGNATURES -->
| signature | kind | playbook | confidence | note |
|---|---|---|---|---|
| #1100 | error-code | products/maestro/playbooks/folder-not-accessible.md | high |  |
| #1230 | error-code | products/maestro/playbooks/foreground-unattended-robot.md | high |  |
| #1671 | error-code | products/maestro/playbooks/unattended-robot-permissions.md | high |  |
| #2818 | error-code | products/maestro/playbooks/no-suitable-runtime-machine.md | high |  |
| 'Create if not exists' is not supported when using a URL for the file path | message | activity-packages/word-activities/playbooks/word-open-sharepoint-url-com-command-failed.md | medium | validation warning — CreateNewFile defaulting True against a URL path |
| 'File name' can not be null, empty or whitespace. | message | activity-packages/ui-automation/playbooks/activity-configuration-error.md | high |  |
| (HTTP Status Code: TooManyRequests) Batching request failed with an unknown reason. | message | activity-packages/o365-activities/playbooks/request-throttled.md | high | throttled sub-request inside a batch — other statuses in the same batching sentence route to transient-service-error.md |
| 0 | error-code | activity-packages/system-activities/playbooks/get-asset-permission-denied.md | high | shared with the 401 not-authenticated failure — discriminator is HTTP 403 Forbidden / 'not authorized' wording |
| 0 | error-code | activity-packages/system-activities/playbooks/get-asset-robot-not-authenticated.md | medium | shared with the 403 permission-denied failure — discriminator is HTTP 401 Unauthorized / 'not authenticated' wording |
| 0x0000052E | error-code | products/orchestrator/playbooks/job-faulted-logon-failure.md | medium | Windows logon failure — bad username or password |
| 0x00000532 | error-code | products/orchestrator/playbooks/job-faulted-logon-failure.md | medium | Windows password expired |
| 0x00000775 | error-code | products/orchestrator/playbooks/job-faulted-logon-failure.md | medium | Windows account locked out |
| 0x40010004 | error-code | products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md | medium | DBG_TERMINATE_PROCESS — executor killed via TerminateProcess, not a workflow throw |
| 0x80004002 | error-code | activity-packages/excel-activities/playbooks/excel-application-scope-failures.md | medium |  |
| 0x80010001 | error-code | activity-packages/excel-activities/playbooks/invoke-vba-com-interop-failure.md | medium | RPC_E_CALL_REJECTED on Invoke VBA — Excel COM rejecting the incoming call (busy/blocked EXCEL.EXE) |
| 0x80010001 | error-code | activity-packages/word-activities/playbooks/replace-text-com-busy.md | medium | RPC_E_CALL_REJECTED at Replace Text; package-level E3 tree → word-com-interop-failures.md |
| 0x80010001 | error-code | activity-packages/word-activities/playbooks/word-com-interop-failures.md | medium | RPC_E_CALL_REJECTED — Word busy/blocked (E3); at Replace Text → replace-text-com-busy.md |
| 0x80010100 | error-code | activity-packages/excel-activities/playbooks/invoke-vba-com-interop-failure.md | medium | RPC_E_SYS_CALL_FAILED on Invoke VBA / modern Excel COM dispatch — EXCEL.EXE blocked, hung, or stalled on a hidden modal dialog |
| 0x80010100 | error-code | activity-packages/word-activities/playbooks/word-com-interop-failures.md | medium | RPC_E_SYS_CALL_FAILED — Word busy/blocked (E3) |
| 0x80010108 | error-code | activity-packages/excel-activities/playbooks/excel-application-card-failures.md | medium | RPC_E_DISCONNECTED — multiple scopes raced on EXCEL.EXE or a prior scope tore it down without an Excel Process Scope (branch 3); on the activity right after a macro → execute-macro-failures.md |
| 0x80010108 | error-code | activity-packages/excel-activities/playbooks/execute-macro-failures.md | medium | RPC_E_DISCONNECTED on the NEXT activity after the macro — VBA called Workbooks.Close / Application.Quit and tore down Excel (branch 3); scope-vs-scope race without a macro → excel-application-card-failures.md |
| 0x8001010A | error-code | activity-packages/excel-activities/playbooks/invoke-vba-com-interop-failure.md | medium | RPC_E_SERVERCALL_RETRYLATER on Invoke VBA — EXCEL.EXE busy servicing another call |
| 0x8001010A | error-code | activity-packages/word-activities/playbooks/replace-text-com-busy.md | medium | RPC_E_SERVERCALL_RETRYLATER at Replace Text / Read Text — orphaned WINWORD.EXE or modal dialog; package-level E3 tree → word-com-interop-failures.md |
| 0x8001010A | error-code | activity-packages/word-activities/playbooks/word-com-interop-failures.md | medium | RPC_E_SERVERCALL_RETRYLATER — Word busy/blocked (E3), any Word activity; at Replace Text / Read Text → replace-text-com-busy.md |
| 0x8001010E | error-code | activity-packages/word-activities/playbooks/word-com-interop-failures.md | medium | RPC_E_WRONG_THREAD as aftermath of a WINWORD.EXE crash mid-operation (E4); live wrong-thread cast at Save Document as PDF → word-export-pdf-com-wrong-thread.md |
| 0x8001010E | error-code | activity-packages/word-activities/playbooks/word-export-pdf-com-wrong-thread.md | medium | RPC_E_WRONG_THREAD live cast at Save Document as PDF / a child of Word Application Scope — external/attached Word or off-STA thread; crash-aftermath variant → word-com-interop-failures.md |
| 0x80020009 | error-code | activity-packages/excel-activities/playbooks/execute-macro-failures.md | medium |  |
| 0x8002801D | error-code | activity-packages/excel-activities/playbooks/excel-application-scope-failures.md | medium | TYPE_E_LIBNOTREGISTERED inner COMException opening a workbook on Excel Application Scope — broken Excel COM/type-library registration despite Excel installed (branch 1) |
| 0x8002801D | error-code | activity-packages/word-activities/playbooks/word-com-interop-failures.md | medium | TYPE_E_LIBNOTREGISTERED on Word COM startup, any Word activity (E1); 'make sure Word application is installed' wording → word-scope-com-not-installed.md |
| 0x80040154 | error-code | activity-packages/excel-activities/playbooks/excel-application-scope-failures.md | medium | REGDB_E_CLASSNOTREG despite a confirmed Excel install → registration corruption; Excel absent → excel-application-card-failures.md |
| 0x80040154 | error-code | activity-packages/word-activities/playbooks/word-com-interop-failures.md | medium | REGDB_E_CLASSNOTREG on Word COM startup (E1) — sibling of 0x8002801D; scope-level not-installed message → word-scope-com-not-installed.md |
| 0x80040154 | error-code | activity-packages/word-activities/playbooks/word-scope-com-not-installed.md | high | REGDB_E_CLASSNOTREG at Word Application Scope startup — Word missing / bitness / broken registration; package-level decision tree → word-com-interop-failures.md |
| 0x800402bd | error-code | activity-packages/ui-automation/playbooks/click-coordinate-off-screen.md | high |  |
| 0x800706BA | error-code | activity-packages/excel-activities/playbooks/excel-application-card-failures.md | medium |  |
| 0x800706BE | error-code | activity-packages/excel-activities/playbooks/invoke-vba-com-interop-failure.md | medium |  |
| 0x80080005 | error-code | activity-packages/excel-activities/playbooks/excel-application-card-failures.md | medium |  |
| 0x800A03EC | error-code | activity-packages/excel-activities/playbooks/append-range-failures.md | medium | on Append Range — sheet name / file extension mismatch (branch 2) or source-vs-target column schema mismatch (branch 5) |
| 0x800A03EC | error-code | activity-packages/excel-activities/playbooks/delete-range-failures.md | medium | on Delete Range — ShiftCells/ShiftOption direction conflicts with merged cells or Excel Tables (branch 3) |
| 0x800A03EC | error-code | activity-packages/excel-activities/playbooks/execute-macro-failures.md | medium | generic Excel COM error raised during macro execution |
| 0x800A03EC | error-code | activity-packages/excel-activities/playbooks/lookup-range-file-locked.md | medium | COM error resolving to a busy/locked workbook on Lookup Range or its scope; malformed Range field on Lookup Range → lookup-range-invalid-range.md |
| 0x800A03EC | error-code | activity-packages/excel-activities/playbooks/lookup-range-invalid-range.md | medium | on Lookup Range — malformed Range field (empty-string literal instead of blank, or invalid A1 reference) |
| 0x800A03EC | error-code | activity-packages/excel-activities/playbooks/read-range-file-locked.md | medium | COMException wrapper of the same file lock under Excel COM — Excel's own message about the file being locked for editing |
| 0x800A03EC | error-code | activity-packages/excel-activities/playbooks/write-cell-failures.md | medium | on Write Cell — COMException near Worksheet.Protect, protected target (branch 5) |
| 0x800AC472 | error-code | activity-packages/excel-activities/playbooks/execute-macro-failures.md | medium |  |
| 0xE0434352 | error-code | activity-packages/database-activities/playbooks/execute-query-failures.md | medium |  |
| 1 or more scope requested are not robot scopes. | message | products/integration-service/playbooks/connector-remote-exception.md | medium |  |
| 1002 | error-code | activity-packages/system-activities/playbooks/get-asset-not-found.md | high |  |
| 102001 | error-code | products/maestro/playbooks/integration-service-404.md | medium | IntSvcResourceNotFound |
| 102002 | error-code | products/integration-service/playbooks/connection-auth-expired.md | high | IntSvcOperationFailed with auth-related details on a previously working connection |
| 102002 | error-code | products/integration-service/playbooks/connection-invalid.md | high | IntSvcOperationFailed at connection resolution — process fails immediately when using the connection |
| 102002 | error-code | products/integration-service/playbooks/operation-failed.md | medium | IntSvcOperationFailed — connection is active but the specific operation fails; auth-shaped details → connection-auth-expired.md |
| 102003 | error-code | products/integration-service/playbooks/operation-failed.md | medium | IntSvcBadRequest |
| 102003 | error-code | products/maestro/playbooks/integration-service-400.md | medium | IntSvcBadRequest |
| 102004 | error-code | products/integration-service/playbooks/operation-failed.md | medium | IntSvcMethodNotSupported |
| 102008 | error-code | products/integration-service/playbooks/connection-invalid.md | high | GetConnectionInvalidInputError |
| 102010 | error-code | products/integration-service/playbooks/operation-failed.md | medium | IntSvcArgumentsError |
| 1100 | error-code | activity-packages/system-activities/playbooks/get-asset-folder-scope-mismatch.md | high |  |
| 1101 | error-code | activity-packages/system-activities/playbooks/get-asset-folder-scope-mismatch.md | high |  |
| 131092 | error-code | products/orchestrator/playbooks/job-faulted-logon-failure.md | medium | appears as 'Last error: 131092' alongside the logon-failure message |
| 170002 | error-code | products/maestro/playbooks/personal-automation-quota.md | high | quota wording propagated through a Maestro service task — child job response carries the quota message |
| 170002 | error-code | products/maestro/playbooks/service-task-child-job-faulted.md | high | Failure in the Orchestrator Job — incident cascades from child job fault |
| 170007 | error-code | products/maestro/playbooks/process-not-found-404.md | high | OrchestratorRpaJobFailedToStart — failure at job-start time |
| 2303 | error-code | activity-packages/system-activities/playbooks/get-asset-external-vault-failure.md | medium |  |
| 2304 | error-code | activity-packages/system-activities/playbooks/get-asset-external-vault-failure.md | medium |  |
| 400 | http-status | activity-packages/gsuite-activities/playbooks/sheets-cell-limit-exceeded.md | high | Google Sheets BadRequest whose message names the 10000000-cell limit; 'Unable to parse range' 400 → sheets-invalid-range.md; Maestro Error_400 → generic-error-400.md (products/maestro) |
| 400 | http-status | activity-packages/gsuite-activities/playbooks/sheets-invalid-range.md | medium | Google Sheets BadRequest 'Unable to parse range'; cell-limit 400 → sheets-cell-limit-exceeded.md; Maestro Error_400 → generic-error-400.md (products/maestro) |
| 400 | http-status | products/maestro/playbooks/argument-mismatch-400.md | medium | with the argument-mismatch wording and no single named field — named-field 400 → missing-required-parameter.md; schema-conformance 400 → input-schema-mismatch.md; empty errorDetails → generic-error-400.md |
| 400 | http-status | products/maestro/playbooks/generic-error-400.md | low | generic 400 with empty errorDetails only — named 400 errors route to their specific playbooks |
| 400 | http-status | products/maestro/playbooks/input-schema-mismatch.md | high | at workflow/agent start with schema-conformance wording (Input does not conform to schema / Agent.InputArgumentsSchema) — other named 400s route to their specific playbooks |
| 400 | http-status | products/maestro/playbooks/insufficient-funds.md | high | from an agent or GenAI activity with the insufficient-funds/credits wording — other named 400s route to their specific playbooks |
| 400 | http-status | products/maestro/playbooks/missing-required-parameter.md | high | at activity execution naming a single missing required parameter — broad schema wording → input-schema-mismatch.md; empty errorDetails → generic-error-400.md |
| 400 | http-status | products/maestro/playbooks/no-message-events.md | high | at a Message Start/Receive Event with the no-events wording — other named 400s route to their specific playbooks |
| 400001 | error-code | products/maestro/playbooks/gateway-no-outgoing-flow.md | high | NoOutgoingFlow |
| 400007 | error-code | products/maestro/playbooks/marker-input-null.md | high | BpmnMarkerInputNullError |
| 400008 | error-code | products/maestro/playbooks/marker-invalid-cast.md | high | BpmnMarkerInputEvaluationFailure |
| 400009 | error-code | products/maestro/playbooks/loop-detected.md | high | ElementExecutionLoopDetected |
| 400300 | error-code | products/maestro/playbooks/expression-evaluation-errors.md | high | InputVariablesEvaluationError |
| 400301 | error-code | products/maestro/playbooks/expression-evaluation-errors.md | high | ExpressionEvaluationError |
| 400302 | error-code | products/maestro/playbooks/expression-evaluation-errors.md | high | FlowExpressionEvaluationError — gateway flows |
| 4006 | error-code | products/maestro/playbooks/deployment-email-received.md | high |  |
| 401 | http-status | activity-packages/system-activities/playbooks/get-asset-robot-not-authenticated.md | medium | on Get Asset/Credential — robot session/token not authenticated; 401 on an IS connection → connection-auth-expired.md |
| 401 | http-status | products/agents/playbooks/is-invalid-credentials.md | high | first IS call in an agent run fails — connection folder/scope mismatch or rotated credentials; IS-connection OAuth expiry outside agents → connection-auth-expired.md |
| 401 | http-status | products/integration-service/playbooks/connection-auth-expired.md | high | OAuth token expired / refresh failed on a previously working IS connection — for agent toolCall 401s see is-invalid-credentials.md |
| 401 | http-status | products/llm-gateway/playbooks/byo-connection-dead.md | high | vendor-surfaced auth error on a BYO LLM call — the IS connection behind the BYO config is dead; for agent IS toolCall 401s see is-invalid-credentials.md |
| 403 | http-status | activity-packages/o365-activities/playbooks/insufficient-graph-scope.md | high | Microsoft Graph 403 on an O365 activity — missing Graph permission scope or per-item access denial; IS connection lockout / BYO LLM / Orchestrator-asset 403s → those domains' playbooks |
| 403 | http-status | activity-packages/system-activities/playbooks/get-asset-permission-denied.md | high | on Get Asset/Credential — Orchestrator RBAC missing Assets view; 403 on an IS connection or BYO LLM call → those domains' playbooks |
| 403 | http-status | products/agents/playbooks/is-connection-disabled.md | medium | IS connection lockout on an agent toolCall span — OAuth2 authorization-code connections only; vendor-direct LLM-call 403s → byo-connection-dead.md |
| 403 | http-status | products/llm-gateway/playbooks/byo-connection-dead.md | high | vendor-surfaced auth error on a BYO LLM call — errors reference the vendor directly, not the UiPath platform; for IS connection lockout see is-connection-disabled.md |
| 404 | http-status | activity-packages/gsuite-activities/playbooks/drive-file-not-found.md | high | Google API NotFound on a GSuite activity (Drive/Sheets/Docs item or Gmail message by ID); O365 Mail folder 404 → mail-folder-not-found.md (o365), Maestro/agents 404s → those domains' playbooks |
| 404 | http-status | activity-packages/o365-activities/playbooks/mail-folder-not-found.md | high | Microsoft Graph 404 while a Mail activity resolves a MailFolder argument; GSuite 404 → drive-file-not-found.md (gsuite), Maestro/agents 404s → those domains' playbooks |
| 404 | http-status | products/agents/playbooks/is-invalid-element-instance.md | high | IS element instance missing — can fire mid-run after earlier successful IS calls |
| 404 | http-status | products/maestro/playbooks/attachment-not-found.md | high | on file/attachment access after retention elapsed — not an IS-call or job-start 404 |
| 404 | http-status | products/maestro/playbooks/integration-service-404.md | medium | on an Integration Service call — connector/connection/action missing; job attachment → attachment-not-found.md; job start → process-not-found-404.md |
| 404 | http-status | products/maestro/playbooks/process-not-found-404.md | high | from Orchestrator at job start — stale ReleaseKey/binding; IS-call 404 → integration-service-404.md; attachment → attachment-not-found.md |
| 429 | http-status | activity-packages/o365-activities/playbooks/request-throttled.md | high | Microsoft Graph rate limit on an O365 activity; Autopilot for Maestro 429 → autopilot-429.md (products/maestro) |
| 429 | http-status | products/maestro/playbooks/autopilot-429.md | high | Autopilot for Maestro apply-failure — backend/LLM Gateway rate limiting; Microsoft Graph 429 on an O365 activity → request-throttled.md (o365-activities) |
| 502 | http-status | products/maestro/playbooks/file-field-required.md | high | raised by an Integration Service activity expecting a file input — DAP-RT-1003 present |
| 502 | http-status | products/maestro/playbooks/index-out-of-bounds.md | low | with System.IndexOutOfRangeException stack trace — engine/platform bug |
| 502 | http-status | products/maestro/playbooks/job-operation-timeout.md | medium | child job often Successful in Orchestrator while Maestro reports timeout — gateway/proxy limit |
| 502 | http-status | products/maestro/playbooks/personal-automation-quota.md | high | at job start with the Personal Automation quota message verbatim in errorMessage |
| 503 | http-status | activity-packages/o365-activities/playbooks/transient-service-error.md | medium | Microsoft Graph service unavailable surfaced by an O365 activity (500/504/timeout forms route here too); Google-side 5xx → transient-and-timeout-errors.md (gsuite) |
| 80040154 | error-code | activity-packages/excel-activities/playbooks/lookup-range-excel-not-installed.md | high | REGDB_E_CLASSNOTREG at Lookup Range / Excel scope init — no registered Excel installation; Excel confirmed installed but COM registration broken → excel-application-scope-failures.md |
| 80080005 | error-code | activity-packages/excel-activities/playbooks/invoke-vba-com-interop-failure.md | medium | COM class factory retrieval failure ('failed due to the following error: 80080005') during Invoke VBA / Excel Process Scope; CO_E_SERVER_EXEC_FAILURE 0x80080005 on a Use Excel File card → excel-application-card-failures.md |
| A file with the specified ID does not exist. | message | activity-packages/o365-activities/playbooks/drive-item-not-found.md | high |  |
| A foreground process is already running. Only one foreground process can run at a time. | message | products/orchestrator/playbooks/foreground-already-running.md | medium |  |
| A sheet with the same name already exists. | message | activity-packages/gsuite-activities/playbooks/add-sheet-name-conflict.md | high |  |
| A task was canceled. | message | activity-packages/gsuite-activities/playbooks/transient-and-timeout-errors.md | medium | GSuite per-request RequestTimeout (HttpClient cancellation) — not a System.TimeoutException, which is auth-phase → connection-and-auth-failures.md |
| AADSTS | error-code-prefix | activity-packages/o365-activities/playbooks/authentication-token-invalid.md | medium | Entra ID failure at token acquisition — 'A configuration error AADSTS<code> occurred in the activity.' |
| Access restricted to the item's owner. | message | activity-packages/o365-activities/playbooks/insufficient-graph-scope.md | high |  |
| Access token has expired or is not yet valid. | message | activity-packages/o365-activities/playbooks/authentication-token-invalid.md | medium |  |
| Activity can not be in another Screen Scope container | message | activity-packages/cv-activities/playbooks/cv-scope-setup-failures.md | medium |  |
| Activity execution exceeded the set timeout. | message | activity-packages/ui-automation/playbooks/timeout-issue.md | low |  |
| activity is not valid in this context | message | activity-packages/word-activities/playbooks/read-text-missing-container.md | high | runtime invalid-context fault on the containerless modern Read Text |
| Activity is only valid inside an Office 365 Scope | message | activity-packages/o365-activities/playbooks/application-scope-misconfigured.md | medium |  |
| Activity is valid only inside a CV Screen Scope | message | activity-packages/cv-activities/playbooks/cv-scope-setup-failures.md | medium |  |
| Activity is valid only inside WordApplicationScope | message | activity-packages/word-activities/playbooks/append-text-missing-container.md | high | App-Integration Append Text outside a Word Application Scope / Use Word File |
| Activity timeout exceeded | message | activity-packages/classic-activities/playbooks/image-target-not-found.md | medium | same discriminator — faulted activity is image-based |
| Activity timeout exceeded | message | activity-packages/classic-activities/playbooks/ui-activity-timeout.md | medium | same discriminator — faulted activity is an element/state wait, not an image activity |
| ActivityTimeoutException | exception | activity-packages/classic-activities/playbooks/image-target-not-found.md | medium | image activities (Wait Image Vanish) — image never matched or still present; for element/state waits see ui-activity-timeout.md |
| ActivityTimeoutException | exception | activity-packages/classic-activities/playbooks/ui-activity-timeout.md | medium | element/state waits (Wait UI Element Appear, any classic UI activity) — for image-based waits see image-target-not-found.md |
| Agent configuration invalid | message | products/agents/playbooks/input-schema-validation-failure.md | high | Variant A error prefix — faults before any LLM call |
| Agent.InputArgumentsSchema | message | products/maestro/playbooks/input-schema-mismatch.md | high |  |
| agent.json failed schema validation | message | products/agents/playbooks/input-schema-validation-failure.md | high | Variant A — agent configuration schema |
| AGENT_RUNTIME.TERMINATION_GUARDRAIL_VIOLATION | error-code | products/agents/playbooks/guardrail-violation.md | high |  |
| AGENT_RUNTIME.UNEXPECTED_ERROR | error-code | products/agents/playbooks/context-grounding-index-not-found.md | high | generic runtime code — routable here only with the ContextGroundingIndex not found detail |
| Allowed.AgentService | error-code | activity-packages/ui-automation/playbooks/healing-agent-no-license.md | high | == 0 with LicensedFeatures [] in uip or licenses info — no HA entitlement on the tenant; > 0 while triaging expected HA surfaces → healing-agent-orch-issues.md |
| Allowed.AgentService | error-code | activity-packages/ui-automation/playbooks/healing-agent-orch-issues.md | high | > 0 while triaging whether an Orchestrator HA status/log/notification is expected; == 0 when the customer wants HA working → healing-agent-no-license.md |
| An error occurred in the activity. | message | activity-packages/gsuite-activities/playbooks/transient-and-timeout-errors.md | medium | GSuite generic fallback for unmapped Google API errors — read the inner status/reason from the trace before concluding |
| An organization unit is required | message | activity-packages/system-activities/playbooks/get-asset-folder-scope-mismatch.md | high |  |
| API key not valid | message | products/llm-gateway/playbooks/byo-connection-dead.md | high |  |
| Application-defined or object-defined error | message | activity-packages/excel-activities/playbooks/write-cell-failures.md | medium | Excel COM on Write Cell — bad cell reference (branch 6); formula-prefix data on Write Range → write-range-failures.md |
| ApplicationNotFoundException | exception | activity-packages/ui-automation/playbooks/application-not-found.md | high |  |
| ApplicationOpenException | exception | activity-packages/ui-automation/playbooks/application-open-failed.md | high |  |
| Archive file cannot be size zero | message | activity-packages/word-activities/playbooks/append-text-zero-byte-file.md | medium |  |
| Argument values did not match definitions | message | products/maestro/playbooks/argument-mismatch-400.md | medium | generic argument-mismatch 400 — no single named field, no broad schema wording |
| ArgumentException | exception | activity-packages/word-activities/playbooks/replace-text-length-limit.md | high | Search/Replace value over 256 characters on a classic UiPath.Word.Activities version; silent truncation variant shows no exception |
| ArgumentNullException | exception | activity-packages/o365-activities/playbooks/application-scope-misconfigured.md | medium | generic .NET exception — this claim is the runtime surface of a missing credential field (e.g. ApplicationId) on the Microsoft 365 Application Scope; an ArgumentNullException wrapping a 'Folder named ... could not be found' sentence → mail-folder-not-found.md |
| ArgumentNullException | exception | activity-packages/o365-activities/playbooks/mail-folder-not-found.md | high | generic .NET exception — this claim is the unwrapped form carrying 'Folder named ... could not be found' as the parameter text; a bare ArgumentNullException naming a credential field → application-scope-misconfigured.md |
| ArgumentOutOfRangeException | exception | activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md | medium | generic .NET exception — this claim is a GSuite Drive by-ID/URL activity given a URL with no extractable ID segment ('Could not extract an object Id from the Url') |
| Assignments are not allowed in expressions | message | products/maestro/playbooks/variable-expression-errors.md | medium |  |
| Attachment not found | message | products/maestro/playbooks/attachment-not-found.md | high | file access fails after job retention deleted the owning job — process initially worked |
| Attachment not found | message | products/maestro/playbooks/file-handling.md | medium | general file-input mishandling — variable vs argument, connector File-type bugs; retention-deleted job → attachment-not-found.md |
| Authentication attempt took longer than | message | activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md | medium | GSuite connection/OAuth token acquisition (System.TimeoutException); the same wording on Microsoft 365 is the connection-creation sign-in wizard → authentication-token-invalid.md (o365) |
| Authentication attempt took longer than | message | activity-packages/o365-activities/playbooks/authentication-token-invalid.md | medium | Microsoft 365 connection-creation interactive sign-in wizard; same wording in GSuite is the auth-phase TimeoutException → connection-and-auth-failures.md (gsuite) |
| Authentication error: the access token is expired or invalid. | message | activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md | medium |  |
| Automation Cloud cannot be reached | message | activity-packages/o365-activities/playbooks/authentication-token-invalid.md | medium | in an authentication context — connection could not be resolved; the same message on a mid-run Graph call is transient-service-error |
| Automation Cloud cannot be reached | message | activity-packages/o365-activities/playbooks/transient-service-error.md | medium | network fluctuation on the Runtime machine mid-run; the same message at authentication time is claimed by authentication-token-invalid |
| BadImageFormatException | exception | activity-packages/python-activities/playbooks/python-scope-architecture-version-mismatch.md | medium | generic .NET — here: Target bitness does not match the installed interpreter |
| Batching request failed with an unknown reason. | message | activity-packages/o365-activities/playbooks/transient-service-error.md | medium | any embedded status — but the '(HTTP Status Code: TooManyRequests)' form routes to request-throttled.md; check the status, not the sentence alone |
| BC36754 | error-code | activity-packages/python-activities/playbooks/invoke-method-failures.md | medium | design-time VB compile error on InputParameters — argument is not an Object array (M3) |
| because it is being used by another process | message | activity-packages/database-activities/playbooks/connect-to-database-failures.md | medium | Connect to Database against a file-based (ACE OLE DB / ODBC) source — workbook held by another process (branch 3) |
| because it is being used by another process | message | activity-packages/excel-activities/playbooks/lookup-range-file-locked.md | medium | on Lookup Range or its Excel Application Scope / Use Excel File — workbook file handle held; Read Range family full lock-owner chain → read-range-file-locked.md |
| because it is being used by another process | message | activity-packages/excel-activities/playbooks/read-range-file-locked.md | medium | on Read Range family / Excel Application Scope / Use Excel File — full lock-owner investigation (user edit, orphan EXCEL.EXE, share lock, concurrent jobs, AV/sync client) |
| because it is being used by another process | message | activity-packages/excel-activities/playbooks/write-cell-failures.md | medium | on Write Cell — external locker (→ read-range-file-locked.md) or Classic Workbook Write Cell racing an open Excel scope on the same path (branch 1) |
| Both FileName and Arguments arguments are null | message | activity-packages/classic-activities/playbooks/application-launch-failed.md | medium |  |
| BrowserFailedToNavigateToUrlException | exception | activity-packages/ui-automation/playbooks/browser-navigation-failed.md | medium |  |
| BrowserInvalidURLException | exception | activity-packages/ui-automation/playbooks/browser-navigation-failed.md | medium |  |
| BrowserOperationException | exception | activity-packages/classic-activities/playbooks/browser-open-or-attach-failed.md | medium |  |
| btoa is not defined | message | products/maestro/playbooks/js-runtime-discrepancy.md | high |  |
| Call was rejected by callee | message | activity-packages/word-activities/playbooks/replace-text-com-busy.md | medium | RPC_E_CALL_REJECTED wording — same busy/blocked surface |
| CanConsume=False | message | activity-packages/ui-automation/playbooks/healing-agent-no-license.md | high | App Insights / backend logs, with licenseCode HealingAgent or HealingAgent.Test |
| cannot be opened because there are problems with the contents | message | activity-packages/word-activities/playbooks/word-scope-file-corrupted.md | medium |  |
| Cannot be used outside of a MicrosoftOffice365 Application Scope | message | activity-packages/o365-activities/playbooks/application-scope-misconfigured.md | medium |  |
| Cannot convert the item into PDF format. | message | activity-packages/o365-activities/playbooks/download-file-conversion-or-destination.md | high |  |
| Cannot convert type 'String' to 'IResource' | message | activity-packages/mail-activities/playbooks/move-outlook-mail-failures.md | medium | modern Move Email fed a classic string input after a dependency update (branch 3) |
| Cannot create an instance of Microsoft.Office.Interop.Excel.ApplicationClass | message | activity-packages/excel-activities/playbooks/lookup-range-excel-not-installed.md | high |  |
| Cannot create an instance of Microsoft.Office.Interop.Word.ApplicationClass | message | activity-packages/word-activities/playbooks/word-scope-com-not-installed.md | high |  |
| Cannot create folder path: | message | activity-packages/o365-activities/playbooks/create-folder-invalid-path.md | high |  |
| Cannot create unknown type '{clr-namespace:UiPath.Word.Activities;assembly=UiPath.Word.Activities}WordApplicationScope' | message | activity-packages/word-activities/playbooks/word-scope-cannot-create-unknown-type.md | high | runtime/load-time missing UiPath.Word.Activities dependency; design-time Studio crash on drop → replace-text-version-mismatch.md |
| Cannot deserialize the current JSON array | message | activity-packages/web-activities/playbooks/deserialize-type-mismatch.md | medium |  |
| Cannot deserialize the current JSON object | message | activity-packages/web-activities/playbooks/deserialize-type-mismatch.md | medium |  |
| Cannot find item configured with connection | message | activity-packages/gsuite-activities/playbooks/drive-file-not-found.md | high | GSuite connection-browser item (Drive/Sheets) that no longer resolves; the same wrapper on O365 → drive-item-not-found.md or mail-folder-not-found.md (o365) |
| Cannot find item configured with connection | message | activity-packages/o365-activities/playbooks/drive-item-not-found.md | high | O365 Drive item / path form; the same wrapper text on a Mail activity is a mail folder → mail-folder-not-found.md, and on GSuite → drive-file-not-found.md (gsuite) |
| Cannot find item configured with connection | message | activity-packages/o365-activities/playbooks/mail-folder-not-found.md | high | wrapper around 'Folder named ... could not be found' on a Mail activity; the same wrapper on a Files activity is a Drive item → drive-item-not-found.md, on GSuite → drive-file-not-found.md (gsuite) |
| Cannot find the UI element corresponding to this selector | message | activity-packages/classic-activities/playbooks/ui-element-not-found.md | medium |  |
| Cannot get the screen rectangle of this UI node. | message | activity-packages/ui-automation/playbooks/element-found-not-actionable.md | medium |  |
| cannot have leading or trailing whitespace. | message | activity-packages/o365-activities/playbooks/create-folder-invalid-path.md | high |  |
| Cannot locate file. Please ensure that you have proper permissions to access it. | message | activity-packages/o365-activities/playbooks/download-file-conversion-or-destination.md | high |  |
| Cannot run the macro | message | activity-packages/excel-activities/playbooks/execute-macro-failures.md | medium | via Execute Macro / Run Spreadsheet Macro — macro name absent from the workbook (branch 1) or macros disabled by Trust Center policy (branch 5); via Invoke VBA → invoke-vba-code-file-path.md / invoke-vba-entry-method-name.md |
| Cannot run the macro | message | activity-packages/excel-activities/playbooks/invoke-vba-code-file-path.md | medium | Invoke VBA faulting while loading/compiling the external code file — file missing, wrong encoding, or code not wrapped in Sub/Function; Execute Macro surface → execute-macro-failures.md |
| Cannot run the macro | message | activity-packages/excel-activities/playbooks/invoke-vba-entry-method-name.md | high | Invoke VBA at Application.Run — EntryMethodName does not resolve (typo, appended parentheses, Private/nested Sub) while the code file itself compiles; code-file load/compile failure → invoke-vba-code-file-path.md; Execute Macro surface → execute-macro-failures.md |
| Cannot save the document because it is read-only | message | activity-packages/word-activities/playbooks/replace-text-file-locked.md | medium |  |
| Cannot send input to UI element because it is outside of screen bounds. | message | activity-packages/ui-automation/playbooks/click-coordinate-off-screen.md | high |  |
| CNS1000 | error-code | products/integration-service/playbooks/cs-connection-not-found.md | high |  |
| CNS1001 | error-code | products/integration-service/playbooks/cs-connector-unavailable.md | high |  |
| CNS1002 | error-code | products/integration-service/playbooks/cs-connector-unavailable.md | high |  |
| CNS1003 | error-code | products/integration-service/playbooks/cs-connection-not-found.md | high |  |
| CNS1004 | error-code | products/integration-service/playbooks/cs-connector-unavailable.md | high |  |
| CNS1005 | error-code | products/integration-service/playbooks/cs-events-callback-failed.md | medium |  |
| CNS1006 | error-code | products/integration-service/playbooks/cs-connection-not-found.md | high |  |
| CNS1007 | error-code | products/integration-service/playbooks/cs-operation-conflict.md | high |  |
| CNS1008 | error-code | products/integration-service/playbooks/cs-connection-not-authenticated.md | high |  |
| CNS1014 | error-code | products/integration-service/playbooks/cs-trigger-operation-failed.md | high |  |
| CNS1015 | error-code | products/integration-service/playbooks/cs-events-callback-failed.md | medium |  |
| CNS1019 | error-code | products/integration-service/playbooks/cs-events-callback-failed.md | medium |  |
| CNS1020 | error-code | products/integration-service/playbooks/cs-trigger-operation-failed.md | high |  |
| CNS1021 | error-code | products/integration-service/playbooks/cs-connection-not-authenticated.md | high |  |
| CNS1024 | error-code | products/integration-service/playbooks/cs-events-callback-failed.md | medium |  |
| CNS1025 | error-code | products/integration-service/playbooks/cs-trigger-operation-failed.md | high |  |
| CNS1029 | error-code | products/integration-service/playbooks/cs-events-callback-failed.md | medium |  |
| CNS1038 | error-code | products/integration-service/playbooks/cs-operation-conflict.md | high |  |
| CNS1039 | error-code | products/integration-service/playbooks/cs-trigger-operation-failed.md | high |  |
| CNS1042 | error-code | products/integration-service/playbooks/cs-dependency-unavailable.md | high |  |
| CNS1043 | error-code | products/integration-service/playbooks/cs-permission-denied.md | high |  |
| CNS1044 | error-code | activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md | medium | surfaced inside a GSuite activity ConnectionHttpException; raw Connection Service API surface → cs-permission-denied.md |
| CNS1044 | error-code | products/integration-service/playbooks/cs-permission-denied.md | high | raw Connection Service API surface; inside a GSuite activity ConnectionHttpException → gsuite connection-and-auth-failures.md |
| CNS1045 | error-code | activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md | medium | surfaced inside a GSuite activity ConnectionHttpException; raw Connection Service API surface → cs-permission-denied.md |
| CNS1045 | error-code | products/integration-service/playbooks/cs-permission-denied.md | high | raw Connection Service API surface; inside a GSuite activity ConnectionHttpException → gsuite connection-and-auth-failures.md |
| CNS1046 | error-code | products/integration-service/playbooks/cs-permission-denied.md | high |  |
| CNS1047 | error-code | products/integration-service/playbooks/cs-permission-denied.md | high |  |
| CNS1049 | error-code | products/integration-service/playbooks/cs-connection-not-found.md | high |  |
| CNS1050 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1055 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1056 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1057 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1058 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1059 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1060 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1061 | error-code | products/integration-service/playbooks/cs-connection-not-authenticated.md | high |  |
| CNS1063 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1064 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1065 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1066 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1067 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1068 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1069 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1070 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1071 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1072 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1074 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium |  |
| CNS1075 | error-code | products/integration-service/playbooks/cs-connector-unavailable.md | high | 409 ConnectorNotDeployed on a direct Connection Service call; inside a Solutions package install/validation flow → cs-solutions-install-failed.md |
| CNS1075 | error-code | products/integration-service/playbooks/cs-solutions-install-failed.md | medium | surfaced as a per-resource ValidationError during a Solutions package install/validation; on a direct Connection Service call → cs-connector-unavailable.md |
| CNS1101 | error-code | products/integration-service/playbooks/cs-dependency-unavailable.md | high |  |
| CNS2000 | error-code | products/integration-service/playbooks/cs-events-callback-failed.md | medium |  |
| CNS2003 | error-code | products/integration-service/playbooks/cs-dependency-unavailable.md | high |  |
| CNS2004 | error-code | products/integration-service/playbooks/cs-trigger-operation-failed.md | high |  |
| CNS2005 | error-code | products/integration-service/playbooks/cs-dependency-unavailable.md | high |  |
| CNS2006 | error-code | products/integration-service/playbooks/cs-dependency-unavailable.md | high |  |
| CNS2007 | error-code | products/integration-service/playbooks/cs-dependency-unavailable.md | high |  |
| CNS2009 | error-code | products/integration-service/playbooks/cs-dependency-unavailable.md | high |  |
| CNS2010 | error-code | products/integration-service/playbooks/cs-dependency-unavailable.md | high |  |
| CNS2011 | error-code | products/integration-service/playbooks/cs-events-callback-failed.md | medium |  |
| CNS2012 | error-code | products/integration-service/playbooks/cs-dependency-unavailable.md | high |  |
| CNS2045 | error-code | products/integration-service/playbooks/cs-connector-unavailable.md | high |  |
| CNS3001 | error-code | products/integration-service/playbooks/cs-permission-denied.md | high |  |
| CNS3002 | error-code | products/integration-service/playbooks/cs-operation-conflict.md | high |  |
| Collection was modified; enumeration operation may not execute | message | activity-packages/mail-activities/playbooks/delete-outlook-mail-failures.md | medium | Delete runs inside a For Each over the live message list (branch 2) |
| Column not found: | message | activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md | medium |  |
| COMException | exception | activity-packages/cv-activities/playbooks/cv-action-failed-after-find.md | medium | raw driver exception with NO UiPath.CV.* type and no CV resource key — the find already passed; no *_ComputerVision dump exists for the run |
| Command Failed | message | activity-packages/word-activities/playbooks/export-pdf-missing-output-dir.md | medium | generic Export to PDF / Save Document as PDF failure — most common cause is a missing output directory; lowercase 'Command failed' on Documents.Open → word-open-sharepoint-url-com-command-failed.md |
| Command failed | message | activity-packages/word-activities/playbooks/word-open-sharepoint-url-com-command-failed.md | medium | on the open path (Documents.Open / WordDocumentFactory) with a :w:/:f: sharing-link FilePath; 'Command Failed' at Export to PDF → export-pdf-missing-output-dir.md |
| CommandText property has not been initialized | message | activity-packages/database-activities/playbooks/execute-non-query-failures.md | medium |  |
| Compile error | message | activity-packages/excel-activities/playbooks/invoke-vba-code-file-path.md | medium |  |
| Computer Vision cannot be enabled: the current user is not authenticated. | message | activity-packages/cv-activities/playbooks/cv-server-auth-throttling-network.md | medium |  |
| Computer Vision rate limit exceeded. | message | activity-packages/cv-activities/playbooks/cv-server-auth-throttling-network.md | medium |  |
| Connection is disabled. Please enable the connection to continue. | message | products/integration-service/playbooks/connector-general-exception.md | high |  |
| ContextGroundingIndex not found | message | products/agents/playbooks/context-grounding-index-not-found.md | high |  |
| ContinueOnError = true | state | activity-packages/cv-activities/playbooks/cv-silent-failures-and-false-results.md | medium | on the CV activity or the CVScope — every exception swallowed to default output; the real error is in the Trace.TraceError line |
| could not be found on this account. | message | activity-packages/o365-activities/playbooks/mail-folder-not-found.md | high |  |
| Could not cast or convert from System.String | message | activity-packages/web-activities/playbooks/deserialize-type-mismatch.md | medium |  |
| Could not establish trust relationship for the SSL/TLS secure channel | message | activity-packages/web-activities/playbooks/http-request-connection-failure.md | medium |  |
| Could not extract an object Id from the Url | message | activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md | medium |  |
| Could not find a machine with Unattended or NonProduction runtimes in the current folder | message | products/maestro/playbooks/no-suitable-runtime-machine.md | high |  |
| Could not find a part of the path | message | activity-packages/excel-activities/playbooks/read-range-file-not-found.md | medium | DirectoryNotFoundException message at Excel workbook open — a WorkbookPath segment is missing (relative path, unmapped drive, deleted parent) |
| Could not find a part of the path | message | activity-packages/word-activities/playbooks/word-scope-file-path-not-found.md | medium | folder segment of the Word document path missing — relative path / mapped drive / bad concatenation |
| Could not find an asset with this name | message | activity-packages/system-activities/playbooks/get-asset-not-found.md | high |  |
| Could not find any enabled consumption pools | message | activity-packages/ui-automation/playbooks/healing-agent-no-license.md | high | App Insights / backend logs — heals not allocated to this tenant or pool not enabled |
| Could not find file | message | activity-packages/word-activities/playbooks/word-scope-file-path-not-found.md | medium | Word Application Scope document path does not resolve on the robot host |
| Could not find table. Cell targeting supports only tables as target | message | activity-packages/cv-activities/playbooks/cv-cell-targeting-failures.md | high |  |
| Could not find target application. | message | activity-packages/ui-automation/playbooks/application-not-found.md | high |  |
| Could not find the asset | message | activity-packages/system-activities/playbooks/get-asset-not-found.md | high |  |
| Could not get screenshot | message | activity-packages/cv-activities/playbooks/cv-element-not-found.md | medium | trace-only line before the throw — scope-refresh failure branch (window closed/minimized, locked session) |
| Could not load file or assembly 'Microsoft.Office.Interop.Excel' | message | activity-packages/excel-activities/playbooks/lookup-range-excel-not-installed.md | high |  |
| Could not load file or assembly 'Microsoft.Office.Interop.Word' | message | activity-packages/word-activities/playbooks/word-scope-com-not-installed.md | high |  |
| Could not obtain access token. | message | products/integration-service/playbooks/connector-remote-exception.md | medium |  |
| Could not open target application. | message | activity-packages/ui-automation/playbooks/application-open-failed.md | high |  |
| Could not retrieve the selected asset | message | activity-packages/o365-activities/playbooks/application-scope-misconfigured.md | medium |  |
| Could not start executor | message | products/orchestrator/playbooks/job-faulted-logon-failure.md | medium |  |
| Could not uniquely identify the user-interface element for this action. | message | activity-packages/ui-automation/playbooks/ambiguous-selector.md | high |  |
| Couldn't find any user with unattended robot permissions in the current folder | message | products/maestro/playbooks/unattended-robot-permissions.md | high |  |
| CvElementExistsWithDescriptor Result = false with the element plainly present | state | activity-packages/cv-activities/playbooks/cv-silent-failures-and-false-results.md | medium | false negative — closed/minimized window or failed screenshot surfaces as ElementNotFoundException and is converted to false by design |
| CvGetTextWithDescriptor completed without faulting but Result is empty / null / stale / partial | state | activity-packages/cv-activities/playbooks/cv-get-text-empty-or-wrong-result.md | medium | the defining no-fault signature — MethodType (OCR vs ClipboardRow/ClipboardAll) splits the branches |
| dailyLimitExceeded | error-code | activity-packages/gsuite-activities/playbooks/transient-and-timeout-errors.md | medium |  |
| DAP-GE- | error-code-prefix | products/integration-service/playbooks/connector-general-exception.md | high |  |
| DAP-GE-3000 | error-code | products/integration-service/playbooks/connector-general-exception.md | high | Failed to retrieve connection — detail names invalid/no-access, missing Connections.View permission, or Bad Gateway |
| DAP-GE-3005 | error-code | products/integration-service/playbooks/connector-general-exception.md | high | connection exists and is bound correctly but is disabled |
| DAP-RT- | error-code-prefix | products/integration-service/playbooks/connector-runtime-exception.md | high |  |
| DAP-RT-1002 | error-code | products/integration-service/playbooks/connector-runtime-exception.md | high | Connection ID is empty — no connection bound to the activity |
| DAP-RT-1003 | error-code | products/integration-service/playbooks/connector-runtime-exception.md | high | a required input field of the connector operation is empty/null at runtime |
| DAP-RT-1003 | error-code | products/maestro/playbooks/file-field-required.md | high | surfaced as a Maestro element fault (502); raw connector activity fault in a job → integration-service connector-runtime-exception.md |
| DAP-RT-1052 | error-code | products/integration-service/playbooks/connector-runtime-exception.md | high | Trigger activity could not find any matches |
| DAP-RT-1101 | error-code | products/integration-service/playbooks/connector-runtime-exception.md | high | downstream HTTP status with ProviderMessage/ProviderErrorCode block from the external service |
| Data at the root level is invalid | message | activity-packages/web-activities/playbooks/deserialize-malformed-input.md | high |  |
| Data failed json schema validation | message | products/agents/playbooks/input-schema-validation-failure.md | high | Variant B — names the offending field and type code inline |
| Data.Allowed.AgentService == 0 | state | activity-packages/ui-automation/playbooks/healing-agent-no-license.md | high | uip or licenses info with LicensedFeatures: [] — no HA entitlement on the tenant |
| Descriptor or InputRegion is required | message | activity-packages/cv-activities/playbooks/cv-scope-setup-failures.md | medium |  |
| Descriptor value: | message | activity-packages/cv-activities/playbooks/cv-invalid-descriptor.md | high | always the last line of the composite message — names the offending Descriptor argument expression |
| Destination should be a folder. | message | activity-packages/classic-activities/playbooks/file-operation-failed.md | medium |  |
| DocumentFormat.OpenXml.OpenXmlPackageException | exception | activity-packages/excel-activities/playbooks/read-range-null-reference.md | low | OpenXML provider failure — workbook structural corruption or unsupported OpenXML feature |
| does not exist in the workbook | message | activity-packages/excel-activities/playbooks/read-range-sheet-not-found.md | medium | modern Use Excel File family wording of the same sheet-name mismatch |
| does not have the required permissions | message | activity-packages/system-activities/playbooks/get-asset-permission-denied.md | high |  |
| does not work with assets of type Credential | message | activity-packages/system-activities/playbooks/get-asset-wrong-activity-type.md | high |  |
| DynamicJobConnectedMachinesInvalid | error-code | products/orchestrator/playbooks/job-pending-stale-dispatch.md | high | no-host-family PendingReasons code captured at dispatch, no longer describing current state |
| DynamicJobConnectedMachinesWindowsRobotVersionInvalid | error-code | products/orchestrator/playbooks/job-pending-stale-dispatch.md | high | no-host-family PendingReasons code captured at dispatch, no longer describing current state |
| Element not found | message | activity-packages/cv-activities/playbooks/cv-element-not-found.md | medium | canonical literal — three root causes share it (genuine mismatch, scope-refresh failure, OCR degradation); the *_ComputerVision dump screenshot is the discriminator |
| ElementNotInteractableException | exception | activity-packages/ui-automation/playbooks/selector-failure-healing-disabled.md | high | Healing Agent disabled — AutopilotForRobots Enabled: false or HealingEnabled: false (or field absent) |
| ElementNotInteractableException | exception | activity-packages/ui-automation/playbooks/selector-failure-healing-fix.md | high | HA enabled with recovery data present (healing-fixes.json entry or InferredRecoveryInfo/RecoveryInfo in uia/*.json) |
| ElementNotInteractableException | exception | activity-packages/ui-automation/playbooks/selector-failure-manual.md | medium | HA enabled but no fix produced, or source code available for manual selector analysis |
| ElementNotSetException | exception | activity-packages/classic-activities/playbooks/ui-activity-configuration-error.md | high | leaf reports no target while its own Selector is set — originating fault is the enclosing scope |
| ElementNotSetException | exception | activity-packages/cv-activities/playbooks/cv-action-failed-after-find.md | medium | remapped from UninitializedNodeException after the find succeeded — post-find action failure, not the scope-entry variant |
| ElementOperationException | exception | activity-packages/classic-activities/playbooks/ui-element-interaction-failed.md | medium |  |
| Encountered errors while trying to kill a process | message | activity-packages/classic-activities/playbooks/kill-process-failed.md | low |  |
| Error converting value | message | activity-packages/web-activities/playbooks/deserialize-type-mismatch.md | medium |  |
| Error evaluating expression in activity inputs for element | message | products/maestro/playbooks/expression-evaluation-errors.md | high |  |
| Error initializing Python engine | message | activity-packages/python-activities/playbooks/load-script-failures.md | medium | engine init at the scope layer (L1b-L1e: bitness, Library path, unsupported version, missing .NET Desktop Runtime); see also python-scope-architecture-version-mismatch.md |
| Error initializing the Python engine | message | activity-packages/python-activities/playbooks/python-scope-architecture-version-mismatch.md | medium |  |
| Error invoking Python method | message | activity-packages/python-activities/playbooks/invoke-python-method-pipe-is-broken.md | medium |  |
| Error invoking the python method | message | activity-packages/python-activities/playbooks/invoke-method-failures.md | medium | wrapper around a Python-side exception raised inside the invoked function |
| Error loading the python script | message | activity-packages/python-activities/playbooks/load-script-failures.md | medium | script-layer failure executing the module body (L2: syntax error, top-level exception, failed import) |
| Error opening document, make sure Word application is installed | message | activity-packages/word-activities/playbooks/word-scope-com-not-installed.md | high | Word Application Scope COM startup — no desktop Word / bitness / damaged registration; unattended Session-0 variant with 'Office Repair may be required' → word-com-start-background-session0.md |
| Error opening document, make sure Word application is installed. If already installed, an Office Repair may be required. | message | activity-packages/word-activities/playbooks/word-com-start-background-session0.md | medium | full two-clause text on COM start in Session 0 / Background Process; first clause alone → word-scope-com-not-installed.md |
| Error opening workbook. Make sure Excel is installed. | message | activity-packages/excel-activities/playbooks/excel-application-card-failures.md | medium | Excel genuinely absent or install broken on a card/scope needing COM (branch 1); Excel confirmed installed with inner 0x8002801D/0x80040154 → excel-application-scope-failures.md |
| Error opening workbook. Make sure Excel is installed. | message | activity-packages/excel-activities/playbooks/excel-application-scope-failures.md | medium | host DOES have Excel — inner COMException 0x8002801D TYPE_E_LIBNOTREGISTERED / 0x80040154 means broken COM registration (branch 1); no Excel install at all → excel-application-card-failures.md |
| Error while sending request. | message | activity-packages/cv-activities/playbooks/cv-server-auth-throttling-network.md | medium |  |
| Error_400 | message | products/maestro/playbooks/generic-error-400.md | low | error name with no specifics — errorDetails empty or non-actionable |
| ErrorInvalidIdMalformed | error-code | activity-packages/o365-activities/playbooks/mail-message-not-found.md | high |  |
| ErrorInvalidMailboxItemId | error-code | activity-packages/o365-activities/playbooks/mail-message-not-found.md | high |  |
| ErrorInvalidRecipients | error-code | activity-packages/o365-activities/playbooks/send-mail-rejected.md | medium |  |
| ErrorItemNotFound | error-code | activity-packages/o365-activities/playbooks/mail-message-not-found.md | high |  |
| ErrorMessageSizeExceeded | error-code | activity-packages/o365-activities/playbooks/send-mail-rejected.md | medium |  |
| ErrorSendAsDenied | error-code | activity-packages/o365-activities/playbooks/send-mail-rejected.md | medium |  |
| Excel Application Scope not found | message | activity-packages/excel-activities/playbooks/delete-range-failures.md | medium |  |
| Excel File path is empty or not set | message | activity-packages/excel-activities/playbooks/excel-application-card-failures.md | medium |  |
| Excel is not installed | message | activity-packages/excel-activities/playbooks/lookup-range-excel-not-installed.md | high | at classic Lookup Range (ExcelLookUpRange) init on a host without Excel; scope-level 'Error opening workbook. Make sure Excel is installed.' → excel-application-scope-failures.md / excel-application-card-failures.md |
| ExceptionCheckActivity | message-key | activity-packages/ui-automation/playbooks/verify-execution-failure.md | high | generic assertion failure — NOT the TypeInto-specific keys |
| ExceptionRecoveredButValidationFailed | message-key | activity-packages/ui-automation/playbooks/verify-execution-failure.md | high |  |
| ExceptionVerificationImageCouldNotBeRetrieved | message-key | activity-packages/ui-automation/playbooks/verify-execution-failure.md | high |  |
| ExceptionVerificationTargetNotFoundOrInvalid | message-key | activity-packages/ui-automation/playbooks/verify-execution-failure.md | high |  |
| ExceptionVerificationTextNotSupported | message-key | activity-packages/ui-automation/playbooks/verify-execution-failure.md | high |  |
| Execute Non Query: A database error occurred | message | activity-packages/database-activities/playbooks/execute-non-query-failures.md | medium |  |
| Execute Query: A database error occurred | message | activity-packages/database-activities/playbooks/execute-query-failures.md | medium |  |
| Execute Query: Timeout expired | message | activity-packages/database-activities/playbooks/execute-query-failures.md | medium |  |
| Expected: end of statement | message | activity-packages/excel-activities/playbooks/invoke-vba-code-file-path.md | medium |  |
| Expression could not be parameterized | message | products/maestro/playbooks/expression-evaluation-errors.md | high | parallel multi-instance subprocesses |
| Failed | state | products/orchestrator/playbooks/queue-items-failing.md | medium | queue item status, not job state — multiple distinct error types may be present across items |
| Failed opening the Excel file. Possible reasons: file is corrupt, already used by another process or password protected. | message | activity-packages/excel-activities/playbooks/excel-application-scope-failures.md | medium |  |
| Failed to apply | message | products/maestro/playbooks/autopilot-429.md | high | Autopilot for Maestro surface — backend/LLM Gateway rate limiting |
| Failed to evaluate the input collection variable | message | products/maestro/playbooks/variable-expression-errors.md | medium | designer-surface variant — swimlane drag/drop cleared references; marker runtime failures → marker-invalid-cast.md |
| Failed to evaluate the input collection variable for the marker element | message | products/maestro/playbooks/marker-invalid-cast.md | high | with inner InvalidCastException System.Object[] to ExpressionList — JS 'Items' expression bug |
| Failed to evaluate the input collection variable for the marker element | message | products/maestro/playbooks/multi-instance-parallel.md | medium | general marker input issues — batch over 50 items, non-array collection, NoneType properties; JS Object[] cast → marker-invalid-cast.md |
| Failed to execute IS call to | message | products/agents/playbooks/is-invalid-credentials.md | high | with HTTP Status: 401 - Unauthorized — for 404 Invalid Element Instance see is-invalid-element-instance.md |
| Failed to execute IS call to | message | products/agents/playbooks/is-invalid-element-instance.md | high | with HTTP Status: 404 - Not Found — for 401 Unauthorized see is-invalid-credentials.md |
| Failed to execute IS Event call | message | products/agents/playbooks/is-connection-disabled.md | medium | with HTTP Status: 403 - Forbidden on an agent toolCall span |
| Failed to load library (ErrorCode: 126) | message | activity-packages/database-activities/playbooks/execute-non-query-failures.md | medium |  |
| Failed to navigate to the specified URL. | message | activity-packages/ui-automation/playbooks/browser-navigation-failed.md | medium |  |
| Failed to open the indicated local URL. | message | activity-packages/ui-automation/playbooks/browser-navigation-failed.md | medium | local file:// URL on a Chromium browser without the Allow-access-to-file-URLs extension permission |
| Failed to read from Credential Store type | message | activity-packages/system-activities/playbooks/get-asset-external-vault-failure.md | medium |  |
| Failed to retrieve connection. Consider using a different connection. | message | products/integration-service/playbooks/connector-general-exception.md | high |  |
| Failing on Empty Header | message | activity-packages/excel-activities/playbooks/write-range-failures.md | medium |  |
| Failing the instance to prevent infinite loop | message | products/maestro/playbooks/loop-detected.md | high |  |
| Failure in the Orchestrator Job | message | products/maestro/playbooks/service-task-child-job-faulted.md | high |  |
| field is required. Error code: DAP-RT-1003 | message | products/maestro/playbooks/file-field-required.md | high |  |
| File cannot be null | message | activity-packages/classic-activities/playbooks/file-operation-failed.md | medium |  |
| File does not exist: | message | activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md | medium | local filesystem path on a GSuite activity (legacy SendEmail attachment, upload source, service-account key) — the same sentence on an O365 send is a missing attachment → send-mail-rejected.md (o365) |
| File does not exist: | message | activity-packages/o365-activities/playbooks/send-mail-rejected.md | medium | missing attachment path on an O365 send/forward/reply — the same sentence from a GSuite activity is a local attachment/upload/key path → invalid-or-null-input.md (gsuite) |
| File not found: | message | activity-packages/gsuite-activities/playbooks/drive-file-not-found.md | high |  |
| File should have a name: | message | activity-packages/o365-activities/playbooks/download-file-conversion-or-destination.md | high |  |
| FileNotFoundError | message | activity-packages/python-activities/playbooks/working-folder-relative-path.md | medium | Python-side, referencing a relative path — CWD is the robot per-package folder, not the project; the activities themselves succeed |
| FileNotFoundError | exception | activity-packages/python-activities/playbooks/working-folder-relative-path.md | medium | Python exception class, raised script-side on a relative path while the UiPath activities succeed — CWD is the robot per-package folder, not the project |
| Folder does not exist or the user does not have access to the folder | message | activity-packages/system-activities/playbooks/get-asset-folder-scope-mismatch.md | high | raised by Get Asset/Credential inside an RPA job — executing robot's folder scope; surfaced by a Maestro instance → maestro folder-not-accessible.md |
| Folder does not exist or the user does not have access to the folder | message | products/maestro/playbooks/folder-not-accessible.md | high | surfaced by a Maestro instance calling Orchestrator (HTTP 400/403, code #1100); raised by Get Asset/Credential inside an RPA job → system-activities get-asset-folder-scope-mismatch.md |
| Folder path must contain at least one segment. | message | activity-packages/o365-activities/playbooks/create-folder-invalid-path.md | high |  |
| Folders cannot be downloaded with this activity. | message | activity-packages/o365-activities/playbooks/download-file-conversion-or-destination.md | high |  |
| Foreground job requires an unattended robot to be defined on your user | message | products/maestro/playbooks/foreground-unattended-robot.md | high |  |
| Format of the initialization string does not conform to specification starting at index | message | activity-packages/database-activities/playbooks/connect-to-database-failures.md | medium |  |
| GmailException | exception | activity-packages/gsuite-activities/playbooks/get-newest-email-not-found.md | high | generic Gmail exception — this claim is the empty-result fault from GetNewestEmailConnections or a NewEmailReceived / EmailSent trigger debug run |
| GSuiteException | exception | activity-packages/gsuite-activities/playbooks/add-sheet-name-conflict.md | high | generic GSuite package exception — this claim is the AddSheetConnections duplicate sheet-name fault (ConflictResolution = Fail) |
| GSuiteException | exception | activity-packages/gsuite-activities/playbooks/drive-multiple-items-name-conflict.md | high | generic GSuite package exception — this claim is the Drive ConflictResolution name-conflict lookup fault (Create/Copy/Move/Rename/Upload/Create Spreadsheet/Create Document) |
| guardrailEvaluation | message | products/agents/playbooks/guardrail-violation.md | high | span type carrying guardrailName/action/validationResult — also toolGuardrailEvaluation |
| has no attribute | message | activity-packages/python-activities/playbooks/invoke-method-failures.md | medium | Python AttributeError — the Name property does not match a module-level def (M1: typo, case mismatch, nested, or __main__-guarded) |
| Healing agent configuration. | message | activity-packages/ui-automation/playbooks/healing-agent-orch-issues.md | high | benign Info-level config read on every run — zero consumption |
| Healing Agent settings | message | activity-packages/ui-automation/playbooks/healing-agent-orch-issues.md | high | reworded variant of the benign config-read Info line |
| HealingAgent | error-code | activity-packages/ui-automation/playbooks/healing-agent-no-license.md | high | operation code in the robot log line / backend licenseCode — regular Heals pool requested (release ProcessType is not TestAutomationProcess) |
| HealingAgent.Test | error-code | activity-packages/ui-automation/playbooks/healing-agent-no-license.md | high | operation code / licenseCode — Test Heals pool requested (release ProcessType = TestAutomationProcess); Flex tenants cannot assign Test Heals |
| hidden rows | message | activity-packages/excel-activities/playbooks/append-range-failures.md | medium | append region intersects hidden rows on the target sheet (package v2.8.5+); hidden rows inside a Write Range rectangle → write-range-failures.md |
| hidden rows | message | activity-packages/excel-activities/playbooks/write-range-failures.md | medium | hidden rows/columns inside the Write Range target rectangle (package v2.8.5+, branch 4); append region intersecting hidden rows → append-range-failures.md |
| hit the maximum number of words it is able to identify | message | activity-packages/cv-activities/playbooks/cv-server-auth-throttling-network.md | medium | covers the cloud (MaxOCRCloud) and local-server (MaxOCR) word-limit variants — thrown even on HTTP 200 |
| HttpStatusCode is NotFound | message | activity-packages/gsuite-activities/playbooks/drive-file-not-found.md | high |  |
| Id is malformed. | message | activity-packages/o365-activities/playbooks/mail-message-not-found.md | high |  |
| Ignore empty source | message | activity-packages/excel-activities/playbooks/write-range-failures.md | medium | BusinessException — source DataTable has 0 rows with ExcludeHeaders=False (branch 3) |
| Illegal characters in path | message | activity-packages/excel-activities/playbooks/excel-application-card-failures.md | medium |  |
| Index was outside the bounds of the array. | message | products/maestro/playbooks/index-out-of-bounds.md | low |  |
| Input collection for the marker element must not be null | message | products/maestro/playbooks/marker-input-null.md | high |  |
| Input does not conform to schema | message | products/maestro/playbooks/input-schema-mismatch.md | high |  |
| Input validation failed | message | products/agents/playbooks/input-schema-validation-failure.md | high | Variant B error prefix — caller payload fails the input schema at invocation time |
| InRegion is bound | state | activity-packages/cv-activities/playbooks/cv-silent-failures-and-false-results.md | medium | bypasses CV detection entirely — CvElementExistsWithDescriptor always returns True; Click/Type fire at raw coordinates |
| Insufficient funds: Your account doesn't have enough credits for execution | message | products/maestro/playbooks/insufficient-funds.md | high |  |
| Insufficient information | message | products/agents/playbooks/llm-insufficient-information.md | medium | detail field of the error JSON on a completion or agentRun span — names the missing context |
| Insufficient privileges to complete the operation. | message | activity-packages/o365-activities/playbooks/insufficient-graph-scope.md | high |  |
| IntegrationService.Activities.SWEntities | message | products/integration-service/playbooks/connector-null-reference.md | medium | stack fragment — ForEach enumerating a null connector List/Get output |
| Internal server error occurred. Please try again later. | message | activity-packages/gsuite-activities/playbooks/transient-and-timeout-errors.md | medium |  |
| Invalid asset type | message | activity-packages/system-activities/playbooks/get-asset-wrong-activity-type.md | high |  |
| Invalid authentication credentials. | message | activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md | medium |  |
| Invalid cell number | message | activity-packages/cv-activities/playbooks/cv-cell-targeting-failures.md | high |  |
| Invalid column number | message | activity-packages/cv-activities/playbooks/cv-cell-targeting-failures.md | high |  |
| Invalid Credential Store configuration | message | activity-packages/system-activities/playbooks/get-asset-external-vault-failure.md | medium |  |
| invalid credentials | message | products/llm-gateway/playbooks/byo-connection-dead.md | high | vendor-surfaced wording on an LLM call that previously worked |
| Invalid Descriptor | message | activity-packages/cv-activities/playbooks/cv-invalid-descriptor.md | high |  |
| Invalid Element Instance Id provided. | message | products/agents/playbooks/is-invalid-element-instance.md | high | on an agent toolCall span (agent trace) — for the Maestro/IS activity surface see integration-service-404.md |
| Invalid Element Instance Id provided. | message | products/maestro/playbooks/integration-service-404.md | medium | surfaced through a Maestro IS call; in an agent run's trace spans → products/agents is-invalid-element-instance.md |
| Invalid filter clause: | message | activity-packages/o365-activities/playbooks/mail-invalid-odata-query.md | high |  |
| Invalid or empty shortcut sequence. | message | activity-packages/ui-automation/playbooks/activity-configuration-error.md | high |  |
| Invalid Organization or User secret, or invalid Element token provided. | message | products/agents/playbooks/is-invalid-credentials.md | high |  |
| Invalid Query. Please use OData format for filter queries. | message | activity-packages/o365-activities/playbooks/mail-invalid-odata-query.md | high |  |
| Invalid row number | message | activity-packages/cv-activities/playbooks/cv-cell-targeting-failures.md | high |  |
| InvalidCastException | exception | products/maestro/playbooks/marker-invalid-cast.md | high | System.Object[] to ExpressionList on a multi-instance marker |
| InvalidNodeException | exception | activity-packages/ui-automation/playbooks/element-found-not-actionable.md | medium |  |
| IOException | exception | activity-packages/excel-activities/playbooks/lookup-range-file-locked.md | medium | generic .NET IO class (leaf form) — on Lookup Range or its Excel Application Scope / Use Excel File, the workbook file handle is held by another process; Read Range family full lock-owner chain → read-range-file-locked.md |
| is invalid or you do not have access | message | products/integration-service/playbooks/connection-invalid.md | high | connection missing, cross-workspace, disabled, or caller lacks permissions — when raised as DAP-GE-3000 on a connector activity see connector-general-exception.md |
| is invalid or you do not have access to it | message | activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md | medium |  |
| is locked for editing by | message | activity-packages/excel-activities/playbooks/lookup-range-file-locked.md | medium |  |
| is not a valid Win32 application | message | activity-packages/python-activities/playbooks/python-scope-architecture-version-mismatch.md | medium | inner error of the bitness mismatch |
| is the duplicate of another item name | message | activity-packages/classic-activities/playbooks/add-queue-item-failed.md | medium | same key supplied in both ItemInformation and ItemInformationCollection |
| isAvailable: false | message | products/llm-gateway/playbooks/validation-probe-failed.md | medium | validation probe — vendor key cannot reach the requested model |
| isCompatible: false | message | products/llm-gateway/playbooks/validation-probe-failed.md | medium | validation probe — (model, api-flavor) pair not allowed |
| isModelNameSimilar: false | message | products/llm-gateway/playbooks/validation-probe-failed.md | medium | validation probe — model name not recognized (typo or deprecated variant) |
| Issues Detected | state | activity-packages/ui-automation/playbooks/healing-agent-orch-issues.md | high | Jobs-grid Healing Agent column / job detail Healing Agent tab — detection-only status |
| itemNotFound | error-code | activity-packages/o365-activities/playbooks/drive-item-not-found.md | high | legacy activities — raw Microsoft.Graph.ServiceException with 'Code: itemNotFound' |
| Job Operation Timeout | message | products/maestro/playbooks/job-operation-timeout.md | medium |  |
| Job stopped with an unexpected exit code: 0x40010004 | message | products/orchestrator/playbooks/job-stopped-exit-code-0x40010004.md | medium |  |
| Keyword not supported | message | activity-packages/database-activities/playbooks/execute-query-failures.md | medium |  |
| Library not registered | message | activity-packages/mail-activities/playbooks/send-outlook-mail-failures.md | medium | COMException binding Outlook COM at Send Outlook Mail (branch 1); Word type-library variant carries 0x8002801D → word-com-interop-failures.md |
| limit was exceeded. | message | activity-packages/gsuite-activities/playbooks/transient-and-timeout-errors.md | medium | covers 'The daily limit was exceeded.' / 'The user rate limit was exceeded.' / 'The rate limit was exceeded.' — Google 429 rate/quota reasons, NOT the storage quota ('storage quota was exceeded' → upload-storage-quota-exceeded.md) |
| Local File Path should point to a folder or directly to a .pdf file. | message | activity-packages/o365-activities/playbooks/download-file-conversion-or-destination.md | high |  |
| Logon failed for user | message | products/orchestrator/playbooks/job-faulted-logon-failure.md | medium |  |
| Max file size exceeded. | message | activity-packages/o365-activities/playbooks/upload-file-quota-or-size.md | medium |  |
| maxFileSizeExceeded | error-code | activity-packages/o365-activities/playbooks/upload-file-quota-or-size.md | medium |  |
| Maximum stream size exceeded. | message | activity-packages/o365-activities/playbooks/upload-file-quota-or-size.md | medium |  |
| may not be null or empty. | message | activity-packages/classic-activities/playbooks/add-queue-item-failed.md | medium | tail of the 'Queue name' validation message — empty/null QueueName input |
| Microsoft.Graph.ServiceException | exception | activity-packages/o365-activities/playbooks/request-throttled.md | high | generic Graph SDK exception from legacy (non-Connections) O365 activities — this claim is the raw throttle wording / 429; 5xx or timeout wording → transient-service-error.md |
| Microsoft.Graph.ServiceException | exception | activity-packages/o365-activities/playbooks/transient-service-error.md | medium | generic Graph SDK exception from legacy (non-Connections) O365 activities — this claim is the raw 5xx / timeout wording; throttle wording / 429 → request-throttled.md |
| Missing output variables | message | products/maestro/playbooks/variable-expression-errors.md | medium |  |
| Missing value for required parameter | message | products/maestro/playbooks/missing-required-parameter.md | high |  |
| ModuleNotFoundError | exception | activity-packages/python-activities/playbooks/load-script-failures.md | medium | Python exception class — top-level import missing from the interpreter at the scope's Path during Load Python Script (L2a); lazy import inside a called function → invoke-method-failures.md |
| ModuleNotFoundError: No module named | message | activity-packages/python-activities/playbooks/load-script-failures.md | medium | top-level import missing from the interpreter at the scope's Path (L2a); lazy import inside a called function → invoke-method-failures.md |
| Multiple items with the name | message | activity-packages/gsuite-activities/playbooks/drive-multiple-items-name-conflict.md | high | GSuiteException from a Drive activity's ConflictResolution lookup — not for DownloadAttachmentsConnections (local path conflict); the same wording from O365 downloads → download-multiple-items-name-conflict.md (o365) |
| Multiple items with the name | message | activity-packages/o365-activities/playbooks/download-multiple-items-name-conflict.md | high | Office365Exception from a download activity — conflict is in the LOCAL destination folder; same wording from GSuite Drive → drive-multiple-items-name-conflict.md (gsuite) |
| Multiple similar matches found. | message | activity-packages/ui-automation/playbooks/ambiguous-selector.md | high |  |
| must be placed inside | message | activity-packages/excel-activities/playbooks/append-range-failures.md | medium |  |
| must be placed inside a Use Word File | message | activity-packages/word-activities/playbooks/append-text-missing-container.md | high | App-Integration Append Text outside its container; modern Read Text variant → read-text-missing-container.md |
| must be placed inside a Use Word File | message | activity-packages/word-activities/playbooks/read-text-missing-container.md | high | modern Word-pack Read Text dropped outside its container; App-Integration Append Text variant → append-text-missing-container.md |
| Named ranges with cell value are invalid. | message | activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md | medium |  |
| Network error occurred before reaching the server. | message | activity-packages/gsuite-activities/playbooks/transient-and-timeout-errors.md | medium |  |
| Newtonsoft.Json.JsonReaderException | exception | activity-packages/web-activities/playbooks/deserialize-malformed-input.md | high | raised by DeserializeJson / DeserializeJsonArray — input string is not valid JSON (most often an upstream HTTP call returned an HTML/error body) |
| Newtonsoft.Json.JsonSerializationException | exception | activity-packages/web-activities/playbooks/deserialize-type-mismatch.md | medium | on DeserializeJson<T> — well-formed JSON whose shape does not fit the target type T |
| No available license / Agentic units to perform healing analysis and recovery | message | activity-packages/ui-automation/playbooks/healing-agent-no-license.md | high | Error-level robot log — the deterministic signal when the customer wants HA working; operation code HealingAgent vs HealingAgent.Test picks the consumable pool |
| No available license / Agentic units to perform healing analysis and recovery | message | activity-packages/ui-automation/playbooks/healing-agent-orch-issues.md | high | Surface 4 informational notice — benign if customer does NOT want HA (job continues); if they DO want HA it is the real licensing error → healing-agent-no-license.md |
| No compiled code to run | message | activity-packages/classic-activities/playbooks/invoke-code-failed.md | medium |  |
| No condition for an outgoing flow was met | message | products/maestro/playbooks/gateway-no-outgoing-flow.md | high |  |
| No default connection is available. | message | activity-packages/o365-activities/playbooks/authentication-token-invalid.md | medium |  |
| No email matching the filter criteria, received in the last 1 hour has been found | message | activity-packages/gsuite-activities/playbooks/get-newest-email-not-found.md | high | GmailException from the Gmail NewEmailReceived trigger in debug/test mode; the identical sentence as an Office365Exception → get-newest-email-no-match.md (o365) |
| No email matching the filter criteria, received in the last 1 hour has been found | message | activity-packages/o365-activities/playbooks/get-newest-email-no-match.md | high | Office365Exception from O365 GetNewestEmail (also WaitForEmailReceived / NewEmailReceived sample lookups); the identical sentence as a GmailException is the Gmail trigger debug run → get-newest-email-not-found.md (gsuite) |
| No email matching the filter criteria, sent in the last 1 hour has been found | message | activity-packages/gsuite-activities/playbooks/get-newest-email-not-found.md | high |  |
| No email matching the search criteria has been found | message | activity-packages/gsuite-activities/playbooks/get-newest-email-not-found.md | high |  |
| No File events found | message | products/maestro/playbooks/no-message-events.md | high | OneDrive/SharePoint file trigger variant |
| No host is available on the machine template assigned for this job | message | products/orchestrator/playbooks/job-pending-no-host.md | high |  |
| No Message events found | message | products/maestro/playbooks/no-message-events.md | high |  |
| No package resource with type 'Property' and key 'EMAIL_RECEIVED' was found | message | products/maestro/playbooks/deployment-email-received.md | high |  |
| No row in column | message | activity-packages/cv-activities/playbooks/cv-cell-targeting-failures.md | high | row-search value matched no cell in the search column |
| No such host is known | message | activity-packages/web-activities/playbooks/http-request-connection-failure.md | medium | DNS failure on modern .NET (targetFramework Windows, .NET 6+) |
| NodeNotFoundException | exception | activity-packages/ui-automation/playbooks/scope-container-wrong-page.md | medium | closest matches in the exception belong to a different page/locale — enclosing scope container attached wrong; the inner selector itself is correct |
| NodeNotFoundException | exception | activity-packages/ui-automation/playbooks/selector-failure-healing-disabled.md | high | Healing Agent disabled — AutopilotForRobots Enabled: false or HealingEnabled: false (or field absent) |
| NodeNotFoundException | exception | activity-packages/ui-automation/playbooks/selector-failure-healing-fix.md | high | HA enabled with recovery data present (healing-fixes.json entry or InferredRecoveryInfo/RecoveryInfo in uia/*.json) |
| NodeNotFoundException | exception | activity-packages/ui-automation/playbooks/selector-failure-manual.md | medium | HA enabled but no fix produced, or source code available for manual selector analysis |
| NodeNotFoundException | exception | activity-packages/ui-automation/playbooks/timeout-issue.md | low | element never appeared within the wait — activity duration close to the configured timeout |
| not found against object of type ExpressionDictionary | message | products/maestro/playbooks/expression-evaluation-errors.md | high |  |
| Object reference not set to an instance of an object | message | activity-packages/mail-activities/playbooks/send-outlook-mail-failures.md | medium | at Send Outlook Mail — null To/Subject/Body or empty attachment path (branch 3) |
| Object reference not set to an instance of an object | message | activity-packages/system-activities/playbooks/get-asset-activity-bug-silent-failure.md | medium | same downstream-consumer discriminator as the exception signature — the faulting activity is not the Get Asset itself |
| Object reference not set to an instance of an object | message | activity-packages/workflowevents-activities/playbooks/handle-app-request-null-reference.md | medium | at HandleAppRequest — failure is in the App-invoked workflow's execution, not the channel; downstream consumer of a null Get Asset output → get-asset-activity-bug-silent-failure.md |
| Object reference not set to an instance of an object | message | runtime-exceptions/playbooks/null-reference-exception.md | medium | member access on a null variable/expression in the user's workflow logic; upstream Get Asset silent-null → system-activities get-asset-activity-bug-silent-failure.md |
| Office365Exception | exception | activity-packages/o365-activities/playbooks/create-folder-invalid-path.md | high | generic O365 package exception — this claim is the Create Folder (CreateFolderConnections) input-validation family: null/empty name, path, or parent folder, empty or whitespace path segments, or a file occupying a segment |
| Office365Exception | exception | activity-packages/o365-activities/playbooks/download-file-conversion-or-destination.md | high | generic O365 package exception — this claim is the download/export surface on DownloadFileConnections / DownloadFile / ExportAsPdf: folder given where a file is required, unsupported PDF conversion source, bad local destination, or an unresolvable shared item's parent |
| Office365Exception | exception | activity-packages/o365-activities/playbooks/download-multiple-items-name-conflict.md | high | generic O365 package exception — this claim is the local-destination name conflict on download activities (DownloadEmailConnections / DownloadFileConnections / DownloadEmailAttachments with ConflictResolution = Fail) |
| Office365Exception | exception | activity-packages/o365-activities/playbooks/get-newest-email-no-match.md | high | generic O365 package exception — this claim is the GetNewestEmail empty-result fault (no email matched the configured filter) |
| Office365Exception | exception | activity-packages/o365-activities/playbooks/item-name-already-exists.md | high | generic O365 package exception — this claim is the remote OneDrive/SharePoint/Excel name conflict (Create/Copy/Move/Rename/Upload/Create Workbook/Add Sheet/Rename Sheet with ConflictBehavior = Fail) |
| One or more errors occurred | message | activity-packages/python-activities/playbooks/invoke-method-failures.md | medium | on Invoke Python Method with a Python traceback naming a line inside the function (M4); at Python Scope open → python-scope-architecture-version-mismatch.md; at script load → load-script-failures.md |
| One or more errors occurred | message | activity-packages/python-activities/playbooks/load-script-failures.md | medium | at Load Python Script — wrapper around a script-layer load failure (L2); at engine init → python-scope-architecture-version-mismatch.md; on Invoke Python Method → invoke-method-failures.md |
| One or more errors occurred | message | activity-packages/python-activities/playbooks/python-scope-architecture-version-mismatch.md | medium | at Python Scope open, no Python traceback — engine init: Target bitness, Version, Library path, or missing .NET Desktop Runtime |
| OpenMode=Never | state | activity-packages/ui-automation/playbooks/application-not-found.md | high | gating condition — the scope was told not to launch the app |
| options can be set | message | activity-packages/classic-activities/playbooks/ui-activity-configuration-error.md | high | tail of 'Only one of the {0} and {1} options can be set.' — two mutually exclusive options enabled |
| Orchestrator information is not available | message | activity-packages/system-activities/playbooks/get-asset-network-connectivity.md | low |  |
| OutRegion = (0,0,0,0) | state | activity-packages/cv-activities/playbooks/cv-action-failed-after-find.md | medium | no error but empty OutRegion — click/clipboard failure swallowed post-find (window moved, focus stolen, input blocked) |
| OutRegion = (0,0,0,0) | state | activity-packages/cv-activities/playbooks/cv-silent-failures-and-false-results.md | medium | default empty Rectangle output after a swallowed exception (ContinueOnError or Element Exists conversion) — downstream consumers get garbage |
| outside the range: 0 to | message | activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md | medium | covers 'RelativeRowIndex <i> outside the range: 0 to <n>.' and 'RelativeColumnIndex <i> outside the range: 0 to <n>.' from Write Row/Column overwrite bounds |
| Package entry points definition is invalid | message | products/maestro/playbooks/deployment-datetime-input.md | high | deployment fails after adding DateTime input parameters to a BPMN start event |
| Pending | state | products/orchestrator/playbooks/job-pending-no-host.md | high | assigned template currently has zero connected runtimes (robotVersions empty) — if a runtime IS connected, see job-pending-stale-dispatch.md |
| Pending | state | products/orchestrator/playbooks/job-pending-stale-dispatch.md | high | no-host-family PendingReasons.Errors BUT robotVersions populated AND JobHistory contains only the original Pending entry |
| Pending | state | products/orchestrator/playbooks/robot-credentials.md | high | with PendingReason RobotNoMatchingUsernames or TemplateNoLicense — robot/machine configuration, not host availability |
| Permission to the resource was denied. | message | activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md | medium |  |
| Pipe is broken | message | activity-packages/python-activities/playbooks/invoke-python-method-pipe-is-broken.md | medium | Python host process died — missing pip module in the scope's interpreter, unhandled script exception, hard exit, or stdout flood |
| Please make sure you have UiPath.ComputerVision.LocalServer package installed | message | activity-packages/cv-activities/playbooks/cv-scope-setup-failures.md | medium |  |
| Please select an account. | message | activity-packages/o365-activities/playbooks/application-scope-misconfigured.md | medium |  |
| Possible loop detected | message | products/maestro/playbooks/loop-detected.md | high |  |
| Programmatic access to Office VBA project is denied | message | activity-packages/excel-activities/playbooks/invoke-vba-trust-access.md | high |  |
| Programmatic access to Visual Basic Project is not trusted | message | activity-packages/excel-activities/playbooks/invoke-vba-trust-access.md | high |  |
| provider is not registered on the local machine | message | activity-packages/database-activities/playbooks/connect-to-database-failures.md | medium |  |
| quotaLimitReached | error-code | activity-packages/o365-activities/playbooks/upload-file-quota-or-size.md | medium |  |
| rateLimitExceeded | error-code | activity-packages/gsuite-activities/playbooks/transient-and-timeout-errors.md | medium |  |
| Reason: Invalid image reference or value | message | activity-packages/cv-activities/playbooks/cv-invalid-descriptor.md | high |  |
| Reason: Target must be set | message | activity-packages/cv-activities/playbooks/cv-invalid-descriptor.md | high |  |
| Recommendations for resolution or self-healing procedures have been quickly generated | message | activity-packages/ui-automation/playbooks/healing-agent-orch-issues.md | high | email/in-app Notification Summary, Component = Healing Agent — real HA event |
| Reference is not valid | message | activity-packages/excel-activities/playbooks/lookup-range-invalid-range.md | medium |  |
| REGDB_E_CLASSNOTREG | error-code | activity-packages/word-activities/playbooks/word-scope-com-not-installed.md | high | no usable desktop Word for Interop at Word Application Scope startup |
| Request deadline exceeded. | message | activity-packages/gsuite-activities/playbooks/transient-and-timeout-errors.md | medium |  |
| Request time out. | message | activity-packages/o365-activities/playbooks/transient-service-error.md | medium |  |
| Request to Integration Services failed with status code '400' | message | products/maestro/playbooks/integration-service-400.md | medium |  |
| Request to Integration Services failed with status code '404' | message | products/maestro/playbooks/integration-service-404.md | medium |  |
| RequestBroker--ParseUri | error-code | activity-packages/o365-activities/playbooks/mail-invalid-odata-query.md | high |  |
| Requested URL is invalid, value is null. | message | activity-packages/ui-automation/playbooks/browser-navigation-failed.md | medium |  |
| Required argument 'Saved image' was not provided. | message | activity-packages/ui-automation/playbooks/activity-configuration-error.md | high |  |
| Required argument 'Script code' was not provided. | message | activity-packages/ui-automation/playbooks/inject-js-failed.md | medium |  |
| Required argument 'URL' was not provided. | message | activity-packages/ui-automation/playbooks/browser-navigation-failed.md | medium |  |
| requires a processor that accepts AVX2 instructions. | message | activity-packages/cv-activities/playbooks/cv-scope-setup-failures.md | medium |  |
| requires Microsoft Visual C++ Redistributable 2015-2022 for X64. | message | activity-packages/cv-activities/playbooks/cv-scope-setup-failures.md | medium |  |
| Response from server is not valid. | message | activity-packages/cv-activities/playbooks/cv-server-auth-throttling-network.md | medium | generic fall-through masking transport errors — the real cause is in the trace, not the surfaced message |
| Retrieving the COM class factory for component with CLSID {000209FF-0000-0000-C000-000000000046} failed | message | activity-packages/word-activities/playbooks/word-scope-com-not-installed.md | high | CLSID of Word.Application — COM class factory unavailable |
| Retrieving the COM class factory for component with CLSID {00024500-0000-0000-C000-000000000046} failed | message | activity-packages/excel-activities/playbooks/lookup-range-excel-not-installed.md | high |  |
| RobotNoMatchingUsernames | error-code | products/orchestrator/playbooks/robot-credentials.md | high | robot user account does not match any machine user mapping |
| Running | state | products/maestro/playbooks/service-task-child-job-faulted.md | high | instance stuck Running with an Open incident — not a plain long-runner |
| Running | state | products/orchestrator/playbooks/job-stuck.md | low | unusually long with no progress visible in job traces — distinct from the Pending-state playbooks |
| RuntimeTimeoutException | exception | activity-packages/ui-automation/playbooks/timeout-issue.md | low |  |
| Scrolled the entire screen, but element was not found | message | activity-packages/cv-activities/playbooks/cv-scroll-search-failures.md | medium | hardcoded English, never localized — the word Scrolled is the discriminator from plain Element not found |
| Searched element Target or Input UI Element must be set when Scroll type is set to Until element is found. | message | activity-packages/ui-automation/playbooks/activity-configuration-error.md | high |  |
| SelectorNotFoundException | exception | activity-packages/classic-activities/playbooks/ui-element-not-found.md | medium | faulting activity is a CLASSIC UI activity (Click, Type Into, Attach — UiPath.Core.Activities); modern N-prefixed activities → ui-automation selector-failure playbooks (Healing Agent applies there, never to classic) |
| SelectorNotFoundException | exception | activity-packages/ui-automation/playbooks/scope-container-wrong-page.md | medium | closest matches in the exception belong to a different page/locale — enclosing scope container attached wrong; the inner selector itself is correct |
| SelectorNotFoundException | exception | activity-packages/ui-automation/playbooks/selector-failure-healing-disabled.md | high | Healing Agent disabled — AutopilotForRobots Enabled: false or HealingEnabled: false (or field absent) |
| SelectorNotFoundException | exception | activity-packages/ui-automation/playbooks/selector-failure-healing-fix.md | high | HA enabled with recovery data present (healing-fixes.json entry or InferredRecoveryInfo/RecoveryInfo in uia/*.json) |
| SelectorNotFoundException | exception | activity-packages/ui-automation/playbooks/selector-failure-manual.md | medium | HA enabled but no fix produced, or source code available for manual selector analysis |
| Server or OCR engine is required. | message | activity-packages/cv-activities/playbooks/cv-scope-setup-failures.md | medium |  |
| Server URL is empty and UseLocalServer option is false | message | activity-packages/cv-activities/playbooks/cv-server-auth-throttling-network.md | medium |  |
| SignalR connection did not establish within 60 seconds | message | activity-packages/workflowevents-activities/playbooks/app-request-trigger-connection-lost.md | medium |  |
| SignalR: Invalid SessionId | message | activity-packages/workflowevents-activities/playbooks/initialize-hub-connection-aggregate-failure.md | medium |  |
| storageQuotaExceeded | error-code | activity-packages/gsuite-activities/playbooks/upload-storage-quota-exceeded.md | high |  |
| Strings.NodeNotFoundMultipleMatches | message-key | activity-packages/ui-automation/playbooks/ambiguous-selector.md | high |  |
| Sub or Function not defined | message | activity-packages/excel-activities/playbooks/invoke-vba-code-file-path.md | medium | raised while compiling the injected module — code file malformed or statements outside a procedure block; file compiles but the named entry point does not resolve → invoke-vba-entry-method-name.md |
| Sub or Function not defined | message | activity-packages/excel-activities/playbooks/invoke-vba-entry-method-name.md | high | at Application.Run — the named entry point is not a top-level Public Sub/Function in the loaded file; compile failure of the file itself → invoke-vba-code-file-path.md |
| Success | state | activity-packages/database-activities/playbooks/start-transaction-failures.md | medium | job green but database unchanged/partial (child fault swallowed, no rollback — branch 1) or no in-scope activity logs at all (v1.5.0 body-skip — branch 2) |
| System.AggregateException | exception | activity-packages/web-activities/playbooks/net-http-request-aggregate-failure.md | medium | on UiPath.Web.Activities.NetHttpRequest (modern HTTP Request) — async pipeline wrapper; the InnerException is the real cause |
| System.AggregateException | exception | activity-packages/workflowevents-activities/playbooks/initialize-hub-connection-aggregate-failure.md | medium | at InitializeHubConnection in a Studio Web app-workflow run — SignalR hub bootstrap failed; unwrap the inner exception; connector activity stacks → connector-aggregate-exception.md |
| System.AggregateException | exception | products/integration-service/playbooks/connector-aggregate-exception.md | low | async wrapper on a connector activity stack — the real error is InnerExceptions[0]; route on the inner exception |
| System.ArgumentException | exception | activity-packages/cv-activities/playbooks/cv-scope-setup-failures.md | medium | scope-entry fault before any child CV activity ran — LocalServer missing or local-server prerequisite; the faulted activity in XAML is the CV Screen Scope itself |
| System.ArgumentException | exception | activity-packages/cv-activities/playbooks/cv-server-auth-throttling-network.md | medium | built by CVSessionData.Compute / ToErrorMessageWithCode() with [Error code: N] text — surfaces lazily on a child's first refresh, not at scope entry |
| System.ArgumentException | exception | activity-packages/database-activities/playbooks/connect-to-database-failures.md | medium | on Connect to Database with initialization-string / invalid-connection-string wording (branch 1) — the class alone is too generic to route on; CV scope/server ArgumentException → cv-activities playbooks |
| System.ArgumentNullException | exception | activity-packages/cv-activities/playbooks/cv-action-failed-after-find.md | medium | parameter name Secure — CV Type Into with a null SecureString, thrown before any keystroke |
| System.ArgumentNullException | exception | activity-packages/o365-activities/playbooks/copy-item-argument-null.md | high | raw, from legacy O365 CopyItem with Parameter 'DriveItem' — upstream lookup left the DriveItem input null |
| System.ArgumentNullException | exception | activity-packages/web-activities/playbooks/deserialize-null-input.md | high | on DeserializeJson — input guard for null/empty JsonString; parameter name 'JSON string' |
| System.ArgumentNullException | exception | runtime-exceptions/playbooks/argument-null-exception.md | medium | user-code activity stack, not a UiPath framework namespace — a null argument passed by the user's workflow logic |
| System.DllNotFoundException | exception | activity-packages/database-activities/playbooks/execute-non-query-failures.md | medium |  |
| System.IndexOutOfRangeException | exception | products/maestro/playbooks/index-out-of-bounds.md | low |  |
| System.InvalidCastException | exception | activity-packages/excel-activities/playbooks/excel-application-scope-failures.md | medium | cast of System.__ComObject to a Microsoft.Office.Interop.Excel interface fails with E_NOINTERFACE — COM add-in clash (branch 3); marshaling EntryMethodParameters on Invoke VBA → invoke-vba-parameter-formatting.md |
| System.InvalidCastException | exception | activity-packages/excel-activities/playbooks/invoke-vba-parameter-formatting.md | medium | marshaling EntryMethodParameters into Application.Run — expression is not an IEnumerable<Object>; QueryInterface E_NOINTERFACE on System.__ComObject → excel-application-scope-failures.md |
| System.InvalidCastException | exception | activity-packages/mail-activities/playbooks/send-outlook-mail-failures.md | medium | binding the Outlook COM server at Send Outlook Mail — Outlook not installed / bitness mismatch / corrupted Office registry (branch 1) |
| System.InvalidOperationException | exception | activity-packages/database-activities/playbooks/connect-to-database-failures.md | medium | on Connect to Database with the ACE/Jet OLE DB provider-not-registered wording (branch 2) — the class alone is too generic to route on |
| System.InvalidOperationException | exception | activity-packages/workflowevents-activities/playbooks/app-request-trigger-connection-lost.md | medium | at AppRequestTrigger — SignalR client driven in a non-connected/disposed state; discriminator is the faulted activity |
| System.InvalidOperationException | exception | products/orchestrator/playbooks/foreground-already-running.md | medium | only with the foreground-process-already-running message — the class alone is too generic to route on |
| System.IO.DirectoryNotFoundException | exception | activity-packages/excel-activities/playbooks/read-range-file-not-found.md | medium | at Excel workbook open — a segment of the WorkbookPath's parent path does not exist (wrong CWD, unmapped drive, unreachable share) |
| System.IO.FileNotFoundException | exception | activity-packages/excel-activities/playbooks/read-range-file-not-found.md | medium | at Excel workbook open — configured WorkbookPath's parent directory exists but the file does not |
| System.IO.FileNotFoundException | exception | activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md | medium | generic .NET exception — this claim is a GSuite activity's local path miss (legacy SendEmail attachment, upload source, service-account key file); at Excel workbook open → read-range-file-not-found.md (excel) |
| System.IO.IOException | exception | activity-packages/excel-activities/playbooks/read-range-file-locked.md | medium | on Read Range / Excel read-write family or the surrounding scope — cannot acquire the workbook file; pass-through .NET IO message names the path |
| System.IO.IOException | exception | activity-packages/excel-activities/playbooks/write-cell-failures.md | medium | on Write Cell — file lock or Classic Workbook Write Cell racing an open Excel scope on the same path (branch 1); Read Range surface → read-range-file-locked.md |
| System.IO.IOException | exception | activity-packages/python-activities/playbooks/invoke-python-method-pipe-is-broken.md | medium | generic .NET — surfaces as 'RemoteException wrapping System.IO.IOException: Pipe is broken' on Invoke Python Method / Run Python Script |
| System.IO.IOException | exception | activity-packages/workflowevents-activities/playbooks/app-request-trigger-connection-lost.md | medium | at AppRequestTrigger — SignalR/RobotJS transport dropped while awaiting an App request; discriminator is the faulted activity |
| System.IO.PipeException | exception | activity-packages/python-activities/playbooks/invoke-method-failures.md | medium | mid-call on Invoke Python Method — oversized return payload or destabilized engine (M5); 'Pipe is broken' wording → invoke-python-method-pipe-is-broken.md |
| System.Net.Http.HttpRequestException | exception | activity-packages/web-activities/playbooks/net-http-request-aggregate-failure.md | medium | inner exception of NetHttpRequest's AggregateException — transport/HTTP failure after retries (DNS, connection refused, TLS, exhausted status retries) |
| System.Net.WebException | exception | activity-packages/web-activities/playbooks/http-request-connection-failure.md | medium | on UiPath.Web.Activities.HttpClient — status / DNS / connection / TLS failure; message 'The operation has timed out.' → http-request-timeout.md |
| System.NullReferenceException | exception | activity-packages/cv-activities/playbooks/cv-scope-setup-failures.md | medium | raw, no message — a child CV activity executed outside a CV Screen Scope at runtime (design-time validation bypassed) |
| System.NullReferenceException | exception | activity-packages/database-activities/playbooks/execute-query-failures.md | medium | raised at Execute Query — null / expired / out-of-scope DatabaseConnection (branch 1) |
| System.NullReferenceException | exception | activity-packages/excel-activities/playbooks/append-range-failures.md | medium | raised at Append Range — source DataTable argument is Nothing (branch 4) |
| System.NullReferenceException | exception | activity-packages/excel-activities/playbooks/lookup-range-null-reference.md | medium | at Lookup Range resolving its target — sheet name absent from the workbook, undefined named range/table, or activity outside any Excel scope |
| System.NullReferenceException | exception | activity-packages/excel-activities/playbooks/read-range-null-reference.md | low | from inside UiPath.Excel.Activities / DocumentFormat.OpenXml parsing after the workbook opened — sensitivity label, structural corruption, broken named range, unsupported OpenXML feature, or scale (low-confidence multi-branch) |
| System.NullReferenceException | exception | activity-packages/excel-activities/playbooks/write-range-failures.md | medium | raised at Write Range — source DataTable argument is Nothing (branch 1) |
| System.NullReferenceException | exception | activity-packages/mail-activities/playbooks/send-outlook-mail-failures.md | medium | raised at Send Outlook Mail — uninitialized To/Subject/Body variable or empty attachment path (branch 3) |
| System.NullReferenceException | exception | activity-packages/o365-activities/playbooks/legacy-mail-null-reference.md | medium | raw, with stack frames in UiPath.MicrosoftOffice365.Activities.Mail.* (legacy) — Connections activities remap it to 'The object used in the activity does not exist.' |
| System.NullReferenceException | exception | activity-packages/python-activities/playbooks/invoke-method-failures.md | medium | on Invoke Python Method — Instance not bound to a successful Load Python Script result (M6) |
| System.NullReferenceException | exception | activity-packages/system-activities/playbooks/get-asset-activity-bug-silent-failure.md | medium | thrown by a DOWNSTREAM consumer of a value an upstream Get Asset / Get Orchestrator Asset produced as null/empty with NO error of its own — check UiPath.System.Activities version (22.10.x Ctrl+K bug); plain null in user workflow logic → runtime-exceptions null-reference-exception.md |
| System.NullReferenceException | exception | activity-packages/web-activities/playbooks/deserialize-null-input.md | high | on DeserializeJsonArray — no null-input guard, a null JsonString hits JArray.Parse directly |
| System.NullReferenceException | exception | activity-packages/web-activities/playbooks/http-client-null-reference.md | medium | on UiPath.Web.Activities.HttpClient — a request input (EndPoint, header, cookie, parameter, body) resolved null during request building; no HTTP status or transport phrase in the message |
| System.NullReferenceException | exception | activity-packages/workflowevents-activities/playbooks/handle-app-request-null-reference.md | medium | faulted activity is HandleAppRequest in a UiPath-App-invoked job — the NRE is raised inside the App-invoked workflow or by a null App input argument; generic in-workflow NRE → null-reference-exception.md |
| System.NullReferenceException | exception | products/integration-service/playbooks/connector-null-reference.md | medium | on or just after a connector activity — stack shows a ForEach over an IntegrationService SWEntities output; for user-code NREs see null-reference-exception.md |
| System.NullReferenceException | exception | runtime-exceptions/playbooks/null-reference-exception.md | medium | user-code workflow stack, not a UiPath package namespace — on a connector activity (SWEntities ForEach) see connector-null-reference.md; null traces back to an upstream Get Asset/Get Credential that logged no error → system-activities get-asset-activity-bug-silent-failure.md |
| System.OutOfMemoryException | exception | activity-packages/excel-activities/playbooks/write-range-failures.md | medium | oversized DataTable written in one call via Excel COM (branch 5) |
| System.Reflection.TargetInvocationException | exception | activity-packages/excel-activities/playbooks/read-range-null-reference.md | low | reflection wrapper from Excel Read Range parsing — unwrap the InnerException and re-categorize |
| System.Reflection.TargetInvocationException | exception | activity-packages/word-activities/playbooks/replace-text-version-mismatch.md | medium | design-time — Studio errors on dropping Replace Text / opening the workflow; Studio vs UiPath.Word.Activities version mismatch |
| System.Runtime.InteropServices.COMException | exception | activity-packages/excel-activities/playbooks/write-cell-failures.md | medium | on Write Cell — protected sheet or read-only workbook (branch 5); Word Export to PDF surface → export-pdf-com-hang.md |
| System.Runtime.InteropServices.COMException | exception | activity-packages/word-activities/playbooks/export-pdf-com-hang.md | medium | at Export to PDF / Save Document as PDF — orphaned WINWORD.EXE or locked input document; 'Command failed' on open with a SharePoint link → word-open-sharepoint-url-com-command-failed.md |
| System.Runtime.InteropServices.COMException | exception | activity-packages/word-activities/playbooks/word-open-sharepoint-url-com-command-failed.md | medium | message 'Command failed' faulting on Documents.Open — FilePath is a SharePoint/OneDrive sharing link; at Export to PDF with an orphaned/locked WINWORD.EXE → export-pdf-com-hang.md |
| System.Threading.Tasks.TaskCanceledException | exception | activity-packages/web-activities/playbooks/net-http-request-aggregate-failure.md | medium | inner exception of NetHttpRequest's AggregateException — request exceeded TimeoutInMiliseconds |
| System.TimeoutException | exception | activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md | medium | GSuite auth-phase only — 'Authentication attempt took longer than <N> seconds' wording during connection/OAuth token acquisition; per-request timeouts cancel as 'A task was canceled.' instead |
| System.TimeoutException | exception | activity-packages/web-activities/playbooks/http-request-timeout.md | medium | on legacy .NET Framework HttpClient when RestSharp reports TimedOut; modern .NET surfaces WebException with the same message |
| System.TimeoutException | exception | activity-packages/workflowevents-activities/playbooks/app-request-trigger-connection-lost.md | medium | at AppRequestTrigger in a UiPath-App-invoked job — App↔robot SignalR channel never connected; HTTP-request timeouts → http-request-timeout.md |
| System.Xml.XmlException | exception | activity-packages/web-activities/playbooks/deserialize-malformed-input.md | high | raised by DeserializeXml (XDocument.Parse) — input string is not valid XML |
| Table does not have any column with column name containing | message | activity-packages/cv-activities/playbooks/cv-cell-targeting-failures.md | high |  |
| Table only contains | message | activity-packages/cv-activities/playbooks/cv-cell-targeting-failures.md | high | covers the columns / rows / cell-number out-of-range variants |
| TargetFoundButNotVisibleException | exception | activity-packages/ui-automation/playbooks/element-found-not-actionable.md | medium |  |
| TargetNotFoundBrowserBlockedException | exception | activity-packages/ui-automation/playbooks/element-found-not-actionable.md | medium |  |
| TemplateNoHostsAvailable | error-code | products/orchestrator/playbooks/job-pending-stale-dispatch.md | high | stale dispatch-time snapshot — template currently reports a connected runtime (robotVersions populated) |
| TemplateNoLicense | error-code | products/orchestrator/playbooks/robot-credentials.md | high | machine template has zero Unattended runtime slots allocated |
| The action is not allowed by the system. | message | activity-packages/o365-activities/playbooks/insufficient-graph-scope.md | high |  |
| The app or user has been throttled. | message | activity-packages/o365-activities/playbooks/request-throttled.md | high |  |
| The application called an interface that was marshalled for a different thread | message | activity-packages/word-activities/playbooks/word-export-pdf-com-wrong-thread.md | medium |  |
| The asset does not have a value associated with this robot | message | activity-packages/system-activities/playbooks/get-asset-per-robot-no-value.md | high |  |
| The authentication parameters could not be read | message | activity-packages/o365-activities/playbooks/application-scope-misconfigured.md | medium |  |
| The caller doesn't have permission to perform the action. | message | activity-packages/o365-activities/playbooks/insufficient-graph-scope.md | high |  |
| The caller is not authenticated. | message | activity-packages/o365-activities/playbooks/authentication-token-invalid.md | medium |  |
| The cell reference | message | activity-packages/excel-activities/playbooks/write-cell-failures.md | medium | BusinessException 'The cell reference ... is invalid' — malformed A1 notation or unknown named range on Write Cell (branch 6) |
| The client did not complete the authentication after | message | activity-packages/o365-activities/playbooks/authentication-token-invalid.md | medium | with InteractiveToken authentication wording — mid-run sign-in never completed (unattended/Agent context) |
| The Client ID or Client Secret is incorrect. | message | products/integration-service/playbooks/connector-remote-exception.md | medium |  |
| The current state conflicts with what the request expects. | message | activity-packages/gsuite-activities/playbooks/transient-and-timeout-errors.md | medium |  |
| The data you want to write has a wrong format, or Excel is busy | message | activity-packages/excel-activities/playbooks/write-cell-failures.md | medium | on Write Cell — rejected formula syntax (branch 2) or loop-induced Excel COM thrash (branch 3); on Write Range → write-range-failures.md |
| The data you want to write has a wrong format, or Excel is busy | message | activity-packages/excel-activities/playbooks/write-range-failures.md | medium | on Write Range — oversized batch or formula-prefix cell values (branch 5); on Write Cell → write-cell-failures.md |
| The domain administrators have disabled Drive apps. | message | activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md | medium |  |
| The file appears to be corrupted | message | activity-packages/word-activities/playbooks/word-scope-file-corrupted.md | medium |  |
| The file is read-only | message | activity-packages/word-activities/playbooks/replace-text-file-locked.md | medium | read-only attribute or locked target when the Word scope persists the edit |
| The file limit for this shared drive has been exceeded. | message | activity-packages/gsuite-activities/playbooks/upload-storage-quota-exceeded.md | high |  |
| The folder does not exist | message | activity-packages/mail-activities/playbooks/move-outlook-mail-failures.md | medium | deterministic every-run at Move — destination folder path / Account mismatch (branch 2) |
| The identified element does not belong to the target application/browser. | message | activity-packages/ui-automation/playbooks/wrong-target-application.md | high |  |
| The job's associated process could not be found | message | products/maestro/playbooks/process-not-found-404.md | high |  |
| The macro ' | message | activity-packages/excel-activities/playbooks/invoke-vba-entry-method-name.md | high |  |
| The message filter indicated that the application is busy | message | activity-packages/word-activities/playbooks/replace-text-com-busy.md | medium | at Replace Text / Read Text inside a Word scope — WINWORD.EXE busy, locked, or stalled on a hidden modal dialog |
| The network path was not found | message | activity-packages/excel-activities/playbooks/read-range-file-not-found.md | medium | UNC workbook path — share unreachable from the Robot host |
| The object used in the activity does not exist. | message | activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md | medium |  |
| The operation failed | message | activity-packages/mail-activities/playbooks/move-outlook-mail-failures.md | medium | intermittent at Move Outlook Mail Message — COM session loss (branch 1); followed by 'An object could not be found' → delete-outlook-mail-failures.md |
| The operation failed. An object could not be found. | message | activity-packages/mail-activities/playbooks/delete-outlook-mail-failures.md | medium | stale message reference — item moved/deleted between Get and Delete (branch 1) |
| The operation has timed out | message | activity-packages/mail-activities/playbooks/delete-outlook-mail-failures.md | medium | at Delete Outlook Mail — COM blocked by a modal programmatic-access dialog or privilege mismatch (branch 4); on Get → get-outlook-mail-failures.md |
| The operation has timed out | message | activity-packages/mail-activities/playbooks/get-outlook-mail-failures.md | medium | at Get Outlook Mail Messages — large folder vs TimeoutMS (branch 2); on Delete → delete-outlook-mail-failures.md |
| The operation has timed out | message | activity-packages/web-activities/playbooks/http-request-timeout.md | medium | on HttpClient exceeding TimeoutMS — surfaces as WebException on modern .NET, TimeoutException on legacy; match the message, not the type |
| The Outlook application is not running | message | activity-packages/mail-activities/playbooks/get-outlook-mail-failures.md | medium | COM session broken / no running Outlook for the Robot's user (branch 3) |
| The process cannot access the file because it is being used by another process | message | activity-packages/word-activities/playbooks/replace-text-file-locked.md | medium | Word scope save — Auto Save racing another access, a concurrent job, or a sync/AV client holding the handle |
| The range is invalid | message | activity-packages/excel-activities/playbooks/delete-range-failures.md | medium |  |
| The remote name could not be resolved | message | activity-packages/web-activities/playbooks/http-request-connection-failure.md | medium | DNS failure on legacy .NET Framework |
| The remote server returned an error | message | activity-packages/web-activities/playbooks/http-request-connection-failure.md | medium |  |
| The requested data exceeds the maximum payload accepted by the server. | message | activity-packages/cv-activities/playbooks/cv-server-auth-throttling-network.md | medium |  |
| The resource could not be found. | message | activity-packages/o365-activities/playbooks/drive-item-not-found.md | high | raised by a OneDrive/SharePoint Files activity — for Mail activities the same sentence means a missing folder (mail-folder-not-found) or message (mail-message-not-found) |
| The resource could not be found. | message | activity-packages/o365-activities/playbooks/mail-folder-not-found.md | high | raised by a Mail activity resolving a MailFolder argument — on Drive activities → drive-item-not-found, on message-by-ID activities → mail-message-not-found |
| The resource could not be found. | message | activity-packages/o365-activities/playbooks/mail-message-not-found.md | high | raised by a Mail activity that addresses a specific message ID — folder-argument activities → mail-folder-not-found, Drive activities → drive-item-not-found |
| The resource was not found. | message | activity-packages/gsuite-activities/playbooks/drive-file-not-found.md | high |  |
| The Select methods only work on editable text | message | activity-packages/cv-activities/playbooks/cv-get-text-empty-or-wrong-result.md | medium | design-time warning — clipboard mode on a non-editable target |
| The server is unable to process the current request. | message | activity-packages/o365-activities/playbooks/transient-service-error.md | medium |  |
| The service is currently unavailable. Please try again later. | message | activity-packages/gsuite-activities/playbooks/transient-and-timeout-errors.md | medium |  |
| The sheet with the name | message | activity-packages/excel-activities/playbooks/read-range-sheet-not-found.md | medium | legacy Excel Application Scope family — configured SheetName matches no sheet in the workbook; the write-side playbooks pivot here for the same signature |
| The Size property has an invalid size of 0 | message | activity-packages/database-activities/playbooks/execute-non-query-failures.md | medium |  |
| The source file does not exist. | message | activity-packages/classic-activities/playbooks/file-operation-failed.md | medium |  |
| The specified Computer Vision server | message | activity-packages/cv-activities/playbooks/cv-server-auth-throttling-network.md | medium | covers the 403 variant with the server name and the 502/503/504/408 could-not-be-reached variant |
| The specified folder does not exist | message | activity-packages/mail-activities/playbooks/get-outlook-mail-failures.md | medium | at Get Outlook Mail Messages — MailFolder/Account not resolved (branch 1); intermittent / unattended-only on Move → move-outlook-mail-failures.md |
| The specified folder does not exist | message | activity-packages/mail-activities/playbooks/move-outlook-mail-failures.md | medium | intermittent or unattended-only at Move — COM session loss (branch 1); deterministic on Get → get-outlook-mail-failures.md |
| The specified item name already exists. | message | activity-packages/o365-activities/playbooks/item-name-already-exists.md | high |  |
| The specified object was not found in the store. | message | activity-packages/o365-activities/playbooks/mail-message-not-found.md | high |  |
| The specified Python path is not valid | message | activity-packages/python-activities/playbooks/load-script-failures.md | medium | surfacing at Load Python Script (first scope child) — engine init, scope Path misconfigured (L1a); dedicated diagnostic → python-path-not-valid.md |
| The specified Python path is not valid | message | activity-packages/python-activities/playbooks/python-path-not-valid.md | high | at Python Scope open — Path points at python.exe or the WindowsApps Store alias instead of the install folder |
| The specified shared item does not exist. | message | activity-packages/o365-activities/playbooks/drive-item-not-found.md | high |  |
| The string argument cannot be empty | message | activity-packages/excel-activities/playbooks/delete-range-failures.md | medium |  |
| The target container does not have any items. | message | activity-packages/ui-automation/playbooks/select-item-no-items.md | medium |  |
| The target element is disabled. Operation canceled. | message | activity-packages/ui-automation/playbooks/disabled-element.md | high |  |
| The target Element was not specified for this activity | message | activity-packages/classic-activities/playbooks/ui-activity-configuration-error.md | high |  |
| The target Element was not specified for this activity. | message | activity-packages/cv-activities/playbooks/cv-action-failed-after-find.md | medium | post-find variant — a child's find succeeded, then the action failed. Scope-entry variant (no child ran) → cv-scope-setup-failures.md |
| The target Element was not specified for this activity. | message | activity-packages/cv-activities/playbooks/cv-scope-setup-failures.md | medium | scope-entry variant — no child ran; root-selector COMException on a matched window or a genuinely null scope Target. Post-find variant → cv-action-failed-after-find.md |
| The type initializer for 'Microsoft.Data.SqlClient.SqlConnection' threw an exception | message | activity-packages/database-activities/playbooks/connect-to-database-failures.md | medium | connection open with empty or SqlClient ProviderName after Windows-Legacy → Windows migration (branch 4); reached through a Start Transaction scope → start-transaction-failures.md |
| The type initializer for 'Microsoft.Data.SqlClient.SqlConnection' threw an exception | message | activity-packages/database-activities/playbooks/start-transaction-failures.md | medium | reached through a Start Transaction scope after Windows-Legacy → Windows migration, or DatabaseConnection type unresolvable at design time (branch 3); on a plain Connect to Database → connect-to-database-failures.md |
| The UI element is invalid. Make sure the target application is open and the element is on the screen. | message | activity-packages/ui-automation/playbooks/element-found-not-actionable.md | medium |  |
| The UiElement is not initialized | message | activity-packages/classic-activities/playbooks/ui-activity-configuration-error.md | high |  |
| The unattended robot has the wrong machine credentials to execute the job | message | products/orchestrator/playbooks/robot-credentials.md | high |  |
| The user does not have sufficient permissions for the file. | message | activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md | medium |  |
| The user has reached their quota limit. | message | activity-packages/o365-activities/playbooks/upload-file-quota-or-size.md | medium |  |
| The user's Drive storage quota has been exceeded. | message | activity-packages/gsuite-activities/playbooks/upload-storage-quota-exceeded.md | high |  |
| There was an error on the email server. Please try modifying your Query or Top values to continue. | message | activity-packages/o365-activities/playbooks/transient-service-error.md | medium |  |
| This action would increase the number of cells in the workbook above the limit of 10000000 cells | message | activity-packages/gsuite-activities/playbooks/sheets-cell-limit-exceeded.md | high |  |
| Timeout period elapsed prior to completion of the operation | message | activity-packages/database-activities/playbooks/execute-query-failures.md | medium |  |
| TimeoutException | exception | activity-packages/ui-automation/playbooks/timeout-issue.md | low | classic activities — ambiguous; only follow this playbook if the faulted activity is a UI automation type |
| Too many requests. | message | activity-packages/o365-activities/playbooks/request-throttled.md | high |  |
| Type mismatch | message | activity-packages/excel-activities/playbooks/invoke-vba-parameter-formatting.md | medium |  |
| TYPE_E_LIBNOTREGISTERED | error-code | activity-packages/mail-activities/playbooks/send-outlook-mail-failures.md | medium | Outlook COM type library not registered (branch 1) |
| UiElementNotFoundException | exception | activity-packages/ui-automation/playbooks/scope-container-wrong-page.md | medium | closest matches in the exception belong to a different page/locale — enclosing scope container attached wrong; the inner selector itself is correct |
| UiElementNotFoundException | exception | activity-packages/ui-automation/playbooks/selector-failure-healing-disabled.md | high | Healing Agent disabled — AutopilotForRobots Enabled: false or HealingEnabled: false (or field absent) |
| UiElementNotFoundException | exception | activity-packages/ui-automation/playbooks/selector-failure-healing-fix.md | high | HA enabled with recovery data present (healing-fixes.json entry or InferredRecoveryInfo/RecoveryInfo in uia/*.json) |
| UiElementNotFoundException | exception | activity-packages/ui-automation/playbooks/selector-failure-manual.md | medium | HA enabled but no fix produced, or source code available for manual selector analysis |
| UiNodeHasNoItemsException | exception | activity-packages/ui-automation/playbooks/select-item-no-items.md | medium |  |
| UiNodeUninitializedElementException | exception | activity-packages/ui-automation/playbooks/element-found-not-actionable.md | medium |  |
| UiPath.ConnectionClient.Contracts.ConnectionHttpException | exception | activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md | medium | GSuite token fetch / Integration Service connection resolution — on O365 Mail triggers → email-trigger-connection-event-failure.md (o365) |
| UiPath.ConnectionClient.Contracts.ConnectionHttpException | exception | activity-packages/o365-activities/playbooks/email-trigger-connection-event-failure.md | medium | from an O365 Mail trigger (NewEmailReceived / EmailSent) event, sample lookup, or token fetch — Office365Exception may carry the identical message; on GSuite activities → connection-and-auth-failures.md (gsuite) |
| UiPath.Core.Activities.OrchestratorCommunicationException | exception | activity-packages/system-activities/playbooks/get-asset-robot-not-authenticated.md | medium |  |
| UiPath.CoreIpc.RemoteException | exception | products/integration-service/playbooks/connector-remote-exception.md | medium | same phenomenon as UiPath.Ipc.RemoteException across two IPC library generations |
| UiPath.CV.ElementNotFoundException | exception | activity-packages/cv-activities/playbooks/cv-cell-targeting-failures.md | high | carrying one of the nine cell-specific sentences and Descriptor.Target.CellExtraInfo set — NOT the plain Element not found or the Scrolled message |
| UiPath.CV.ElementNotFoundException | exception | activity-packages/cv-activities/playbooks/cv-element-not-found.md | medium | plain parameterless Element not found after TimeoutMS exhausts — no cell sentence, no Scrolled prefix; timeout expiry surfaces as this, NOT TimeoutException |
| UiPath.CV.ElementNotFoundException | exception | activity-packages/cv-activities/playbooks/cv-scroll-search-failures.md | medium | message contains the Scrolled-the-entire-screen literal and ScrollDirection != None — scroll-search exhausted, not a plain find timeout |
| UiPath.CV.InvalidDescriptorException | exception | activity-packages/cv-activities/playbooks/cv-invalid-descriptor.md | high |  |
| UiPath.Excel.BusinessException | exception | activity-packages/excel-activities/playbooks/read-range-sheet-not-found.md | medium | with sheet-name wording — see message signature; other BusinessException wordings → write-cell-failures.md / write-range-failures.md / append-range-failures.md / delete-range-failures.md |
| UiPath.Excel.BusinessException | exception | activity-packages/excel-activities/playbooks/write-cell-failures.md | medium | on Write Cell — wrong-format/Excel-busy (branches 2/3) or invalid cell reference (branch 6) wordings; sheet-name wording → read-range-sheet-not-found.md |
| UiPath.Excel.ExcelException | exception | activity-packages/excel-activities/playbooks/read-range-null-reference.md | low | provider wrapper for in-activity parsing failures; with sheet-name wording 'does not exist in the workbook' → read-range-sheet-not-found.md |
| UiPath.IntegrationService.Activities.Runtime.Exceptions.GeneralException | exception | products/integration-service/playbooks/connector-general-exception.md | high |  |
| UiPath.IntegrationService.Activities.Runtime.Exceptions.RuntimeException | exception | products/integration-service/playbooks/connector-runtime-exception.md | high |  |
| UiPath.Ipc.RemoteException | exception | products/integration-service/playbooks/connector-remote-exception.md | medium | connector failure only when the faulted activity is a connector activity AND the unwrapped inner message is token/auth, transport, or downstream HTTP |
| UiPath.UIAutomationNext.Exceptions.NodeAmbiguousException | exception | activity-packages/ui-automation/playbooks/ambiguous-selector.md | high |  |
| UiPath.UIAutomationNext.Exceptions.UiAutomationException | exception | activity-packages/ui-automation/playbooks/click-coordinate-off-screen.md | high | message is the outside-of-screen-bounds literal; inner COMException HRESULT 0x800402bd — element was located, coordinate rejected |
| UiPath.UIAutomationNext.Exceptions.UiNodeDisabledElementException | exception | activity-packages/ui-automation/playbooks/disabled-element.md | high |  |
| UiPath.UIAutomationNext.Exceptions.VerifyActivityExecutionException | exception | activity-packages/ui-automation/playbooks/verify-execution-failure.md | high |  |
| UiPath.Word.WordException | exception | activity-packages/word-activities/playbooks/word-com-start-background-session0.md | medium | COM-start fault on an unattended/background run — stack through WordAppHelpers.StartNewApplication |
| Unable to cast COM object | message | activity-packages/mail-activities/playbooks/send-outlook-mail-failures.md | medium | Outlook COM bind at Send Outlook Mail (branch 1); Word interop casts name a Microsoft.Office.Interop.Word interface → word-export-pdf-com-wrong-thread.md |
| Unable to cast COM object of type 'System.__ComObject' to interface type 'Microsoft.Office.Interop.Word._Document' | message | activity-packages/word-activities/playbooks/word-export-pdf-com-wrong-thread.md | medium | _Document cast failing on the export path |
| Unable to cast object of type | message | activity-packages/excel-activities/playbooks/invoke-vba-parameter-formatting.md | medium |  |
| Unable to connect to the remote server | message | activity-packages/web-activities/playbooks/http-request-connection-failure.md | medium |  |
| Unable to find the searched element. | message | activity-packages/ui-automation/playbooks/activity-configuration-error.md | high |  |
| Unable to parse range: | message | activity-packages/gsuite-activities/playbooks/sheets-invalid-range.md | medium |  |
| UnauthorizedAccessException | exception | activity-packages/classic-activities/playbooks/file-operation-failed.md | medium | generic .NET — discriminator is the faulted file activity (Rename File / Move File / Append Line) |
| Unexpected character encountered while parsing value | message | activity-packages/web-activities/playbooks/deserialize-malformed-input.md | high |  |
| Unexpected end of content while loading JArray | message | activity-packages/web-activities/playbooks/deserialize-malformed-input.md | high |  |
| UninitializedNodeException | exception | activity-packages/classic-activities/playbooks/ui-activity-configuration-error.md | high | the uninitialized node is the scope's context window — wrong selector shape / null window on the scope |
| Unlicensed version | state | activity-packages/ui-automation/playbooks/healing-agent-orch-issues.md | high | Healing Agent tab banner — preview UIA 24.10.x detecting unlicensed |
| Upload failed after | message | activity-packages/gsuite-activities/playbooks/upload-storage-quota-exceeded.md | high |  |
| Upload session | message | activity-packages/o365-activities/playbooks/upload-file-quota-or-size.md | medium | covers 'Upload session failed.' / 'Upload session incomplete.' / 'Upload session not found.' — broken chunked upload |
| userRateLimitExceeded | error-code | activity-packages/gsuite-activities/playbooks/transient-and-timeout-errors.md | medium |  |
| Value cannot be null | message | runtime-exceptions/playbooks/argument-null-exception.md | medium | typically followed by (Parameter 'paramName') — the parameter name identifies the rejected argument |
| Value cannot be null. (Parameter 'DriveItem') | message | activity-packages/o365-activities/playbooks/copy-item-argument-null.md | high |  |
| Value cannot be null. (Parameter 'Folder name') | message | activity-packages/o365-activities/playbooks/create-folder-invalid-path.md | high |  |
| Value cannot be null. (Parameter 'Folder path') | message | activity-packages/o365-activities/playbooks/create-folder-invalid-path.md | high |  |
| Value cannot be null. (Parameter 'JSON string') | message | activity-packages/web-activities/playbooks/deserialize-null-input.md | high |  |
| Value cannot be null. (Parameter 'Parent folder') | message | activity-packages/o365-activities/playbooks/create-folder-invalid-path.md | high |  |
| Value cannot be null. (Parameter 'Secure') | message | activity-packages/cv-activities/playbooks/cv-action-failed-after-find.md | medium |  |
| Value for property [Movement units] can not be lower than 1. | message | activity-packages/ui-automation/playbooks/activity-configuration-error.md | high |  |
| Value is 'null' but should be 'object' | message | products/maestro/playbooks/input-schema-mismatch.md | high | optional file/attachment passed as null |
| Word experienced an error trying to open the file | message | activity-packages/word-activities/playbooks/word-scope-file-corrupted.md | medium |  |
| WordAppHelpers.StartNewApplication | message | activity-packages/word-activities/playbooks/word-com-start-background-session0.md | medium | stack frame — COM start path, before any Documents.Open |
| WordDocumentFactory.OpenOrCreateNewDocument | message | activity-packages/word-activities/playbooks/word-open-sharepoint-url-com-command-failed.md | medium | stack frame — open path, not COM start |
| Wrong number of arguments or invalid property assignment | message | activity-packages/excel-activities/playbooks/invoke-vba-parameter-formatting.md | medium |  |
| WrongTargetApplicationException | exception | activity-packages/ui-automation/playbooks/wrong-target-application.md | high |  |
| You are not authenticated! | message | activity-packages/system-activities/playbooks/get-asset-robot-not-authenticated.md | medium |  |
| You are not authorized! | message | activity-packages/system-activities/playbooks/get-asset-permission-denied.md | high |  |
| You do not have access to any Drives named | message | activity-packages/o365-activities/playbooks/drive-item-not-found.md | high |  |
| You do not have the following labels | message | activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md | medium |  |
| You must provide a literal value for | message | activity-packages/o365-activities/playbooks/application-scope-misconfigured.md | medium |  |
| You must provide a value for at least one of the following properties: To, Cc, Bcc | message | activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md | medium |  |
| Your connection has been temporarily disabled due to multiple unsuccessful attempts | message | products/agents/playbooks/is-connection-disabled.md | medium |  |
| Your user's monthly Personal Automation quota has been exceeded | message | products/maestro/playbooks/personal-automation-quota.md | high |  |
| {0002096B-0000-0000-C000-000000000046} | message | activity-packages/word-activities/playbooks/word-export-pdf-com-wrong-thread.md | medium | IID of Microsoft.Office.Interop.Word._Document in the QueryInterface failure |

### Disambiguations

- `activity-packages/classic-activities/playbooks/browser-open-or-attach-failed.md`: NOT for browser type vs communication method incompatibility → ui-activity-configuration-error.md
- `activity-packages/classic-activities/playbooks/ui-activity-timeout.md`: NOT for Wait Image Vanish / image still matching on screen → image-target-not-found.md
- `activity-packages/cv-activities/playbooks/cv-action-failed-after-find.md`: NOT for Element not found / Scrolled the entire screen → cv-element-not-found.md / cv-scroll-search-failures.md
- `activity-packages/cv-activities/playbooks/cv-action-failed-after-find.md`: NOT for Get Text empty in OCR mode (no clicks/clipboard involved) → cv-get-text-empty-or-wrong-result.md
- `activity-packages/cv-activities/playbooks/cv-action-failed-after-find.md`: NOT for Invalid Descriptor → cv-invalid-descriptor.md
- `activity-packages/cv-activities/playbooks/cv-action-failed-after-find.md`: NOT for Server errors during a refresh → cv-server-auth-throttling-network.md
- `activity-packages/cv-activities/playbooks/cv-cell-targeting-failures.md`: NOT for Cell message swallowed to Result = false by CvElementExistsWithDescriptor → cv-silent-failures-and-false-results.md
- `activity-packages/cv-activities/playbooks/cv-cell-targeting-failures.md`: NOT for Generic Element not found with Version >= V3 and a non-cell target → cv-element-not-found.md
- `activity-packages/cv-activities/playbooks/cv-cell-targeting-failures.md`: NOT for Scrolled the entire screen, but element was not found → cv-scroll-search-failures.md
- `activity-packages/cv-activities/playbooks/cv-element-not-found.md`: NOT for Cell-targeting sentences (Could not find table, Invalid column number, Table only contains...) → cv-cell-targeting-failures.md
- `activity-packages/cv-activities/playbooks/cv-element-not-found.md`: NOT for Invalid Descriptor / Reason: Target must be set → cv-invalid-descriptor.md
- `activity-packages/cv-activities/playbooks/cv-element-not-found.md`: NOT for Scrolled the entire screen, but element was not found → cv-scroll-search-failures.md
- `activity-packages/cv-activities/playbooks/cv-element-not-found.md`: NOT for Server errors (401/403/429/5xx, word limit, transport) → cv-server-auth-throttling-network.md
- `activity-packages/cv-activities/playbooks/cv-get-text-empty-or-wrong-result.md`: NOT for Activity threw ElementNotFoundException (descriptor never matched) → cv-element-not-found.md
- `activity-packages/cv-activities/playbooks/cv-get-text-empty-or-wrong-result.md`: NOT for Activity threw Scrolled the entire screen, but element was not found → cv-scroll-search-failures.md
- `activity-packages/cv-activities/playbooks/cv-get-text-empty-or-wrong-result.md`: NOT for Activity threw a server/OCR error with an error code → cv-server-auth-throttling-network.md
- `activity-packages/cv-activities/playbooks/cv-invalid-descriptor.md`: NOT for CvElementExistsWithDescriptor returned Result = false with no fault → cv-element-not-found.md / cv-silent-failures-and-false-results.md
- `activity-packages/cv-activities/playbooks/cv-invalid-descriptor.md`: NOT for ElementNotFoundException after a find ran → cv-element-not-found.md
- `activity-packages/cv-activities/playbooks/cv-invalid-descriptor.md`: NOT for Scope faulted before any descriptor activity ran → cv-scope-setup-failures.md
- `activity-packages/cv-activities/playbooks/cv-invalid-descriptor.md`: NOT for Server-side ArgumentException (auth 401, unreachable, throttling 429, word limits) → cv-server-auth-throttling-network.md
- `activity-packages/cv-activities/playbooks/cv-scope-setup-failures.md`: NOT for A child activity started and the find/analysis failed → cv-element-not-found.md / cv-server-auth-throttling-network.md
- `activity-packages/cv-activities/playbooks/cv-scope-setup-failures.md`: NOT for OCR word-limit message (surfaces lazily on the first child's analysis call, not at scope entry) → cv-server-auth-throttling-network.md
- `activity-packages/cv-activities/playbooks/cv-scope-setup-failures.md`: NOT for The target Element was not specified — after a child's find succeeded → cv-action-failed-after-find.md
- `activity-packages/cv-activities/playbooks/cv-scroll-search-failures.md`: NOT for Cell-targeting sentences → cv-cell-targeting-failures.md
- `activity-packages/cv-activities/playbooks/cv-scroll-search-failures.md`: NOT for CvElementExistsWithDescriptor returned false after a scroll search (message swallowed) → cv-silent-failures-and-false-results.md
- `activity-packages/cv-activities/playbooks/cv-scroll-search-failures.md`: NOT for Generic not-found without Scrolled in the message, or ScrollDirection = None → cv-element-not-found.md
- `activity-packages/cv-activities/playbooks/cv-server-auth-throttling-network.md`: NOT for CvElementExistsWithDescriptor returned false — it only swallows not-found; server errors still fault
- `activity-packages/cv-activities/playbooks/cv-server-auth-throttling-network.md`: NOT for Element not found with no error code (the analysis call succeeded) → cv-element-not-found.md
- `activity-packages/cv-activities/playbooks/cv-server-auth-throttling-network.md`: NOT for Local-server install/prerequisite errors (LocalServer package missing, VC++ redistributable, AVX2) → cv-scope-setup-failures.md
- `activity-packages/cv-activities/playbooks/cv-silent-failures-and-false-results.md`: NOT for Activity actually threw (ContinueOnError = false, InRegion unbound) → cv-element-not-found.md / cv-server-auth-throttling-network.md / cv-invalid-descriptor.md
- `activity-packages/cv-activities/playbooks/cv-silent-failures-and-false-results.md`: NOT for Cell descriptor config confirmed as the problem → cv-cell-targeting-failures.md
- `activity-packages/cv-activities/playbooks/cv-silent-failures-and-false-results.md`: NOT for Get Text wrong text after ruling out ContinueOnError / InRegion / mode mismatch → cv-get-text-empty-or-wrong-result.md
- `activity-packages/database-activities/playbooks/start-transaction-failures.md`: NOT for child SQL-syntax / parameter / command-timeout faults inside the scope → execute-query-failures.md / execute-non-query-failures.md
- `activity-packages/excel-activities/playbooks/append-range-failures.md`: NOT for BusinessException 'The sheet with the name ... does not exist' → read-range-sheet-not-found.md
- `activity-packages/excel-activities/playbooks/append-range-failures.md`: NOT for IOException 'being used by another process' → read-range-file-locked.md
- `activity-packages/excel-activities/playbooks/delete-range-failures.md`: NOT for BusinessException 'The sheet with the name ... does not exist' → read-range-sheet-not-found.md
- `activity-packages/excel-activities/playbooks/delete-range-failures.md`: NOT for file lock 'cannot access the file' / 'used by another process' → read-range-file-locked.md
- `activity-packages/excel-activities/playbooks/excel-application-card-failures.md`: NOT for child activity BusinessException 'must be placed inside' → append-range-failures.md / delete-range-failures.md
- `activity-packages/excel-activities/playbooks/excel-application-scope-failures.md`: NOT for Excel truly not installed, empty/illegal WorkbookPath, multi-scope RPC races, child outside scope, sensitivity label → excel-application-card-failures.md
- `activity-packages/excel-activities/playbooks/lookup-range-null-reference.md`: NOT for Excel is not installed / COM class factory → lookup-range-excel-not-installed.md
- `activity-packages/excel-activities/playbooks/lookup-range-null-reference.md`: NOT for file-in-use wording → lookup-range-file-locked.md
- `activity-packages/excel-activities/playbooks/write-cell-failures.md`: NOT for BusinessException 'The sheet with the name ... does not exist' → read-range-sheet-not-found.md
- `activity-packages/excel-activities/playbooks/write-range-failures.md`: NOT for BusinessException 'The sheet with the name ... does not exist' → read-range-sheet-not-found.md
- `activity-packages/excel-activities/playbooks/write-range-failures.md`: NOT for IOException 'being used by another process' → read-range-file-locked.md
- `activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md`: NOT for The resource was not found. (404) → drive-file-not-found.md
- `activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md`: NOT for The storage quota was exceeded. / Upload failed after <N> bytes (403 quota, not authorization) → upload-storage-quota-exceeded.md
- `activity-packages/gsuite-activities/playbooks/connection-and-auth-failures.md`: NOT for Transient 5xx / rate limit / A task was canceled. → transient-and-timeout-errors.md
- `activity-packages/gsuite-activities/playbooks/drive-file-not-found.md`: NOT for File does not exist: <path> (local filesystem miss) → invalid-or-null-input.md
- `activity-packages/gsuite-activities/playbooks/drive-file-not-found.md`: NOT for Permission to the resource was denied. / Invalid authentication credentials. (403/401) → connection-and-auth-failures.md
- `activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md`: NOT for 401/403/auth-timeout → connection-and-auth-failures.md
- `activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md`: NOT for Invalid data[0]: Unable to parse range (server-side Google 400) → sheets-invalid-range.md
- `activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md`: NOT for The resource was not found. / Cannot find item configured with connection → drive-file-not-found.md
- `activity-packages/gsuite-activities/playbooks/invalid-or-null-input.md`: NOT for This action would increase the number of cells → sheets-cell-limit-exceeded.md
- `activity-packages/gsuite-activities/playbooks/transient-and-timeout-errors.md`: NOT for Authentication attempt took longer than <N> seconds (auth-phase TimeoutException) → connection-and-auth-failures.md
- `activity-packages/gsuite-activities/playbooks/transient-and-timeout-errors.md`: NOT for Clean 401/403/404 with a definite message → connection-and-auth-failures.md, drive-file-not-found.md
- `activity-packages/gsuite-activities/playbooks/transient-and-timeout-errors.md`: NOT for The storage quota was exceeded. / Upload failed after <N> bytes → upload-storage-quota-exceeded.md
- `activity-packages/o365-activities/playbooks/application-scope-misconfigured.md`: NOT for Messages carrying a Graph result (403/404/429/503 or AADSTS token errors) → insufficient-graph-scope.md, request-throttled.md, transient-service-error.md, authentication-token-invalid.md
- `activity-packages/o365-activities/playbooks/authentication-token-invalid.md`: NOT for Authenticated caller lacking Graph permission (403 wording) → insufficient-graph-scope.md
- `activity-packages/o365-activities/playbooks/authentication-token-invalid.md`: NOT for Pre-authentication configuration faults (asset / 'You must provide a value') → application-scope-misconfigured.md
- `activity-packages/o365-activities/playbooks/copy-item-argument-null.md`: NOT for The resource could not be found. → drive-item-not-found.md
- `activity-packages/o365-activities/playbooks/copy-item-argument-null.md`: NOT for Value cannot be null. (Parameter '<localized property>') from a Connections activity → create-folder-invalid-path.md
- `activity-packages/o365-activities/playbooks/create-folder-invalid-path.md`: NOT for The resource could not be found. / Cannot find item configured with connection (parent folder does not resolve) → drive-item-not-found.md
- `activity-packages/o365-activities/playbooks/create-folder-invalid-path.md`: NOT for The specified item name already exists. → item-name-already-exists.md
- `activity-packages/o365-activities/playbooks/download-file-conversion-or-destination.md`: NOT for Multiple items with the name <name> found ... → download-multiple-items-name-conflict.md
- `activity-packages/o365-activities/playbooks/download-file-conversion-or-destination.md`: NOT for The resource could not be found. / A file with the specified ID does not exist. → drive-item-not-found.md
- `activity-packages/o365-activities/playbooks/download-multiple-items-name-conflict.md`: NOT for The specified item name already exists. (remote OneDrive/SharePoint/Excel conflict) → item-name-already-exists.md
- `activity-packages/o365-activities/playbooks/drive-item-not-found.md`: NOT for The resource could not be found. from a Mail activity → mail-folder-not-found.md
- `activity-packages/o365-activities/playbooks/email-trigger-connection-event-failure.md`: NOT for No email matching the filter criteria, received in the last 1 hour has been found → get-newest-email-no-match.md
- `activity-packages/o365-activities/playbooks/email-trigger-connection-event-failure.md`: NOT for The resource could not be found. after the event was retrieved → mail-folder-not-found.md, mail-message-not-found.md
- `activity-packages/o365-activities/playbooks/email-trigger-connection-event-failure.md`: NOT for Token / AADSTS / No default connection messages without a ConnectionHttpException → authentication-token-invalid.md
- `activity-packages/o365-activities/playbooks/insufficient-graph-scope.md`: NOT for The caller is not authenticated. / token-expiry messages → authentication-token-invalid.md
- `activity-packages/o365-activities/playbooks/insufficient-graph-scope.md`: NOT for The sharing link no longer exists, or you do not have permission to access it. (per-resource shared-link failure) → drive-item-not-found.md
- `activity-packages/o365-activities/playbooks/item-name-already-exists.md`: NOT for Multiple items with the name <name> found in the specified folder. (local destination conflict) → download-multiple-items-name-conflict.md
- `activity-packages/o365-activities/playbooks/legacy-mail-null-reference.md`: NOT for NullReferenceException whose stack trace is in the user's workflow code → null-reference-exception.md
- `activity-packages/o365-activities/playbooks/mail-folder-not-found.md`: NOT for The resource could not be found. from message-by-ID activities (MarkAsReadUnreadConnections, DeleteEmailConnections, ...) → mail-message-not-found.md
- `activity-packages/o365-activities/playbooks/mail-invalid-odata-query.md`: NOT for There was an error on the email server. Please try modifying your Query or Top values to continue. → transient-service-error.md
- `activity-packages/o365-activities/playbooks/mail-invalid-odata-query.md`: NOT for Zero results with no error → get-newest-email-no-match.md
- `activity-packages/o365-activities/playbooks/mail-message-not-found.md`: NOT for The resource could not be found. from activities taking a MailFolder argument and no message ID → mail-folder-not-found.md
- `activity-packages/o365-activities/playbooks/request-throttled.md`: NOT for The app or user has exceeded the allowed quota. (storage/quota limit) → upload-file-quota-or-size.md
- `activity-packages/o365-activities/playbooks/request-throttled.md`: NOT for The server is unable to process the current request. (503) / request timeouts → transient-service-error.md
- `activity-packages/o365-activities/playbooks/send-mail-rejected.md`: NOT for Batching request failed with an unknown reason. → transient-service-error.md, request-throttled.md
- `activity-packages/o365-activities/playbooks/send-mail-rejected.md`: NOT for The caller doesn't have permission to perform the action. (403) → insufficient-graph-scope.md
- `activity-packages/o365-activities/playbooks/send-mail-rejected.md`: NOT for Token / AADSTS / not-authenticated messages → authentication-token-invalid.md
- `activity-packages/o365-activities/playbooks/transient-service-error.md`: NOT for Invalid Query. Please use OData format for filter queries. (deterministic parse failure) → mail-invalid-odata-query.md
- `activity-packages/o365-activities/playbooks/transient-service-error.md`: NOT for Too many requests. / The app or user has been throttled. (429) → request-throttled.md
- `activity-packages/o365-activities/playbooks/upload-file-quota-or-size.md`: NOT for The resource could not be found. → drive-item-not-found.md
- `activity-packages/o365-activities/playbooks/upload-file-quota-or-size.md`: NOT for The specified item name already exists. → item-name-already-exists.md
- `activity-packages/o365-activities/playbooks/upload-file-quota-or-size.md`: NOT for Too many requests. / The app or user has been throttled. → request-throttled.md
- `activity-packages/python-activities/playbooks/invoke-method-failures.md`: NOT for engine-init / script-load faults (Error initializing Python engine, top-level ModuleNotFoundError, syntax error) → load-script-failures.md
- `activity-packages/python-activities/playbooks/python-path-not-valid.md`: NOT for engine-init errors (One or more errors occurred / Error initializing the Python engine) → python-scope-architecture-version-mismatch.md
- `activity-packages/system-activities/playbooks/get-asset-robot-not-authenticated.md`: NOT for HTTP 403 'not authorized' (permission/RBAC) → get-asset-permission-denied.md
- `activity-packages/ui-automation/playbooks/ambiguous-selector.md`: NOT for Absent HA recovery data for this fault is expected (HA bypasses NodeAmbiguousException) — not no-recovery-data.md
- `activity-packages/ui-automation/playbooks/ambiguous-selector.md`: NOT for NodeNotFoundException / SelectorNotFoundException / UiElementNotFoundException (zero matches) → selector-failure-manual.md
- `activity-packages/ui-automation/playbooks/application-not-found.md`: NOT for App missing and OpenMode != Never (launch attempted) → application-open-failed.md
- `activity-packages/ui-automation/playbooks/application-not-found.md`: NOT for Selector found a window owned by a different process → wrong-target-application.md
- `activity-packages/ui-automation/playbooks/application-open-failed.md`: NOT for Open = Never (scope told not to launch, app absent) → application-not-found.md
- `activity-packages/ui-automation/playbooks/application-open-failed.md`: NOT for Scope reached an element owned by a different app → wrong-target-application.md
- `activity-packages/ui-automation/playbooks/click-coordinate-off-screen.md`: NOT for Healing enabled but produced no fix → no-recovery-data.md
- `activity-packages/ui-automation/playbooks/click-coordinate-off-screen.md`: NOT for Not a selector-resolution failure — do not match selector-failure-* playbooks (selector resolved successfully)
- `activity-packages/ui-automation/playbooks/disabled-element.md`: NOT for SelectorNotFoundException / UiElementNotFoundException / NodeNotFoundException (element not found) → selector-failure-manual.md
- `activity-packages/ui-automation/playbooks/disabled-element.md`: NOT for TimeoutException → timeout-issue.md
- `activity-packages/ui-automation/playbooks/element-found-not-actionable.md`: NOT for Outside-of-screen-bounds coordinate injection on Hardware Events → click-coordinate-off-screen.md
- `activity-packages/ui-automation/playbooks/element-found-not-actionable.md`: NOT for Target found but disabled → disabled-element.md
- `activity-packages/ui-automation/playbooks/healing-agent-no-license.md`: NOT for AutopilotForRobots.HealingEnabled = false → selector-failure-healing-disabled.md
- `activity-packages/ui-automation/playbooks/healing-agent-no-license.md`: NOT for Customer does not want HA (informational notice, job continues) → healing-agent-orch-issues.md
- `activity-packages/ui-automation/playbooks/healing-agent-no-license.md`: NOT for HA licensed but produced no data (connectivity, image-only target, classic activities) → no-recovery-data.md
- `activity-packages/ui-automation/playbooks/healing-agent-orch-issues.md`: NOT for Customer wants HA working and the robot log carries the no-license line → healing-agent-no-license.md
- `activity-packages/ui-automation/playbooks/healing-agent-orch-issues.md`: NOT for HA licensed and engaged but produced no data (connectivity, classic activity, image-only target) → no-recovery-data.md
- `activity-packages/ui-automation/playbooks/scope-container-wrong-page.md`: NOT for HA disabled at the process/job level (un-helped click is an enablement issue) → selector-failure-healing-disabled.md
- `activity-packages/ui-automation/playbooks/selector-failure-manual.md`: NOT for Scope container attached to a different page/window than the inner selector expects → scope-container-wrong-page.md
- `activity-packages/ui-automation/playbooks/verify-execution-failure.md`: NOT for ExceptionCheckActivityPassword / ExceptionCheckActivityTypeInto / ExceptionCheckActivityTypeIntoWithSpecialKeys / ExceptionCheckActivityTypeIntoInputDisappeared — NTypeInto text-mismatch keys, separate planned playbook (not yet authored)
- `activity-packages/web-activities/playbooks/deserialize-type-mismatch.md`: NOT for JsonReaderException (input itself is not valid JSON) → deserialize-malformed-input.md
- `activity-packages/web-activities/playbooks/http-client-null-reference.md`: NOT for WebException with an HTTP status or transport phrase → http-request-connection-failure.md
- `activity-packages/web-activities/playbooks/http-request-connection-failure.md`: NOT for WebException 'The operation has timed out.' → http-request-timeout.md
- `activity-packages/web-activities/playbooks/http-request-timeout.md`: NOT for NetHttpRequest timeout (AggregateException → TaskCanceledException) → net-http-request-aggregate-failure.md
- `activity-packages/word-activities/playbooks/add-picture-failures.md`: NOT for Word COM HRESULTs (0x8002801D / 0x8001010A / 0x8001010E) — environmental C2 surface → word-com-interop-failures.md
- `activity-packages/word-activities/playbooks/export-pdf-missing-output-dir.md`: NOT for busy/locked Word COM session (COMException or hang) → export-pdf-com-hang.md
- `activity-packages/word-activities/playbooks/export-pdf-missing-output-dir.md`: NOT for invalid or un-suffixed output path → export-pdf-output-path-format.md
- `activity-packages/word-activities/playbooks/export-pdf-output-path-format.md`: NOT for correct path but missing output folder (generic Command Failed) → export-pdf-missing-output-dir.md
- `activity-packages/word-activities/playbooks/read-text-protected-view.md`: NOT for Protected View blocking a write/save rather than a read → word-scope-file-corrupted.md
- `activity-packages/word-activities/playbooks/read-text-protected-view.md`: NOT for unattended hang on an invisible Protected View bar → word-scope-hangs-background-prompt.md
- `activity-packages/word-activities/playbooks/replace-text-headers-textboxes-skipped.md`: NOT for body-text silent miss caused by run-splitting → replace-text-silent-no-substitution.md
- `activity-packages/word-activities/playbooks/replace-text-loop-template-overwrite.md`: NOT for IOException from Auto Save racing a shared file in a loop → replace-text-file-locked.md
- `activity-packages/word-activities/playbooks/replace-text-loop-template-overwrite.md`: NOT for placeholder split across Word XML runs (fails on every row, including the first) → replace-text-silent-no-substitution.md
- `activity-packages/word-activities/playbooks/replace-text-multiline-formatting.md`: NOT for long replacement text hitting the 256-character input cap → replace-text-length-limit.md
- `activity-packages/word-activities/playbooks/replace-text-version-mismatch.md`: NOT for runtime 'Cannot create unknown type WordApplicationScope' fault → word-scope-cannot-create-unknown-type.md
- `activity-packages/word-activities/playbooks/word-com-start-background-session0.md`: NOT for faults on Documents.Open with COMException 'Command failed' → word-open-sharepoint-url-com-command-failed.md
- `activity-packages/word-activities/playbooks/word-com-start-background-session0.md`: NOT for wrong-thread cast 0x8001010E on a child activity → word-export-pdf-com-wrong-thread.md
- `activity-packages/word-activities/playbooks/word-open-sharepoint-url-com-command-failed.md`: NOT for wrong-thread cast 0x8001010E on a child activity → word-export-pdf-com-wrong-thread.md
- `activity-packages/workflowevents-activities/playbooks/app-request-trigger-connection-lost.md`: NOT for AggregateException at InitializeHubConnection → initialize-hub-connection-aggregate-failure.md
- `activity-packages/workflowevents-activities/playbooks/app-request-trigger-connection-lost.md`: NOT for NullReferenceException at HandleAppRequest → handle-app-request-null-reference.md
- `activity-packages/workflowevents-activities/playbooks/handle-app-request-null-reference.md`: NOT for SignalR / transport fault at AppRequestTrigger → app-request-trigger-connection-lost.md
- `products/integration-service/playbooks/connector-aggregate-exception.md`: NOT for inner GeneralException (DAP-GE) → connector-general-exception.md
- `products/integration-service/playbooks/connector-aggregate-exception.md`: NOT for inner Ipc/CoreIpc RemoteException → connector-remote-exception.md
- `products/integration-service/playbooks/connector-aggregate-exception.md`: NOT for inner NullReferenceException → connector-null-reference.md
- `products/integration-service/playbooks/connector-aggregate-exception.md`: NOT for inner RuntimeException (DAP-RT) → connector-runtime-exception.md
- `products/maestro/playbooks/argument-mismatch-400.md`: NOT for error mentions schema conformance broadly → input-schema-mismatch.md
- `products/maestro/playbooks/argument-mismatch-400.md`: NOT for error names a single required field → missing-required-parameter.md
- `products/maestro/playbooks/deployment-failure.md`: NOT for Package entry points definition is invalid after adding DateTime inputs → deployment-datetime-input.md
- `products/maestro/playbooks/deployment-failure.md`: NOT for error code 4006 / EMAIL_RECEIVED → deployment-email-received.md
- `products/maestro/playbooks/file-field-required.md`: NOT for file orphaned by job retention → attachment-not-found.md
- `products/maestro/playbooks/file-handling.md`: NOT for attachment orphaned by job retention policy → attachment-not-found.md
- `products/maestro/playbooks/marker-input-null.md`: NOT for InvalidCastException on JS marker items (400008) → marker-invalid-cast.md
- `products/maestro/playbooks/marker-invalid-cast.md`: NOT for null input collection (400007) → marker-input-null.md
- `products/maestro/playbooks/multi-instance-parallel.md`: NOT for JS expression InvalidCastException → marker-invalid-cast.md
- `products/orchestrator/playbooks/job-pending-no-host.md`: NOT for connected runtime present + JobHistory has only the original Pending entry → job-pending-stale-dispatch.md
- `products/orchestrator/playbooks/job-pending-stale-dispatch.md`: NOT for template has no connected runtime (robotVersions empty) → job-pending-no-host.md

### Silent playbooks (no greppable signature — route via the no-signature table below)

- activity-packages/classic-activities/playbooks/foreach-row-failed.md
- activity-packages/classic-activities/playbooks/invoke-workflow-failed.md
- activity-packages/excel-activities/playbooks/lookup-range-active-filters.md
- activity-packages/excel-activities/playbooks/lookup-range-formula-cells.md
- activity-packages/ui-automation/playbooks/no-recovery-data.md
- activity-packages/word-activities/playbooks/add-picture-failures.md
- activity-packages/word-activities/playbooks/export-pdf-output-path-format.md
- activity-packages/word-activities/playbooks/read-text-doc-format.md
- activity-packages/word-activities/playbooks/read-text-protected-view.md
- activity-packages/word-activities/playbooks/replace-text-headers-textboxes-skipped.md
- activity-packages/word-activities/playbooks/replace-text-loop-template-overwrite.md
- activity-packages/word-activities/playbooks/replace-text-multiline-formatting.md
- activity-packages/word-activities/playbooks/replace-text-silent-no-substitution.md
- activity-packages/word-activities/playbooks/word-scope-hangs-background-prompt.md
- products/integration-service/playbooks/activity-configuration-corrupt.md
- products/integration-service/playbooks/connection-not-resolved.md
- products/integration-service/playbooks/http-client-exception.md
- products/integration-service/playbooks/missing-required-input.md
- products/integration-service/playbooks/request-failed.md
- products/integration-service/playbooks/response-mapping-mismatch.md
- products/integration-service/playbooks/token-refresh-failed.md
- products/integration-service/playbooks/trigger-execution-failed.md
- products/integration-service/playbooks/trigger-not-firing.md
- products/llm-gateway/playbooks/byo-routing-bypassed.md
- products/maestro/playbooks/agent-traces-disappearing.md
- products/maestro/playbooks/boundary-event-duplicate-task.md
- products/maestro/playbooks/bpmn-job-stuck.md
- products/maestro/playbooks/debug-vs-deploy.md
- products/maestro/playbooks/deployment-failure.md
- products/maestro/playbooks/maestro-service-disabled.md
<!-- END GENERATED SIGNATURES -->

## No-signature routing

For problems with nothing greppable (no exception, no error code — silent failures, hangs, wrong results), map the symptom to a domain, then check that domain's silent playbooks (listed above) and its `summary.md`:

| Symptom | Domain | Entry |
|---|---|---|
| Job/run Successful but the action had no effect or output is wrong | The acting activity's package (ui-automation, word, excel, gsuite, o365, database) | Activity-level trace logs — look for zero-count lines ("Replaced 0 occurrence"), Simulate/inert-verify configurations, provider quirks |
| Job stuck Pending | orchestrator | `PendingReasons` on the job record — its error codes ARE greppable signatures; re-grep after fetching |
| Job/instance stuck Running | orchestrator (plain job) / maestro (BPMN instance) | Child-job states + open incidents; a Maestro instance with an Open incident is blocked until the incident is resolved |
| Works in Debug, fails deployed | maestro | Debug-vs-deploy silent playbook |
| Duplicate task/element executions | maestro | Boundary-event silent playbook |
| Traces/evidence missing or disappearing | maestro / orchestrator retention | Silent playbooks; retention windows |
| Robot unresponsive, heartbeat gaps | orchestrator | Machine/session state via the orchestrator investigation guide |
| Hang mid-activity, no fault, no timeout | The activity's package | Package overview "common failure patterns" (e.g., Word background modal dialogs, Python stdout flooding) |
| Reads/writes the wrong files with no error | The activity's package | Relative-path resolution quirks (e.g., Python per-package WorkingFolder) |
| Slowness / degradation without errors | Owning product | Product overview + `uip docsai ask` |

Cross-domain rule: the symptom's *reporting* surface is not necessarily the owning domain — extract entity keys from the fetched records and follow them one hop before settling on a domain.

## Signal-extraction cheatsheet

Where each signal kind lives (fetch per the domain's `investigation_guide.md`; exact commands are documented there and in playbook `## Investigation` sections):

| Signal kind | Where to find it |
|---|---|
| exception (class/FQN) | Job record `Info` field; error-level job logs; trace span error attributes; Maestro incident body. Unwrap `System.AggregateException` / `--->` chains — the INNER exception is the routable signal |
| message / message-key | Verbatim friendly message in job `Info` / logs; localization resource keys quoted in UIA exception details |
| error-code | Message text (`DAP-*`, `#NNNN`, `AADSTS*`, HRESULTs like `0x8004027D`); Maestro incident code (e.g. `170002`); job `PendingReasons.ErrorCodes` |
| http-status | Message text ("Bad Gateway", "429"); trace span attributes |
| state | Job `State` + `PendingReasons`; Maestro instance status + incident open/closed; connection status |
| faulting activity + package | `[Name]` prefix in error log message bodies; span names; exception FQN prefix maps to the owning package (see `references/summary.md` domain namespaces) |
| package versions | `project.json` dependencies (source-required); job record package version fields |
