"""CLI-level controllable parameters: every order-listed parameter must be
pinnable from the command line (or generator.generate API), with pinned runs
reproducible and the pinned values actually landing in ground truth."""

import random
import subprocess
import sys

import pytest

from contract_gen.generator import generate
from contract_gen.layouts import LAYOUTS


def test_pinned_parameters_land_in_ground_truth(tmp_path):
    out = str(tmp_path / "pinned")
    results = generate(seed=7, per_layout=2, out_dir=out, verbose=False,
                       overrides={"milestone_count": 3, "benefit_count": 5,
                                  "renewal": True, "breach_variant_idx": 1,
                                  "amount_notation": "upper_digits",
                                  "date_notation": "iso"})
    import json
    import os
    for r in results:
        gt = json.load(open(r["ground_truth"], encoding="utf-8"))
        assert gt["fields"]["milestone_count"]["value"] == 3
        assert gt["fields"]["benefit_count"]["value"] == 5
        assert gt["fields"]["has_renewal"]["value"] is True
        assert gt["amount_notation"] == "upper_digits"
        assert gt["date_notation"] == "iso"
        assert gt["breach_variant_idx"] == 1


def test_layout_subset_and_forced_media(tmp_path):
    out = str(tmp_path / "subset")
    results = generate(seed=7, per_layout=2, out_dir=out, verbose=False,
                       layouts=["standard_clause", "supplement_agreement"],
                       media="scan")
    assert len(results) == 4
    for r in results:
        doc_id = r["doc_id"]
        assert doc_id.endswith(("standard_clause", "supplement_agreement"))
        import json
        gt = json.load(open(r["ground_truth"], encoding="utf-8"))
        assert gt["media"] == "scan"
        assert gt["page_text_extractable"] is False


def test_pinned_run_is_reproducible(tmp_path):
    import hashlib
    import os

    def run(seed, out):
        generate(seed=seed, per_layout=1, out_dir=out, verbose=False,
                 overrides={"milestone_count": 2, "benefit_count": 3,
                            "renewal": False, "amount_notation": "thousands",
                            "date_notation": "cn_numerals"})
        return {f: hashlib.sha256(open(os.path.join(out, f), "rb").read()).hexdigest()
                for f in sorted(os.listdir(out))}

    a = run(9, str(tmp_path / "a"))
    b = run(9, str(tmp_path / "b"))
    assert a == b


def test_cli_help_lists_all_parameters():
    cli = subprocess.run(
        [sys.executable, "gen_fake_contracts.py", "--help"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=None,
    )
    assert cli.returncode == 0
    for flag in ("--seed", "--per-layout", "--layouts", "--media",
                 "--milestones", "--benefits", "--renewal",
                 "--breach-variant", "--amount-notation", "--date-notation"):
        assert flag in cli.stdout
