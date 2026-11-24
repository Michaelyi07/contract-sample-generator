"""Batch generation: parameters -> fictional contracts + ground truth.

One seeded ``random.Random`` instance drives every random choice (entity
pools, USCC digits, layout parameters, media effects), so the same seed
reproduces byte-identical outputs (AC-1).
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import random

from . import layouts as L
from . import media as M
from . import pools, templates as T
from .params import (AMOUNT_NOTATIONS, DATE_NOTATIONS, random_period, split_cents)
from .pdfgen import Renderer
from .uscc import generate as uscc_generate

GT_FIELDS = (
    "contract_no", "party_a_name", "party_a_uscc", "party_a_signatory",
    "party_b_name", "party_b_uscc", "party_b_signatory",
    "total_amount_cents", "total_amount_display", "currency",
    "service_start_date", "service_end_date",
    "milestone_count", "benefit_count", "has_renewal",
)


def build_spec(doc_id: str, layout: str, media: str, rng: random.Random,
               milestone_count: int | None = None,
               benefit_count: int | None = None,
               renewal: bool | None = None,
               breach_variant_idx: int | None = None,
               amount_notation: str | None = None,
               date_notation: str | None = None) -> L.DocSpec:
    party_a_name = pools.company_name(rng)
    party_b_name = pools.party_b_name(rng)
    while party_b_name == party_a_name:  # deterministic redraw: 甲方 != 乙方
        party_b_name = pools.party_b_name(rng)
    start, end = random_period(rng)
    if milestone_count is None:
        milestone_count = rng.randint(1, 4)
    if benefit_count is None:
        benefit_count = rng.randint(2, 8)
    if renewal is None:
        renewal = rng.random() < 0.5
    if breach_variant_idx is None:
        breach_variant_idx = rng.randrange(len(pools.BREACH_CLAUSES))
    if amount_notation is None:
        amount_notation = rng.choice(AMOUNT_NOTATIONS)
    if date_notation is None:
        date_notation = rng.choice(DATE_NOTATIONS)

    total_cents = rng.randint(600, 9900) * 10000  # 60,000.00 - 990,000.00 CNY, whole yuan
    milestone_amounts = split_cents(rng, total_cents, milestone_count)
    span = (end - start).days
    milestone_dates = []
    for i in range(milestone_count):
        d = start + _dt.timedelta(days=span * i // milestone_count + rng.randint(0, 14))
        milestone_dates.append(min(d, end))

    return L.DocSpec(
        doc_id=doc_id, layout=layout, media=media,
        milestone_count=milestone_count, benefit_count=benefit_count,
        renewal=renewal, breach_variant_idx=breach_variant_idx,
        amount_notation=amount_notation, date_notation=date_notation,
        contract_no=pools.contract_no(rng),
        party_a_name=party_a_name,
        party_a_uscc=uscc_generate(rng),
        party_a_signatory=pools.signatory(rng),
        party_a_addr=pools.address(rng),
        party_b_name=party_b_name,
        party_b_uscc=uscc_generate(rng),
        party_b_signatory=pools.signatory(rng),
        party_b_addr=pools.address(rng),
        start=start, end=end, total_cents=total_cents,
        milestone_amounts=milestone_amounts, milestone_dates=milestone_dates,
        benefit_texts=pools.benefits(rng, benefit_count),
        breach_text=pools.BREACH_CLAUSES[breach_variant_idx],
        service_text=rng.choice(pools.SERVICE_CONTENTS),
    )


def _render_blocks(spec: L.DocSpec) -> Renderer:
    r = Renderer()
    for blk in L.build_blocks(spec):
        kind = blk["kind"]
        if kind == "pagebreak":
            r.add_pagebreak()
        elif kind == "sp":
            r.add_space(blk["h"])
        elif kind == "table":
            r.add_table(blk["rows"], blk["col_widths"])
        else:
            r.add_text(blk["text"], style=kind, fields=blk.get("fields"))
    return r


def _ground_truth(spec: L.DocSpec, r: Renderer) -> dict:
    records = r.recorder.records
    from .params import format_amount
    amt = format_amount(spec.total_cents, spec.amount_notation)
    values = {
        "contract_no": spec.contract_no,
        "party_a_name": spec.party_a_name,
        "party_a_uscc": spec.party_a_uscc,
        "party_a_signatory": spec.party_a_signatory,
        "party_b_name": spec.party_b_name,
        "party_b_uscc": spec.party_b_uscc,
        "party_b_signatory": spec.party_b_signatory,
        "total_amount_cents": spec.total_cents,
        "total_amount_display": amt,
        "currency": "CNY",
        "service_start_date": spec.start.isoformat(),
        "service_end_date": spec.end.isoformat(),
        "milestone_count": spec.milestone_count,
        "benefit_count": spec.benefit_count,
        "has_renewal": spec.renewal,
    }
    fields = {}
    for key in GT_FIELDS:
        rec = records.get(key)
        page = rec["page"] if rec else None
        snippet = rec["snippet"] if rec else None
        if key != "has_renewal" and (page is None or not snippet):
            raise RuntimeError(f"field {key} never rendered in {spec.doc_id}")
        if key == "has_renewal" and spec.renewal and rec is None:
            raise RuntimeError(f"has_renewal clause missing in {spec.doc_id}")
        fields[key] = {"value": values[key], "page": page, "snippet": snippet}
    return {
        "doc_id": spec.doc_id,
        "layout": spec.layout,
        "media": spec.media,
        "page_count": r.page_count,
        "page_text_extractable": spec.media == L.MEDIA_TEXT,
        "breach_variant_idx": spec.breach_variant_idx,
        "amount_notation": spec.amount_notation,
        "date_notation": spec.date_notation,
        "fields": fields,
    }


def generate_document(spec: L.DocSpec, rng: random.Random) -> tuple[bytes, dict]:
    """Render one document -> (final pdf bytes, ground truth dict)."""
    r = _render_blocks(spec)
    gt = _ground_truth(spec, r)
    pdf_bytes = r.build_bytes()
    pdf_bytes = M.apply_media(pdf_bytes, spec.media, rng, seal_text=spec.party_b_name)
    return pdf_bytes, gt


def default_specs(seed: int, per_layout: int, layouts: list[str] | None = None,
                  media: str | None = None,
                  overrides: dict | None = None) -> tuple[list[L.DocSpec], random.Random]:
    """Default run: 4 layouts x per_layout docs.

    Deterministic parameter schedule (no RNG needed for coverage):
      - doc 0 of each layout: milestones=1, benefits=2, renewal=False
      - doc 1 of each layout: milestones=4, benefits=8, renewal=True
      - docs 2..: rng-driven
      - amount / date / breach variants and media cycle by doc index, so every
        variant appears in every default run.

    ``layouts`` restricts the layout list; ``media`` forces one media type for
    every document; ``overrides`` pins any of the controllable parameters
    (milestone_count, benefit_count, renewal, breach_variant_idx,
    amount_notation, date_notation) to a fixed value for all documents -
    these are the CLI-exposed parameters.
    """
    overrides = overrides or {}
    rng = random.Random(seed)
    specs = []
    idx = 0
    for layout in (layouts or L.LAYOUTS):
        for j in range(per_layout):
            idx += 1
            m = media or L.MEDIA_TYPES[j % len(L.MEDIA_TYPES)]
            if j == 0:
                mc, bc, rn = 1, 2, False
            elif j == 1:
                mc, bc, rn = 4, 8, True
            else:
                mc = rng.randint(1, 4)
                bc = rng.randint(2, 8)
                rn = rng.random() < 0.5
            spec = build_spec(
                doc_id=f"doc_{idx:02d}_{layout}",
                layout=layout, media=m, rng=rng,
                milestone_count=overrides.get("milestone_count", mc),
                benefit_count=overrides.get("benefit_count", bc),
                renewal=overrides.get("renewal", rn),
                breach_variant_idx=overrides.get("breach_variant_idx", j % 3),
                amount_notation=overrides.get("amount_notation",
                                              AMOUNT_NOTATIONS[j % 3]),
                date_notation=overrides.get("date_notation",
                                            DATE_NOTATIONS[j % 4]),
            )
            specs.append(spec)
    return specs, rng


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: str, obj: dict) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def generate(seed: int = 42, per_layout: int = 10, out_dir: str = "samples",
             layouts: list[str] | None = None, media: str | None = None,
             overrides: dict | None = None, verbose: bool = True) -> list[dict]:
    """Generate the corpus into ``out_dir``; returns per-doc results."""
    os.makedirs(out_dir, exist_ok=True)
    specs, rng = default_specs(seed, per_layout, layouts=layouts, media=media,
                               overrides=overrides)
    results = []
    for spec in specs:
        pdf_bytes, gt = generate_document(spec, rng)
        base = spec.doc_id
        pdf_path = os.path.join(out_dir, f"{base}.pdf")
        gt_path = os.path.join(out_dir, f"{base}.ground_truth.json")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        gt["seed"] = seed
        write_json(gt_path, gt)
        results.append({
            "doc_id": spec.doc_id, "pdf": pdf_path, "ground_truth": gt_path,
            "sha256_pdf": _sha256(pdf_bytes),
            "sha256_gt": _sha256(open(gt_path, "rb").read()),
        })
        if verbose:
            print(f"generated {spec.doc_id} media={spec.media} pages={gt['page_count']}")
    return results


def export_spotcheck(samples_dir: str, png_dir: str) -> list[str]:
    """Export 5 PNG pages for visual spot-check: 1 text, 2 scan, 2 photo."""
    import pypdfium2 as pdfium

    os.makedirs(png_dir, exist_ok=True)
    gts = sorted(
        (os.path.join(samples_dir, f) for f in os.listdir(samples_dir)
         if f.endswith(".ground_truth.json")),
    )
    picked: dict[str, list[str]] = {L.MEDIA_TEXT: [], L.MEDIA_SCAN: [], L.MEDIA_PHOTO: []}
    for gt_path in gts:
        with open(gt_path, encoding="utf-8") as f:
            media = json.load(f)["media"]
        if media not in picked:
            picked[media] = []
        picked[media].append(gt_path)
    files = []
    plan = [L.MEDIA_SCAN, L.MEDIA_SCAN, L.MEDIA_PHOTO, L.MEDIA_PHOTO, L.MEDIA_TEXT]
    for media in plan:
        if not picked[media]:
            # small runs may lack a media type; fall back to the largest bucket
            media = max(picked, key=lambda m: len(picked[m]))
        gt_path = picked[media].pop(0)
        doc_id = os.path.basename(gt_path).replace(".ground_truth.json", "")
        pdf_path = os.path.join(samples_dir, f"{doc_id}.pdf")
        png = M.export_page_png(open(pdf_path, "rb").read(), page_no=1)
        out = os.path.join(png_dir, f"{doc_id}_page1.png")
        png.save(out)
        files.append(out)
    return files
