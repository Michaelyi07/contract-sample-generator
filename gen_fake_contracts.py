#!/usr/bin/env python3
"""Fictional sample contract generator (CLI).

Batch-generates fictional membership-service contracts and ground-truth
answer files, for development testing of the document-automation module and
the evaluation corpus. All data is synthetic: entity names follow
示例××科技有限公司（虚构）, USCCs use the reserved non-existent division code
999999, signatories are 张三（虚构）-style placeholders.

Examples:
  python gen_fake_contracts.py --seed 42 --per-layout 10 --out samples
  python gen_fake_contracts.py --seed 42 --per-layout 3 --out /tmp/quick
  python gen_fake_contracts.py --seed 42 --out samples --export-png-dir spotcheck
"""

from __future__ import annotations

import argparse
import sys

from contract_gen import generator
from contract_gen.layouts import LAYOUTS, MEDIA_TYPES


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):  # Windows GBK console safety
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=int, default=42,
                    help="random seed; identical seed reproduces identical bytes")
    ap.add_argument("--per-layout", type=int, default=10,
                    help="documents per layout (default 10 -> 40 docs over 4 layouts)")
    ap.add_argument("--out", default="samples", help="output directory")
    ap.add_argument("--export-png-dir", default=None,
                    help="optional: also export 5 spot-check PNG pages (1 text, 2 scan, 2 photo)")
    args = ap.parse_args(argv)

    results = generator.generate(seed=args.seed, per_layout=args.per_layout,
                                 out_dir=args.out)
    print(f"--- {len(results)} documents written to {args.out} "
          f"(seed={args.seed}, {len(LAYOUTS)} layouts x {args.per_layout}) ---")
    if args.export_png_dir:
        pngs = generator.export_spotcheck(args.out, args.export_png_dir)
        print(f"--- {len(pngs)} spot-check PNGs written to {args.export_png_dir} ---")
        for p in pngs:
            print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
