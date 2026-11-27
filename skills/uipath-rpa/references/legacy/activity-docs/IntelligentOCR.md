# UiPath IntelligentOCR (Document Understanding) Activities - Legacy Reference

> **See also**: [_DU-PROCESS.md](_DU-PROCESS.md) — the Document Understanding Process template that uses these activities in a complete pipeline

## Overview
Legacy Document Understanding framework: digitize, classify, extract, validate, train, and redact documents. Package: `UiPath.IntelligentOCR.Activities`. **#24 by adoption (2.97%)**.

---

## Activity Architecture

All activities follow a **scope + child** pattern:
- **Scopes** (ClassifyDocumentScope, DataExtractionScope, TrainClassifiersScope, TrainExtractorsScope) contain child activities
- **Children** (classifiers, extractors, trainers) run inside their respective scopes
- **Standalone** activities (DigitizeDocument, LoadTaxonomy, ValidationStation, etc.) run independently

---

## Core Activities

### Digitization
| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `DigitizeDocument` | OCR + DOM creation | DocumentPath (req), DegreeOfParallelism (def 1), DetectCheckboxes (def true), OCREngine (ActivityDelegate) -> DocumentObjectModel, DocumentText |
| `LoadTaxonomy` | Load taxonomy definition | (hardcoded path) -> Taxonomy (DocumentTaxonomy) |

### Classification
| Activity | Type | Key Arguments |
|----------|------|---------------|
| `ClassifyDocumentScope` | Scope | DocumentText, DocumentObjectModel, DocumentPath, Taxonomy (all req) -> ClassificationResults[] |
| `IntelligentKeywordClassifier` | Child | LearningFilePath OR LearningData, Endpoint, ApiKey, TimeoutMs (def 100,000), UsePageNumbers, PerformDocumentSplitting |
| `KeywordBasedClassifier` | Child (DEPRECATED) | LearningFilePath OR LearningData |
| `DuAppClassifier` | Child | SelectedProject (req), SelectedVersion, SelectedTag, TimeoutMs (def 15,000) |
| `PresentClassificationStation` | Standalone | AutomaticClassificationResults, DocumentObjectModel/Text/Path, Taxonomy (all req), EnablePageReorderging (typo in name) |

### Data Extraction
| Activity | Type | Key Arguments |
|----------|------|---------------|
| `DataExtractionScope` | Scope | ClassificationResult, DocumentText/ObjectModel/Path, Taxonomy (req), FormatValuesIfPossible, ApplyGenerativeValidation |
| `DuAppExtractor` | Child | SelectedProject (req), SelectedVersion, SelectedTag, TimeoutMs (def 15,000) |
| `FormExtractor` | Child | Endpoint (req), ApiKey, MinOverlapPercentage (def 65), Timeout (def 100,000), SerializedTemplates |
| `RegexBasedExtractor` | Child | Configuration (JSON, req), Timeout (def 2,000), UseVisualAlignment |
| `ExportExtractionResults` | Standalone | ExtractionResult (req), IncludeConfidence, IncludeOCRConfidence -> DataSet |

### Validation
| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `PresentValidationStation` | Human validation UI | AutomaticExtractionResults, DocumentObjectModel/Text/Path, Taxonomy (req), FieldsValidationConfidence (0-100), DisplayMode (Compact/Expanded) |

### Training
| Activity | Type | Key Arguments |
|----------|------|---------------|
| `TrainClassifiersScope` | Scope | HumanValidatedData OR HumanValidatedClassificationData, DocumentText/ObjectModel/Path (req) |
| `TrainExtractorsScope` | Scope | HumanValidatedData (req), DocumentText/ObjectModel/Path (req) |
| `KeywordBasedClassifierTrainer` | Child | LearningFilePath OR LearningData |
| `IntelligentKeywordClassifierTrainer` | Child | LearningFilePath OR LearningData |
| `DuAppExtractorTrainer` | Child | SelectedProject (req), ActionInput (req) |

### Redaction & Orchestrator
| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `RedactDocument` | Redact sensitive data | DocumentPath, DocumentObjectModel (req), ExtractionResults OR WordsToRedact, FillColor, OutputFile |
| `CreateDocumentValidationArtifacts` | Upload for external validation | FolderPath (req), DocumentPath/Text/ObjectModel, Taxonomy |
| `RetrieveDocumentValidationArtifacts` | Download validated results | ContentValidationDataInput (req), DownloadFolderPath |

---

## Critical Gotchas

### Setup & Dependencies
1. **Requires CoreIPC 2.0.1+** - validated at CacheMetadata; throws InvalidOperationException at runtime if missing
2. **Requires UIAutomation >= 19.8** for DigitizeDocument
3. **PDF license required** for Digitize, FormExtractor, and Redaction (`PdfLicenseManager.EnsureValidLicense()`)
4. **OCR engine must be explicitly wired** as ActivityDelegate in DigitizeDocument

### LoadTaxonomy
5. **TaxonomyFilePath is HARDCODED** - no activity argument to override; reads from `HardCodedPaths.DefaultTaxonomyFilePath`
6. **Large taxonomies (100+ doc types) slow to load** - comprehensive metadata extraction on every call

### Classification
7. **ClassifyDocumentScope must contain at least one classifier child** - empty scope fails
8. **LearningFilePath OR LearningData** - must specify one, not both, not neither (validation error)
9. **KeywordBasedClassifier is DEPRECATED** - should not be placed in TrainClassifiersScope
10. **UsePageNumbers without PerformDocumentSplitting** generates warning

### Extraction
11. **RegexBasedExtractor Configuration cannot be empty array** - validation error
12. **Variable-bound Configuration skips validation** - assumes correctness
13. **If document type ID in regex config doesn't match, returns empty results SILENTLY**
14. **FormExtractor MinOverlapPercentage must be >0** - range 50-100 sensible
15. **RegexBasedExtractor default timeout (2000ms)** may be insufficient for complex patterns

### Validation Station
16. **FieldsValidationConfidence must be 0-100 or null** - values outside throw InvalidOperationException
17. **EnablePageReorderging (typo!)** must be true if results contain reordered page ranges
18. **UI may timeout** if user doesn't interact - activity hangs if Classification/Validation Station crashes

### Training
19. **ALL child classifiers/extractors must have PersistenceId set** and mapped in taxonomy configuration
20. **TrainClassifiersScope: HumanValidatedData OR HumanValidatedClassificationData** - not both, not neither
21. **If using HumanValidatedClassificationData, Taxonomy is REQUIRED**
22. **Training is incremental** - learning data grows over time and may impact performance

### Redaction
23. **Must specify ExtractionResults OR WordsToRedact** - not both, not neither
24. **Word matching is case-sensitive**
25. **Redaction is permanent** - output file overwrites; no undo

### DU App Activities
26. **SelectedProject is always REQUIRED** - validation fails if empty
27. **Default timeout 15,000ms** may be insufficient for large documents
28. **Dropdown lists empty if DU App service unreachable** - no fallback
29. **Training jobs are async at service** - activity returns when enqueued, not completed
