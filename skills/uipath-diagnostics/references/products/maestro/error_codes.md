# Maestro Error Codes

Source: `UiPath.PO.Errors/ErrorCode.cs` + `ErrorCodeMessages.resx`

## Error Code Ranges

| Range | Subsystem |
|-------|-----------|
| 100000–100052 | Temporal & Instance Service |
| 100101–100119 | BPMN Package Download & Assets |
| 101000–101004 | Element Service |
| 102000–102018 | Integration Service |
| 103000–103002 | Incident Service |
| 104000–104067 | Instance DB (Cosmos & SQL) |
| 105000–105101 | Incident DB (Cosmos & SQL) |
| 106000–106026 | Process DB & Element Execution DB |
| 107000–107004 | TraceView Service |
| 108000–108102 | Insights & Instance Globals |
| 150001–150009 | Auth & Header Errors |
| 150100–150110 | GWS (Data Move) |
| 150200–150203 | Blob Storage |
| 160000–160012 | Cloud Events |
| 170000–170041 | Orchestrator Runtime (OR) |
| 180000–180003 | Studio Web (SW) |
| 190001 | Timer |
| 200000–200103 | Activity & Observability |
| 200200–200201 | Hermes |
| 300000–300010 | BPMN Engine |
| 300100–300103 | Data Pipe |
| 300200–300208 | Data Fabric |
| 300300–300301 | VDO |
| 300400–300403 | Business Rules |
| 300450–300461 | Case Management |
| 300500–300503 | Script Tasks |
| 300600–300604 | HTTP Request Tasks |
| 400000–400023 | BPMN Elements |
| 400050–400051 | Case Select Next Stage |
| 400100–400110 | Instance Operations |
| 400200–400404 | PTS & Process Service |
| 400300–400302 | Expression Evaluation |
| 400500–400505 | Licensing |
| 400600–400601 | Optimize |
| 400700 | PIMS Middleware |
| 400800–400805 | Admin |
| 400900–400908 | Tenant Metadata |
| 400911–400923 | Overwatch |
| 410000–410202 | DynamicExpresso & Variable Storage |
| 420000 | Call Activity |
| 430000–430002 | IXP (Document Understanding) |
| 440000–440002 | Signal Events & Instance Globals |
| 450002–450013 | Message Events |

## Temporal & Instance Service (100000–100052)

| Code | Name | Message |
|------|------|---------|
| 100000 | InstancesServiceTemporalClient | Error creating temporal client |
| 100001 | TemporalFacadeCreateConflict | Instance already exists in storage |
| 100002 | InstancesServiceDuplicateRequest | Duplicate request to Instances service |
| 100003 | TemporalFacadeCreateException | Error creating instance |
| 100004 | TemporalFacadeResetException | Error resetting workflow |
| 100005 | TemporalClientFacadeFetchHistoryException | Error fetching history |
| 100006 | TemporalFacadePauseException | Error pausing workflow |
| 100007 | TemporalFacadeCompleteSuspendedActivityException | Error completing suspended activity |
| 100008 | TemporalFacadeResumeException | Error resuming workflow |
| 100009 | InstancesServicePausingStatusChangeFailed | Pausing status change failed |
| 100010 | InstancesServiceResumingStatusChangeFailed | Resuming status change failed |
| 100011 | InstancesServiceRetryStatusChangeFailed | Retry status change failed |
| 100012 | TemporalFacadeRetryException | Error retrying execution |
| 100013 | TemporalFacadeDebugCreateConflict | Debug instance creation conflict |
| 100014 | TemporalFacadeDebugCreateException | Debug instance creation error |
| 100015 | TemporalFacadeBreakpointException | Error setting breakpoint |
| 100016 | TemporalFacadeReopenCaseException | Failed to reopen case instance |
| 100017 | TemporalFacadeContinueOnBreakpointException | Error continuing on breakpoint |
| 100018 | VariablesProcessorInvalidJsonPatch | Invalid JSON patch for variables |
| 100019 | CosmosInstanceConflictException | Instance already exists in storage |
| 100020 | TemporalFacadeCancelException | Error canceling workflow |
| 100021 | InstancesServiceUpgradingStatusChangeFailed | Upgrading status change failed |
| 100022 | TemporalFacadeUpgradeException | Error upgrading workflow |
| 100023 | TemporalUpdateVariablesException | Error updating variables |
| 100024 | UpdatingInstanceVersionFailed | Failed to update the instance package |
| 100025 | InstanceInvalidPackageKey | Invalid package key format |
| 100026 | TemporalFacadeVariablesException | Error getting variables |
| 100027 | InstVarServiceParseBpmnXml | Error parsing BPMN XML for variables |
| 100028 | VariableEndpointQueryParamInvalid | Invalid query parameter for variables endpoint |
| 100029 | InstancesServiceGetInstanceRunNotFound | Instance run not found |
| 100030 | InstancesServiceGetInstanceRunMultipleRuns | Instance has multiple runs (not allowed) |
| 100031 | InstancesServiceGetInstancesSummaryFailed | Error getting instances summary |
| 100032 | TemporalFacadeCompleteSuspendedActivityRpcException | Error completing suspended activity (RPC) |
| 100033 | TemporalFacadeVariablesUnableToFetch | Unable to fetch variables |
| 100034 | InstanceStatusInvalid | Invalid instance status |
| 100035 | TemporalActivityAlreadyCompletedException | The Temporal activity is already completed and cannot be completed again |
| 100036 | TemporalActivityNotFoundToCompleteException | The Temporal activity is not found to complete the activity |
| 100037 | TemporalFacadeApplyGoToTransitionsException | Error applying GoTo transitions |
| 100038 | TemporalFacadeGetGoToCursorsException | Error getting GoTo cursors |
| 100039 | TemporalFacadeCancelRpcException | Error canceling workflow (RPC) |
| 100040 | TemporalFacadeElementActivationException | Error activating element |
| 100041 | TemporalFacadePauseElementActivationException | Error pausing element activation |
| 100042 | TemporalWorkflowNotFound | Workflow not found |
| 100043 | TemporalFacadeContinueOnBreakpointCompletedException | Breakpoint continuation completed |
| 100044 | TemporalFacadeCancelElementException | Error while canceling element in Temporal |
| 100045 | TemporalFacadeRetryElementException | Failed to retry element in the instance |
| 100046 | ReopenCaseNotCaseManagementInstance | Instance is not a case management process and cannot be reopened |
| 100047 | ReopenCaseInstanceNotCompleted | Case instance must be in Completed status before it can be reopened |
| 100048 | InstancesGetAllInvalidPageSize | pageSize must be less than or equal to 500 |
| 100049 | InstancesGetAllMissingPackageId | packageId filter must be provided along with packageVersion |
| 100050 | InstancesGetAllInvalidDateRange | startedTimeUtcStart must be before or equal to startedTimeUtcEnd |
| 100051 | InstancesGetAllInvalidStatus | One or more provided status values are invalid |
| 100052 | InstancesGetAllInvalidSortField | Invalid sortBy value |

## BPMN Package Download & Assets (100101–100119)

| Code | Name | Message |
|------|------|---------|
| 100101 | InstancesServiceBpmnDownloadHttpException | HTTP error downloading BPMN package |
| 100102 | InstancesServiceBpmnDownloadException | Error downloading BPMN package |
| 100103 | InstancesServiceBpmnDownloadFailed | BPMN download failed |
| 100104 | InstancesServiceBpmnDownloadInvalidArgument | Invalid argument for BPMN download |
| 100105 | DebugBpmnDownloadHttpException | Failed to get the debug package |
| 100106 | DebugBpmnDownloadException | Failed to get the debug package |
| 100107 | BpmnServiceNotPde | BPMN service not PDE |
| 100108 | DebugBpmnFileNotFound | Unable to find file in nuget for debug |
| 100109 | InstancesServiceBpmnFileNotFound | Unable to find BPMN file in package |
| 100110 | InstancesServiceFileNotFound | Unable to find file in package |
| 100111 | DebugFileNotFound | Unable to find file in debug package |
| 100113 | DebugPackageDownloadHttpException | Failed to get the debug package |
| 100114 | DebugPackageDownloadException | Failed to get the debug package |
| 100115 | AssetNotFound | Asset not found for the specified process |
| 100116 | AssetDownloadFailed | Failed to download asset from package |
| 100117 | ProcessReleaseNotFound | No release found for the specified process key and version |
| 100118 | AssetInvalidType | Invalid asset type. Valid values are: bpmn, case, flow |
| 100119 | ReleasesApiError | Failed to query releases from Orchestrator |

## Integration Service (102000–102018)

| Code | Name | Message |
|------|------|---------|
| 102000 | IntSvcResultNull | Integration Services unexpected empty result |
| 102001 | IntSvcResourceNotFound | Integration Services resource not found |
| 102002 | IntSvcOperationFailed | Integration Services operation failed |
| 102003 | IntSvcBadRequest | Integration Services bad request |
| 102004 | IntSvcMethodNotSupported | Integration Services method not supported |
| 102005 | CreateTriggerInvalidInputError | Integration Services invalid input on create trigger operation |
| 102006 | DeleteTriggerInvalidInputError | Integration Services invalid input on delete trigger operation |
| 102007 | GetEventPayloadInvalidInputError | Integration Services invalid input on get payload operation |
| 102008 | GetConnectionInvalidInputError | Integration Services invalid input on get connection operation |
| 102009 | SendIntSvcTaskInvalidInputError | Integration Services invalid input on send task operation |
| 102010 | IntSvcArgumentsError | Integration Services invalid value in input |
| 102011 | DeleteTriggerFailed | Integration Services delete trigger failed |
| 102012 | LatestRunIdNotFound | Latest run ID not found |
| 102013 | ExternalAgentApiArgumentsError | External Agent API invalid value in input |
| 102014 | FileRefRequiredToDataFabric | File reference required to host a file in Data Fabric |
| 102015 | IntSvcListElementsFailed | Integration Services failed on listing elements operation |
| 102016 | DebugTriggerEventNoDataError | Trigger activity could not find any matches |
| 102017 | IntSvcUnifiedHttpRequestInvalidInputError | Invalid input on Unified HttpRequest operation |
| 102018 | IntSvcUnifiedHttpRequestArgumentsError | Invalid value in Unified HttpRequest input |

## Orchestrator Runtime (170000–170041)

| Code | Name | Message |
|------|------|---------|
| 170000 | HitlTaskOperationFailed | Failure in the AppTasks request |
| 170001 | HitlTaskResultByIdFailed | Failure mapping the data from the task result |
| 170002 | OrchestratorJobFailed | Failure in the Orchestrator Job |
| 170003 | PoRuntimeOperationFailed | Failure in the PO runtime operation |
| 170004 | HitlTaskInputInvalid | Invalid input for the HITL task |
| 170005 | OrchestratorRpaTaskInputInvalid | Invalid input arguments for the Orchestrator RPA task |
| 170006 | OrchestratorRpaFailed | Failure in the Orchestrator RPA job |
| 170007 | OrchestratorRpaJobFailedToStart | Failure to start the Orchestrator RPA job |
| 170008 | ExecuteWorkflowApiInputError | Invalid input for the ExecuteWorkflowApi activity |
| 170009 | ApiWorkflowExecutionArgumentsError | Invalid value in input for Api Workflow Execution |
| 170010 | OrchestratorQueueArgumentsError | Invalid arguments for Orchestrator queue-items |
| 170011 | OrchestratorQueueItemNotInExpectedState | Orchestrator queue-item is not in expected state, yet |
| 170012 | OrchestratorQueueItemFailed | Orchestrator queue-item is in Failed state |
| 170013 | OrchestratorJobDeserializeError | Failure in deserializing Orchestrator Job response |
| 170014 | HiltTaskAppsFetchFailed | HITL task apps fetch failed |
| 170015 | HitlTaskNoAppsFoundForGivenInput | No apps found for given input |
| 170016 | JobAttachmentDownloadError | Error downloading job attachment from Orchestrator |
| 170030 | OrchestratorApiServerlessJobFailed | Failed to invoke serverless job via Orchestrator API |
| 170031 | OrchestratorApiFolderLookupFailed | Failed to retrieve folders from Orchestrator API |
| 170032 | UnknownJobAttachmentRefError | Unknown job attachment reference |
| 170033 | InvalidJobAttachmentRefError | Invalid job attachment reference |
| 170034 | OrchestratorGetMachineClientIdError | Failure to start the Orchestrator RPA job |
| 170035 | OrchestratorServerlessJobFailed | Failure to start the Orchestrator RPA job |
| 170036 | OrchestratorGetRetentionPeriodError | Failed to retrieve retention period from Orchestrator |
| 170037 | HitlAppTaskDetailsFetchFailed | Failure to fetch actionable app task details |
| 170038 | OrchestratorQueueItemCreateFailed | Failed to create queue-item in Orchestrator |
| 170039 | OrchestratorQueueItemFetchFailed | Failed to fetch queue-item |
| 170040 | OrchestratorQueueItemDeleted | Queue item is in deleted state |
| 170041 | OrchestratorGetReleasesBindingsFailed | Failed to fetch bindings from Orchestrator for release |

## BPMN Engine (300000–300010)

| Code | Name | Message |
|------|------|---------|
| 300000 | UnsupportedExtensionType | Unsupported extension type |
| 300001 | InvalidOrCorruptedBpmnModel | Invalid or corrupted BPMN model |
| 300002 | PatchGlobalVariablesFailure | Error patching global variables |
| 300003 | PatchElementInputsFailure | Error patching inputs |
| 300004 | EngineMetadataDeserializationError | Error deserializing engine result metadata |
| 300005 | FaultedElementThrewNonProblemDetailsException | Unexpected error thrown by BPMN element |
| 300006 | GoToTransitionSourceNotFound | Source in GoTo transition not found |
| 300007 | GoToTransitionTargetNotFound | Target in GoTo transition not found |
| 300008 | GoToTransitionTargetTypeNotSupported | Target type in GoTo transition not supported |
| 300009 | GoToTransitionSubprocessElementsNotSupported | Transitions involving subprocess elements are not supported |
| 300010 | UserDefined | User Defined Error |

## Data Fabric (300200–300208)

| Code | Name | Message |
|------|------|---------|
| 300200 | DataFabricOperationError | Error in a Data Fabric operation |
| 300201 | DataFabricUploadFileError | Error uploading file to Data Fabric |
| 300202 | DataFabricDownloadFileError | Error downloading file from Data Fabric |
| 300203 | DataFabricReadRecordError | Error reading record from Data Fabric |
| 300204 | DataFabricInsertRecordError | Error inserting record in Data Fabric |
| 300205 | DataFabricQueryExpansionError | Error executing query expansion in Data Fabric |
| 300206 | DataFabricQueryExpansionInvalidFilterError | Invalid filter expression for Data Fabric query expansion |
| 300207 | DataFabricQueryExpansionNoResultsError | No results found for Data Fabric query expansion |
| 300208 | DataFabricUpdateRecordError | Error updating record in Data Fabric |

## Business Rules (300400–300403)

| Code | Name | Message |
|------|------|---------|
| 300400 | BusinessRulesTaskArgumentsError | Invalid business rule task arguments |
| 300401 | BusinessRulesGetRuleFailed | Error getting business rule |
| 300402 | BusinessRulesDownloadRuleFailed | Error downloading business rule |
| 300403 | BusinessRulesParseRuleFailed | Error parsing business rule |

## Script Tasks (300500–300503)

| Code | Name | Message |
|------|------|---------|
| 300500 | ScriptTaskArgumentsError | Invalid script task arguments |
| 300501 | ScriptTaskInvocationError | Error invoking script task |
| 300502 | ScriptTaskInvocationResultError | Error obtaining valid script task result |
| 300503 | ScriptTaskInternalInvocationError | Internal script task invocation error |

## HTTP Request Tasks (300600–300604)

| Code | Name | Message |
|------|------|---------|
| 300600 | HttpRequestArgumentsError | Invalid HTTP request arguments |
| 300601 | HttpRequestExecutionError | Error executing HTTP request |
| 300602 | HttpRequestTimeoutError | HTTP request timed out |
| 300603 | HttpRequestInvalidResponseError | Invalid HTTP response received |
| 300604 | HttpRequestUnexpectedError | Unexpected error occurred during HTTP request |

## BPMN Elements (400000–400023)

| Code | Name | Message |
|------|------|---------|
| 400000 | ErrorEndEvent | User defined error for BPMN end event |
| 400001 | NoOutgoingFlow | No condition for an outgoing flow was met. At least one outgoing flow condition needs to evaluate to true or have a default flow. |
| 400002 | ElementExecution | Failed to Execute Bpmn Element |
| 400003 | FailedToParseXml | Failed To Parse BPMN Xml |
| 400004 | InvalidBpmnWorkflowArgs | Invalid Bpmn Workflow Args |
| 400005 | FailedToRetrieveXml | Failed to Retrieve BPMN XML |
| 400006 | BpmnGenericWorkflowFailure | BPMN generic workflow failure |
| 400007 | BpmnMarkerInputNullError | Input collection for the marker element must not be null |
| 400008 | BpmnMarkerInputEvaluationFailure | Failed to evaluate the input collection variable for the marker element |
| 400009 | ElementExecutionLoopDetected | This element has executed an abnormal number of times. Potential loop detected. |
| 400010 | CaseManagementInvalidJson | Invalid case management process metadata JSON format |
| 400020 | CreateTriggersForEventSubProcessFailed | Failed to create triggers for Event SubProcess |
| 400023 | CasePlanOverviewParseError | Failed to retrieve the case plan overview |

## Expression Evaluation (400300–400302)

| Code | Name | Message |
|------|------|---------|
| 400300 | InputVariablesEvaluationError | Error evaluating expression in activity inputs |
| 400301 | ExpressionEvaluationError | Error evaluating expression |
| 400302 | FlowExpressionEvaluationError | Error evaluating outgoing flow expression from gateway |

## Licensing (400500–400505)

| Code | Name | Message |
|------|------|---------|
| 400500 | LicensingClientCanConsumeException | Licensing consumption error |
| 400501 | LicensingRegisterConsumptionException | Licensing registration error |
| 400502 | LicensingIsNotValidException | User is not authorized to debug due to missing license |
| 400503 | LicensingCanConsumeDebugException | User is not licensed to continue |
| 400504 | LicensingIsNotValidOnRetryException | User is not licensed to continue |
| 400505 | InvalidLicensingContextFormat | The licensing context format is invalid |

## Auth & Permissions (150001–150009)

| Code | Name | Message |
|------|------|---------|
| 150001 | FolderScopedAttributeFolderKeyMissing | Required header 'x-uipath-folderkey' is missing or empty |
| 150006 | AuthzFolderPermissionMissing | Folder permission missing |
| 150007 | AuthzFolderPermissionException | Permission denied for folder |
| 150009 | AccessTokenPrtIdAccountHeaderMismatch | Unauthorized |

## Message Events (450002–450013)

| Code | Name | Message |
|------|------|---------|
| 450002 | MaestroMessageSendEventArgsError | Invalid arguments for Message Send Event |
| 450003 | MaestroMessageSendEventInputError | Invalid input for Message Send Event |
| 450004 | MaestroMessageReceiveEventArgsError | Invalid arguments for Message Receive Event |
| 450005 | MaestroMessageBufferingFailure | Failed to buffer message for later consumption |
| 450006 | MaestroMessagePublishFailure | Failed to publish message |
| 450007 | MaestroMessageDuplicateSubscriber | Duplicate message subscription detected |
| 450008 | MaestroMessageSubscriptionFailed | Failed to create message subscription |
| 450010 | MaestroMessageReceiveFromBlobFailed | No message found |
| 450011 | MaestroMessageSendEventBlobFailure | Failed to handle message publish |
| 450012 | MaestroMessageSendFailure | Failed to send maestro message |
| 450013 | MaestroMessageReceiverNotFound | Message receiver not found |
