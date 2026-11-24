"""Unified Social Credit Code generation per GB 32100-2015.

Generation side only. An *independent* validator lives in
``contract_gen.validate`` so tests never reuse the generator's own logic.

Digits 3-8 are locked to the non-existent administrative division code
999999 so generated codes can never collide with a real enterprise.
"""

from __future__ import annotations

import random

# GB 32100-2015 appendix A character set (values 0..30; excludes I, O, Z, S, V)
CHARSET = "0123456789ABCDEFGHJKLMNPQRTUWXY"
VALUES = {ch: i for i, ch in enumerate(CHARSET)}

# GB 32100-2015 table 4 weighting factors for positions 1..17
WEIGHTS = (1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28)

# fixed prefix: registration department 9 (market regulation) + entity type 1 (enterprise)
PREFIX = "91"
# positions 3..8 locked to the reserved / non-existent division code
RESERVED_DIVISION = "999999"

LENGTH = 18


def compute_check_char(first17: str) -> str:
    """GB 32100-2015 appendix B: C18 = 31 - MOD(sum(Ci*Wi), 31)."""
    if len(first17) != 17:
        raise ValueError("need exactly 17 characters")
    total = sum(VALUES[ch] * w for ch, w in zip(first17, WEIGHTS))
    return CHARSET[(31 - total % 31) % 31]


def generate(rng: random.Random) -> str:
    """Generate one valid 18-character USCC with digits 3-8 == 999999."""
    body = "".join(rng.choice(CHARSET) for _ in range(9))  # positions 9..17
    first17 = PREFIX + RESERVED_DIVISION + body
    return first17 + compute_check_char(first17)
