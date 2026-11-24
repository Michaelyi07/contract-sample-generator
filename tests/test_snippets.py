"""AC-3: every source text snippet in ground_truth can be found in the
corresponding page text (text-layer PDF auto-validation)."""

import json
import os

from contract_gen.validate import check_snippets, load_ground_truth


def test_every_snippet_found_in_page_text(samples_dir):
    res = check_snippets(samples_dir)
    assert res["failures"] == [], f"snippet failures: {res['failures'][:10]}"
    assert res["docs_checked"] > 0
    assert res["snippets_checked"] >= 200


def test_docs_checked_equals_text_layer_docs(samples_dir):
    gts = load_ground_truth(samples_dir)
    n_text = sum(1 for g in gts if g["media"] == "text_pdf")
    res = check_snippets(samples_dir)
    assert res["docs_checked"] == n_text


def test_scan_photo_docs_declared_not_extractable(samples_dir):
    gts = load_ground_truth(samples_dir)
    for gt in gts:
        if gt["media"] in ("scan", "photo"):
            assert gt["page_text_extractable"] is False
        else:
            assert gt["page_text_extractable"] is True


def test_snippet_matches_canonical_value(samples_dir):
    """The snippet stored must be the printed form of the canonical value
    (for identity fields the printed string IS the value)."""
    gts = load_ground_truth(samples_dir)
    for gt in gts:
        f = gt["fields"]
        assert f["contract_no"]["snippet"] == f["contract_no"]["value"]
        assert f["party_a_uscc"]["snippet"] == f["party_a_uscc"]["value"]
        assert f["total_amount_display"]["snippet"] == f["total_amount_display"]["value"]
