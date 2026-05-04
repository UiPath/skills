# Document Understanding Review Checklist

Quality checklist for UiPath projects that use Document Understanding (DU) — extracting structured data from unstructured documents (invoices, contracts, forms, receipts).

> Use this checklist alongside [rpa-review-checklist.md](../rpa/rpa-review-checklist.md). DU projects are RPA projects with DU-specific packages and activities. Review both checklists.

## 1. Detection — Is This a DU Project?

A project uses Document Understanding if **any** of these signals are present:

| Signal | Where to Check |
|---|---|
| `UiPath.IntelligentOCR.Activities` in dependencies | `project.json` → `dependencies` |
| `UiPath.DocumentUnderstanding.ML.Activities` in dependencies | `project.json` → `dependencies` |
| `UiPath.DocumentProcessing.Contracts` in dependencies | `project.json` → `dependencies` |
| `Digitize Document` activity in XAML | Grep `.xaml` for `DigitizeDocument` |
| `Classify Document Scope` activity in XAML | Grep `.xaml` for `ClassifyDocumentScope` |
| `Data Extraction Scope` activity in XAML | Grep `.xaml` for `DataExtractionScope` |
| `Present Validation Station` activity in XAML | Grep `.xaml` for `PresentValidationStation` |
| Document Understanding Process Template usage | Check project template origin |

If none of these signals are present, skip this checklist.

## 2. Pipeline Architecture

### Four-Stage Pipeline

Every DU project must implement the four-stage pipeline. Verify each stage is present:

| Stage | Required Activity | Severity if Missing |
|---|---|---|
| 1. Digitization | `Digitize Document` (OCR) | Critical — no text extraction without it |
| 2. Classification | `Classify Document Scope` with at least one classifier | Warning — unclassified documents cannot route to correct extractors |
| 3. Extraction | `Data Extraction Scope` with at least one extractor | Critical — no data extraction without it |
| 4. Validation | `Present Validation Station` or auto-validation logic | Warning — no human review for low-confidence results |

### Template Usage

| Check | Severity | How to Verify |
|---|---|---|
| DU Process Template used as base (not built from scratch) | Info | Check project template metadata or workflow structure |
| Pipeline stages are in correct order (Digitize → Classify → Extract → Validate) | Critical | Read workflow structure — verify activity sequence |
| Each document type routes to its own extraction configuration | Warning | Check classifier-to-extractor mapping |
| Pipeline handles multi-page documents correctly | Warning | Verify document splitting/merging logic |

## 3. Digitization / OCR Configuration

### OCR Engine Selection

| Document Quality | Recommended Engine | Flag If Wrong |
|---|---|---|
| High-quality scans, digital PDFs | UiPath Document OCR | Using expensive cloud OCR unnecessarily (Info) |
| Poor-quality scans, faded/skewed | Google Cloud Vision or Azure Computer Vision | Using basic OCR on poor scans (Warning) |
| Handwritten text | Specialized OCR or GenAI extraction | Using standard OCR on handwritten (Warning) |
| Multiple languages in one document | Verify engine supports all languages | Missing language support (Warning) |

### OCR Checks

| Check | Severity | How to Verify |
|---|---|---|
| OCR engine is explicitly configured (not relying on default) | Warning | Check `Digitize Document` activity properties |
| OCR language setting matches document language | Warning | Check language configuration |
| Image pre-processing configured for poor-quality inputs | Info | Check for deskew, rotation, noise removal settings |
| OCR engine tested with representative document samples | Info | Check for test results or evaluation notes |
| No unnecessary OCR on already-digital PDFs | Info | Check if digital PDF bypass is configured |

## 4. Classification Stage

### Classifier Configuration

| Check | Severity | How to Verify |
|---|---|---|
| At least one classifier configured in `Classify Document Scope` | Critical | Read XAML — check classifier activities inside scope |
| Multiple classifiers chained for reliability | Info | Check for >1 classifier in the scope |
| Classifier order follows reliability escalation (Keyword → ML → GenAI) | Info | Verify classifier sequence |
| Confidence threshold configured per document type | Warning | Check classifier confidence settings |
| Fallback handling for unrecognized document types | Warning | Check for default/unknown classification path |

### Classifier Chaining Strategy

| Classifier Type | When to Use | Detection |
|---|---|---|
| Keyword Classifier | Documents with distinctive headers/keywords (e.g., "INVOICE", "PURCHASE ORDER") | Grep for `KeywordClassifier` in XAML |
| Intelligent Keyword Classifier | Enhanced version with ML-backed keyword matching | Grep for `IntelligentKeywordClassifier` |
| ML Classifier | Complex documents, many types, layout variations | Grep for `MLClassifier` or `DocumentClassifier` |
| GenAI Classification | Zero-shot for new document types, prototyping | Grep for GenAI classifier activities |

### Classification Quality Checks

| Check | Severity | How to Verify |
|---|---|---|
| Documents below confidence threshold route to human review | Warning | Check classification confidence branching logic |
| Classification results logged for monitoring | Info | Check for logging after classification |
| All expected document types have classifier coverage | Warning | Compare configured types against PDD/requirements |
| Unrecognized documents do not silently fail | Critical | Verify exception path for unknown types |

## 5. Extraction Stage

### Extractor Configuration

| Check | Severity | How to Verify |
|---|---|---|
| At least one extractor configured in `Data Extraction Scope` | Critical | Read XAML — check extractor activities inside scope |
| Extractors chained per document type for coverage | Warning | Check for >1 extractor per type |
| Extractor order follows cost-efficiency (RegEx → Form → ML → GenAI) | Info | Verify extractor sequence |
| Per-field confidence thresholds set based on business criticality | Warning | Check field-level confidence settings |
| All required fields defined in extraction taxonomy | Critical | Compare extracted fields against PDD/requirements |

### Extractor Type Appropriateness

| Extractor Type | Best For | Flag If Misused |
|---|---|---|
| RegEx Extractor | Structured fields: dates, amounts, IDs, phone numbers | Used for free-text fields (Warning) |
| Form Extractor | Fixed-layout forms with consistent field positions | Used for variable-layout documents (Warning) |
| ML Extractor | Variable layouts, trained on document samples | Used without training data for production (Warning) |
| GenAI Extraction | New document types, zero-shot, prototyping, low volume | Used for high-volume production without ML (Info) |

### Extraction Quality Checks

| Check | Severity | How to Verify |
|---|---|---|
| High-criticality fields (amounts, dates, IDs) have stricter confidence thresholds | Warning | Compare threshold values per field |
| Extraction handles missing/optional fields gracefully | Warning | Check for null/empty field handling |
| Table extraction configured for line-item documents (invoices, POs) | Warning | Check for table extraction activities if documents contain tables |
| Extraction results mapped to correct output variables | Critical | Verify field-to-variable mapping |
| No hardcoded field names that differ from taxonomy definitions | Warning | Compare extraction config against taxonomy |
| Business rule validation used for cross-field checks (e.g., net + tax = total) | Warning | Check for post-extraction validation logic using regex or formula checks |

### Confidence Threshold Guidance

Confidence thresholds are a **safety net / fallback**, not the primary error detection method:
- Confidence can never be 100% — there is always a small percentage of correct predictions with low confidence and wrong predictions with high confidence
- A **missing field has NO confidence** — thresholds cannot catch missing-field errors. Add explicit null/empty checks.
- Check BOTH Extraction Confidence AND OCR Confidence for each value
- Sort test results by confidence to identify where errors begin; set threshold above that level

## 6. Validation & Human-in-the-Loop

| Check | Severity | How to Verify |
|---|---|---|
| Validation Station configured for human review | Warning | Grep for `PresentValidationStation` |
| Auto-validation for high-confidence results (skip human review) | Info | Check for confidence-based branching before Validation Station |
| Validation Station shows only fields that need review (not entire document) | Info | Check Validation Station configuration |
| Validated corrections feed back to improve ML models | Info | Check for `Train Classifiers Scope` or `Train Extractors Scope` |
| Action Center configured for routing (if multi-user validation) | Info | Check Action Center integration |
| Validation timeout configured (documents not stuck indefinitely) | Warning | Check timeout settings |

## 7. Model Management

| Check | Severity | How to Verify |
|---|---|---|
| ML model retraining process documented | Info | Check project documentation |
| Training data versioned and stored securely | Warning | Check for training data management |
| Model performance metrics tracked (accuracy, F1 score) | Info | Check for monitoring/reporting |
| GenAI used for prototyping, ML models for high-volume production | Info | Verify model strategy matches volume |
| Model version pinned in production (not auto-updating) | Warning | Check model version configuration |

### Tenant Migration (Critical Production Issue)

DU model references are **tenant-specific**. When publishing from DEV to PROD, the model ID baked into the workflow points to the DEV tenant. The automation fails with "The resource requested on StartDigitization cannot be found."

| Check | Severity | How to Verify |
|---|---|---|
| DU model references are environment-agnostic or parameterized | Critical | Check if model IDs are hardcoded in XAML or configurable via assets |
| DU project exists in target tenant before deployment | Critical | Verify DU project is created in each target environment |
| Model re-linking documented in deployment procedure | Warning | Check deployment documentation for DU-specific steps |
| Multi-tenant deployment strategy documented (if deploying to multiple tenants) | Warning | Check for per-tenant model management |

### Architecture Pattern

For complex DU projects, verify the three-tier separation:

| Tier | Purpose | Flag If Missing |
|---|---|---|
| **Initiator** | Classification, extraction, verification routing | Warning if monolithic process combines all tiers |
| **Validation Processor** | Human task coordination via Action Center / Validation Station | Warning if verification blocks remaining document processing |
| **Post-Processing** | Data export, model training feedback, downstream integration | Info if combined with initiator |

## 8. Exception Handling

| Check | Severity | How to Verify |
|---|---|---|
| Unrecognized document types handled (not silently dropped) | Critical | Check classification exception path |
| Digitization failures handled (corrupt, password-protected, unreadable) | Warning | Check for error handling around `Digitize Document` |
| Low-confidence extraction triggers human review (not auto-accepted) | Warning | Check confidence-based routing |
| Empty extraction results handled (no data found in document) | Warning | Check for empty result handling |
| Document processing errors logged with document identifier | Warning | Check logging in error paths |
| Failed documents tracked for reprocessing or manual handling | Warning | Check for failure queue or status tracking |

## 9. Performance and Optimization

| Check | Severity | How to Verify |
|---|---|---|
| Batch processing configured for high-volume scenarios | Info | Check for batch/queue-based document processing |
| OCR calls minimized (no redundant digitization of same document) | Info | Check for duplicate OCR calls |
| Large documents handled without memory issues | Warning | Check for document size limits or chunking |
| Cloud API calls tracked for cost monitoring (GenAI, Cloud OCR) | Info | Check for API call logging |
| Processing throughput matches PDD/SLA requirements | Info | Compare estimated throughput against requirements |

## 10. IXP vs Document Understanding Decision

UiPath IXP (Intelligent Xtraction and Processing) is the next-generation platform that unifies Communications Mining and Document Understanding. When reviewing a project, assess whether IXP or classic DU is more appropriate:

| Criterion | Use IXP | Use Classic DU |
|---|---|---|
| New document types with no training data | Yes (zero-shot generative extraction) | No (requires model training) |
| Mixed data sources (documents + emails + chat) | Yes (multi-modal processing) | No (documents only) |
| Rapid prototyping / proof of concept | Yes (works out-of-the-box) | Slower (needs trained models) |
| Agent-driven processes needing document processing | Yes (native agent tool) | Requires workflow wrapping |
| High-volume production with trained models | Either (IXP can use specialized models) | Yes (optimized throughput) |
| Specialized document types with custom models | Either | Yes (highest accuracy) |
| Regulatory/auditable extraction logic | Evaluate | Yes (deterministic rule-based extractors) |

| Check | Severity | How to Verify |
|---|---|---|
| IXP vs DU choice matches the use case (see decision table above) | Info | Compare project requirements against decision criteria |
| If using IXP: generative extraction used for prototyping, specialized models for production | Info | Check model strategy |
| If using IXP: extraction schemas clearly defined with field types and validation rules | Warning | Check IXP extraction configuration |
| If using IXP as agent tool: agent properly configured to invoke IXP | Warning | Check agent tool configuration |

## 11. Cost and Accuracy Antipatterns

| Check | Severity | How to Verify |
|---|---|---|
| Generative AI Extractor NOT used for fixed-layout structured documents | Info | For documents with consistent layouts (standard invoices from one vendor, government forms, internal templates), a RegEx or Form extractor is deterministic, faster, and free. Generative adds AI Unit cost, latency, and non-determinism |
| Validation Station / Action Center used for business-critical fields (not relying solely on confidence thresholds) | Warning | UiPath docs: "Confidence thresholds should only be used as a fallback, a safety net, but never as the main way to detect business-critical errors." Missing fields have NO confidence, so thresholds cannot catch them. Business rules + human review are the reliable detectors. For financial/medical/legal documents, flag as **Critical** if Validation Station absent |
| Business rule validation configured (cross-field checks — e.g., net + tax = total) | Warning | Business rules catch errors confidence thresholds cannot |
