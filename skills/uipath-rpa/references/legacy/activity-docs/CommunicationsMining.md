# UiPath Communications Mining Activities - Legacy Reference

## Overview
Data validation workflows for Communications Mining AI engine (email/chat classification). Package: `UiPath.CommunicationsMining.Activities`.

---

## Activities

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `CreateCommunicationsMiningValidationAction` | Create Action Center task | ActionTitle, ActionPriority, ActionCatalogue -> CreatedValidationAction |
| `CreateCommunicationsMiningValidationArtifacts` | Upload training data | OrchestratorBucketFolderPath |
| `RetrieveCommunicationsMiningValidationArtifacts` | Download validated data | ContentValidationData, RemoveDataFromStorage -> StreamResult |
| `WaitForCommunicationsMiningValidationAction` | Wait for human review | (blocks until Action Center complete) |

---

## Critical Gotchas

1. **Requires Communications Mining tenant/project setup** in UiPath platform
2. **Action Center integration** for human-in-the-loop validation workflows
3. **Bearer token authentication** for CM API calls
4. **Cloud storage bucket path required** for artifact storage
5. **Async operations** - must handle task lifecycle properly
6. **Discovery client needs OAuth configuration** for API endpoints
7. **Streaming predictions** via CM API client for real-time classification
8. **Depends on**: UiPath.DocumentProcessing.Contracts, UiPath.DocumentUnderstanding.Persistence
