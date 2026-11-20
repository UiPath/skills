using System.Activities;
using System.Activities.Validation;
using System.Activities.XamlIntegration;

namespace XamlRunner;

public static class XamlLoader
{
    public static Activity Load(string path)
    {
        using var reader = new StreamReader(path);
        return ActivityXamlServices.Load(reader, new ActivityXamlServicesSettings { CompileExpressions = false });
    }

    // CoreWF reports "Compiler error(s) encountered." with no BC diagnostic when Roslyn's in-memory
    // assembly build throws rather than when the expression is wrong, and under load that happens
    // about once in a hundred compiles. It is not a verdict on the workflow, so reload and revalidate.
    public static (Activity Activity, ValidationResults Results, int Retries) LoadAndValidate(string path)
    {
        for (var attempt = 0; ; attempt++)
        {
            var activity = Load(path);
            var results = ActivityValidationServices.Validate(activity);
            var transient = results.Errors.Count > 0 && results.Errors.All(e => e.Message.Contains("Compiler error(s) encountered.") && !e.Message.Contains(" error BC"));
            if (!transient || attempt == 2) return (activity, results, attempt);
        }
    }
}
