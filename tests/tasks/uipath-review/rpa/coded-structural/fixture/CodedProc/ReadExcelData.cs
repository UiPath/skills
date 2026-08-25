using System;
using System.Collections.Generic;
using System.Data;
using UiPath.CodedWorkflows;
using UiPath.Core;
using UiPath.Excel;
using UiPath.Excel.Activities;
using UiPath.Excel.Activities.API;
using UiPath.Excel.Activities.API.Models;

namespace CodedProc
{
    public class ReadExcelData : CodedWorkflow
    {
        [Workflow]
        public DataTable Execute(string filePath)
        {
            Log($"Reading Excel file: {filePath}");

            DataTable excelData;
            using (var wb = excel.UseWorkBook(filePath))
            {
                excelData = ExcelOperations.ReadRange(wb, "Invoices", null, true, false);
            }

            Log($"Successfully read {excelData.Rows.Count} rows with {excelData.Columns.Count} columns.");
            return excelData;
        }
    }
}
