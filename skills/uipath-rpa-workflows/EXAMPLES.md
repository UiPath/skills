# UiPath RPA Workflows — Solopreneur Examples

Real end-to-end RPA (XAML) workflow examples for automating desktop and web applications commonly used by solopreneurs.

---

## Example 1: Web Form Auto-Fill from Excel

**Scenario:** You have a list of clients in Excel and need to submit each one through a government portal or legacy web form.

### Project setup

```bash
# Create a new RPA project
uip rpa create-project \
  --name "FormAutoFill" \
  --location "C:/Projects" \
  --studio-dir "<STUDIO_DIR>" \
  --format json

# Install required packages
uip rpa install-or-update-packages \
  --packages '[{"id":"UiPath.Excel.Activities"},{"id":"UiPath.UIAutomation.Activities"}]' \
  --project-dir "C:/Projects/FormAutoFill" \
  --format json
```

### Main.xaml workflow structure

```xml
<!-- High-level XAML structure for form auto-fill -->
<Activity DisplayName="FormAutoFill Main">
  <!-- 1. Read data source -->
  <ExcelApplicationScope FilePath="clients.xlsx">
    <ReadRange SheetName="Clients" Output="[clientData]" AddHeaders="True"/>
  </ExcelApplicationScope>

  <!-- 2. Open browser -->
  <OpenBrowser Url="https://portal.example.gov" BrowserType="Chrome" Output="[browser]">

    <!-- 3. Loop through each client row -->
    <ForEachRow DataTable="[clientData]" CurrentRow="[row]">

      <!-- 4. Fill each form field -->
      <TypeInto Target="[firstNameField]" Text="[row(&quot;FirstName&quot;).ToString]"/>
      <TypeInto Target="[lastNameField]"  Text="[row(&quot;LastName&quot;).ToString]"/>
      <TypeInto Target="[emailField]"     Text="[row(&quot;Email&quot;).ToString]"/>

      <!-- 5. Submit -->
      <Click Target="[submitButton]"/>

      <!-- 6. Wait for confirmation -->
      <WaitForElement Target="[successMessage]" Timeout="10000"/>

      <LogMessage Message="['Submitted: ' + row(&quot;Email&quot;).ToString]"/>
    </ForEachRow>

  </OpenBrowser>
</Activity>
```

### Indicate elements

Use UiPath Studio to indicate each target element:
```bash
# List Studio instances to get PROJECT_DIR
uip rpa list-instances --format json

# Indicate the first name field (opens Studio's indicate UI)
uip rpa indicate-element \
  --project-dir "C:/Projects/FormAutoFill" \
  --studio-dir "<STUDIO_DIR>" \
  --element-name "firstNameField" \
  --format json
```

---

## Example 2: Automated Invoice Download from Supplier Portals

**Scenario:** Log into 3 supplier portals each month, download the latest invoices as PDFs, and save them to a local folder organized by supplier name.

### Workflow pattern per supplier

```bash
# Discover activities for browser automation
uip rpa find-activities --query "Navigate To" --project-dir "<PROJECT_DIR>" --format json
uip rpa find-activities --query "Click" --project-dir "<PROJECT_DIR>" --format json
uip rpa find-activities --query "Download" --project-dir "<PROJECT_DIR>" --format json
```

### XAML structure

```xml
<Activity DisplayName="Download Supplier Invoices">
  <Sequence>
    <!-- Get credentials from Orchestrator -->
    <GetAsset AssetName="SupplierACredential" Asset="[supplierCred]"/>

    <!-- Open browser and log in -->
    <OpenBrowser Url="https://supplier-a.com/login" Output="[browser]">
      <TypeInto Target="[usernameField]" Text="[supplierCred.UserName]"/>
      <TypeInto Target="[passwordField]" Text="[supplierCred.Password]"/>
      <Click Target="[loginButton]"/>

      <!-- Navigate to invoices section -->
      <Click Target="[invoicesMenuLink]"/>

      <!-- Filter to current month -->
      <Click Target="[currentMonthFilter]"/>

      <!-- Download each invoice -->
      <GetText Target="[invoiceCount]" Value="[countText]"/>
      <ForEach TypeArgument="Int32" Values="[Enumerable.Range(0, Integer.Parse(countText))]" CurrentItem="[i]">
        <Click Target="[downloadLinks(i)]"/>
        <Delay Duration="2000"/>
      </ForEach>
    </OpenBrowser>

    <!-- Move downloaded files to organized folder -->
    <MoveFile From="[downloadsPath + &quot;\*.pdf&quot;]" To="[&quot;C:\Invoices\SupplierA\&quot; + DateTime.Now.ToString(&quot;yyyy-MM&quot;)]"/>
  </Sequence>
</Activity>
```

---

## Example 3: Legacy Desktop App Data Entry

**Scenario:** You receive orders as CSV exports from an old system and must enter each into a legacy Windows desktop application that has no API.

### Project setup

```bash
uip rpa create-project \
  --name "LegacyDataEntry" \
  --location "C:/Projects" \
  --studio-dir "<STUDIO_DIR>" \
  --format json

# Windows UI Automation for desktop apps
uip rpa install-or-update-packages \
  --packages '[{"id":"UiPath.UIAutomation.Activities"},{"id":"UiPath.System.Activities"}]' \
  --project-dir "C:/Projects/LegacyDataEntry" \
  --format json
```

### Indicate desktop app elements

```bash
# Indicate the desktop application window
uip rpa indicate-application \
  --project-dir "C:/Projects/LegacyDataEntry" \
  --studio-dir "<STUDIO_DIR>" \
  --application-name "OrderEntryApp" \
  --format json

# Indicate specific input fields within the app
uip rpa indicate-element \
  --project-dir "C:/Projects/LegacyDataEntry" \
  --studio-dir "<STUDIO_DIR>" \
  --element-name "orderNumberField" \
  --format json
```

### XAML pattern

```xml
<Activity DisplayName="Legacy Data Entry">
  <!-- Read CSV data -->
  <ReadCSV FilePath="orders.csv" Output="[orderData]" HasHeaders="True"/>

  <!-- Attach to running desktop application -->
  <AttachWindow Target="[legacyAppWindow]">
    <ForEachRow DataTable="[orderData]" CurrentRow="[order]">

      <!-- Click New Order button -->
      <Click Target="[newOrderButton]"/>

      <!-- Fill fields using keyboard input (fastest for legacy apps) -->
      <TypeInto Target="[orderNumberField]" Text="[order(&quot;OrderID&quot;).ToString]" SimulateType="True"/>
      <TypeInto Target="[customerField]"    Text="[order(&quot;Customer&quot;).ToString]"  SimulateType="True"/>
      <TypeInto Target="[amountField]"      Text="[order(&quot;Amount&quot;).ToString]"    SimulateType="True"/>

      <!-- Use keyboard shortcut to save (F5 or Ctrl+S) -->
      <KeyboardShortcut Key="F5"/>

      <!-- Wait for save confirmation indicator -->
      <WaitForElement Target="[savedIndicator]"/>

      <LogMessage Message="['Entered order: ' + order(&quot;OrderID&quot;).ToString]"/>
      <Delay Duration="500"/>
    </ForEachRow>
  </AttachWindow>
</Activity>
```

---

## Example 4: Scheduled Web Scraping for Competitor Price Monitoring

**Scenario:** Check competitor product prices daily, compare with your own prices, and alert you on Slack if a competitor is significantly cheaper.

### Project setup and scheduling

```bash
# Create project
uip rpa create-project \
  --name "PriceMonitor" \
  --location "C:/Projects" \
  --studio-dir "<STUDIO_DIR>" \
  --format json

# Deploy and create a schedule (runs daily at 7 AM)
uip solution pack --project-dir "C:/Projects/PriceMonitor" --output-dir "./dist" --format json
uip solution publish --package-path "./dist/PriceMonitor.1.0.0.nupkg" --format json

# Create trigger in Orchestrator (via REST API — CLI triggers not yet available)
source ~/.uipath/.auth
curl -X POST "${UIPATH_URL}/${UIPATH_ORG_NAME}/${UIPATH_TENANT_NAME}/orchestrator_/odata/ProcessSchedules" \
  -H "Authorization: Bearer ${UIPATH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-UIPATH-OrganizationUnitId: <FOLDER_ID>" \
  -d '{
    "Name": "DailyPriceCheck",
    "StartProcessCronExpression": "0 7 * * *",
    "ReleaseKey": "<RELEASE_KEY>",
    "Strategy": "ModernJobsCount",
    "JobsCount": 1,
    "RuntimeType": "Unattended",
    "Enabled": true
  }'
```

### XAML scraping workflow pattern

```xml
<Activity DisplayName="Price Monitor">
  <Sequence>
    <GetAsset AssetName="SlackWebhookUrl" Asset="[slackUrl]"/>
    <GetAsset AssetName="MyProductPrice" Asset="[myPrice]"/>
    <AssignActivity>
      <To>[myPriceDecimal]</To>
      <Value>[Decimal.Parse(myPrice)]</Value>
    </AssignActivity>

    <OpenBrowser Url="https://competitor.com/products/widget" Output="[browser]">
      <GetText Target="[priceElement]" Value="[competitorPriceText]"/>
      <AssignActivity>
        <To>[competitorPrice]</To>
        <Value>[Decimal.Parse(competitorPriceText.Replace("$","").Trim())]</Value>
      </AssignActivity>
    </OpenBrowser>

    <!-- Alert if competitor is >10% cheaper -->
    <If Condition="[competitorPrice &lt; myPriceDecimal * 0.9D]">
      <Then>
        <HttpRequest Endpoint="[slackUrl]" Method="POST"
          Body="[&quot;{&quot;&quot;text&quot;&quot;: &quot;&quot;⚠️ Competitor price $&quot;&quot; + competitorPrice.ToString() + &quot;&quot; is significantly below your $&quot;&quot; + myPriceDecimal.ToString() + &quot;&quot;&quot;&quot;}&quot;]"/>
      </Then>
    </If>

    <LogMessage Message="['Price check complete. Competitor: $' + competitorPrice.ToString()]"/>
  </Sequence>
</Activity>
```

---

## Common Patterns for Solopreneur Workflows

| Task | Key Activities | Package |
|---|---|---|
| Read Excel/CSV | `ReadRange`, `ReadCSV`, `ForEachRow` | `UiPath.Excel.Activities` |
| Web automation | `OpenBrowser`, `Click`, `TypeInto`, `GetText` | `UiPath.UIAutomation.Activities` |
| Send email | `SendMailMessage` | `UiPath.Mail.Activities` |
| REST API call | `HTTP Request` | `UiPath.Web.Activities` |
| Get Orchestrator asset | `Get Asset` | `UiPath.System.Activities` |
| Add queue item | `Add Queue Item` | `UiPath.System.Activities` |
| Create folder | `Create Directory` | `UiPath.System.Activities` |
| Wait for element | `WaitForElement`, `ElementExists` | `UiPath.UIAutomation.Activities` |
| Log message | `Log Message` | Built-in |
