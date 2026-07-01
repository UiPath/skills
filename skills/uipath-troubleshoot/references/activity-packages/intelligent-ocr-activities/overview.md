# Intelligent OCR / Document Understanding (Classic) Activities

Activities from the `UiPath.IntelligentOCR.Activities` package — the **classic Document Understanding** framework: **Digitize Document** (`DigitizeDocument`), **Classify Document Scope** (`ClassifyDocumentScope`), **Data Extraction Scope** (`DataExtractionScope`), **Present Validation Station** (`PresentValidationStation`), **Export Extraction Results** (`ExportExtractionResults`), and the Train Classifiers/Extractors scopes. Taxonomies, classifiers, and extractors drive the digitize → classify → extract → validate → export pipeline.

## How These Activities Work

The pipeline combines local config (taxonomy, classifier/extractor configuration) with calls to external services:

1. **Tenant / project setup.** The activities resolve the Document Understanding tenant context (project list, tenant key). If DU isn't enabled/licensed on the tenant, this fails before any document is processed.
2. **DU server calls.** Digitization (OCR) and ML extraction/classification call a Document Understanding server / endpoint over HTTP (`DUServerCaller`). The call is authenticated with an API key / license; failures here surface as `UiPath.SmartData.Utils.DocumentUnderstandingClient.DUApiException` carrying the HTTP status, response content, `CF-RAY`, and `AppId`.
3. **Storage access.** Taxonomy, trained models, and validated extraction results are read from / written to Orchestrator storage buckets and folders. A missing bucket / blob path / folder fails the read.
4. **Validation Station.** `Present Validation Station` shows a human the extracted data; the human can reject the document, which raises `DocumentRejectedByUserException`.

## Key Activities

- **Digitize Document** (`UiPath.IntelligentOCR.Activities.DigitizeDocument`) — OCR + text/layout via a DU endpoint.
- **Classify Document Scope** (`ClassifyDocumentScope`) — classify the document type.
- **Data Extraction Scope** (`DataExtractionScope`) — extract fields via configured extractors.
- **Present Validation Station** (`PresentValidationStation`) — human-in-the-loop validation.
- **Export Extraction Results** (`ExportExtractionResults`) — emit results (e.g. DataSet).

## Common Failure Patterns

- **License / endpoint rejected the call** — `DUApiException`: `Your license could not be validated...`, `Failed to consume the requested number of pages...`, `You have exceeded the request size limitations...`, `The service has rejected the request. Please make sure you are using the correct endpoint...`, `Response signature is invalid. Endpoint is not supported.`, or the generic `DocumentUnderstanding server returned <code> ...`. See [du-license-or-endpoint-rejected.md](./playbooks/du-license-or-endpoint-rejected.md).
- **DU not enabled / tenant key** — `Failed to fetch Document Understanding projects list. Please connect to a tenant that has Document Understanding enabled.`, `Couldn't retrieve a tenant key.`, `Information about tenant <id> couldn't be retrieved.`. See [du-not-enabled-or-tenant-key.md](./playbooks/du-not-enabled-or-tenant-key.md).
- **Storage bucket / taxonomy / folder missing** — `No such bucket named '<name>'`, `Couldn't find path <p> in bucket <b> associated with '<x>'`, `The local directory path '<path>' could not be found.`, `Could not load the <x> from storage bucket <b> and path <p>`, `Could not find Orchestrator Folder '<name>'`. See [du-storage-or-taxonomy-missing.md](./playbooks/du-storage-or-taxonomy-missing.md).
- **Document rejected at Validation Station** — `DocumentRejectedByUserException` (a human rejected the document). See [du-document-rejected.md](./playbooks/du-document-rejected.md).

> The **invalid-API-key** case IS reproducible locally (Digitize Document + UiPath Document OCR with a bad key). **Tenant-not-enabled**, **storage/taxonomy**, and **document-rejected** failures generally need a licensed DU endpoint + OCR + trained models / a non-DU tenant / a HITL pipeline. Diagnosis is evidence-based from the faulted job's exception text + configuration.

## Package

NuGet: `UiPath.IntelligentOCR.Activities` · Exceptions: `UiPath.SmartData.Utils.DocumentUnderstandingClient.DUApiException`, `UiPath.IntelligentOCR.Exceptions.DocumentRejectedByUserException`
