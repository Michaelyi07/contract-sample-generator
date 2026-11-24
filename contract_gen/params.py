"""Canonical amounts and dates: formatting variants + normalized values.

Monetary amounts are stored as integers in "cents" (统一技术约定).
"""

from __future__ import annotations

import datetime as _dt
import random

UPPER_DIGITS = "upper_digits"      # 大写加小写
DIGITS_ONLY = "digits_only"        # 仅小写
THOUSANDS = "thousands"            # 千分位
AMOUNT_NOTATIONS = (UPPER_DIGITS, DIGITS_ONLY, THOUSANDS)

CN_FULLDATE = "cn_fulldate"        # 2027年01月15日
ISO = "iso"                        # 2027-01-15
SLASH = "slash"                    # 2027/01/15
CN_NUMERALS = "cn_numerals"        # 二〇二七年一月十五日
DATE_NOTATIONS = (CN_FULLDATE, ISO, SLASH, CN_NUMERALS)

CN_DIGITS = "零壹贰叁肆伍陆柒捌玖"
CN_UNITS = ("", "拾", "佰", "仟")
CN_GROUPS = ("", "万", "亿", "万亿")

_DATE_CN_YEARS = "〇一二三四五六七八九"


def split_cents(rng: random.Random, total_cents: int, n: int) -> list[int]:
    """Split a whole-yuan total into n milestone amounts (multiples of 100
    yuan = 10000 cents) summing exactly to total; the last part absorbs
    rounding so milestone amounts are always exact."""
    if n <= 0:
        raise ValueError("n must be >= 1")
    base = total_cents // n // 10000 * 10000
    parts = [base] * n
    parts[-1] += total_cents - base * n
    if parts[-1] < 10000 and n > 1:  # keep every milestone >= 100 yuan
        raise ValueError("total too small to split")
    return parts


def yuan_str(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


def thousands_str(cents: int) -> str:
    s = f"{cents / 100:,.2f}"
    return s


def chinese_uppercase(cents: int) -> str:
    """壹拾贰万叁仟肆佰伍拾陆元柒角捌分 / ...元整 style."""
    if cents < 0:
        raise ValueError("negative amounts not supported")
    yuan, jiao, fen = cents // 100, cents // 10 % 10, cents % 10

    def _group4(g: int) -> str:
        s = f"{g:04d}"
        out = []
        for i, ch in enumerate(s):
            d = int(ch)
            if d:
                out.append(CN_DIGITS[d] + CN_UNITS[3 - i])
            elif out and out[-1] != "零":
                out.append("零")
        return "".join(out).rstrip("零") if out else ""

    # contract totals are kept < 1,000,000 yuan so at most one 万-group exists
    if yuan == 0:
        int_part = "零"
    else:
        g0, g1 = yuan % 10000, yuan // 10000
        parts = []
        if g1:
            parts.append(_group4(g1) + "万")
        if g0 == 0:
            pass
        elif g0 < 1000 and g1:
            parts.append("零" + _group4(g0))
        else:
            parts.append(_group4(g0))
        int_part = "".join(parts)
    out = int_part + "元"
    if jiao == 0 and fen == 0:
        out += "整"
    else:
        if jiao > 0:
            out += CN_DIGITS[jiao] + "角"
        elif fen > 0 and yuan > 0:
            out += "零"
        if fen > 0:
            out += CN_DIGITS[fen] + "分"
    return out


def format_amount(cents: int, notation: str) -> str:
    if notation == UPPER_DIGITS:
        return f"人民币{chinese_uppercase(cents)}（¥{thousands_str(cents)}）"
    if notation == DIGITS_ONLY:
        return f"¥{yuan_str(cents)}"
    if notation == THOUSANDS:
        return f"{thousands_str(cents)} 元"
    raise ValueError(f"unknown notation: {notation}")


def format_date(d: _dt.date, notation: str) -> str:
    if notation == CN_FULLDATE:
        return f"{d.year}年{d.month:02d}月{d.day:02d}日"
    if notation == ISO:
        return d.isoformat()
    if notation == SLASH:
        return f"{d.year}/{d.month:02d}/{d.day:02d}"
    if notation == CN_NUMERALS:
        y = "".join(_DATE_CN_YEARS[int(c)] for c in str(d.year))
        m = _cn_md(d.month)
        day = _cn_md(d.day)
        return f"{y}年{m}月{day}日"
    raise ValueError(f"unknown notation: {notation}")


def _cn_md(n: int) -> str:
    if n == 10:
        return "十"
    if n < 10:
        return _DATE_CN_YEARS[n]
    if n < 20:
        return "十" + _DATE_CN_YEARS[n - 10]
    tens, ones = divmod(n, 10)
    return _DATE_CN_YEARS[tens] + "十" + (_DATE_CN_YEARS[ones] if ones else "")


def random_period(rng: random.Random) -> tuple[_dt.date, _dt.date]:
    start = _dt.date(2027, 1, 1) + _dt.timedelta(days=rng.randint(0, 500))
    years = rng.choice((1, 2, 3))
    try:
        end = start.replace(year=start.year + years) - _dt.timedelta(days=1)
    except ValueError:  # Feb 29
        end = start.replace(year=start.year + years, month=2, day=28) - _dt.timedelta(days=1)
    return start, end
