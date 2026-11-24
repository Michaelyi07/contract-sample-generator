"""Independent validators (test-side).

Deliberately implemented WITHOUT reusing the generator's own building blocks,
so pytest assertions are not graded by the code that produced the answers.
"""

from __future__ import annotations

import json
import os

import pypdfium2 as pdfium

USCC_CHARSET = "0123456789ABCDEFGHJKLMNPQRTUWXY"
# GB 32100-2015 table 4 weighting factors, positions 1..17
USCC_WEIGHTS = (1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28)


def uscc_is_valid(code: str) -> bool:
    """Full GB 32100-2015 checksum validation of an 18-character USCC."""
    if not isinstance(code, str) or len(code) != 18:
        return False
    if any(ch not in USCC_CHARSET for ch in code):
        return False
    total = sum(USCC_CHARSET.index(ch) * w for ch, w in zip(code[:17], USCC_WEIGHTS))
    expect = USCC_CHARSET[(31 - total % 31) % 31]
    return code[17] == expect


def uscc_reserved_band(code: str) -> bool:
    """Digits 3-8 must equal the reserved non-existent division code 999999."""
    return isinstance(code, str) and len(code) == 18 and code[2:8] == "999999"


def load_ground_truth(samples_dir: str) -> list[dict]:
    out = []
    for name in sorted(os.listdir(samples_dir)):
        if name.endswith(".ground_truth.json"):
            with open(os.path.join(samples_dir, name), encoding="utf-8") as f:
                out.append(json.load(f))
    return out


def page_texts(pdf_path: str) -> list[str]:
    doc = pdfium.PdfDocument(pdf_path)
    texts = [page.get_textpage().get_text_range() for page in doc]
    doc.close()
    return texts


def check_snippets(samples_dir: str) -> dict:
    """AC-3: every source text snippet must be found in the corresponding
    page text. Auto-validation applies to text-layer PDFs (scan/photo pages
    are image-only by design and carry page_text_extractable=false)."""
    checked_docs = 0
    checked_snippets = 0
    failures = []
    for gt in load_ground_truth(samples_dir):
        doc_id = gt["doc_id"]
        pdf_path = os.path.join(samples_dir, f"{doc_id}.pdf")
        if not os.path.exists(pdf_path):
            failures.append(f"{doc_id}: pdf missing")
            continue
        if not gt.get("page_text_extractable"):
            continue  # scan / photo: no text layer by design
        texts = page_texts(pdf_path)
        checked_docs += 1
        for key, entry in gt["fields"].items():
            snippet = entry.get("snippet")
            if snippet is None:
                continue
            page = entry["page"]
            if page is None or page < 1 or page > len(texts):
                failures.append(f"{doc_id}/{key}: bad page {page}")
                continue
            if snippet not in texts[page - 1]:
                failures.append(f"{doc_id}/{key}: snippet not found on page {page}")
            else:
                checked_snippets += 1
    return {
        "docs_checked": checked_docs,
        "snippets_checked": checked_snippets,
        "failures": failures,
    }
