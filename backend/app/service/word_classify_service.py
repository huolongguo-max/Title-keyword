"""
词池分类与质量得分服务
四层级自动分类 + min-max 归一化质量得分计算

可调参数集中定义在模块顶部，便于后续调优
"""

from typing import Optional
from app.schemas.common import SearchWordItem


# ================================================================
# 可调参数
# ================================================================

# 质量得分权重（三者之和应为 1.0）
WEIGHT_AMOUNT = 0.5      # 成交金额权重
WEIGHT_CLICKS = 0.3      # 点击次数权重
WEIGHT_IMPRESSIONS = 0.2 # 曝光次数权重

# 互斥词库：每个元组内的词互斥，若一个关键词同时包含元组中 ≥2 个元素则判定冲突
# 格式：(词A, 词B, ...)，支持后续扩展
CONFLICT_PAIRS: list[tuple[str, ...]] = [
    # 年份互斥
    ("2024", "2025"),
    ("2025", "2026"),
    ("2023", "2024"),
    ("2024", "2026"),
    # 规格互斥
    ("10件套", "6件套"),
    ("10件套", "8件套"),
    ("6件套", "8件套"),
    ("大号", "小号"),
    ("加大", "小号"),
    ("特大", "小号"),
    ("XL", "S"),
    ("XXL", "XS"),
    # 材质互斥
    ("纯棉", "涤纶"),
    ("真皮", "PU"),
    ("实木", "密度板"),
    # 人群互斥
    ("男", "女"),
    ("男士", "女士"),
    ("男款", "女款"),
    ("成人", "儿童"),
    # 季节互斥
    ("夏季", "冬季"),
    ("春夏", "秋冬"),
    ("薄款", "加厚"),
]

# ================================================================
# 分类结果模型（轻量 dict，不依赖 Pydantic）
# ================================================================

def _build_classified_word(
    kw: SearchWordItem,
    score: float,
    pool: str,
    pool_label: str,
    pool_tag: str,
) -> dict:
    """构建单条分类结果"""
    return {
        "keyword": kw.keyword,
        "impressions": kw.impressions,
        "clicks": kw.clicks,
        "ctr": kw.ctr,
        "cart_adds": kw.cart_adds,
        "orders": kw.orders,
        "amount": kw.amount,
        "traffic": kw.traffic,
        "score": round(score, 2),
        "pool": pool,
        "pool_label": pool_label,
        "pool_tag": pool_tag,
    }


# ================================================================
# 互斥冲突检测
# ================================================================

def _detect_conflict(keyword: str) -> bool:
    """
    检测关键词是否包含互斥冲突

    规则：关键词同时包含某个互斥组中 ≥2 个元素，则判定为冲突
    例："2024新款2025潮流" → 同时含 2024 和 2025 → 冲突
    """
    for pair in CONFLICT_PAIRS:
        hits = [w for w in pair if w in keyword]
        if len(hits) >= 2:
            return True
    return False


# ================================================================
# Min-Max 归一化
# ================================================================

def _min_max_norm(values: list[float]) -> list[float]:
    """
    Min-Max 归一化，输出映射到 [0, 100]

    边界处理：
    - 若所有值相同（min == max），全部返回 50（中间值）
    - 空列表返回空列表
    """
    if not values:
        return []
    v_min, v_max = min(values), max(values)
    if v_max == v_min:
        return [50.0] * len(values)
    return [(v - v_min) / (v_max - v_min) * 100 for v in values]


# ================================================================
# 质量得分计算
# ================================================================

def _compute_scores(keywords: list[SearchWordItem]) -> list[float]:
    """
    为每个关键词计算 0-100 分制的质量得分

    流程：
    1. 分别对成交金额、点击次数、曝光次数做 min-max 归一化
    2. 加权求和：amount * 0.5 + clicks * 0.3 + impressions * 0.2
    """
    n = len(keywords)
    if n == 0:
        return []

    amounts = [float(kw.amount) for kw in keywords]
    clicks = [float(kw.clicks) for kw in keywords]
    impressions = [float(kw.impressions) for kw in keywords]

    norm_amounts = _min_max_norm(amounts)
    norm_clicks = _min_max_norm(clicks)
    norm_impressions = _min_max_norm(impressions)

    scores = []
    for i in range(n):
        s = (
            norm_amounts[i] * WEIGHT_AMOUNT +
            norm_clicks[i] * WEIGHT_CLICKS +
            norm_impressions[i] * WEIGHT_IMPRESSIONS
        )
        scores.append(s)

    return scores


# ================================================================
# 主分类入口
# ================================================================

def classify_keywords(keywords: list[SearchWordItem]) -> dict:
    """
    对搜索词列表执行四层级分类 + 质量得分计算

    输入：上传解析后的搜索词列表
    输出：
    {
        "core_transaction":   { "name", "tag", "keywords": [...] },
        "potential_growth":   { "name", "tag", "keywords": [...] },
        "invalid_weak":       { "name", "tag", "keywords": [...] },
        "conflict_risk":      { "name", "tag", "keywords": [...] },
    }
    每个池内按质量得分降序排列
    """
    if not keywords:
        return {
            "core_transaction": _empty_pool("核心成交词池", "高权重、高转化，必须放标题前半段"),
            "potential_growth": _empty_pool("潜力增长词池", "流量稳步上涨、有点击无成交，增量流量来源"),
            "invalid_weak": _empty_pool("无效弱词池", "纯曝光僵尸词，建议全部剔除"),
            "conflict_risk": _empty_pool("冲突违规词池", "包含互斥属性词，需人工审核确认"),
        }

    # ---- 计算质量得分 ----
    scores = _compute_scores(keywords)

    # ---- 计算整体均值（潜力增长词池判定用） ----
    all_impressions = [kw.impressions for kw in keywords]
    all_clicks = [kw.clicks for kw in keywords]
    avg_impressions = sum(all_impressions) / len(all_impressions) if all_impressions else 0
    avg_clicks = sum(all_clicks) / len(all_clicks) if all_clicks else 0

    # ---- 分类 ----
    core: list[dict] = []
    potential: list[dict] = []
    invalid: list[dict] = []
    conflict: list[dict] = []

    for i, kw in enumerate(keywords):
        score = scores[i]
        is_conflict = _detect_conflict(kw.keyword)

        # 优先级：冲突 > 核心成交 > 无效弱词 > 潜力增长

        if is_conflict:
            conflict.append(_build_classified_word(
                kw, score, "conflict_risk", "冲突违规词", "包含互斥属性词，需人工审核确认"
            ))
        elif kw.orders > 0:
            # ① 核心成交词池：成交订单量 > 0
            core.append(_build_classified_word(
                kw, score, "core_transaction", "核心成交词", "高权重、高转化，必须放标题前半段"
            ))
        elif kw.impressions > 0 and kw.clicks == 0 and kw.cart_adds == 0 and kw.orders == 0:
            # ③ 无效弱词池：有曝光但零点击、零加购、零成交
            invalid.append(_build_classified_word(
                kw, score, "invalid_weak", "无效弱词", "纯曝光僵尸词，建议全部剔除"
            ))
        elif kw.orders == 0 and kw.impressions > avg_impressions and kw.clicks > avg_clicks:
            # ② 潜力增长词池：无成交 + 曝光和点击均高于均值
            potential.append(_build_classified_word(
                kw, score, "potential_growth", "潜力增长词", "流量稳步上涨、有点击无成交，增量流量来源"
            ))
        else:
            # 其他零散低曝光词 → 归入无效弱词池
            invalid.append(_build_classified_word(
                kw, score, "invalid_weak", "无效弱词", "纯曝光僵尸词，建议全部剔除"
            ))

    # ---- 各池按得分降序排列 ----
    core.sort(key=lambda x: x["score"], reverse=True)
    potential.sort(key=lambda x: x["score"], reverse=True)
    invalid.sort(key=lambda x: x["score"], reverse=True)
    conflict.sort(key=lambda x: x["score"], reverse=True)

    return {
        "core_transaction": {
            "name": "核心成交词池",
            "tag": "高权重、高转化，必须放标题前半段",
            "count": len(core),
            "keywords": core,
        },
        "potential_growth": {
            "name": "潜力增长词池",
            "tag": "流量稳步上涨、有点击无成交，增量流量来源",
            "count": len(potential),
            "keywords": potential,
        },
        "invalid_weak": {
            "name": "无效弱词池",
            "tag": "纯曝光僵尸词，建议全部剔除",
            "count": len(invalid),
            "keywords": invalid,
        },
        "conflict_risk": {
            "name": "冲突违规词池",
            "tag": "包含互斥属性词，需人工审核确认",
            "count": len(conflict),
            "keywords": conflict,
        },
    }


def _empty_pool(name: str, tag: str) -> dict:
    """构建空词池"""
    return {
        "name": name,
        "tag": tag,
        "count": 0,
        "keywords": [],
    }
