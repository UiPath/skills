using System;
using System.Data;
using System.IO;
using PdfSharp.Drawing;
using PdfSharp.Drawing.Layout;
using PdfSharp.Fonts;
using PdfSharp.Pdf;

namespace CodedProc
{
    public static class InvoicePdfGenerator
    {
        private static bool _fontResolverInitialized;

        public static string Generate(DataRow row, string outputFolder)
        {
            if (!_fontResolverInitialized)
            {
                GlobalFontSettings.FontResolver = new WindowsFontResolver();
                _fontResolverInitialized = true;
            }

            var invoiceId = row["Invoice ID"].ToString();
            var invoiceDate = row["Invoice Date"].ToString();
            var customerName = row["Customer Name"].ToString();
            var customerEmail = row["Customer Email"].ToString();
            var itemDescription = row["Item Description"].ToString();
            var quantity = row["Quantity"].ToString();
            var unitPrice = row["Unit Price"].ToString();
            var totalAmount = row["Total Amount"].ToString();
            var status = row["Status"].ToString();

            var fileName = $"Invoice_{invoiceId}.pdf";
            var filePath = Path.Combine(outputFolder, fileName);

            var document = new PdfDocument();
            document.Info.Title = $"Invoice #{invoiceId}";
            var page = document.AddPage();
            var gfx = XGraphics.FromPdfPage(page);

            var fontTitle = new XFont("Arial", 22, XFontStyleEx.Bold);
            var fontSubtitle = new XFont("Arial", 10, XFontStyleEx.Regular);
            var fontLabel = new XFont("Arial", 11, XFontStyleEx.Bold);
            var fontNormal = new XFont("Arial", 11, XFontStyleEx.Regular);
            var fontHeaderCell = new XFont("Arial", 10, XFontStyleEx.Bold);
            var fontCell = new XFont("Arial", 10, XFontStyleEx.Regular);
            var fontTotal = new XFont("Arial", 14, XFontStyleEx.Bold);
            var fontFooter = new XFont("Arial", 8, XFontStyleEx.Regular);

            var accentColor = XColor.FromArgb(30, 58, 138);
            var accentBrush = new XSolidBrush(accentColor);
            var greyBrush = new XSolidBrush(XColors.Gray);
            var lightGreyBrush = new XSolidBrush(XColor.FromArgb(245, 245, 245));

            double margin = 50;
            double y = margin;
            double contentWidth = page.Width - 2 * margin;

            // Header — Invoice title
            gfx.DrawString($"INVOICE #{invoiceId}", fontTitle, accentBrush,
                new XRect(margin, y, contentWidth, 30), XStringFormats.TopLeft);
            y += 32;

            // Date
            gfx.DrawString($"Date: {invoiceDate}", fontSubtitle, greyBrush,
                new XRect(margin, y, contentWidth, 15), XStringFormats.TopLeft);
            y += 20;

            // Separator line
            gfx.DrawLine(new XPen(XColors.LightGray, 1), margin, y, margin + contentWidth, y);
            y += 20;

            // Bill To section
            gfx.DrawString("Bill To:", fontLabel, XBrushes.Black,
                new XRect(margin, y, contentWidth, 15), XStringFormats.TopLeft);
            y += 18;
            gfx.DrawString(customerName, fontNormal, XBrushes.Black,
                new XRect(margin, y, contentWidth, 15), XStringFormats.TopLeft);
            y += 16;
            gfx.DrawString(customerEmail, fontSubtitle, greyBrush,
                new XRect(margin, y, contentWidth, 15), XStringFormats.TopLeft);
            y += 30;

            // Table — column widths
            double col1 = contentWidth * 0.45;
            double col2 = contentWidth * 0.15;
            double col3 = contentWidth * 0.20;
            double col4 = contentWidth * 0.20;
            double rowHeight = 30;
            double cellPadding = 8;

            // Table header
            gfx.DrawRectangle(accentBrush, margin, y, contentWidth, rowHeight);
            double hx = margin;
            gfx.DrawString("Description", fontHeaderCell, XBrushes.White,
                new XRect(hx + cellPadding, y, col1 - cellPadding, rowHeight), XStringFormats.CenterLeft);
            hx += col1;
            gfx.DrawString("Qty", fontHeaderCell, XBrushes.White,
                new XRect(hx + cellPadding, y, col2 - cellPadding, rowHeight), XStringFormats.CenterLeft);
            hx += col2;
            gfx.DrawString("Unit Price", fontHeaderCell, XBrushes.White,
                new XRect(hx + cellPadding, y, col3 - cellPadding, rowHeight), XStringFormats.CenterLeft);
            hx += col3;
            gfx.DrawString("Total", fontHeaderCell, XBrushes.White,
                new XRect(hx + cellPadding, y, col4 - cellPadding, rowHeight), XStringFormats.CenterLeft);
            y += rowHeight;

            // Table data row
            gfx.DrawRectangle(lightGreyBrush, margin, y, contentWidth, rowHeight);
            hx = margin;
            gfx.DrawString(itemDescription, fontCell, XBrushes.Black,
                new XRect(hx + cellPadding, y, col1 - cellPadding, rowHeight), XStringFormats.CenterLeft);
            hx += col1;
            gfx.DrawString(quantity, fontCell, XBrushes.Black,
                new XRect(hx + cellPadding, y, col2 - cellPadding, rowHeight), XStringFormats.CenterLeft);
            hx += col2;
            gfx.DrawString($"${unitPrice}", fontCell, XBrushes.Black,
                new XRect(hx + cellPadding, y, col3 - cellPadding, rowHeight), XStringFormats.CenterLeft);
            hx += col3;
            gfx.DrawString($"${totalAmount}", fontLabel, XBrushes.Black,
                new XRect(hx + cellPadding, y, col4 - cellPadding, rowHeight), XStringFormats.CenterLeft);
            y += rowHeight;

            // Bottom border
            gfx.DrawLine(new XPen(XColors.LightGray, 1), margin, y, margin + contentWidth, y);
            y += 25;

            // Total amount — right aligned
            gfx.DrawString($"Total: ${totalAmount}", fontTotal, accentBrush,
                new XRect(margin, y, contentWidth, 20), XStringFormats.TopRight);
            y += 22;

            // Status — right aligned with color
            XBrush statusBrush;
            if (status == "Paid")
                statusBrush = new XSolidBrush(XColor.FromArgb(21, 128, 61));
            else if (status == "Overdue")
                statusBrush = new XSolidBrush(XColor.FromArgb(185, 28, 28));
            else
                statusBrush = new XSolidBrush(XColor.FromArgb(217, 119, 6));

            gfx.DrawString($"Status: {status}", fontLabel, statusBrush,
                new XRect(margin, y, contentWidth, 15), XStringFormats.TopRight);

            // Footer
            gfx.DrawString($"Generated on {DateTime.Now:yyyy-MM-dd HH:mm}", fontFooter, greyBrush,
                new XRect(margin, page.Height - margin, contentWidth, 15), XStringFormats.TopCenter);

            document.Save(filePath);
            return filePath;
        }
    }
}
