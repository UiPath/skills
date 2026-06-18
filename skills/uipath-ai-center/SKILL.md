---
name: uipath-ai-center
description: "UiPath AI Center and Document Understanding assistant — ML model deployment, out-of-box ML packages, Document Understanding pipelines (classification, data extraction, validation), AI Center project management, and ML Skills usage in coded and RPA workflows. TRIGGER when: User wants to use Document Understanding (DU) to process invoices, forms, IDs, contracts, or any structured/semi-structured documents; User wants to deploy or consume an ML model via UiPath AI Center; User asks about UiPath ML Skills, ML packages, or out-of-box AI models; User wants to classify documents, extract fields, or validate extracted data; User mentions intelligent document processing (IDP), OCR, or AI-based data extraction; User wants to train or retrain an ML model in AI Center. DO NOT TRIGGER when: User is asking about general UiPath automation without AI/ML components (use uipath-coded-workflows or uipath-rpa-workflows instead), or asking about Orchestrator deployment only (use uipath-platform instead)."
metadata:
   allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath AI Center & Document Understanding Assistant

Build intelligent document processing pipelines and deploy ML models using UiPath AI Center and Document Understanding.

## When to Use This Skill

- User wants to **process documents** (invoices, purchase orders, receipts, contracts, ID cards, forms) with AI-based extraction
- User wants to **classify documents** automatically by type
- User wants to **extract fields** from semi-structured documents (e.g., invoice number, total amount, vendor name)
- User wants to **deploy an ML model** to AI Center and call it from a workflow
- User wants to **use out-of-box ML packages** (Invoice, Receipt, Purchase Order, ID card extractors)
- User wants to **set up a human-in-the-loop validation** step for low-confidence extractions
- User wants to **train or retrain** a Document Understanding model with their own data
- User wants to **monitor ML model performance** and accuracy

## Quick Start

### Step 1 — Ensure AI Center and Document Understanding licenses

AI Center and Document Understanding require specific UiPath licenses. Verify in Orchestrator → Admin → Licenses.

### Step 2 — Choose your document processing approach

| Document Type | Recommended Extractor |
|---|---|
| Invoices | `UiPath.DocumentUnderstanding.ML.Activities` — InvoiceModel |
| Receipts | Out-of-box ReceiptModel ML package |
| Purchase Orders | Out-of-box PurchaseOrderModel ML package |
| ID / Passports | Out-of-box IDModel ML package |
| Custom forms | Train a custom DocumentUnderstanding model in AI Center |
| Contracts / free text | Generative AI extractor (GPT-based) |

### Step 3 — Add Document Understanding packages

```bash
# Add the core Document Understanding package
uip rpa install-or-update-packages \
  --packages '[{"id":"UiPath.DocumentUnderstanding.ML.Activities"}]' \
  --project-dir "<PROJECT_DIR>" \
  --format json

# Add OCR engine (Omnipage, UiPath Document OCR, or Google OCR)
uip rpa install-or-update-packages \
  --packages '[{"id":"UiPath.OmniPage.Activities"}]' \
  --project-dir "<PROJECT_DIR>" \
  --format json
```

### Step 4 — Build the pipeline

Follow the Document Understanding pipeline pattern:

```
1. Digitize     → Convert PDF/image to digital text + layout
2. Classify     → Determine document type (optional)
3. Extract      → Pull field values using ML extractor
4. Validate     → Human review for low-confidence results
5. Export       → Push extracted data to downstream system
```

## Task Navigation

| I need to... | Read these |
|---|---|
| **Digitize a document (OCR)** | [Digitization](#digitization-ocr) |
| **Classify documents by type** | [Document Classification](#document-classification) |
| **Extract fields from documents** | [Data Extraction](#data-extraction) |
| **Set up human validation** | [Human Validation Loop](#human-validation-loop) |
| **Deploy a custom ML model** | [AI Center ML Model Deployment](#ai-center-ml-model-deployment) |
| **Call an ML Skill from a workflow** | [Using ML Skills in Workflows](#using-ml-skills-in-workflows) |
| **Train a custom extractor** | [Training Custom Models](#training-custom-models) |
| **Monitor model performance** | [Model Monitoring](#model-monitoring) |

---

## Digitization (OCR)

Convert a physical or digital document into a machine-readable format before extraction.

### Coded Workflow pattern

```csharp
// Requires: UiPath.DocumentUnderstanding.ML.Activities, UiPath.OmniPage.Activities (or other OCR)
using UiPath.DocumentUnderstanding.Models;

[Workflow]
public void Execute(string documentPath)
{
    // Digitize using UiPath Document OCR (cloud) or local OCR
    var document = documentUnderstanding.Digitize(documentPath);
    // 'document' contains text, layout, and bounding boxes for all pages
    Log($"Digitized {document.Pages.Count} pages from {documentPath}");
}
```

### RPA/XAML workflow

In XAML workflows, use the **Digitize Document** activity from `UiPath.DocumentUnderstanding.ML.Activities`.

Key properties:
- `FilePath` — path to PDF, PNG, JPG, or TIFF
- `OCR Engine` — drag an OCR engine activity into the OCR Engine slot
- `Document` (output) — `Document` object for downstream activities

---

## Document Classification

Automatically determine the document type before extraction.

### Keyword-based classifier (no ML required)

Use the **Keyword Based Classifier** for simple, rule-based classification:

```
Documents types → map keywords to each type
e.g., "INVOICE" → Invoice, "RECEIPT" → Receipt
```

### ML-based classifier

Use the **Intelligent Keyword Classifier** or a trained ML classifier from AI Center:

1. Go to AI Center → ML Packages → find a DocumentClassifier package
2. Deploy it as an ML Skill under your Orchestrator tenant
3. Reference the ML Skill endpoint in the **ML Classifier** activity

---

## Data Extraction

Extract specific fields from digitized documents using ML extractors.

### Out-of-box extractors (coded workflow)

```csharp
// Invoice extractor — extracts vendor, total, date, line items, etc.
var extractionResult = documentUnderstanding.ExtractData(
    document,
    new InvoiceMLExtractor()   // or ReceiptMLExtractor, PurchaseOrderMLExtractor
);

foreach (var field in extractionResult.Fields)
{
    Log($"{field.FieldName}: {field.Value} (confidence: {field.Confidence:P0})");
}
```

### ML Skill extractor (custom model from AI Center)

```csharp
// Reference a deployed ML Skill endpoint
var mlSkillEndpoint = system.GetAsset("MyExtractorEndpointUrl");
var apiKey = system.GetAsset("AICenterApiKey");

var extractionResult = documentUnderstanding.ExtractData(
    document,
    new MLExtractor(mlSkillEndpoint, apiKey)
);
```

### Accessing extracted field values

```csharp
// Get a specific field
var invoiceNumber = extractionResult.Fields["InvoiceNumber"]?.Value;
var totalAmount   = extractionResult.Fields["TotalAmount"]?.Value;
var confidence    = extractionResult.Fields["TotalAmount"]?.Confidence ?? 0.0;

// Flag low-confidence results for human review
const double ConfidenceThreshold = 0.8;
bool needsReview = confidence < ConfidenceThreshold;
```

---

## Human Validation Loop

Route low-confidence documents to a human validator before exporting data.

### Pattern: Queue-based validation

```
1. Extract data → check confidence
2. If confidence < threshold → add to "ValidationQueue" with extracted data
3. Attended bot or Action Center task → human reviews and corrects fields
4. Automation picks up validated item and continues
```

### Using Action Center for validation

```csharp
// Create a validation task in Action Center
system.CreateFormTask(
    taskTitle: $"Validate Invoice {invoiceNumber}",
    taskPriority: Priority.Medium,
    taskCatalog: "Invoice Validation",
    assignedTo: "validation-team@company.com"
);
```

### Queue-based pattern

```csharp
// Add to validation queue with extracted data
system.AddQueueItem(
    queueName: "DocumentValidationQueue",
    itemInformation: new Dictionary<string, object> {
        ["DocumentPath"] = documentPath,
        ["ExtractedData"] = JsonConvert.SerializeObject(extractionResult),
        ["Confidence"] = averageConfidence,
        ["NeedsReview"] = true
    }
);
```

---

## AI Center ML Model Deployment

Deploy a trained ML model as an ML Skill callable from any UiPath workflow.

### Step 1 — Upload ML package to AI Center

1. Navigate to AI Center → ML Packages → Upload Package
2. Upload your `.zip` file containing `main.py`, `requirements.txt`, and model artifacts
3. Note the **Package ID** and **Version**

### Step 2 — Create an ML Skill

1. Go to AI Center → ML Skills → Create New
2. Select the ML Package and version
3. Choose the Orchestrator folder where the skill will be available
4. Set replica count and compute resources
5. Deploy — wait for status to show **Available**

### Step 3 — Get the ML Skill endpoint

```bash
# List ML Skills and their endpoints via Orchestrator API
source ~/.uipath/.auth
curl -X GET "${UIPATH_URL}/${UIPATH_ORG_NAME}/${UIPATH_TENANT_NAME}/aifabric_/ai-deployer/v2/mlskills" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json"
```

Store the endpoint URL as an Orchestrator asset for use in workflows.

---

## Using ML Skills in Workflows

Call a deployed AI Center ML Skill from a coded or RPA workflow.

### Coded Workflow

```csharp
using System.Net.Http;
using Newtonsoft.Json;

[Workflow]
public void Execute(string inputText)
{
    var endpointUrl = system.GetAsset("MyMLSkillEndpoint");
    var token = system.GetAsset("AICenterApiKey");  // or use UIPATH_ACCESS_TOKEN

    using var client = new HttpClient();
    client.DefaultRequestHeaders.Authorization =
        new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);

    var payload = JsonConvert.SerializeObject(new { input_data = inputText });
    var response = client.PostAsync(
        $"{endpointUrl}/predict",
        new StringContent(payload, System.Text.Encoding.UTF8, "application/json")).Result;

    var result = response.Content.ReadAsStringAsync().Result;
    Log($"ML Skill prediction: {result}");
}
```

### RPA/XAML Workflow

Use the **ML Skill** activity from `UiPath.MLServices.Activities`:

```bash
uip rpa install-or-update-packages \
  --packages '[{"id":"UiPath.MLServices.Activities"}]' \
  --project-dir "<PROJECT_DIR>" \
  --format json
```

Activity: **ML Skill** → set `Endpoint`, `APIKey`, `InputParameters`, capture `Predictions` output.

---

## Training Custom Models

Train or retrain a Document Understanding extractor with your own labeled documents.

### Step 1 — Create a dataset in AI Center

1. AI Center → Datasets → Create Dataset
2. Upload documents (PDF, images) — minimum 20 labeled samples for reasonable accuracy
3. Label documents using the built-in labeling UI (draw bounding boxes around fields)

### Step 2 — Create a training pipeline

1. AI Center → ML Packages → select your base model (e.g., `DocumentUnderstanding.Invoice`)
2. AI Center → Pipelines → Training → link to your dataset
3. Configure training parameters (epochs, learning rate)
4. Run training — monitor progress in the Logs tab

### Step 3 — Evaluate and promote

1. Review evaluation metrics (F1, precision, recall per field)
2. If acceptable → promote the new version
3. Update the ML Skill to use the new version (zero-downtime update)

### Minimum recommended samples

| Field Count | Min Samples |
|---|---|
| 1–5 fields | 20 documents |
| 6–15 fields | 50 documents |
| 16+ fields | 100+ documents |

---

## Model Monitoring

Track ML Skill performance over time to detect accuracy drift.

### Key metrics to monitor

| Metric | Description | Alert Threshold |
|---|---|---|
| Average confidence | Mean prediction confidence | < 0.75 |
| Human correction rate | % of extractions corrected by validators | > 15% |
| Processing latency | Time per document (ms) | > 5000ms |
| Error rate | % of failed ML Skill calls | > 2% |

### Monitoring via Orchestrator

```bash
# Check ML Skill status
source ~/.uipath/.auth
curl "${UIPATH_URL}/${UIPATH_ORG_NAME}/${UIPATH_TENANT_NAME}/aifabric_/ai-deployer/v2/mlskills/<SKILL_ID>" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}"
```

Log confidence values from every extraction run to an Orchestrator queue or storage bucket for trend analysis.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Low extraction confidence on first run | More training data; improve document quality (scan at 300 DPI min) |
| OCR misses text in scanned PDFs | Switch OCR engine; try UiPath Document OCR or Google Cloud Vision |
| ML Skill returns 503 | Skill is still deploying (wait ~5 min) or replica count too low |
| Field names mismatch between model and code | Field names are case-sensitive; match exactly to model schema |
| Training fails with low dataset error | Minimum 10 labeled docs per field; add more training samples |
| Action Center task not appearing | Verify Task Catalog name and user assignment; check Action Center license |

## References

- **[UiPath Platform Skill](../uipath-platform/SKILL.md)** — Authentication, Orchestrator assets, folder management
- **[Coded Workflows Skill](../uipath-coded-workflows/SKILL.md)** — C# workflow patterns, NuGet packages
- **[RPA Workflows Skill](../uipath-rpa-workflows/SKILL.md)** — XAML activity usage patterns
- **[UiPath Document Understanding docs](https://docs.uipath.com/document-understanding)** — Official product documentation
- **[UiPath AI Center docs](https://docs.uipath.com/ai-center)** — ML model training and deployment
