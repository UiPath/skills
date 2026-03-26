# UiPath Platform — Solopreneur Examples

Real end-to-end examples showing how solopreneurs use the UiPath platform to automate their business operations.

---

## Example 1: Deploy a Lead Enrichment Bot

**Scenario:** You scrape leads from LinkedIn and want to automatically enrich them (add company size, revenue) using an external API, then store results in Orchestrator for downstream processing.

### Step 1 — Authenticate

```bash
uip login --format json
uip login tenant list --format json
uip login tenant set "MyTenant" --format json
```

### Step 2 — Create the folder structure

```bash
# Create a dedicated folder for the lead enrichment automation
uip or folders create --name "LeadEnrichment" --format json

# Store the enrichment API key as an asset
uip resources assets create \
  --name "EnrichmentApiKey" \
  --type Text \
  --value "your-clearbit-or-hunter-api-key" \
  --folder "LeadEnrichment" \
  --format json

# Create an input queue for raw leads
uip resources queues create \
  --name "RawLeadsQueue" \
  --folder "LeadEnrichment" \
  --format json

# Create an output queue for enriched leads
uip resources queues create \
  --name "EnrichedLeadsQueue" \
  --folder "LeadEnrichment" \
  --format json
```

### Step 3 — Pack and publish the workflow

```bash
# Pack the automation project
uip solution pack --project-dir "./LeadEnrichment" --output-dir "./dist" --format json

# Publish to Orchestrator
uip solution publish --package-path "./dist/LeadEnrichment.1.0.0.nupkg" --format json

# Deploy to the LeadEnrichment folder
uip solution deploy run -n "LeadEnrichmentDeploy" -c "ProductionConfig" --format json
```

### Step 4 — Feed leads into the queue

```bash
# Add a batch of raw leads to the queue
uip resources queueitems add \
  --queue "RawLeadsQueue" \
  --folder "LeadEnrichment" \
  --data '{"email":"ceo@acme.com","name":"Jane Doe","company":"Acme Corp"}' \
  --format json
```

---

## Example 2: Batch Invoice Processing Pipeline

**Scenario:** You receive 50–200 PDF invoices per month by email. You want to automatically extract data, validate totals, and export to your accounting spreadsheet.

### Orchestrator setup

```bash
# Create folder
uip or folders create --name "InvoiceProcessing" --format json

# Storage bucket for incoming PDFs
uip resources buckets create --name "InvoicePDFs" --folder "InvoiceProcessing" --format json

# Asset for email credentials
uip resources assets create \
  --name "GmailCredential" \
  --type Credential \
  --username "invoices@mycompany.com" \
  --password "app-specific-password" \
  --folder "InvoiceProcessing" \
  --format json

# Queue for processing results
uip resources queues create \
  --name "ProcessedInvoices" \
  --folder "InvoiceProcessing" \
  --format json
```

### Upload invoices to storage bucket for batch processing

```bash
# Upload PDFs to the storage bucket
uip resources buckets upload \
  --name "InvoicePDFs" \
  --folder "InvoiceProcessing" \
  --file "./downloads/invoice-jan.pdf" \
  --format json
```

### Monitor the processing job

```bash
# List running jobs
uip or jobs list --folder "InvoiceProcessing" --format json

# Check queue processing status
uip resources queues get --name "ProcessedInvoices" --folder "InvoiceProcessing" --format json
```

---

## Example 3: CI/CD Pipeline for Automation Deployment

**Scenario:** You maintain automation projects in Git and want every push to main to automatically pack, publish, and deploy to Orchestrator.

### Non-interactive login (CI/CD)

```bash
# In GitHub Actions / Azure DevOps — use client credentials
uip login \
  --client-id "$UIPATH_CLIENT_ID" \
  --client-secret "$UIPATH_CLIENT_SECRET" \
  --tenant "$UIPATH_TENANT" \
  --format json
```

### Full deployment pipeline

```bash
# 1. Validate the project before packing
uip rpa validate --project-dir "./MyAutomation" --studio-dir "$STUDIO_DIR" --format json

# 2. Pack
uip solution pack --project-dir "./MyAutomation" --output-dir "./dist" --format json

# 3. Publish to Orchestrator
uip solution publish --package-path "./dist/MyAutomation.1.0.0.nupkg" --format json

# 4. Deploy
uip solution deploy run -n "MyAutomationDeploy" -c "ProductionConfig" --format json

# 5. Verify deployment
uip or releases list --folder "Production" --format json
```

### GitHub Actions workflow snippet

```yaml
- name: Deploy UiPath automation
  env:
    UIPATH_CLIENT_ID: ${{ secrets.UIPATH_CLIENT_ID }}
    UIPATH_CLIENT_SECRET: ${{ secrets.UIPATH_CLIENT_SECRET }}
    UIPATH_TENANT: ${{ secrets.UIPATH_TENANT }}
  run: |
    uip login --client-id "$UIPATH_CLIENT_ID" --client-secret "$UIPATH_CLIENT_SECRET" --tenant "$UIPATH_TENANT" --format json
    uip solution pack --project-dir "./MyAutomation" --output-dir "./dist" --format json
    uip solution publish --package-path "./dist/MyAutomation.1.0.0.nupkg" --format json
    uip solution deploy run -n "Deploy-$(date +%Y%m%d)" -c "ProductionConfig" --format json
```

---

## Example 4: Asset Management for Multi-Environment Setup

**Scenario:** You run automations in Dev, Staging, and Production with different API endpoints and credentials per environment.

```bash
# Create folders for each environment
uip or folders create --name "Dev" --format json
uip or folders create --name "Staging" --format json
uip or folders create --name "Production" --format json

# Set different API endpoints per environment
uip resources assets create --name "ApiBaseUrl" --type Text \
  --value "https://dev.api.internal" --folder "Dev" --format json

uip resources assets create --name "ApiBaseUrl" --type Text \
  --value "https://staging.api.mycompany.com" --folder "Staging" --format json

uip resources assets create --name "ApiBaseUrl" --type Text \
  --value "https://api.mycompany.com" --folder "Production" --format json

# Workflow reads the same asset name regardless of environment
# uip or folders list → get folder ID → pass as X-UIPATH-OrganizationUnitId
```

Workflows always call `system.GetAsset("ApiBaseUrl")` — the folder context determines which value is returned.
