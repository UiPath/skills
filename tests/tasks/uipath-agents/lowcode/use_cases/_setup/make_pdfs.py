#!/usr/bin/env python3
"""Render every `<name>.pdf.txt` under the given directory into `<name>.pdf`.

Use-case tasks attach sample documents (invoices, SOC 2 excerpts, ...) to the
user's request. The repo keeps them as plain text so fixtures stay reviewable
and binary-free; a task's pre_run turns them into real, text-based PDFs inside
the sandbox and deletes the sources:

    python3 _setup/make_pdfs.py attachments && rm -rf _setup

A form feed (\\f) in the source starts a new page. Standard library only.
"""

import sys
from pathlib import Path

PAGE_W, PAGE_H = 612, 792
MARGIN, LEADING, FONT_SIZE = 56, 14, 10
LINES_PER_PAGE = (PAGE_H - 2 * MARGIN) // LEADING


def escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def pages_of(text: str) -> list[list[str]]:
    pages = []
    for chunk in text.split("\f"):
        lines = chunk.strip("\n").splitlines() or [""]
        for i in range(0, len(lines), LINES_PER_PAGE):
            pages.append(lines[i : i + LINES_PER_PAGE])
    return pages


def render(text: str) -> bytes:
    pages = pages_of(text)
    objects: list[bytes] = []
    n_pages = len(pages)
    # 1 catalog, 2 pages tree, 3 font, then (page, content) pairs.
    kids = " ".join(f"{4 + 2 * i} 0 R" for i in range(n_pages))
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    for i, lines in enumerate(pages):
        content_ref = 5 + 2 * i
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_ref} 0 R >>".encode()
        )
        ops = [f"BT /F1 {FONT_SIZE} Tf {LEADING} TL {MARGIN} {PAGE_H - MARGIN} Td"]
        ops += [f"({escape(line)}) Tj T*" for line in lines]
        ops.append("ET")
        stream = "\n".join(ops).encode("cp1252", errors="replace")
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for num, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{num} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    sources = sorted(root.rglob("*.pdf.txt"))
    for src in sources:
        target = src.with_name(src.name[: -len(".txt")])
        target.write_bytes(render(src.read_text(encoding="utf-8")))
        src.unlink()
        print(f"rendered {target}")
    if not sources:
        print(f"no *.pdf.txt under {root}")


if __name__ == "__main__":
    main()
