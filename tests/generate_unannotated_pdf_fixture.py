"""Generate tests/in/unannotated pdf.rmdoc.

A reMarkable PDF that was added but never annotated: its `.content` has
`tags` and `pages` set to null and no `cPages`. Reproduces the crash fixed in
get_document_tags / get_pages_data. Run from the repository root:

    python tests/generate_unannotated_pdf_fixture.py
"""
import json
import pathlib
import zipfile

DOC_ID = "00000000-0000-4000-8000-000000000083"
OUT = pathlib.Path(__file__).resolve().parent / "in" / "unannotated pdf.rmdoc"


def minimal_pdf() -> bytes:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << >> >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    return bytes(out)


def main() -> None:
    content = {
        "fileType": "pdf",
        "formatVersion": 1,
        "pageCount": 1,
        "tags": None,
        "pages": None,
    }
    metadata = {
        "type": "DocumentType",
        "visibleName": "unannotated pdf",
        "parent": "",
        "lastModified": "1700000000000",
        "lastOpened": "1700000000000",
        "lastOpenedPage": 0,
        "pinned": False,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{DOC_ID}.content", json.dumps(content, indent=2))
        archive.writestr(f"{DOC_ID}.metadata", json.dumps(metadata, indent=2))
        archive.writestr(f"{DOC_ID}.pdf", minimal_pdf())

    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
