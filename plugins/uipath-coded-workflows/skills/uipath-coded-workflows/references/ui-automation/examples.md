# UI Automation Examples

Examples using the `uiAutomation` service from `UiPath.UIAutomation.Activities` package.

**Required package:** `"UiPath.UIAutomation.Activities": "[25.10.21]"`

---

## Basic Login Flow (Object Repository Descriptors)

```csharp
namespace MyProject
{
    public class LoginWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(string username, string password)
        {
            // Open the app and get a reference to the Login screen
            var loginScreen = uiAutomation.Open(Descriptors.MyApp.Login);

            // Type credentials
            loginScreen.TypeInto(Descriptors.MyApp.Login.Username, username);
            loginScreen.TypeInto(Descriptors.MyApp.Login.Password, password);

            // Click login button
            loginScreen.Click(Descriptors.MyApp.Login.Submit);

            // Attach to the Home screen (app is already open, just need a new screen reference)
            var homeScreen = uiAutomation.Attach(Descriptors.MyApp.Home);

            // Verify login success
            string welcomeMessage = homeScreen.GetText(Descriptors.MyApp.Home.WelcomeMessage);
            Log($"Login successful: {welcomeMessage}");
        }
    }
}
```

## Multi-Screen Navigation with Object Repository

```csharp
namespace MyProject
{
    public class SearchWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Open the app on the Home screen
            var homeScreen = uiAutomation.Open(Descriptors.ExampleApp.Home);
            homeScreen.Click(Descriptors.ExampleApp.Home.SearchButton);

            // Attach to the Search screen (same app, different screen)
            var searchScreen = uiAutomation.Attach(Descriptors.ExampleApp.Search);
            searchScreen.TypeInto(Descriptors.ExampleApp.Search.SearchBox, "example search query");

            // Attach to the SearchResults screen (same app, different screen)
            var searchResultsScreen = uiAutomation.Attach(Descriptors.ExampleApp.SearchResults);

            // Count results using GetChildren
            var count = searchResultsScreen.GetChildren(
                Descriptors.ExampleApp.SearchResults.Items, selectorFilter: null).Count();

            if (count > 0)
            {
                system.InvokeProcess("MyProcess");
            }
        }
    }
}
```

## Using String-Based Targets

```csharp
namespace MyProject
{
    public class StringTargetWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Open using screen name (string)
            var app = uiAutomation.Open("MainScreen", appName: "MyApp");

            // Interact using target names (strings defined in Object Repository)
            app.TypeInto("UsernameField", "admin");
            app.TypeInto("PasswordField", "password123");
            app.Click("LoginButton");

            // Get text from a target
            string status = app.GetText("StatusLabel");
            Log($"Status: {status}");
        }
    }
}
```

## Click with Advanced Options

```csharp
namespace MyProject
{
    public class ClickOptionsWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var app = uiAutomation.Open(Descriptors.MyApp.Main);

            // Double-click
            app.Click("item", NClickType.Double, NMouseButton.Left);

            // Right-click
            app.Click("item", NClickType.Single, NMouseButton.Right);

            // Click with Ctrl held down (for multi-select)
            app.Click("item", Options.Click().With(keyModifiers: NKeyModifiers.Ctrl));

            // Click with verification — retry until a success message appears
            app.Click("submitBtn", Options.Click()
                .Until("successMessage", until: NVerifyMode.Appears, retry: true, timeout: 5));
        }
    }
}
```

## TypeInto with Options

```csharp
namespace MyProject
{
    public class TypeIntoOptionsWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var app = uiAutomation.Open(Descriptors.MyApp.Form);

            // Type with field clearing first
            app.TypeInto("nameField", Options.TypeInto("John Doe")
                .With(emptyFieldMode: NEmptyFieldMode.SingleLine));

            // Type with click before and custom delay
            app.TypeInto("searchField", Options.TypeInto("search term")
                .With(clickBeforeMode: NClickMode.Single, delayBetweenKeys: 0.05));

            // Type and verify the text was entered correctly
            app.TypeInto("emailField", Options.TypeInto("user@example.com")
                .UntilText("user@example.com", retry: true, timeout: 3));

            // Type with SecureString
            var securePassword = new System.Security.SecureString();
            foreach (char c in "secret") securePassword.AppendChar(c);
            app.TypeInto("passwordField", securePassword);
        }
    }
}
```

## Browser Automation

```csharp
namespace MyProject
{
    public class BrowserWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Set runtime browser to Chrome
            uiAutomation.SetRuntimeBrowser(NBrowserType.Chrome);

            // Open a browser screen with browser options
            var browser = uiAutomation.Open(Descriptors.MyWebApp.Main,
                Options.AppOpen().WithBrowserOptions(isIncognito: true));

            // Navigate to a URL
            browser.GoToUrl("https://example.com/dashboard");

            // Get current URL
            string currentUrl = browser.GetUrl();
            Log($"Current URL: {currentUrl}");

            // Interact with web elements
            browser.TypeInto(Descriptors.MyWebApp.Main.SearchInput, "test query");
            browser.Click(Descriptors.MyWebApp.Main.SearchButton);

            // Wait for results to appear
            bool appeared = browser.WaitState(
                Descriptors.MyWebApp.Main.ResultsPanel,
                NCheckStateMode.WaitAppear, timeout: 10);

            if (appeared)
            {
                string resultText = browser.GetText(Descriptors.MyWebApp.Main.FirstResult);
                Log($"First result: {resultText}");
            }
        }
    }
}
```

## Keyboard Shortcuts

```csharp
namespace MyProject
{
    public class KeyboardWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var app = uiAutomation.Open(Descriptors.MyApp.Editor);

            // Select all text with Ctrl+A
            app.KeyboardShortcut("textArea", Options.KeyboardShortcutCtrlA());

            // Copy with Ctrl+C
            app.KeyboardShortcut("textArea", Options.KeyboardShortcutCtrlC());

            // Navigate to another field
            app.Click("outputField");

            // Paste with Ctrl+V
            app.KeyboardShortcut("outputField", Options.KeyboardShortcutCtrlV());

            // Send Escape
            app.KeyboardShortcut("dialog", Options.KeyboardShortcutEsc());

            // Custom shortcut Ctrl+S
            app.KeyboardShortcut("editor", Options.KeyboardShortcutCtrl("s"));

            // Send keyboard shortcut without a target (to active window)
            app.KeyboardShortcut(Options.KeyboardShortcutTab());
        }
    }
}
```

## Data Extraction from Table

```csharp
using System.Data;

namespace MyProject
{
    public class ExtractDataWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var app = uiAutomation.Open(Descriptors.MyApp.DataPage);

            // Extract table data using Object Repository configuration
            DataTable data = app.ExtractTableData(
                Descriptors.MyApp.DataPage.DataTable,
                Options.ExtractTableData(
                    delayBetweenPages: 1.0,
                    interactionMode: NChildInteractionMode.SameAsCard,
                    limitExtractionTo: LimitType.Rows,
                    numberOfItems: 100));

            Log($"Extracted {data.Rows.Count} rows");

            foreach (DataRow row in data.Rows)
            {
                Log($"Name: {row["Name"]}, Value: {row["Value"]}");
            }
        }
    }
}
```

## WaitState and Conditional Logic

```csharp
namespace MyProject
{
    public class WaitStateWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var app = uiAutomation.Open(Descriptors.MyApp.Main);

            // Click submit and wait for processing
            app.Click("submitButton");

            // Wait for loading spinner to disappear
            bool disappeared = app.WaitState("loadingSpinner",
                NCheckStateMode.WaitDisappear, timeout: 30);

            if (!disappeared)
            {
                Log("Timeout waiting for loading to complete");
                return;
            }

            // Check if success message appeared
            bool success = app.WaitState("successMessage",
                NCheckStateMode.WaitAppear, timeout: 5);

            if (success)
            {
                Log("Operation completed successfully");
            }
            else
            {
                // Check if element is enabled
                bool retryEnabled = app.IsEnabled("retryButton");
                if (retryEnabled)
                {
                    app.Click("retryButton");
                }
            }
        }
    }
}
```

## Scrolling and Element Discovery

```csharp
using System.Collections.Generic;
using System.Linq;

namespace MyProject
{
    public class ScrollAndDiscoverWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var app = uiAutomation.Open(Descriptors.MyApp.List);

            // Scroll down in a list
            app.MouseScroll("listContainer", NScrollDirection.Down, movementUnits: 5);

            // Scroll until a specific element is visible
            app.MouseScroll("listContainer", "targetItem",
                NScrollDirection.Down, movementUnits: 100);

            // Get children of an element
            IEnumerable<RuntimeTarget> children = app.GetChildren(
                "listContainer", selectorFilter: "<listitem />", recursive: false);

            Log($"Found {children.Count()} list items");

            // Interact with discovered children
            foreach (var child in children)
            {
                string text = app.GetText(child);
                Log($"Item: {text}");
            }
        }
    }
}
```

## SAP Automation

```csharp
namespace MyProject
{
    public class SAPWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var sapApp = uiAutomation.Open(Descriptors.SAP.MainScreen);

            // Call a transaction
            sapApp.SAPCallTransaction("VA01");

            // Select a menu item
            sapApp.SAPSelectMenuItem("System/User Profile/Own Data");

            // Click a toolbar button
            sapApp.SAPClickToolbarButton("toolbar", "Execute");

            // Select a date in calendar
            sapApp.SAPSelectDatesInCalendar("calendarField", DateTime.Today);

            // Select date range
            sapApp.SAPSelectDatesInCalendar("calendarField",
                new DateTime(2024, 1, 1), new DateTime(2024, 12, 31));

            // Read statusbar
            var statusbar = sapApp.SAPReadStatusbar();
            Log($"SAP Status: {statusbar.MessageType} - {statusbar.MessageText}");

            // Expand tree
            sapApp.SAPExpandTree("treeControl", "Root/Level1/Level2");
        }
    }
}
```

## Form Filling

```csharp
namespace MyProject
{
    public class FormFillingWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var app = uiAutomation.Open(Descriptors.MyApp.RegistrationForm);

            // Fill a form using a data source
            var formData = new Dictionary<string, object>
            {
                { "FirstName", "John" },
                { "LastName", "Doe" },
                { "Email", "john.doe@example.com" }
            };

            app.FillForm(formData);

            // Or with options
            app.FillForm(Options.FillForm(formData).With(enableValidation: true));

            // Close any popup that may appear
            app.ClosePopup(Options.ClosePopup(
                preferredButtons: new[] { "OK", "Accept" },
                popupAppearTimeout: 3));
        }
    }
}
```

## Screenshots and Drag-and-Drop

```csharp
namespace MyProject
{
    public class MiscWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var app = uiAutomation.Open(Descriptors.MyApp.Canvas);

            // Take a screenshot of a specific element
            app.TakeScreenshot("chartArea", @"C:\temp\chart.png");

            // Take a screenshot of the whole screen (via service)
            uiAutomation.TakeScreenshot(Options.TakeScreenshotToFile(@"C:\temp\fullscreen.png"));

            // Highlight an element for debugging
            app.Highlight("importantElement", KnownColor.Red, duration: 5);

            // Drag and drop using descriptors
            app.DragAndDrop(
                Descriptors.MyApp.Canvas.SourceItem,
                Descriptors.MyApp.Canvas.DropZone);

            // Drag and drop using string targets with options
            app.DragAndDrop("sourceItem", app["dropTarget"],
                keyModifiers: NKeyModifiers.Ctrl);

            // Get attribute
            string className = app.GetAttribute("myElement", "class");
            Log($"Element class: {className}");

            // Clipboard operations
            uiAutomation.SetClipboard(new SetClipboardOptions { Text = "Hello from clipboard" });
            string clipboardText = uiAutomation.GetClipboard(new GetClipboardOptions());
            Log($"Clipboard: {clipboardText}");
        }
    }
}
```

## JavaScript Injection (Browser)

```csharp
namespace MyProject
{
    public class JsInjectionWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var browser = uiAutomation.Open(Descriptors.MyWebApp.Main);

            // Inject and execute a JavaScript file
            string result = browser.InjectJsScript(
                Descriptors.MyWebApp.Main.WebPage,
                Options.InjectJsScript("scripts/getData.js", inputParameter: "param1"));

            Log($"JS result: {result}");
        }
    }
}
```

## UI Task (AI Agent) — ScreenPlay

```csharp
namespace MyProject
{
    public class UITaskWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var app = uiAutomation.Open(Descriptors.MyApp.Main);

            // Simple UITask — let the AI agent perform a task described in natural language
            var result = app.UITask(
                "Click the 'New Order' button, fill in Customer Name with 'Acme Corp' and Amount with '1500', then click Submit",
                NUITaskAgentType.GeminiFlash25);

            Log($"Status: {result.Status}, Result: {result.Result}");

            // UITask with full options
            var detailedResult = app.UITask(Options.UITask("Navigate to the Reports tab and export the monthly summary as PDF")
                .With(
                    agentType: NUITaskAgentType.GPT5,
                    maxIterations: 15,
                    isDOMEnabled: true,
                    clipboardMode: NTypeByClipboardMode.WhenPossible,
                    traceAttachMode: NTraceAttachMode.Always));

            if (detailedResult.ErrorMessage != null)
            {
                Log($"UITask failed: {detailedResult.ErrorMessage}");
            }
            else
            {
                Log($"Export completed: {detailedResult.Result}");
            }

            // Async variant
            var asyncResult = app.UITaskAsync(
                "Verify that the order confirmation dialog is displayed and close it",
                NUITaskAgentType.DOMBasedGPT41).GetAwaiter().GetResult();

            Log($"Verification: {asyncResult.Status}");
        }
    }
}
```

## Multi-Screen Web Form with UILibrary Package Descriptors

Demonstrates navigating across multiple screens using descriptors from a UILibrary NuGet package, filling a web form, checking results, and sending a notification email. Note the `using` statement references the **package** namespace, not the project namespace.

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
using UiPath.UIAutomationNext.API.Contracts;
using UiPath.UIAutomationNext.API.Models;
using UiPath.UIAutomationNext.Enums;
using UiPath.Mail.Activities.Api;
using Acme.InsurancePortal.ObjectRepository;  // UILibrary package namespace, NOT project namespace

namespace MyProject
{
    public class SubmitInsuranceQuote : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Open the app on the Dashboard screen
            var dashboard = uiAutomation.Open(Descriptors.InsurancePortal.Dashboard);

            // Navigate — click elements that belong to the Dashboard screen using its handle
            dashboard.Click(Descriptors.InsurancePortal.Dashboard.Services);
            dashboard.Click(Descriptors.InsurancePortal.Dashboard.NewQuote);

            // Attach to the next screen — use a NEW handle for CategorySelection elements
            var categoryScreen = uiAutomation.Attach(Descriptors.InsurancePortal.CategorySelection);
            categoryScreen.Click(Descriptors.InsurancePortal.CategorySelection.AutoInsurance);

            // Fill the form on the QuoteForm screen
            var formScreen = uiAutomation.Attach(Descriptors.InsurancePortal.QuoteForm);
            formScreen.TypeInto(Descriptors.InsurancePortal.QuoteForm.FullName, "John Doe");
            formScreen.TypeInto(Descriptors.InsurancePortal.QuoteForm.Email, "john.doe@example.com");
            formScreen.TypeInto(Descriptors.InsurancePortal.QuoteForm.VehicleYear, "2023");
            // Use TypeInto for web dropdowns — SelectItem often fails on web <select> elements
            formScreen.TypeInto(Descriptors.InsurancePortal.QuoteForm.CoverageType, "Comprehensive");
            formScreen.TypeInto(Descriptors.InsurancePortal.QuoteForm.Deductible, "500");
            formScreen.Click(Descriptors.InsurancePortal.QuoteForm.Submit);

            // Check result on the Confirmation screen
            var confirmScreen = uiAutomation.Attach(Descriptors.InsurancePortal.Confirmation);
            bool isApproved = confirmScreen.WaitState(
                Descriptors.InsurancePortal.Confirmation.ApprovedBanner,
                NCheckStateMode.WaitAppear, timeout: 10);

            string status = isApproved
                ? $"Quote APPROVED. Premium: {confirmScreen.GetText(Descriptors.InsurancePortal.Confirmation.PremiumAmount)}"
                : "Quote DECLINED";

            // Send result via email
            mail.Outlook().SendMail(
                new SendOutlookMailOptions()
                    .WithTo(new List<string> { "john.doe@example.com" })
                    .WithSubject("Insurance Quote Result")
                    .WithBody($"Result: {status}"));

            Log($"Done. Status: {status}");
        }
    }
}
```

**Key patterns demonstrated:**
- **UILibrary package descriptors**: `using Acme.InsurancePortal.ObjectRepository;` — the namespace comes from the package, not the project
- **Screen handle affinity**: Each screen's elements are used ONLY with that screen's handle (`dashboard` for Dashboard elements, `formScreen` for QuoteForm elements — mixing them causes `"Target name 'X' is not part of the current screen"`)
- **`TypeInto` for web dropdowns**: Use `TypeInto` instead of `SelectItem` for web `<select>` elements — `SelectItem` often fails with `"Cannot select item"`
- **Multi-screen navigation**: `Open` for the first screen, `Attach` for subsequent screens
- **`WaitState` for result checking**: Check if a success/failure element appears after form submission

## Using Dispose Pattern

```csharp
namespace MyProject
{
    public class DisposePatternWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // UiTargetApp implements IDisposable
            using (var app = uiAutomation.Open(Descriptors.MyApp.Main))
            {
                app.TypeInto(Descriptors.MyApp.Main.Input, "test");
                app.Click(Descriptors.MyApp.Main.Submit);
            }
            // App handle is disposed here - depending on CloseMode, the app may be closed
        }
    }
}
```
