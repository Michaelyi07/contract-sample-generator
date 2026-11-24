"""AC-2: every USCC in the 40 ground_truth files passes GB 32100 checksum
validation and carries the reserved division code 999999 in digits 3-8.

Validators here are independent implementations (contract_gen.validate),
not the generator's own logic.
"""

from contract_gen.validate import load_ground_truth, uscc_is_valid, uscc_reserved_band


def test_40_documents_present(samples_dir):
    gts = load_ground_truth(samples_dir)
    assert len(gts) == 40


def test_all_uscc_pass_checksum_and_reserved_band(samples_dir):
    gts = load_ground_truth(samples_dir)
    assert gts, "no ground truth files found"
    checked = 0
    for gt in gts:
        for key in ("party_a_uscc", "party_b_uscc"):
            code = gt["fields"][key]["value"]
            assert uscc_reserved_band(code), f"{gt['doc_id']}/{key}: digits 3-8 != 999999: {code}"
            assert uscc_is_valid(code), f"{gt['doc_id']}/{key}: GB 32100 checksum failed: {code}"
            assert code.startswith("91"), f"{gt['doc_id']}/{key}: expected enterprise prefix 91"
            checked += 1
    assert checked == 80  # 40 docs x 2 parties
