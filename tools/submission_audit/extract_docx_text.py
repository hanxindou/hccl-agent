"""Extract review text from a DOCX without modifying the source document.

The extractor walks WordprocessingML in document order and tracks explicit or
last-rendered page breaks.  It is intentionally small and standard-library
only so the competition requirement audit does not need an extra dependency.
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"


def extract_lines(docx_path: Path) -> list[tuple[int, str]]:
    """Return non-empty paragraph/table-cell text with an estimated page."""

    with zipfile.ZipFile(docx_path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))

    page = 1
    lines: list[tuple[int, str]] = []
    body = root.find(f"{W}body")
    if body is None:
        return lines

    for block in body:
        if block.tag not in {f"{W}p", f"{W}tbl"}:
            continue
        parts: list[str] = []
        for node in block.iter():
            if node.tag == f"{W}lastRenderedPageBreak":
                if parts:
                    text = "".join(parts).strip()
                    if text:
                        lines.append((page, text))
                    parts = []
                page += 1
            elif node.tag == f"{W}br" and node.get(f"{W}type") == "page":
                if parts:
                    text = "".join(parts).strip()
                    if text:
                        lines.append((page, text))
                    parts = []
                page += 1
            elif node.tag == f"{W}t" and node.text:
                parts.append(node.text)
            elif node.tag in {f"{W}tab", f"{W}tc"} and parts:
                parts.append("\t")
        text = "".join(parts).strip()
        if text:
            lines.append((page, text))
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("docx", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = "\n".join(
        f"{index:04d}\tpage={page}\t{text}"
        for index, (page, text) in enumerate(extract_lines(args.docx), start=1)
    )
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
