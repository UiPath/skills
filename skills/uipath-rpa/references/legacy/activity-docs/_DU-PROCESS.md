# UiPath Document Understanding Process Template - Complete Reference

## Overview
The Document Understanding Process is a **fully functional Studio template** for processing documents through a complete pipeline: digitize, classify, validate classification, extract data, validate extraction, train models, and export results. It comes with built-in retry logic, error handling, multi-robot synchronization, and Action Center integration.

**Source**: [UiPath Docs](https://docs.uipath.com/document-understanding/automation-suite/2024.10/classic-user-guide/du-process) | [Forum Announcement](https://forum.uipath.com/t/document-understanding-process-new-studio-template/330234)

**Key Design**: One job per document (not bulk). Requires a **dispatcher** to feed queue items.

---

## 1. File Structure (from Desktop Template)

```
DocumentUnderstandingProcess/
├── Main-ActionCenter.xaml              # Entry point for UNATTENDED (Action Center validation)
├── Main-Attended.xaml                  # Entry point for ATTENDED (local Validation Station)
├── project.json                        # Project config (supportsPersistence=true!)
│
├── Data/
│   ├── Config.xlsx                     # Configuration (Settings/Constants/Assets)
│   └── ExampleDocuments/
│       └── MergedDocuments.pdf         # Sample multi-page document
│
├── DocumentProcessing/
│   ├── taxonomy.json                   # Document taxonomy definition
│   └── IntelligentKeywordLearningFile.json  # Classifier training data
│
├── Framework/                          # Processing pipeline (numbered for execution order)
│   ├── 00_ReadConfigFile.xaml          # Read Config.xlsx → Dictionary
│   ├── 10_InitializeProcess.xaml       # Load taxonomy + Orchestrator assets
│   ├── 15_GetTransactionItem.xaml      # Get queue item + extract TargetFile
│   ├── 20_Digitize.xaml               # OCR → Document Object Model + Text
│   ├── 30_Classify.xaml               # Auto-classify document type
│   ├── 35_ClassificationBussinessRuleValidation.xaml  # Validate classification
│   ├── 40_TrainClassifiers.xaml        # Train classifier with validated data
│   ├── 50_Extract.xaml                # Extract field values
│   ├── 55_ExtractionBussinessRuleValidation.xaml      # Validate extraction
│   ├── 60_TrainExtractors.xaml         # Train extractor with validated data
│   ├── 70_Export.xaml                 # Export results (Excel example)
│   ├── 80_EndProcess.xaml             # Mark transaction successful
│   ├── ERR_AbortProcess.xaml           # Handle fatal process errors
│   ├── ERR_HandleDocumentError.xaml    # Handle per-document errors
│   └── ReusableWorkflows/
│       ├── SetTransactionStatus.xaml   # Set queue item Success/Failed
│       ├── SetTransactionProgress.xaml # Update progress in Orchestrator
│       ├── InvoicePostProcessing.xaml  # Invoice-specific validation rules
│       ├── LockFile.xaml              # File lock for multi-robot sync
│       ├── UnlockFile.xaml            # File unlock
│       ├── GetWritePermission.xaml     # Queue-based semaphore acquire
│       └── GiveUpWritePermission.xaml  # Queue-based semaphore release
│
├── UserGuide/
│   └── Document Understanding Process - User Guide.pdf
│
└── Exceptions_Screenshots/             # (optional) Error screenshots
```

---

## 2. Two Entry Points: Attended vs Action Center

| | Main-Attended.xaml | Main-ActionCenter.xaml |
|---|-------------------|----------------------|
| **`in_UseQueue`** | `False` (default) | `True` (default) |
| **Validation** | Local Validation Station (desktop UI) | Action Center (Orchestrator web UI) |
| **Persistence** | Not required | `supportsPersistence=true` required |
| **Robot Type** | Attended or unattended | Unattended (long-running) |
| **Human-in-loop** | User sees validation dialog | User completes tasks in Action Center |
| **Queue** | Optional | Required |

### Main.xaml Arguments
| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `in_TargetFile` | InArgument\<String\> | | Path to document to process |
| `in_UseQueue` | InArgument\<Boolean\> | True/False | Whether using Orchestrator queues |

---

## 3. Processing Pipeline (Step by Step)

```
00_ReadConfigFile → 10_Initialize → 15_GetTransactionItem
                                          ↓
    ┌─────── FOR EACH CLASSIFIED DOCUMENT ────────┐
    │                                               │
    │  20_Digitize → 30_Classify                   │
    │       ↓                                       │
    │  35_ClassificationValidation                  │
    │       ↓ (if manual needed)                    │
    │  [Classification Station / Action Center]     │
    │       ↓                                       │
    │  40_TrainClassifiers (with validated data)    │
    │       ↓                                       │
    │  50_Extract → 55_ExtractionValidation         │
    │       ↓ (if manual needed)                    │
    │  [Validation Station / Action Center]         │
    │       ↓                                       │
    │  60_TrainExtractors (with validated data)     │
    │       ↓                                       │
    │  70_Export → 80_EndProcess                    │
    │                                               │
    └───────────────────────────────────────────────┘
           ↓ (on error)
    ERR_HandleDocumentError (per-document)
    ERR_AbortProcess (fatal/process-level)
```

---

## 4. Workflow Details

### 00_ReadConfigFile.xaml
- Reads Config.xlsx Settings + Constants sheets into Dictionary\<String, String\>
- Calculates `MaxAttempts` (minimum 1) and `RetryInterval` from config
- **No retry mechanism** — config file must be accessible

### 10_InitializeProcess.xaml
- **LoadTaxonomy** from `taxonomy.json`
- Reads Assets sheet → fetches each from Orchestrator via **Get Robot Asset**
- If asset fetch fails but key exists in config: silently continues (fallback value)
- If asset fetch fails and key missing: throws (asset is required)
- Wrapped in **RetryScope** for Orchestrator connectivity issues

### 15_GetTransactionItem.xaml
- **Get Transaction Item** from Orchestrator queue
- Extracts `TargetFile` from `TransactionItem.SpecificContent["TargetFile"]`
- **Copies ALL SpecificContent into Config dictionary** for process-wide access
- Wrapped in RetryScope

### 20_Digitize.xaml
- **DigitizeDocument** activity with embedded OCR engine
- Default: **UiPath Document OCR** (cloud API)
- DegreeOfParallelism=-1 (unlimited parallel page processing)
- Has config-specific `MaxExecutionAttemptsDigitize` override
- **Warning**: OCR is API-based and incurs costs on retry

### 30_Classify.xaml
- **ClassifyDocumentScope** with **IntelligentKeywordClassifier**
- Uses learning file from `DocumentProcessing/IntelligentKeywordLearningFile.json`
- Pre-configured for: Receipt, Invoice, W-9, Certificate-of-filing
- Returns ClassificationResult[] with confidence scores

### 35_ClassificationBussinessRuleValidation.xaml (Flowchart)
- Checks `AlwaysValidateClassification` config flag
- FlowSwitch on DocumentTypeId for type-specific rules
- Sets `AutoClassificationSuccess` = False to trigger manual validation
- **Customization point**: Add your classification business rules here

### 40_TrainClassifiers.xaml
- **File locking** mechanism for multi-robot synchronization:
  1. LockFile.xaml copies classifier file with `.lock` suffix
  2. TrainClassifiersScope writes to lock copy
  3. UnlockFile.xaml moves lock copy back (Overwrite=True)
- **ContinueOnError=True** on training (prefer losing training data over blocking extraction)
- **ContinueOnError=False** on unlock (critical — failure blocks ALL future training)

### 50_Extract.xaml
- **DataExtractionScope** with configured extractors
- Extractor choice depends on document type (Form Extractor, ML Extractor, Regex)
- Has config-specific `MaxExecutionAttemptsExtract` override

### 55_ExtractionBussinessRuleValidation.xaml (Flowchart)
- Checks `AlwaysValidateExtraction` config flag
- FlowSwitch on DocumentTypeId
- **Invoice case**: Calls InvoicePostProcessing.xaml with validation rules:
  1. Verify mandatory fields extracted
  2. Verify Quantity × Unit Price = Line Amount per row
  3. Verify sum of Line Amounts = Net Amount
  4. Verify Net Amount + charges = Total
  5. Verify field confidence thresholds
- Sets `AutoExtractionSuccess` = False for manual validation

### 60_TrainExtractors.xaml
- **TrainExtractorsScope** with human-validated data
- ContinueOnError=True (prefer export over training loss)

### 70_Export.xaml
- **ExportExtractionResults** → DataSet (IncludeConfidence=True)
- Default: Writes each DataTable to Excel sheet
- Output path: `ExportsFolder/DocumentId_StartPage-EndPage.xlsx`
- **Example only** — real implementations should use Data Service or database

### 80_EndProcess.xaml
- Calls SetTransactionStatus with Success
- Customization point for post-export logic

---

## 5. Error Handling

### Two Error Handlers
| Handler | Scope | Triggered By | Default Action |
|---------|-------|-------------|----------------|
| `ERR_HandleDocumentError.xaml` | Per-document | Exception during document processing | Log warning, continue to next document |
| `ERR_AbortProcess.xaml` | Process-level | Fatal exception (init failure, queue error) | Log error, terminate process |

### Exception Types (same as REFramework)
- **BusinessRuleException**: Data problem → skip document, don't retry
- **System.Exception**: Technical problem → can retry with reinitialization

### SetTransactionStatus (Flowchart)
- **Success**: Both exceptions null → Set status "Successful"
- **Business Exception**: BusinessRuleException or DocumentRejectedByUserException → Status "Failed", ErrorType "Business"
- **System Exception**: Any other exception → Status "Failed", ErrorType "Application"

---

## 6. Multi-Robot Synchronization

Two mechanisms for concurrent access to training files:

### File Locking (used by default for classifier training)
1. `LockFile.xaml`: Copy file with `.lock` suffix → work on copy
2. `UnlockFile.xaml`: Move copy back → overwrite original
- **Risk**: Two robots writing simultaneously → one's training data lost

### Queue-Based Semaphore (alternative)
1. Create Orchestrator queue with SINGLE item, no auto-retry
2. `GetWritePermission.xaml`: Loop until queue item obtained (= semaphore acquired)
3. `GiveUpWritePermission.xaml`: Mark item successful + recreate it (= semaphore released)
- **Stronger guarantee** but requires Orchestrator queue setup

---

## 7. Dependencies (Current Template)

```json
{
  "UiPath.DocumentUnderstanding.ML.Activities": "[1.9.1]",
  "UiPath.Excel.Activities": "[2.11.4]",
  "UiPath.IntelligentOCR.Activities": "[5.0.2]",
  "UiPath.System.Activities": "[21.10.2]",
  "UiPath.UIAutomation.Activities": "[21.10.3]"
}
```

Additional assembly references: `UiPath.Persistence.Activities`, `UiPath.OmniPage.Activities`, `UiPath.PDF.Activities`, `UiPath.DocumentProcessing.Contracts`, `UiPath.OCR.Contracts`

**Key**: `supportsPersistence: true` in project.json (required for Action Center mode)

---

## 8. Taxonomy Structure (taxonomy.json)

Pre-configured document types:

| Document Type ID | Category |
|-----------------|----------|
| `Semi-StructuredDocuments.Financial.Receipt` | Receipts |
| `Semi-StructuredDocuments.Financial.Invoice` | Invoices (with line items table) |
| `StructuredDocuments.LendingForms.W-9` | US tax form |
| `Documents.Other.Certificate-of-filing` | Filing certificates |

### Invoice Fields (example)
- **Header**: Vendor Name, Address, VAT Number, Invoice No, PO No, Invoice Date, Due Date
- **Amounts**: Net Amount, Tax Amount, Total, Discount, Shipping Charges
- **Line Items Table**: Line Number, Description, Quantity, Unit Price, Line Amount, Part Number
- **Payment**: Terms, Currency

Supported languages: 26 (EN, DE, FR, ES, RU, ZH, JA, etc.)

---

## 9. Config.xlsx Key Settings

| Setting | Purpose | Default |
|---------|---------|---------|
| `MaxExecutionAttempts` | Default retry count | 3 |
| `RetryInterval` | Seconds between retries | 5 |
| `MaxExecutionAttemptsDigitize` | Digitization-specific retries | (overrides default) |
| `MaxExecutionAttemptsClassify` | Classification-specific retries | (overrides default) |
| `MaxExecutionAttemptsExtract` | Extraction-specific retries | (overrides default) |
| `AlwaysValidateClassification` | Force manual classification review | True/False |
| `AlwaysValidateExtraction` | Force manual extraction review | True/False |
| `DocumentUnderstandingQueueName` | Orchestrator queue name | |
| `DocumentUnderstandingQueuePath` | Orchestrator queue folder | |
| `ClassifierLearningFilePath` | Path to classifier training file | |
| `ExportsFolder` | Output folder for exported results | |
| `logKey` | Auto-generated GUID+timestamp for log tracking | |

---

## 10. Critical Gotchas

### Architecture
1. **One job per document** — NOT bulk processing. Requires dispatcher to populate queue.
2. **supportsPersistence=true required** for Action Center mode — set in project.json
3. **Process.xaml does NOT exist at root** — business logic is inside the numbered Framework workflows
4. **NOT a State Machine** — unlike REFramework, this is a Sequence/Flowchart pipeline

### OCR & Digitization
5. **OCR is API-based (cloud)** — incurs costs on every call, including retries
6. **DegreeOfParallelism=-1** means unlimited — can hit API rate limits
7. **"Input document not found"** — [common error](https://forum.uipath.com/t/document-understanding-process-download-document/738008) when path resolution fails
8. **.NET framework missing** — [reported issue](https://forum.uipath.com/t/document-understanding-error-install-missing-frameworks-for-net/727634) with template setup

### Classification & Extraction
9. **Classifiers and extractors are process-dependent** — must configure for YOUR document types
10. **IntelligentKeywordClassifier needs training data** — `IntelligentKeywordLearningFile.json` must be populated
11. **ML Extractor failures** — [common](https://forum.uipath.com/t/machine-learning-extractor-failed-in-50-extract-document-understanding-template/539547) with wrong API keys or model configuration
12. **Taxonomy must match exactly** — DocumentTypeId in taxonomy.json must match classifier configuration

### Training & Synchronization
13. **Training data CAN be lost** — ContinueOnError=True on training; two robots writing simultaneously overwrites
14. **UnlockFile ContinueOnError=False** — if unlock fails, ALL future training blocked
15. **Queue semaphore requires setup** — single-item queue with NO auto-retry

### Validation
16. **InvoicePostProcessing uses EN-US culture** — decimal ".", thousand "," — will fail for other locales
17. **"Do NOT use InvoicePostProcessing as-is"** — template annotation warns it's for demos only
18. **AlwaysValidateClassification/Extraction** — set True during development, tune confidence thresholds for production

### Action Center Mode
19. **Requires Orchestrator 2021.10+** for full Action Center support
20. **Persistence activities serialize workflow state** — all variables at suspension point must be serializable
21. **Cannot have open UI scopes** across Action Center suspension points

---

## 11. Customization Checklist

- [ ] **Config.xlsx**: Set queue name, asset names, retry parameters
- [ ] **taxonomy.json**: Define YOUR document types and fields via Taxonomy Manager
- [ ] **30_Classify.xaml**: Configure classifiers for your document types
- [ ] **50_Extract.xaml**: Configure extractors for your document types
- [ ] **35_ClassificationBussinessRuleValidation.xaml**: Add classification rules
- [ ] **55_ExtractionBussinessRuleValidation.xaml**: Add extraction validation rules
- [ ] **70_Export.xaml**: Replace Excel export with your target system (DB, API, Data Service)
- [ ] **Dispatcher workflow**: Create separate workflow to populate queue with TargetFile paths
- [ ] Choose entry point: Main-Attended.xaml (local) or Main-ActionCenter.xaml (Orchestrator)
- [ ] Train classifiers with sample documents before production

---

## Sources
- [UiPath Docs - Document Understanding Process Template](https://docs.uipath.com/document-understanding/automation-suite/2024.10/classic-user-guide/du-process)
- [UiPath Forum - DU Process Template Announcement](https://forum.uipath.com/t/document-understanding-process-new-studio-template/330234)
- [UiPath Docs - About DU Process](https://docs.uipath.com/activities/other/latest/document-understanding/about-document-understanding-process-studio-template)
- Desktop template: `C:\Users\alexandru.roman\Documents\UiPath\legacy_tests\DocumentUnderstandingProcess\`
