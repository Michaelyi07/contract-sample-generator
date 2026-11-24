"""AC-4 (no real subject information), enforced mechanically:
- every entity/person string carries the （虚构） marker and generic placeholder
  person names only
- no Chinese mobile-phone number pattern anywhere in ground truth or rendered
  text-layer pages
- addresses are fictional (示例市云澜区 + invented streets), never real districts
- USCCs use the reserved non-existent division band 999999 (checked in
  test_uscc.py)
"""

import json
import os
import re

import pytest

from contract_gen import pools
from contract_gen.validate import load_ground_truth, page_texts

# Chinese mobile number pattern; digit boundaries prevent false positives
# from the reserved USCC band (e.g. 9199999984...) which embeds digit runs
MOBILE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")

# real administrative districts that must never appear in rendered documents
REAL_DISTRICTS = (
    "朝阳区", "海淀区", "浦东新区", "福田区", "南山区", "天河区",
    "西湖区", "武侯区", "鼓楼区", "越秀区",
)


def test_names_all_fictional_marker(samples_dir):
    for gt in load_ground_truth(samples_dir):
        f = gt["fields"]
        for key in ("party_a_name", "party_b_name"):
            v = f[key]["value"]
            assert v.startswith("示例") and v.endswith("（虚构）"), v
        for key in ("party_a_signatory", "party_b_signatory"):
            v = f[key]["value"]
            assert v.endswith("（虚构）"), v
            person = v[: -len("（虚构）")]
            assert person in pools.SIGNATORY_NAMES, f"non-placeholder person: {v}"


def test_no_mobile_phone_pattern_in_ground_truth(samples_dir):
    for gt in load_ground_truth(samples_dir):
        blob = json.dumps(gt, ensure_ascii=False)
        assert not MOBILE_RE.search(blob), f"mobile-like number in {gt['doc_id']}"


def test_no_mobile_or_real_district_in_rendered_text(samples_dir):
    gts = load_ground_truth(samples_dir)
    checked = 0
    for gt in gts:
        if gt["media"] != "text_pdf":
            continue
        pdf = os.path.join(samples_dir, f"{gt['doc_id']}.pdf")
        for text in page_texts(pdf):
            assert not MOBILE_RE.search(text), f"mobile-like number in {gt['doc_id']}"
            for district in REAL_DISTRICTS:
                assert district not in text, \
                    f"real district '{district}' in {gt['doc_id']}"
        checked += 1
    assert checked > 0


def test_address_pool_is_fictional():
    rng = __import__("random").Random(3)
    for _ in range(50):
        addr = pools.address(rng)
        assert addr.startswith("示例市云澜区"), addr
        street = addr[len("示例市云澜区"):].rstrip("0123456789号")
        assert street in pools.ADDRESS_STREETS, addr
