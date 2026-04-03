<!-- UIPATH-AUTOMATION-GENOME: This file is a build specification for a UiPath automation project.
     Do NOT execute these steps directly. Use the UiPath skills referenced in Build With to create
     the automation project. -->

# Genome: Classify Document and Create Validation

> Classify documents using a generative AI classifier and route low-confidence results to human reviewers via Action Center.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Use the skills listed in **Build With** below to create a UiPath automation project that implements this workflow.

## Overview

This automation classifies documents using Document Understanding's generative classifier against a configurable set of document types. Each document type is matched using a natural-language prompt, and the classifier returns the best-matching type along with a confidence score.

When the classification confidence falls below a configurable threshold, the automation creates a validation task in Action Center, suspends execution, and waits for a human reviewer to confirm or correct the classification. High-confidence classifications are accepted automatically without human intervention. The process uses Orchestrator persistence to maintain state while suspended, resuming seamlessly once the reviewer completes the task.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Document Understanding | Document classification | Generative classifier with per-type natural-language prompts |
| Action Center | Human-in-the-loop validation | Validation tasks for low-confidence classifications |
| Orchestrator | Process persistence and storage | Storage bucket for documents, folder for Action Center task routing |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Classify document using generative AI | `uipath-rpa-workflows` | Document Understanding generative classifier is an activity-based DU workflow |
| Evaluate confidence and route to validation | `uipath-rpa-workflows` | Conditional logic with Action Center activities in XAML |
| Wait for human validation | `uipath-rpa-workflows` | Action Center create/wait activities with process persistence |

## Configuration Questions

1. Which document types should the classifier recognize? (source project used: Receipt, Invoice, W-9, Certificate of Filing, Form 1040)
2. What minimum confidence for the classifier to return a result? (source project used: 50%)
3. What confidence threshold triggers human validation? (source project used: 70%)
4. Which Orchestrator storage bucket for document storage? (source project used: du_storage_bucket)
5. Which Orchestrator folder for Action Center tasks? (source project used: autopilotuseremail@autopilot.com's workspace)

## Workflow

1. **Receive document file path** (input: file path string; output: document reference):
   a. Accept the path to the document file as an input argument
   b. Load the document from the local file system for classification

2. **Classify document using generative AI** (input: document reference; output: document type and confidence score):
   a. Submit the document to the Document Understanding generative classifier
   b. Evaluate the document against each configured document type using its natural-language prompt (e.g., "Is this Invoice?", "Is this Receipt?")
   c. Return the best-matching document type and a confidence score (0-100%)
   d. The classifier enforces a minimum confidence floor -- results below the minimum are not returned

3. **Evaluate classification confidence** (input: document type and confidence score; output: routing decision):
   a. Compare the confidence score against the configured validation threshold (default: 70%)
   b. If confidence is at or above the threshold, accept the classification result -- no human review needed
   c. If confidence is below the threshold, proceed to human validation

4. **Create human validation task** (input: classification result with low confidence; output: Action Center task):
   a. Create a classification validation task in Action Center with the document file name in the task title
   b. Attach the classifier's initial result so the reviewer sees the suggested document type
   c. Route the task to the configured Orchestrator folder and storage bucket
   d. Set task priority to Medium (configurable)
   e. Log the document type and confidence level for audit tracking

5. **Wait for human validation** (input: Action Center task; output: validated classification result):
   a. Suspend the process -- Orchestrator persistence maintains state while waiting
   b. Resume automatically when the human reviewer completes the validation task
   c. Retrieve the reviewer's validated classification result

## Business Rules

### Step 3: Evaluate classification confidence
- If classification confidence is below 70% (configurable), route to human validation via Action Center; otherwise accept the automated classification result without human review

### General
- Document type classification uses one natural-language prompt per type, enabling non-technical customization of classification behavior without retraining models
- Each document type prompt is independent -- adding or removing a type does not affect other classifications

## Error Handling

Standard error handling -- retry on transient failures, log and skip on permanent errors. The process supports persistence, so transient platform failures during the wait phase do not lose state.

## Acceptance Criteria

- [ ] Given a document file, the automation classifies it against the configured document types and returns a document type with a confidence score
- [ ] Given a classification with confidence at or above the threshold, the automation accepts the result without creating a validation task
- [ ] Given a classification with confidence below the threshold, the automation creates a validation task in Action Center with the document name and the classifier's suggested type
- [ ] Given a validation task is created, the process suspends and resumes only after the human reviewer completes the task
- [ ] Given a low-confidence classification, the automation logs the document type and confidence level before suspending
- [ ] Given process suspension during validation wait, Orchestrator persistence maintains full process state across the pause
- [ ] Given a completed validation task, the automation retrieves the reviewer's corrected or confirmed classification result

## Complexity

medium

## Tags

document-understanding, document-classification, generative-ai, action-center, human-in-the-loop, validation, orchestrator, persistence
