<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     Do NOT execute these steps directly. Use the UiPath skills referenced in Build With to create
     the automation project. -->

# Genome: Classify Document and Create Validation

> Classify documents using a generative AI classifier and route low-confidence results to human reviewers via Action Center.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Use the skills listed in **Build With** below to create a UiPath automation project that implements this workflow.

## Overview

This automation classifies documents using Document Understanding's generative classifier against a configurable set of document types. Each document type is matched using a natural-language prompt, and the classifier returns the best-matching type along with a confidence score.

When the classification confidence falls below a configurable threshold, the automation creates a validation task in Action Center, suspends execution, and waits for a human reviewer to confirm or correct the classification. High-confidence classifications are accepted automatically. Orchestrator persistence keeps the process state while suspended, and execution resumes when the reviewer completes the task.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Document Understanding | Document classification | Generative classifier with per-type natural-language prompts |
| Action Center | Human-in-the-loop validation | Validation tasks for low-confidence classifications |
| Orchestrator | Process persistence and storage | Storage bucket for documents, folder for Action Center task routing |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Steps 1-2: load and classify the document | `uipath-rpa` | Document Understanding generative classifier is an activity-based XAML workflow |
| Steps 3-5: evaluate confidence, create validation task, wait for reviewer | `uipath-rpa` | Conditional logic plus Action Center create/wait activities with process persistence in XAML; consult `uipath-human-in-the-loop` for the validation gate design |

## Platform Dependencies

| Resource | Type | Purpose |
|----------|------|---------|
| du_storage_bucket | Storage bucket | Holds the document while the validation task is open |
| Validation folder | Orchestrator folder | Folder where Action Center tasks are created and assigned |

## Interface

- **Inputs:** `DocumentPath` (string) — path to the document file to classify
- **Outputs:** `DocumentType` (string), `Confidence` (number 0-100), `ValidatedByHuman` (boolean)
- **Side effects:** an Action Center task when confidence is below the threshold; the document uploaded to the storage bucket

## Configuration Questions

1. Which document types should the classifier recognise? (default: Receipt, Invoice, W-9, Certificate of Filing, Form 1040)
2. What minimum confidence must the classifier reach to return a result at all? (default: 50%)
3. What confidence threshold triggers human validation? (default: 70%)
4. Which Orchestrator storage bucket holds documents during validation? (default: du_storage_bucket)
5. Which Orchestrator folder receives the Action Center tasks? (default: the process's own folder)
6. What task priority for validation tasks? (default: Medium)

## Workflow

1. **Receive document** (input: file path; output: document reference):
   a. Accept the document path as an input argument
   b. Load the document from the local file system
2. **Classify document** (input: document reference; output: document type and confidence 0-100%):
   a. Submit the document to the generative classifier
   b. Evaluate it against each configured document type using that type's natural-language prompt (e.g. "Is this an Invoice?")
   c. Return the best-matching type and its confidence; results under the minimum confidence are not returned
3. **Evaluate confidence** (input: type and confidence; output: routing decision):
   a. If confidence is at or above the validation threshold, accept the result — no human review
   b. Otherwise continue to human validation
4. **Create validation task** (input: low-confidence result; output: Action Center task):
   a. Create a classification validation task titled with the document file name
   b. Attach the classifier's suggested type so the reviewer sees it
   c. Route the task to the configured folder and store the document in the configured bucket
   d. Set the configured priority
   e. Log document type and confidence for audit
5. **Wait for validation** (input: task; output: validated type):
   a. Suspend the process; Orchestrator persistence holds the state
   b. Resume when the reviewer completes the task
   c. Read the reviewer's confirmed or corrected type

## Business Rules

### Step 3: Evaluate confidence
- If classification confidence is below the threshold (default 70%), route to human validation; otherwise accept without review.

### General
- One natural-language prompt per document type; adding or removing a type does not affect the others.

## Error Handling

### Step 2: Classify document
- Classifier unavailable or times out: retry once, then fail the item with the error message in the job log.

### Step 5: Wait for validation
- Platform interruption while suspended: persistence restores the wait; no state is lost.

### Global
- Unhandled exception: log the document path and error, mark the job faulted.

## Transactional Shape

Not transactional: one item's work started per item by the caller that passes the document path; a caller that iterates over documents is the candidate consumer and carries the shape.

## Acceptance Criteria

- [ ] Given a document file, the automation returns a document type from the configured set with a confidence score.
- [ ] Given a classification at or above the threshold, no validation task is created and the result is returned as final.
- [ ] Given a classification below the threshold, a validation task appears in Action Center with the document name and the suggested type.
- [ ] Given a validation task is created, the process suspends and resumes only after the reviewer completes it.
- [ ] Given a low-confidence classification, the job log contains the document type and confidence before suspension.
- [ ] Given a completed validation task, the automation returns the reviewer's confirmed or corrected type with `ValidatedByHuman` true.
- [ ] Given the classifier is unavailable twice in a row, the job fails with the classifier error in the log.

## Complexity

medium

## Tags

document-understanding, document-classification, generative-ai, action-center, human-in-the-loop, validation, orchestrator, persistence
