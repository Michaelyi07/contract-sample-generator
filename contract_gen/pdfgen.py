"""Deterministic PDF rendering for contract pages.

Every line of text is emitted as a single ``drawString`` call so that
pypdfium2 text extraction reproduces the exact source string; ground-truth
snippets are cut from the same strings that are rendered (never retyped),
which is what makes AC-3 (snippet-in-page) hold mechanically.

Determinism: ``canvas(invariant=1)`` fixes PDF metadata and document ID; the
renderer itself consumes no wall-clock values. Page geometry is A4.
"""

from __future__ import annotations

import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RLTTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

PAGE_W, PAGE_H = A4
MARGIN = 56.0
USABLE_W = PAGE_W - 2 * MARGIN

_FONT_NAME = "NotoSC"
_FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts", "NotoSansSC-Regular.ttf")

STYLES = {
    "title": {"size": 16, "leading": 24, "center": True},
    "h2": {"size": 12, "leading": 20, "center": False},
    "body": {"size": 11, "leading": 17, "center": False},
    "small": {"size": 10, "leading": 15, "center": False},
}


def register_font() -> None:
    if not pdfmetrics.getRegisteredFontNames() or _FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(RLTTFont(_FONT_NAME, _FONT_PATH))


def get_font_path() -> str:
    return _FONT_PATH


class FieldRecorder:
    """Records (page, snippet) for ground-truth fields at draw time."""

    def __init__(self) -> None:
        self.records: dict[str, dict] = {}

    def record(self, key: str, snippet: str, page: int) -> None:
        self.records[key] = {"page": page, "snippet": snippet}


class Renderer:
    def __init__(self) -> None:
        register_font()
        self.buf = io.BytesIO()
        self.c = canvas.Canvas(self.buf, pagesize=A4, invariant=1)
        self.recorder = FieldRecorder()
        self.y = PAGE_H - MARGIN
        self.page_count = 1

    # ------------------------------------------------------------- internals
    def _new_page(self) -> None:
        self.c.showPage()
        self.page_count += 1
        self.y = PAGE_H - MARGIN

    def _ensure(self, leading: float) -> None:
        if self.y - leading < MARGIN:
            self._new_page()

    def _draw_plain(self, text: str, style: str) -> None:
        st = STYLES[style]
        self.c.setFont(_FONT_NAME, st["size"])
        x = (PAGE_W - pdfmetrics.stringWidth(text, _FONT_NAME, st["size"])) / 2 if st["center"] else MARGIN
        self.c.drawString(x, self.y, text)

    # ------------------------------------------------------------- blocks
    def add_text(self, text: str, style: str = "body", fields: list | None = None) -> None:
        """Draw ``text`` (wrapped). ``fields=[(key, snippet), ...]``: each snippet
        must be a substring of one physical line; the generator asserts this at
        build time so ground-truth snippets can never straddle a wrap boundary."""
        st = STYLES[style]
        size, leading = st["size"], st["leading"]
        pending = list(fields or [])
        lines = wrap_text(text, _FONT_NAME, size, USABLE_W)
        if pending and len(lines) > 1:
            # the field line must fit on one physical line by construction
            raise RuntimeError(f"field line wraps: {[k for k, _ in pending]}")
        for ln in lines:
            self._ensure(leading)
            self.y -= leading
            self._draw_plain(ln, style)
            for key, snippet in list(pending):
                if snippet in ln:
                    self.recorder.record(key, snippet, self.c.getPageNumber())
                    pending.remove((key, snippet))

    def add_space(self, h: float) -> None:
        self.y -= h

    def add_table(self, rows: list[list[str]], col_widths: list[float],
                  fields: dict | None = None, header: bool = True) -> None:
        fields = fields or {}
        row_h = 22.0
        size = 10
        x0 = MARGIN
        for r, row in enumerate(rows):
            if self.y - row_h < MARGIN:
                self._new_page()
            self.y -= row_h
            # row rule
            self.c.setLineWidth(0.5)
            self.c.line(x0, self.y + row_h - 4, x0 + sum(col_widths), self.y + row_h - 4)
            x = x0
            for cidx, cell in enumerate(row):
                self.c.setFont(_FONT_NAME, size)
                self.c.drawString(x + 4, self.y + 4, cell)
                f = fields.get((r, cidx))
                if f is not None:
                    key, snippet = f
                    if snippet in cell:
                        self.recorder.record(key, snippet, self.c.getPageNumber())
                x += col_widths[cidx]
        # bottom rule
        self.c.setLineWidth(0.5)
        self.c.line(x0, self.y - 2, x0 + sum(col_widths), self.y - 2)
        self.y -= 6

    def add_pagebreak(self) -> None:
        self._new_page()

    # ------------------------------------------------------------- output
    def build_bytes(self) -> bytes:
        self.c.showPage()
        self.c.save()
        return self.buf.getvalue()


def wrap_text(text: str, font: str, size: float, max_w: float) -> list[str]:
    words = list(text)  # CJK-aware char wrapping; keep ASCII runs together
    lines: list[str] = []
    cur = ""
    ascii_run = ""
    for ch in words:
        candidate = cur + ascii_run + ch
        if pdfmetrics.stringWidth(candidate, font, size) <= max_w:
            ascii_run += ch
            continue
        if ascii_run:
            cur += ascii_run
            ascii_run = ""
            candidate = cur + ch
            if pdfmetrics.stringWidth(candidate, font, size) <= max_w:
                ascii_run = ch
                continue
        lines.append(cur + ascii_run)
        cur = ""
        ascii_run = ch if ch != " " else ""
        if ch == " ":
            ascii_run = " "
    cur += ascii_run
    if cur:
        lines.append(cur)
    return lines or [text]


def image_to_pdf_bytes(images: list) -> bytes:
    """Wrap rasterized page images into a deterministic PDF (image-only pages,
    i.e. no text layer - by design for simulated scan / photo documents)."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, invariant=1)
    for img in images:
        iw, ih = img.size
        scale = min(PAGE_W / iw, PAGE_H / ih)
        w, h = iw * scale, ih * scale
        c.drawImage(ImageReader(img), (PAGE_W - w) / 2, (PAGE_H - h) / 2, w, h)
        c.showPage()
    c.save()
    return buf.getvalue()
