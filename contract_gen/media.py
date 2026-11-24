"""Media effects: simulated scan and simulated phone photo.

3 media types per ticket:
  text_pdf - plain text-layer PDF (no rasterization)
  scan     - rotation +/-3 deg, noise, blur, red seal overlay
  photo    - perspective distortion, shadow gradient

All randomness comes from the injected seeded ``random.Random``; no effect
uses wall-clock or unseeded state, which is required for byte-identical
re-runs (AC-1).

Scan/photo pages are rasterized and stored as image-only PDF pages: they have
no text layer by design (that is the point of simulating scan/photo media for
a field-recognition eval), so their ``ground_truth`` carries
``page_text_extractable: false`` and AC-3 auto-validation applies to
text-layer PDFs, matching the acceptance criterion's own wording.
"""

from __future__ import annotations

import io
import math
import random

import pypdfium2 as pdfium
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from .pdfgen import image_to_pdf_bytes, get_font_path

RENDER_SCALE = 1.6  # ~115 dpi rasterization of A4 pages


def _rasterize_pages(pdf_bytes: bytes) -> list[Image.Image]:
    doc = pdfium.PdfDocument(pdf_bytes)
    return [page.render(scale=RENDER_SCALE).to_pil().convert("RGB") for page in doc]


def _seal_overlay(img: Image.Image, seal_text: str, rng: random.Random) -> Image.Image:
    """Red circular seal with the party-B company name, alpha-blended."""
    w, h = img.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    cx, cy = int(w * 0.72), int(h * 0.80)
    r = int(min(w, h) * 0.10)
    red = (196, 30, 38, int(rng.randint(170, 200)))
    lw = max(2, r // 22)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=red, width=lw)
    # five-pointed star at center
    star_r = r // 4
    pts = []
    rot = rng.uniform(0, math.pi)
    for k in range(10):
        rr = star_r if k % 2 == 0 else star_r * 0.45
        a = rot - math.pi / 2 + k * math.pi / 5
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    draw.polygon(pts, fill=red)
    # company name text across the seal
    font = ImageFont.truetype(get_font_path(), r // 4)
    tx = cx - r + lw * 3
    ty = cy - r // 3
    draw.text((tx, ty), seal_text[:14], font=font, fill=red)
    alpha = rng.uniform(0.75, 0.9)
    out = img.convert("RGBA")
    out = Image.alpha_composite(out, layer)
    # re-composite against itself to soften (alpha feel)
    return Image.blend(img.convert("RGBA"), out, alpha).convert("RGB")


def _noise(img: Image.Image, rng: random.Random) -> Image.Image:
    """Deterministic gaussian-ish noise: seeded pixels at 1/4 scale, upscaled."""
    w, h = img.size
    nw, nh = max(1, w // 4), max(1, h // 4)
    px = [rng.randint(96, 160) for _ in range(nw * nh)]
    noise = Image.new("L", (nw, nh))
    noise.putdata(px)
    noise = noise.resize((w, h), Image.BILINEAR).convert("RGB")
    alpha = rng.uniform(0.06, 0.12)
    return Image.blend(img, noise, alpha)


def _rotate_scan(img: Image.Image, rng: random.Random) -> Image.Image:
    angle = rng.uniform(-3.0, 3.0)
    return img.rotate(angle, expand=True, resample=Image.BICUBIC,
                      fillcolor=(255, 255, 255))


def _perspective(img: Image.Image, rng: random.Random) -> Image.Image:
    w, h = img.size
    dx = rng.randint(w // 16, w // 7)
    dy = rng.randint(h // 16, h // 7)
    # source quad (full image) -> destination corners pulled by offsets
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    dst = [
        (rng.randint(0, dx), rng.randint(0, dy)),
        (w - rng.randint(0, dx), rng.randint(0, dy)),
        (w - rng.randint(0, dx), h - rng.randint(0, dy)),
        (rng.randint(0, dx), h - rng.randint(0, dy)),
    ]
    coeffs = _find_coeffs(dst, src)
    return img.transform((w, h), Image.PERSPECTIVE, coeffs,
                         resample=Image.BICUBIC, fillcolor=(240, 240, 240))


def _find_coeffs(dst: list, src: list) -> tuple:
    """Solve the 8-coefficient perspective transform mapping dst -> src
    (as required by PIL's PERSPECTIVE convention)."""
    matrix = []
    for (x, y), (X, Y) in zip(dst, src):
        matrix.append([X, Y, 1, 0, 0, 0, -x * X, -x * Y])
        matrix.append([0, 0, 0, X, Y, 1, -y * X, -y * Y])
    A = matrix
    b = [c for pt in dst for c in pt]
    return _gauss_solve(A, b)


def _gauss_solve(A: list, b: list) -> tuple:
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-12:
            raise ValueError("singular perspective system")
        M[col], M[piv] = M[piv], M[col]
        inv = 1.0 / M[col][col]
        for r in range(n):
            if r != col and M[r][col]:
                f = M[r][col] * inv
                for c in range(col, n + 1):
                    M[r][c] -= f * M[col][c]
    return tuple(M[i][n] / M[i][i] for i in range(n))


def _shadow(img: Image.Image, rng: random.Random) -> Image.Image:
    """Linear shadow gradient darkening one side, deterministic direction."""
    w, h = img.size
    strength = rng.uniform(0.18, 0.35)
    vertical = rng.random() < 0.5
    flip = rng.random() < 0.5
    if vertical:
        col = [int(255 * (1 - strength * i / h)) for i in range(h)]
        grad = Image.new("L", (1, h))
        grad.putdata(col)
        grad = grad.resize((w, h))
    else:
        row = [int(255 * (1 - strength * i / w)) for i in range(w)]
        grad = Image.new("L", (w, 1))
        grad.putdata(row)
        grad = grad.resize((w, h))
    if flip:
        grad = grad.transpose(Image.ROTATE_180)
    return ImageChops.multiply(img, grad.convert("RGB"))


def apply_media(pdf_bytes: bytes, media: str, rng: random.Random,
                seal_text: str) -> bytes:
    """Return the final PDF bytes for the requested media type."""
    if media == "text_pdf":
        return pdf_bytes
    pages = _rasterize_pages(pdf_bytes)
    if media == "scan":
        out = []
        for img in pages:
            img = _seal_overlay(img, seal_text, rng)
            img = _rotate_scan(img, rng)
            img = _noise(img, rng)
            img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.8, 1.6)))
            out.append(img)
    elif media == "photo":
        out = []
        for img in pages:
            img = _perspective(img, rng)
            img = _shadow(img, rng)
            out.append(img)
    else:
        raise ValueError(f"unknown media: {media}")
    return image_to_pdf_bytes(out)


def export_page_png(pdf_bytes: bytes, page_no: int) -> Image.Image:
    doc = pdfium.PdfDocument(pdf_bytes)
    return doc[page_no - 1].render(scale=1.6).to_pil().convert("RGB")
