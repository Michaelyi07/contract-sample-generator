"""Synthetic data pools.

Every entry is fictional. No real company name, person name, phone number or
administrative district is ever used; ``tests/test_no_real_subject.py`` enforces
this mechanically against the generated documents.
"""

from __future__ import annotations

import random

# ---------------------------------------------------------------- company names
# Middle brand tokens are invented 2-character combinations from two pools.
NAME_TOKEN_A = (
    "云川", "鼎澜", "安晟", "泓宇", "清岚", "格致", "临溪", "明枢",
    "远山", "素叶", "晨岭", "恒泽", "青野", "知行", "怀谷", "临风",
)
NAME_TOKEN_B = (
    "科技", "数联", "智创", "云维", "元启", "锐维", "新衡", "拓远",
)
COMPANY_SUFFIXES = ("科技有限公司",)  # per ticket: 示例××科技有限公司（虚构）
PARTY_B_SUFFIXES = ("商务服务有限公司",)


def company_name(rng: random.Random, suffix: str = COMPANY_SUFFIXES[0]) -> str:
    """示例××科技有限公司（虚构） format, randomly combined."""
    return f"示例{rng.choice(NAME_TOKEN_A)}{rng.choice(NAME_TOKEN_B)}{suffix}（虚构）"


def party_b_name(rng: random.Random) -> str:
    return company_name(rng, PARTY_B_SUFFIXES[0])


# ---------------------------------------------------------------- signatories
# Generic placeholder person names only, always with the （虚构） marker.
SIGNATORY_NAMES = (
    "张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十",
    "郑甲", "王乙", "冯丙", "陈丁",
)


def signatory(rng: random.Random) -> str:
    return f"{rng.choice(SIGNATORY_NAMES)}（虚构）"


# ---------------------------------------------------------------- addresses
# Fictional districts only; all addresses carry the 示例/虚拟 markers.
ADDRESS_STREETS = (
    "虚拟大道", "示例路", "创元街", "云澜路", "栖霞虚拟街", "启明示例巷",
)
ADDRESS_SUFFIX = "号"


def address(rng: random.Random) -> str:
    return f"示例市云澜区{rng.choice(ADDRESS_STREETS)}{rng.randint(1, 999)}{ADDRESS_SUFFIX}"


# ---------------------------------------------------------------- benefits
# Business membership space benefits (fictional quotas / resources).
BENEFIT_POOL = (
    ("共享会议室使用额度", ("每月8小时", "每月16小时", "每月40小时")),
    ("法务咨询时长", ("每季度2小时", "每季度5小时", "每年20小时")),
    ("行业闭门会邀请名额", ("每季度1个", "每季度2个", "每年6个")),
    ("供应链撮合对接服务", ("基础撮合", "优先撮合", "专属撮合")),
    ("人才招聘通道", ("简历筛选", "直推通道", "专场招聘")),
    ("政策申报辅导", ("基础辅导", "专项辅导", "全程代办")),
    ("媒体曝光资源", ("季度1次专访", "季度2次专栏", "年度品牌专题")),
    ("共享前台接待服务", ("工作日全时段", "工作日上午", "预约制")),
    ("差旅协议价服务", ("经济档协议价", "商务档协议价", "全档协议价")),
    ("云服务资源额度", ("每月100元额度", "每月300元额度", "每月1000元额度")),
    ("培训课程名额", ("每季度2个", "每季度5个", "每年20个")),
    ("展会摊位优先选择权", ("普通优先", "优先中位", "优先首排")),
)


def benefits(rng: random.Random, count: int) -> list[str]:
    picks = rng.sample(BENEFIT_POOL, count)
    return [f"{name}：{rng.choice(levels)}" for name, levels in picks]


# ---------------------------------------------------------------- contract no
def contract_no(rng: random.Random) -> str:
    return f"MEM-{rng.randint(2027, 2029)}-{rng.randint(1000, 9999)}"


# ---------------------------------------------------------------- clauses
BREACH_CLAUSES = (
    "任何一方违反本合同约定且在收到对方书面通知后十五日内未纠正的，违约方应向守约方支付合同总额的百分之十作为违约金。",
    "一方迟延履行主要义务超过三十日的，守约方有权解除本合同，并要求违约方赔偿由此造成的直接损失。",
    "因一方违约给对方造成损失的，违约方除赔偿损失外，还应按合同总额的百分之二十支付违约金；违约金不足以弥补损失的，守约方有权继续追偿。",
)

RENEWAL_CLAUSE = "本合同期满前三十日内，双方无异议的自动续约一年，续约期费用按当期标准执行。"
NO_RENEWAL_CLAUSE = "本合同期满后自动终止，如需续约双方另行签订书面合同。"

SERVICE_CONTENTS = (
    "乙方向甲方提供商务会籍平台会籍服务，包括场地共享、资源对接与商机流转支持。",
    "乙方向甲方提供产业资源连接平台会籍服务，包括供需撮合、活动组织与行业情报服务。",
    "乙方向甲方提供会员会籍服务，包括知识库访问、招商协作与专家咨询对接。",
)
