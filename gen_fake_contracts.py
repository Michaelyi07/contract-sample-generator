#!/usr/bin/env python3
"""Fictional sample contract generator (CLI).

Batch-generates fictional membership-service contracts and ground-truth
answer files, for development testing of the document-automation module and
the evaluation corpus. All data is synthetic: entity names follow
示例××科技有限公司（虚构）, USCCs use the reserved non-existent division code
999999, signatories are 张三（虚构）-style placeholders.

Without parameter flags the deterministic default schedule runs
(4 layouts x per-layout docs, media/notation variants cycled). Every
controllable parameter can also be pinned explicitly; pinned runs are
reproducible too (same seed + same flags => identical bytes).

Examples:
  python gen_fake_contracts.py --seed 42 --per-layout 10 --out samples
  python gen_fake_contracts.py --seed 7 --per-layout 2 --layouts standard_clause,table_payment --media scan
  python gen_fake_contracts.py --seed 7 --per-layout 1 --milestones 3 --benefits 5 \
      --renewal on --breach-variant 1 --amount-notation upper_digits --date-notation iso
"""

from __future__ import annotations

import argparse
import sys

from contract_gen import generator
from contract_gen.layouts import LAYOUTS, MEDIA_TYPES
from contract_gen.params import AMOUNT_NOTATIONS, DATE_NOTATIONS


def _comma_list(value: str) -> list[str]:
    items = [v.strip() for v in value.split(",") if v.strip()]
    return items or LAYOUTS


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):  # Windows GBK console safety
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=42,
                    help="random seed; identical seed reproduces identical bytes")
    ap.add_argument("--per-layout", type=int, default=10,
                    help="documents per layout (default 10 -> 40 docs over 4 layouts)")
    ap.add_argument("--out", default="samples", help="output directory")
    ap.add_argument("--layouts", type=_comma_list, default=None,
                    metavar="L1[,L2...]",
                    help="subset of layouts, comma-separated; one of: " + ", ".join(LAYOUTS))
    ap.add_argument("--media", choices=MEDIA_TYPES + ("all",), default="all",
                    help="force one media type for all docs (default: deterministic cycle)")
    ap.add_argument("--milestones", type=int, choices=range(1, 5), default=None,
                    help="pin payment milestone count 1-4 (default: schedule)")
    ap.add_argument("--benefits", type=int, choices=range(2, 9), default=None,
                    help="pin benefit item count 2-8 (default: schedule)")
    ap.add_argument("--renewal", choices=("auto", "on", "off"), default="auto",
                    help="renewal clause: on/off pins it, auto uses the schedule")
    ap.add_argument("--breach-variant", choices=("auto", "0", "1", "2"), default="auto",
                    help="breach clause wording variant (default: cycle 0/1/2)")
    ap.add_argument("--amount-notation", choices=AMOUNT_NOTATIONS, default=None,
                    help="pin amount notation (default: cycle all 3)")
    ap.add_argument("--date-notation", choices=DATE_NOTATIONS, default=None,
                    help="pin date notation (default: cycle all 4)")
    ap.add_argument("--export-png-dir", default=None,
                    help="optional: also export 5 spot-check PNG pages (2 scan, 2 photo, 1 text)")
    args = ap.parse_args(argv)

    if args.layouts:
        for lay in args.layouts:
            if lay not in LAYOUTS:
                ap.error(f"--layouts: unknown layout {lay!r}; choices: {', '.join(LAYOUTS)}")
    if args.media == "all":
        media = None
    else:
        media = args.media
    overrides: dict = {}
    if args.milestones is not None:
        overrides["milestone_count"] = args.milestones
    if args.benefits is not None:
        overrides["benefit_count"] = args.benefits
    if args.renewal != "auto":
        overrides["renewal"] = args.renewal == "on"
    if args.breach_variant != "auto":
        overrides["breach_variant_idx"] = int(args.breach_variant)
    if args.amount_notation:
        overrides["amount_notation"] = args.amount_notation
    if args.date_notation:
        overrides["date_notation"] = args.date_notation

    results = generator.generate(seed=args.seed, per_layout=args.per_layout,
                                 out_dir=args.out, layouts=args.layouts,
                                 media=media, overrides=overrides or None)
    print(f"--- {len(results)} documents written to {args.out} "
          f"(seed={args.seed}, layouts={len(args.layouts) if args.layouts else len(LAYOUTS)}"
          f" x {args.per_layout}) ---")
    if args.export_png_dir:
        pngs = generator.export_spotcheck(args.out, args.export_png_dir)
        print(f"--- {len(pngs)} spot-check PNGs written to {args.export_png_dir} ---")
        for p in pngs:
            print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
