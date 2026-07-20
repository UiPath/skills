using System;
using System.IO;
using PdfSharp.Fonts;

namespace CodedProc
{
    public class WindowsFontResolver : IFontResolver, IFontResolverMarker
    {
        private static readonly string FontsFolder =
            Environment.GetFolderPath(Environment.SpecialFolder.Fonts);

        public FontResolverInfo ResolveTypeface(string familyName, bool bold, bool italic)
        {
            string fontFile;

            if (bold && italic)
                fontFile = "arialbi.ttf";
            else if (bold)
                fontFile = "arialbd.ttf";
            else if (italic)
                fontFile = "ariali.ttf";
            else
                fontFile = "arial.ttf";

            return new FontResolverInfo(fontFile);
        }

        public byte[] GetFont(string faceName)
        {
            var path = Path.Combine(FontsFolder, faceName);
            if (File.Exists(path))
                return File.ReadAllBytes(path);

            return null;
        }
    }
}
