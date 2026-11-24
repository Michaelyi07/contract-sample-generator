"""Ground truth schema: exactly the 15 standard fields, valid page numbers,
non-empty snippets (except has_renewal=false where the clause is absent)."""

from contract_gen.generator import GT_FIELDS
from contract_gen.validate import load_ground_truth


def test_exactly_15_fields(samples_dir):
    gts = load_ground_truth(samples_dir)
    assert len(GT_FIELDS) == 15
    for gt in gts:
        assert set(gt["fields"].keys()) == set(GT_FIELDS), gt["doc_id"]


def test_pages_and_snippets_valid(samples_dir):
    for gt in load_ground_truth(samples_dir):
        for key, entry in gt["fields"].items():
            page = entry["page"]
            snippet = entry["snippet"]
            if key == "has_renewal" and entry["value"] is False:
                assert page is None and snippet is None
                continue
            assert isinstance(page, int) and 1 <= page <= gt["page_count"], \
                f"{gt['doc_id']}/{key}: bad page {page}"
            assert isinstance(snippet, str) and snippet, \
                f"{gt['doc_id']}/{key}: empty snippet"


def test_cents_are_integers(samples_dir):
    """统一技术约定: monetary amounts stored as integers in cents."""
    for gt in load_ground_truth(samples_dir):
        v = gt["fields"]["total_amount_cents"]["value"]
        assert isinstance(v, int) and v > 0


def test_dates_are_iso_canonical(samples_dir):
    import re
    iso = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for gt in load_ground_truth(samples_dir):
        for key in ("service_start_date", "service_end_date"):
            assert iso.match(gt["fields"][key]["value"]), gt["doc_id"]
