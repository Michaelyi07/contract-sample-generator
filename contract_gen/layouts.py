"""The four contract layouts (版式): block builders.

A "block" is a render instruction consumed by ``contract_gen.pdfgen.Renderer``.
Ground-truth fields are attached to the exact printed strings they annotate;
the snippet equals the printed value substring (single physical line by
construction, enforced by the renderer).

Layouts:
  1. standard_clause       标准条款式 - numbered clauses, milestones as lines
  2. table_payment         表格式付款 - payment schedule as a table
  3. benefits_attachment   附件权益清单式 - benefits moved to a final appendix page
  4. supplement_agreement  补充协议式 - compact supplement document
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field as dc_field

from . import pools, templates as T
from .params import format_amount, format_date


@dataclass
class DocSpec:
    doc_id: str
    layout: str
    media: str
    milestone_count: int
    benefit_count: int
    renewal: bool
    breach_variant_idx: int
    amount_notation: str
    date_notation: str
    contract_no: str
    party_a_name: str
    party_a_uscc: str
    party_a_signatory: str
    party_a_addr: str
    party_b_name: str
    party_b_uscc: str
    party_b_signatory: str
    party_b_addr: str
    start: _dt.date
    end: _dt.date
    total_cents: int
    milestone_amounts: list[int] = dc_field(default_factory=list)
    milestone_dates: list[_dt.date] = dc_field(default_factory=list)
    benefit_texts: list[str] = dc_field(default_factory=list)
    breach_text: str = ""
    service_text: str = ""


LAYOUT_STANDARD = "standard_clause"
LAYOUT_TABLE = "table_payment"
LAYOUT_ATTACHMENT = "benefits_attachment"
LAYOUT_SUPPLEMENT = "supplement_agreement"
LAYOUTS = (LAYOUT_STANDARD, LAYOUT_TABLE, LAYOUT_ATTACHMENT, LAYOUT_SUPPLEMENT)

MEDIA_TEXT = "text_pdf"
MEDIA_SCAN = "scan"
MEDIA_PHOTO = "photo"
MEDIA_TYPES = (MEDIA_TEXT, MEDIA_SCAN, MEDIA_PHOTO)


def _amount(spec: DocSpec, cents: int) -> str:
    return format_amount(cents, spec.amount_notation)


def _date(spec: DocSpec, d: _dt.date) -> str:
    return format_date(d, spec.date_notation)


def _party_blocks(spec: DocSpec) -> list[dict]:
    return [
        {"kind": "body", "text": f"{T.PARTY_A_LABEL}：{spec.party_a_name}",
         "fields": [("party_a_name", spec.party_a_name)]},
        {"kind": "body", "text": f"{T.PARTY_A_USCC_LABEL}：{spec.party_a_uscc}",
         "fields": [("party_a_uscc", spec.party_a_uscc)]},
        {"kind": "body", "text": f"{T.PARTY_A_ADDR_LABEL}：{spec.party_a_addr}"},
        {"kind": "body", "text": f"{T.PARTY_B_LABEL}：{spec.party_b_name}",
         "fields": [("party_b_name", spec.party_b_name)]},
        {"kind": "body", "text": f"{T.PARTY_B_USCC_LABEL}：{spec.party_b_uscc}",
         "fields": [("party_b_uscc", spec.party_b_uscc)]},
        {"kind": "body", "text": f"{T.PARTY_B_ADDR_LABEL}：{spec.party_b_addr}"},
    ]


def _term_blocks(spec: DocSpec) -> list[dict]:
    s, e = _date(spec, spec.start), _date(spec, spec.end)
    return [
        {"kind": "h2", "text": T.CLAUSE_TERM_TITLE},
        {"kind": "body", "text": T.SERVICE_PERIOD_LINE.format(start=s, end=e),
         "fields": [("service_start_date", s), ("service_end_date", e)]},
    ]


def _fee_blocks(spec: DocSpec) -> list[dict]:
    amt = _amount(spec, spec.total_cents)
    return [
        {"kind": "h2", "text": T.CLAUSE_AMOUNT_TITLE},
        {"kind": "body", "text": T.TOTAL_AMOUNT_LINE.format(amount=amt),
         "fields": [("total_amount_display", amt), ("total_amount_cents", amt)]},
        {"kind": "body", "text": "计价货币：人民币（CNY）。",
         "fields": [("currency", "CNY")]},
    ]


def _benefit_blocks(spec: DocSpec, heading: str = T.CLAUSE_BENEFIT_TITLE) -> list[dict]:
    n = spec.benefit_count
    blocks = [
        {"kind": "h2", "text": heading},
        {"kind": "body", "text": f"共{n}项权益，详见下。",
         "fields": [("benefit_count", f"共{n}项权益")]},
    ]
    blocks += [
        {"kind": "body", "text": T.BENEFIT_LINE.format(n=i + 1, text=txt)}
        for i, txt in enumerate(spec.benefit_texts)
    ]
    return blocks


def _milestone_lines(spec: DocSpec) -> list[dict]:
    total = spec.total_cents
    out = []
    for i, (cents, d) in enumerate(zip(spec.milestone_amounts, spec.milestone_dates)):
        ratio = round(cents / total * 100)
        out.append({
            "kind": "body",
            "text": T.MILESTONE_LINE.format(
                n=i + 1, amount=_amount(spec, cents), date=_date(spec, d), ratio=ratio),
        })
    return out


def _payment_summary(spec: DocSpec) -> dict:
    n = spec.milestone_count
    return {"kind": "body", "text": f"付款节点共{n}期，明细如下。",
            "fields": [("milestone_count", f"付款节点共{n}期")]}


def _payment_table(spec: DocSpec) -> list[dict]:
    total = spec.total_cents
    rows = [[T.PAYMENT_TABLE_HEADER[0], T.PAYMENT_TABLE_HEADER[1],
             T.PAYMENT_TABLE_HEADER[2], T.PAYMENT_TABLE_HEADER[3]]]
    for i, (cents, d) in enumerate(zip(spec.milestone_amounts, spec.milestone_dates)):
        rows.append([f"第{i + 1}期", _amount(spec, cents), _date(spec, d),
                     f"{round(cents / total * 100)}%"])
    return [{"kind": "table", "rows": rows,
             "col_widths": [60.0, 240.0, 130.0, 45.0]}]


def _renewal_block(spec: DocSpec) -> dict:
    if spec.renewal:
        return {"kind": "body", "text": pools.RENEWAL_CLAUSE,
                "fields": [("has_renewal", pools.RENEWAL_CLAUSE)]}
    return {"kind": "body", "text": pools.NO_RENEWAL_CLAUSE}


def _signature_blocks(spec: DocSpec) -> list[dict]:
    return [
        {"kind": "body", "text": T.SIGNATURE_PREAMBLE},
        {"kind": "body", "text": ""},
        {"kind": "body", "text": f"{T.SIGN_A_LABEL}：{spec.party_a_signatory}",
         "fields": [("party_a_signatory", spec.party_a_signatory)]},
        {"kind": "body", "text": f"{T.SIGN_B_LABEL}：{spec.party_b_signatory}",
         "fields": [("party_b_signatory", spec.party_b_signatory)]},
        {"kind": "body", "text": f"{T.SIGN_DATE_LABEL}：{_date(spec, spec.start)}"},
    ]


def _service_block(spec: DocSpec) -> list[dict]:
    return [
        {"kind": "h2", "text": T.CLAUSE_SERVICE_TITLE},
        {"kind": "body", "text": spec.service_text},
    ]


def _breach_block(spec: DocSpec) -> list[dict]:
    return [
        {"kind": "h2", "text": T.CLAUSE_BREACH_TITLE},
        {"kind": "body", "text": spec.breach_text},
    ]


def build_blocks(spec: DocSpec) -> list[dict]:
    """Return the ordered render blocks for one document."""
    head = [
        {"kind": "title", "text": T.TITLE_MAIN if spec.layout != LAYOUT_SUPPLEMENT
         else T.TITLE_SUPPLEMENT},
        {"kind": "body", "text": f"合同编号：{spec.contract_no}",
         "fields": [("contract_no", spec.contract_no)]},
        {"kind": "sp", "h": 6},
        *_party_blocks(spec),
    ]

    if spec.layout == LAYOUT_STANDARD:
        body = [
            *_service_block(spec),
            *_term_blocks(spec),
            *_fee_blocks(spec),
            {"kind": "h2", "text": T.CLAUSE_PAYMENT_TITLE},
            _payment_summary(spec),
            *_milestone_lines(spec),
            *_benefit_blocks(spec),
            {"kind": "h2", "text": T.CLAUSE_RENEWAL_TITLE},
            _renewal_block(spec),
            *_breach_block(spec),
            {"kind": "h2", "text": T.CLAUSE_OTHER_TITLE},
            {"kind": "body", "text": "本合同未尽事宜由双方协商解决，相关争议提交合同签署地有管辖权的人民法院。"},
            *_signature_blocks(spec),
        ]
    elif spec.layout == LAYOUT_TABLE:
        body = [
            *_service_block(spec),
            *_term_blocks(spec),
            *_fee_blocks(spec),
            {"kind": "h2", "text": T.CLAUSE_PAYMENT_TITLE},
            _payment_summary(spec),
            *_payment_table(spec),
            *_benefit_blocks(spec),
            {"kind": "h2", "text": T.CLAUSE_RENEWAL_TITLE},
            _renewal_block(spec),
            *_breach_block(spec),
            *_signature_blocks(spec),
        ]
    elif spec.layout == LAYOUT_ATTACHMENT:
        body = [
            *_service_block(spec),
            *_term_blocks(spec),
            *_fee_blocks(spec),
            {"kind": "h2", "text": T.CLAUSE_PAYMENT_TITLE},
            _payment_summary(spec),
            *_milestone_lines(spec),
            {"kind": "h2", "text": T.CLAUSE_RENEWAL_TITLE},
            _renewal_block(spec),
            *_breach_block(spec),
            *_signature_blocks(spec),
            {"kind": "pagebreak"},
            *_benefit_blocks(spec, heading=T.TITLE_BENEFITS_APPENDIX),
        ]
    elif spec.layout == LAYOUT_SUPPLEMENT:
        body = [
            {"kind": "body", "text": "鉴于甲方已加入乙方运营的商务会籍平台，双方就会籍服务的补充事项达成如下协议。"},
            *_term_blocks(spec),
            *_fee_blocks(spec),
            {"kind": "body", "text": "付款安排如下："},
            _payment_summary(spec),
            *_milestone_lines(spec),
            *_benefit_blocks(spec, heading="权益安排"),
            {"kind": "body", "text": "续约安排："},
            _renewal_block(spec),
            *_breach_block(spec),
            *_signature_blocks(spec),
        ]
    else:
        raise ValueError(f"unknown layout: {spec.layout}")

    return head + body
