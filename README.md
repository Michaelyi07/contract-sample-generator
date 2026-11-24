# contract-sample-generator

Fictional sample contract generator for a document-automation module (contract
field recognition) and its evaluation set. Batch-generates fictional
membership-service contracts (PDF) with machine-checkable ground-truth answer
files, in 4 layouts and 3 media variants (text-layer PDF / simulated scan /
simulated phone photo).

**All data is synthetic.** No real person, company, phone number or address is
used: entity names follow `示例××科技有限公司（虚构）`, signatories are
`张三（虚构）`-style placeholders, addresses live in the invented
`示例市云澜区`, and Unified Social Credit Codes are generated per
GB 32100-2015 with digits 3–8 locked to the non-existent administrative
division code `999999`, so generated codes validate checksum-wise but can
never collide with a real enterprise.

## Layouts, parameters, media

| Dimension | Values |
|---|---|
| Layout (4) | `standard_clause` 标准条款式 · `table_payment` 表格式付款 · `benefits_attachment` 附件权益清单式 · `supplement_agreement` 补充协议式 |
| Milestones | 1–4 (`--` default run schedules doc 0 of each layout = 1, doc 1 = 4) |
| Benefit items | 2–8 (default run: doc 0 = 2, doc 1 = 8) |
| Renewal clause | on / off (both appear in the default run) |
| Breach clause | 3 wording variants |
| Amount notation | 3 variants: 大写加小写 / 仅小写 / 千分位 (monetary values stored as integer cents) |
| Date notation | 4 variants: `2027年01月15日` / `2027-01-15` / `2027/01/15` / `二〇二七年一月十五日` |
| Media (3) | `text_pdf` text-layer PDF · `scan` (rotation ±3°, noise, blur, red seal overlay) · `photo` (perspective distortion, shadow gradient) |

Default run: **40 documents = 4 layouts × 10**, media and notation variants
cycled deterministically so every variant appears in every default run.

## Reproduction

```bash
pip install -r requirements.txt
# default corpus: 40 docs into samples/
python gen_fake_contracts.py --seed 42 --per-layout 10 --out samples
# additionally export the 5-image PNG spot-check set (2 scan, 2 photo, 1 text)
python gen_fake_contracts.py --seed 42 --per-layout 10 --out samples --export-png-dir spotcheck
# run the test suite (includes the two-run sha256 determinism check)
python -m pytest tests -q
```

Two runs with the same seed produce byte-identical files (PDFs and JSON):
every random choice - entity pools, USCC digits, layout parameters, media
effects - derives from a single `random.Random(seed)`; PDF metadata is fixed
via reportlab's `invariant` mode; no wall-clock time enters any artifact.

## Ground truth schema

Each document gets `<doc_id>.ground_truth.json`:

```json
{
  "doc_id": "doc_01_standard_clause",
  "layout": "standard_clause",
  "media": "text_pdf",
  "seed": 42,
  "page_count": 2,
  "page_text_extractable": true,
  "amount_notation": "upper_digits",
  "date_notation": "iso",
  "breach_variant_idx": 0,
  "fields": {
    "<field>": {"value": ..., "page": 1, "snippet": "..."}
  }
}
```

`fields` always contains exactly these **15 standard fields**:
`contract_no`, `party_a_name`, `party_a_uscc`, `party_a_signatory`,
`party_b_name`, `party_b_uscc`, `party_b_signatory`, `total_amount_cents`
(integer cents), `total_amount_display` (as printed), `currency`,
`service_start_date`, `service_end_date` (ISO canonical values; the printed
form follows the document's date notation), `milestone_count`,
`benefit_count`, `has_renewal`.

`page` (1-based) and `snippet` (verbatim fragment of the page text, cut from
the same strings that were rendered - never retyped) locate each field.
`has_renewal=false` documents have no renewal clause, so that field carries
`page: null, snippet: null`.

**Scan/photo documents are image-only PDFs (no text layer) by design** - that
is the point of simulating scan/photo media for a field-recognition eval;
their ground truth carries `page_text_extractable: false` and the snippet
auto-validation (below) applies to text-layer PDFs.

## Self-validation (mapped to acceptance criteria)

| Acceptance criterion | Where |
|---|---|
| Same seed ⇒ identical sha256 (test output) | `tests/test_determinism.py` (double run, all 80 files) |
| All USCCs in the 40 ground_truth files pass checksum, digits 3–8 = 999999 | `tests/test_uscc.py` + `contract_gen/validate.py` (independent validator, not the generator) |
| Every ground_truth snippet found in corresponding page text (text-layer auto-validation) | `tests/test_snippets.py` + `contract_gen/validate.py::check_snippets` |
| 5 sample screenshots: scan/photo effects visible, no real subject info | `spotcheck/` PNGs (exported from the delivered `samples/`) + `tests/test_no_real_subject.py` |

Real command outputs and environment versions: see `VERIFICATION.md`.

## Repository layout

```
gen_fake_contracts.py      CLI entry point
contract_gen/
  uscc.py                  GB 32100-2015 generation (reserved 999999 band)
  pools.py                 synthetic entity/benefit/clause pools
  params.py                amount/date notation variants, split logic
  templates.py             layout template texts (clause titles/labels/lines)
  layouts.py               the 4 layout block builders + DocSpec
  pdfgen.py                deterministic renderer (single drawString per line,
                           invariant PDF metadata, image-only page export)
  media.py                 scan/photo effects (seeded, deterministic)
  generator.py             orchestration + ground truth assembly
  validate.py              independent validators (tests use these)
tests/                     pytest suite (24 tests)
samples/                   delivered default corpus: 40 PDFs + 40 ground_truth.json
spotcheck/                 5 exported PNG spot-check pages
fonts/NotoSansSC-Regular.ttf  bundled open-licensed CJK font (see fonts/LICENSE.txt)
```

No interfaces from other tickets are required (【依赖】无); the generator is a
standalone CLI tool.

## Font license

`fonts/NotoSansSC-Regular.ttf` is derived from Noto Sans SC (SIL Open Font
License 1.1), converted to TrueType outlines for PDF embedding. See
`fonts/LICENSE.txt`.
