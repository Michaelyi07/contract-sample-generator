"""Parameter space coverage: layouts, milestone/benefit bounds, renewal toggle,
breach/amount/date variants, media types - over the default 40-document run,
plus explicit in-process boundary checks for milestone=1/4 and benefits=2/8."""

import collections
import random

from contract_gen.generator import build_spec, generate_document
from contract_gen.layouts import (LAYOUTS, MEDIA_TYPES, DocSpec)
from contract_gen.params import AMOUNT_NOTATIONS, DATE_NOTATIONS
from contract_gen.validate import load_ground_truth


def test_default_run_layout_coverage(samples_dir):
    gts = load_ground_truth(samples_dir)
    c = collections.Counter(g["layout"] for g in gts)
    assert set(c) == set(LAYOUTS)
    assert all(v == 10 for v in c.values())


def test_media_types_present(samples_dir):
    gts = load_ground_truth(samples_dir)
    medias = {g["media"] for g in gts}
    assert medias == set(MEDIA_TYPES)


def test_milestone_bounds_1_to_4(samples_dir):
    gts = load_ground_truth(samples_dir)
    vals = {g["fields"]["milestone_count"]["value"] for g in gts}
    assert min(vals) == 1 and max(vals) == 4
    assert all(1 <= v <= 4 for v in vals)


def test_benefit_bounds_2_to_8(samples_dir):
    gts = load_ground_truth(samples_dir)
    vals = {g["fields"]["benefit_count"]["value"] for g in gts}
    assert min(vals) == 2 and max(vals) == 8
    assert all(2 <= v <= 8 for v in vals)


def test_renewal_toggle_both_values(samples_dir):
    gts = load_ground_truth(samples_dir)
    vals = {g["fields"]["has_renewal"]["value"] for g in gts}
    assert vals == {True, False}


def test_breach_amount_date_variants_all_present(samples_dir):
    gts = load_ground_truth(samples_dir)
    assert {g["breach_variant_idx"] for g in gts} == {0, 1, 2}
    assert {g["amount_notation"] for g in gts} == set(AMOUNT_NOTATIONS)
    assert {g["date_notation"] for g in gts} == set(DATE_NOTATIONS)


def _make_gt(spec: DocSpec) -> dict:
    import random as _r
    pdf, gt = generate_document(spec, _r.Random(1234))  # rng for media effects
    return gt


def test_boundary_min_parameters():
    rng = random.Random(7)
    spec = build_spec("bnd_min", LAYOUTS[0], "text_pdf", rng,
                      milestone_count=1, benefit_count=2, renewal=False)
    gt = _make_gt(spec)
    assert gt["fields"]["milestone_count"]["value"] == 1
    assert gt["fields"]["benefit_count"]["value"] == 2
    assert gt["fields"]["has_renewal"]["value"] is False
    assert gt["fields"]["has_renewal"]["page"] is None


def test_boundary_max_parameters():
    rng = random.Random(8)
    spec = build_spec("bnd_max", LAYOUTS[1], "text_pdf", rng,
                      milestone_count=4, benefit_count=8, renewal=True)
    gt = _make_gt(spec)
    assert gt["fields"]["milestone_count"]["value"] == 4
    assert gt["fields"]["benefit_count"]["value"] == 8
    assert gt["fields"]["has_renewal"]["value"] is True
    assert gt["fields"]["has_renewal"]["page"] is not None
    assert len(spec.milestone_amounts) == 4
    assert sum(spec.milestone_amounts) == spec.total_cents  # amounts sum exactly
