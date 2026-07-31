using System;
using System.IO;

namespace CodedProc
{
    // Entry coded workflow for the invoice process. As written it does NOT
    // inherit CodedWorkflow and the Execute method carries no [Workflow]
    // attribute, so it is not a valid coded-workflow entry point.
    public class Main
    {
        public void Execute(string excelFilePath, out string result)
        {
            var raw = File.ReadAllText(@"C:\Invoices\Input.xlsx");
            result = raw.ToUpperInvariant();
        }
    }
}
