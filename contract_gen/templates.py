"""Layout templates: clause pools for the four contract layouts.

Templates are pure data; ``contract_gen.layouts`` turns them into rendered
documents. All texts are fictional boilerplate for test data generation.
"""

from __future__ import annotations

TITLE_MAIN = "会籍服务合同"
TITLE_SUPPLEMENT = "会籍服务补充协议"
TITLE_BENEFITS_APPENDIX = "附件一：会员权益清单"
TITLE_PAYMENT_TABLE = "付款计划表"

PARTY_A_LABEL = "甲方（受服务方）"
PARTY_B_LABEL = "乙方（服务方）"
PARTY_A_USCC_LABEL = "甲方统一社会信用代码"
PARTY_B_USCC_LABEL = "乙方统一社会信用代码"
PARTY_A_ADDR_LABEL = "甲方联系地址"
PARTY_B_ADDR_LABEL = "乙方联系地址"
SIGN_A_LABEL = "甲方签字代表"
SIGN_B_LABEL = "乙方签字代表"
SIGN_DATE_LABEL = "签署日期"

CLAUSE_SERVICE_TITLE = "第一条　服务内容"
CLAUSE_TERM_TITLE = "第二条　服务期限"
CLAUSE_AMOUNT_TITLE = "第三条　服务费用"
CLAUSE_PAYMENT_TITLE = "第四条　付款方式"
CLAUSE_BENEFIT_TITLE = "第五条　会员权益"
CLAUSE_RENEWAL_TITLE = "第六条　续约"
CLAUSE_BREACH_TITLE = "第七条　违约责任"
CLAUSE_OTHER_TITLE = "第八条　其他"

SERVICE_PERIOD_LINE = "服务期限自{start}起至{end}止。"
TOTAL_AMOUNT_LINE = "本合同服务费用总额为{amount}。"
PAYMENT_TABLE_HEADER = ("期次", "金额", "约定支付日期", "占比")
BENEFIT_LINE = "权益{n}：{text}"
MILESTONE_LINE = "第{n}期：{amount}，于{date}前支付，占比{ratio}%。"
SIGNATURE_PREAMBLE = "本合同一式两份，双方各执一份，自双方签字之日起生效。"
PARTY_B_INFO_TITLE = "乙方信息"
