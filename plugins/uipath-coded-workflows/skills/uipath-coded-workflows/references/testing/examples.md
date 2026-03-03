# Testing Examples

Examples using the `testing` service from `UiPath.Testing.Activities` package.

**Required package:** `"UiPath.Testing.Activities": "[25.10.0]"`

---

## Basic Verification Test Case

```csharp
namespace MyProject
{
    public class BasicVerificationTest : CodedWorkflow
    {
        [TestCase]
        public void Execute()
        {
            // Verify a boolean expression
            int count = 10;
            testing.VerifyExpression(count > 0, "Count should be positive");

            // Verify equality
            string expected = "Active";
            string actual = "Active";
            testing.VerifyAreEqual(expected, actual, "Status should be Active");

            // Verify inequality
            testing.VerifyAreNotEqual("Pending", actual, "Status should not be Pending");
        }
    }
}
```

## Comparison Operators Test Case

```csharp
namespace MyProject
{
    public class ComparisonTest : CodedWorkflow
    {
        [TestCase]
        public void Execute()
        {
            decimal price = 49.99m;
            int quantity = 5;

            // Greater than
            testing.VerifyIsGreater(price, 0, "Price must be positive");

            // Greater than or equal
            testing.VerifyIsGreaterOrEqual(quantity, 1, "Quantity must be at least 1");

            // Less than
            testing.VerifyIsLess(price, 1000, "Price must be under 1000");

            // Less than or equal
            testing.VerifyIsLessOrEqual(quantity, 100, "Quantity must be 100 or less");

            // Contains
            string description = "Premium Gold Package";
            testing.VerifyContains(description, "Gold", "Description should contain 'Gold'");

            // Regex match
            string email = "user@example.com";
            testing.VerifyIsRegexMatch(email, @"^[\w.-]+@[\w.-]+\.\w+$", "Should be a valid email");
        }
    }
}
```

## Range Verification

```csharp
namespace MyProject
{
    public class RangeVerificationTest : CodedWorkflow
    {
        [TestCase]
        public void Execute()
        {
            double temperature = 72.5;

            // Verify value is within range
            testing.VerifyRange(
                temperature,
                60.0,
                80.0,
                VerificationType.IsWithin,
                "Temperature should be between 60 and 80"
            );

            // Verify value is NOT within range
            double anomaly = 150.0;
            testing.VerifyRange(
                anomaly,
                60.0,
                80.0,
                VerificationType.IsNotWithin,
                "Anomaly should be outside normal range"
            );
        }
    }
}
```

## Using VerifyExpressionWithOperator

```csharp
namespace MyProject
{
    public class OperatorVerificationTest : CodedWorkflow
    {
        [TestCase]
        public void Execute()
        {
            object actualValue = 42;
            object expectedValue = 42;

            // Equality
            testing.VerifyExpressionWithOperator(
                actualValue,
                Comparison.Equality,
                expectedValue,
                "Values should be equal"
            );

            // Greater than
            testing.VerifyExpressionWithOperator(
                100,
                Comparison.GreaterThan,
                50,
                "100 should be greater than 50"
            );

            // Contains
            testing.VerifyExpressionWithOperator(
                "Hello World",
                Comparison.Contains,
                "World",
                "String should contain 'World'"
            );

            // With continue on failure
            testing.VerifyExpressionWithOperator(
                "test",
                Comparison.RegexMatch,
                @"^\w+$",
                "Should match word pattern",
                continueOnFailure: true,
                alternativeVerificationTitle: "Regex validation",
                takeScreenshotInCaseOfFailingAssertion: true,
                takeScreenshotInCaseOfSucceedingAssertion: false
            );
        }
    }
}
```

## Random Data Generation

```csharp
namespace MyProject
{
    public class RandomDataWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Generate random names
            string firstName = testing.GivenName();
            string lastName = testing.LastName();
            Log($"Name: {firstName} {lastName}");

            // Generate random numbers
            decimal price = testing.RandomNumber(10, 500, 2);
            decimal wholeNumber = testing.RandomNumber(1, 100);
            Log($"Price: {price:C}, Number: {wholeNumber}");

            // Generate a random date
            DateTime randomDate = testing.RandomDate(
                new DateTime(2024, 1, 1),
                new DateTime(2025, 1, 1)
            );
            Log($"Date: {randomDate:yyyy-MM-dd}");

            // Generate a random string
            string code = testing.RandomString(Case.UpperCase, 8);
            Log($"Code: {code}");

            // Generate a random value from a set
            string status = testing.RandomValue(new[] { "Active", "Pending", "Closed" });
            Log($"Status: {status}");

            // Generate an address
            string address = testing.Address();
            Log($"Address: {address}");
        }
    }
}
```

## Test Data Queues

```csharp
namespace MyProject
{
    public class TestDataQueueWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            string queueName = "TestCustomers";

            // Add a single item to the test data queue
            var itemContent = new Dictionary<string, object>
            {
                { "Name", "John Doe" },
                { "Email", "john@example.com" },
                { "Amount", 150.00 }
            };
            testing.AddTestDataQueueItem(queueName, itemContent);

            // Add multiple items in bulk
            var items = new List<TestDataQueueItem>
            {
                new TestDataQueueItem
                {
                    Content = new Dictionary<string, object>
                    {
                        { "Name", "Alice" },
                        { "Email", "alice@example.com" }
                    }
                },
                new TestDataQueueItem
                {
                    Content = new Dictionary<string, object>
                    {
                        { "Name", "Bob" },
                        { "Email", "bob@example.com" }
                    }
                }
            };
            testing.BulkAddTestDataQueueItems(queueName, items);

            // Get the next unconsumed item
            TestDataQueueItem nextItem = testing.GetTestDataQueueItem(queueName);
            if (nextItem != null)
            {
                Log($"Processing: {nextItem.Content["Name"]}");
            }

            // Get multiple items
            IEnumerable<TestDataQueueItem> allItems = testing.GetTestDataQueueItems(queueName);

            // Delete all items
            testing.DeleteTestDataQueueItems(queueName);
        }
    }
}
```

## PDF Document Comparison

```csharp
namespace MyProject
{
    public class PdfComparisonTest : CodedWorkflow
    {
        [TestCase]
        public void Execute()
        {
            // Simple PDF comparison
            ComparisonResult result = testing.ComparePdfDocuments(
                @"C:\Docs\baseline.pdf",
                @"C:\Docs\actual.pdf"
            );

            testing.VerifyExpression(result.AreEquivalent, "PDFs should match");

            if (!result.AreEquivalent)
            {
                Log($"Found {result.Differences.Count} differences:");
                foreach (var diff in result.Differences)
                {
                    Log($"  [{diff.Operation}] {diff.Text}");
                }
            }

            // PDF comparison with options — ignore dates and generate HTML diff
            ComparisonResult detailedResult = testing.ComparePdfDocuments(
                @"C:\Docs\baseline.pdf",
                @"C:\Docs\actual.pdf",
                ComparisonType.Word,
                TestingOptions.CompareDocuments()
                    .WithIgnoreRegexRule("dates", @"\d{2}/\d{2}/\d{4}")
                    .WithIgnoreWildcardRule("timestamps", "??:??:??")
                    .WithIgnoreIdenticalItems(true)
                    .WithGenerateHtml(@"C:\Output\diff.html")
                    .WithContinueOnError(true)
            );
        }
    }
}
```

## Text Comparison

```csharp
namespace MyProject
{
    public class TextComparisonTest : CodedWorkflow
    {
        [TestCase]
        public void Execute()
        {
            string baseline = "The order total is $150.00.\nShipped on 01/15/2024.";
            string actual = "The order total is $150.00.\nShipped on 02/20/2024.";

            // Simple text comparison
            ComparisonResult result = testing.CompareText(baseline, actual);

            if (!result.AreEquivalent)
            {
                Log($"Texts differ: {result.Differences.Count} differences");
            }

            // Compare with rules to ignore dates
            ComparisonResult withRules = testing.CompareText(
                baseline,
                actual,
                ComparisonType.Word,
                TestingOptions.CompareText()
                    .WithIgnoreRegexRule("dates", @"\d{2}/\d{2}/\d{4}")
                    .WithIgnoreIdenticalItems(true)
            );

            testing.VerifyExpression(withRules.AreEquivalent,
                "Texts should match when ignoring dates");
        }
    }
}
```

## Attach Document to Test Results

```csharp
namespace MyProject
{
    public class AttachDocumentTest : CodedWorkflow
    {
        [TestCase]
        public void Execute()
        {
            // Run some test logic
            string result = "Test passed with 100% accuracy";

            // Attach a file to the test results in Orchestrator
            testing.AttachDocument(@"C:\Output\test_report.pdf", "Test Report PDF");

            // Verify the result
            testing.VerifyExpression(result.Contains("passed"), "Test should pass");
        }
    }
}
```

## Full Integration Test — UI + Verification

```csharp
namespace MyProject
{
    public class IntegrationTest : CodedWorkflow
    {
        [TestCase]
        public void Execute()
        {
            // Generate test data
            string testName = testing.GivenName() + " " + testing.LastName();
            string testEmail = $"test_{testing.RandomNumber(1000, 9999)}@example.com";

            // Open app and fill form
            var app = uiAutomation.Open(Descriptors.MyApp.Registration);
            app.TypeInto(Descriptors.MyApp.Registration.NameField, testName);
            app.TypeInto(Descriptors.MyApp.Registration.EmailField, testEmail);
            app.Click(Descriptors.MyApp.Registration.SubmitButton);

            // Attach screenshot
            uiAutomation.TakeScreenshot(Options.TakeScreenshotToFile(@"C:\temp\registration.png"));
            testing.AttachDocument(@"C:\temp\registration.png", "Registration Screenshot");

            // Verify success
            var confirmScreen = uiAutomation.Attach(Descriptors.MyApp.Confirmation);
            string confirmText = confirmScreen.GetText(Descriptors.MyApp.Confirmation.Message);

            testing.VerifyContains(confirmText, "successfully",
                $"Registration should succeed for {testName}");

            testing.VerifyExpressionWithOperator(
                confirmText,
                Comparison.Contains,
                testName,
                "Confirmation should contain the registered name"
            );
        }
    }
}
```

## Data-Driven Test with Test Data Queue

```csharp
namespace MyProject
{
    public class DataDrivenTest : CodedWorkflow
    {
        [TestCase]
        public void Execute()
        {
            // Get test data from Orchestrator queue
            var testData = testing.GetTestDataQueueItems("LoginTestData");

            foreach (var item in testData)
            {
                string username = item.Content["Username"].ToString();
                string password = item.Content["Password"].ToString();
                string expectedResult = item.Content["ExpectedResult"].ToString();

                Log($"Testing login for: {username}");

                var app = uiAutomation.Open(Descriptors.MyApp.Login);
                app.TypeInto(Descriptors.MyApp.Login.Username, username);
                app.TypeInto(Descriptors.MyApp.Login.Password, password);
                app.Click(Descriptors.MyApp.Login.LoginButton);

                if (expectedResult == "Success")
                {
                    bool appeared = app.WaitState("welcomeMessage",
                        NCheckStateMode.WaitAppear, timeout: 5);
                    testing.VerifyExpression(appeared,
                        $"Login should succeed for {username}",
                        continueOnFailure: true);
                }
                else
                {
                    bool errorAppeared = app.WaitState("errorMessage",
                        NCheckStateMode.WaitAppear, timeout: 5);
                    testing.VerifyExpression(errorAppeared,
                        $"Login should fail for {username}",
                        continueOnFailure: true);
                }
            }
        }
    }
}
```
