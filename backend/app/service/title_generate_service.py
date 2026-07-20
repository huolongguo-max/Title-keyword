"""
最优标题一键生成 + 新旧权重对比服务

标题规范（京东标准）：
- 结构：核心大词+类目词 前置 → 高转化属性词 中段 → 潜力热搜词 尾部
- 字数：默认 ≤ 30 汉字（60字符），可配置
- 禁止：冲突词、重复词、无效词

可调参数集中在模块顶部，便于后续优化
"""

import re
from typing import Optional
from app.service.risk_detect_service import detect_title_risks
from app.service.word_classify_service import CONFLICT_PAIRS


# ================================================================
# 可调参数
# ================================================================

DEFAULT_MAX_LENGTH = 30          # 默认最大字数（汉字数）
MAX_LENGTH_MIN = 20              # 最小字数
MAX_LENGTH_MAX = 50              # 最大字数

# 各部分词数分配比例（按优先顺序截取）
# 前置核心词：最多 2 个
MAX_FRONT_CORE = 2
# 中段属性词：无上限（受总字数约束）
# 尾部热搜词：最多 2 个
MAX_TAIL_HOT = 2

# 拼接分隔符
WORD_SEPARATOR = " "  # 词间用空格分隔（京东标题常见写法）

# 互斥词集合（从 CONFLICT_PAIRS 展平，快速查找）
def _build_conflict_set() -> set[str]:
    """构建冲突词全集"""
    s: set[str] = set()
    for group in CONFLICT_PAIRS:
        for w in group:
            s.add(w)
    return s

CONFLICT_WORDS: set[str] = _build_conflict_set()


# ================================================================
# 工具函数
# ================================================================

def _count_chinese(text: str) -> int:
    """统计中文字符数（汉字）"""
    return len(re.findall(r'[一-鿿]', text))


def _count_total_chars(text: str) -> int:
    """统计总字符数（含英文/数字/空格）"""
    return len(text)


def _trim_to_length(text: str, max_chinese: int) -> str:
    """
    截断标题到指定汉字数以内
    从尾部逐词删除，直到满足字数要求
    """
    if _count_chinese(text) <= max_chinese:
        return text

    # 按空格分词，从尾部逐词删除
    parts = text.split(WORD_SEPARATOR)
    while parts and _count_chinese(WORD_SEPARATOR.join(parts)) > max_chinese:
        parts.pop()

    return WORD_SEPARATOR.join(parts)


def _dedup_words(words: list[str]) -> list[str]:
    """去重，保持顺序"""
    seen: set[str] = set()
    result: list[str] = []
    for w in words:
        if w not in seen:
            seen.add(w)
            result.append(w)
    return result


def _check_conflict_between(word1: str, word2: str) -> bool:
    """检查两个词是否互斥"""
    for group in CONFLICT_PAIRS:
        if word1 in group and word2 in group:
            return True
    return False


# ================================================================
# 标题生成核心算法
# ================================================================

def generate_title(
    word_pools: dict,
    original_title: Optional[str] = None,
    max_length: int = DEFAULT_MAX_LENGTH,
) -> dict:
    """
    一键生成最优标题

    Args:
        word_pools: 四词池分类结果
            {
                "core_transaction":  { keywords: [...] },
                "potential_growth":  { keywords: [...] },
                "invalid_weak":      { keywords: [...] },
                "conflict_risk":     { keywords: [...] },
            }
        original_title: 原标题（用于对比）
        max_length: 最大字数限制（汉字数），默认 30

    Returns:
        {
            "new_title": str,
            "word_detail": [...],       # 每个词的位置、来源、权重
            "compare": { ... } | null,  # 新旧对比数据
        }
    """
    # 限制 max_length 范围
    max_length = max(MAX_LENGTH_MIN, min(MAX_LENGTH_MAX, max_length))

    # ---- 提取各池数据 ----
    core_kws = word_pools.get("core_transaction", {}).get("keywords", [])
    potential_kws = word_pools.get("potential_growth", {}).get("keywords", [])
    invalid_kws = word_pools.get("invalid_weak", {}).get("keywords", [])
    conflict_kws = word_pools.get("conflict_risk", {}).get("keywords", [])

    # 无效词/冲突词的黑名单（它们的 keyword 名）
    invalid_set = {kw["keyword"] for kw in invalid_kws}
    conflict_set = {kw["keyword"] for kw in conflict_kws}

    # ---- 步骤①：提取核心大词（前 1-2 个） ----
    # 从核心成交池中按得分降序取，去掉冲突词
    core_sorted = sorted(
        [kw for kw in core_kws if kw["keyword"] not in conflict_set],
        key=lambda x: x["score"],
        reverse=True,
    )
    front_words: list[str] = []
    front_detail: list[dict] = []
    for kw in core_sorted[:MAX_FRONT_CORE]:
        front_words.append(kw["keyword"])
        front_detail.append({
            "word": kw["keyword"],
            "source_pool": "核心成交词池",
            "source_type": "前置核心词",
            "score": kw["score"],
        })

    # ---- 步骤②：提取高转化属性词（中段） ----
    # 从核心成交池中剩余词 + 优先取名为"属性词"的关键词
    used_keywords = set(front_words)
    mid_words: list[str] = []
    mid_detail: list[dict] = []

    for kw in core_sorted:
        if kw["keyword"] in used_keywords:
            continue
        if kw["keyword"] in conflict_set:
            continue
        # 跳过已选为前置的词
        mid_words.append(kw["keyword"])
        mid_detail.append({
            "word": kw["keyword"],
            "source_pool": "核心成交词池",
            "source_type": "中段属性词",
            "score": kw["score"],
        })
        used_keywords.add(kw["keyword"])

    # ---- 步骤③：提取热搜词（尾部 1-2 个） ----
    # 从潜力增长池中按曝光量降序取
    potential_sorted = sorted(
        [kw for kw in potential_kws
         if kw["keyword"] not in conflict_set and kw["keyword"] not in used_keywords],
        key=lambda x: x["impressions"],
        reverse=True,
    )
    tail_words: list[str] = []
    tail_detail: list[dict] = []
    for kw in potential_sorted[:MAX_TAIL_HOT]:
        tail_words.append(kw["keyword"])
        tail_detail.append({
            "word": kw["keyword"],
            "source_pool": "潜力增长词池",
            "source_type": "尾部热搜词",
            "impressions": kw["impressions"],
        })

    # ---- 步骤④：去重、去除冲突词 ----
    all_front = [w for w in front_words if w not in conflict_set]
    all_mid = [w for w in mid_words if w not in conflict_set]
    all_tail = [w for w in tail_words if w not in conflict_set]

    # 全局去重（避免不同段落出现相同词）
    seen_all: set[str] = set()
    dedup_front: list[str] = []
    for w in all_front:
        if w not in seen_all:
            seen_all.add(w)
            dedup_front.append(w)
    dedup_mid: list[str] = []
    for w in all_mid:
        if w not in seen_all:
            seen_all.add(w)
            dedup_mid.append(w)
    dedup_tail: list[str] = []
    for w in all_tail:
        if w not in seen_all:
            seen_all.add(w)
            dedup_tail.append(w)

    # 检测词间互斥（新标题内部不应该有冲突）
    all_candidates = dedup_front + dedup_mid + dedup_tail
    final_words: list[str] = []
    for w in all_candidates:
        has_conflict = False
        for existing in final_words:
            if _check_conflict_between(w, existing):
                has_conflict = True
                break
        if not has_conflict:
            final_words.append(w)

    # ---- 步骤⑤：拼接 + 截断 ----
    raw_title = WORD_SEPARATOR.join(final_words)
    new_title = _trim_to_length(raw_title, max_length)

    # 反向找出最终标题中包含的词（截断后可能丢失尾部词）
    final_title_words = new_title.split(WORD_SEPARATOR)

    # ---- 构建词权重明细 ----
    all_detail = front_detail + mid_detail + tail_detail
    detail_map = {d["word"]: d for d in all_detail}
    word_detail: list[dict] = []
    for w in final_title_words:
        if w in detail_map:
            word_detail.append({
                "word": w,
                "position": final_title_words.index(w),
                **detail_map[w],
            })
        else:
            word_detail.append({
                "word": w,
                "position": final_title_words.index(w),
                "source_pool": "未知",
                "source_type": "未知",
            })

    # ---- 步骤⑥：新旧对比 ----
    compare = None
    if original_title:
        compare = _compare_titles(
            original_title, new_title,
            core_kws, potential_kws, invalid_kws, conflict_kws,
        )

    return {
        "new_title": new_title,
        "chinese_count": _count_chinese(new_title),
        "total_chars": _count_total_chars(new_title),
        "word_detail": word_detail,
        "compare": compare,
    }


# ================================================================
# 新旧标题对比
# ================================================================

def _compare_titles(
    old_title: str,
    new_title: str,
    core_kws: list[dict],
    potential_kws: list[dict],
    invalid_kws: list[dict],
    conflict_kws: list[dict],
) -> dict:
    """
    对比原标题与新标题的各项指标
    """
    core_set = {kw["keyword"] for kw in core_kws}
    invalid_set = {kw["keyword"] for kw in invalid_kws}
    conflict_set = {kw["keyword"] for kw in conflict_kws}

    # --- 原标题统计 ---
    old_risk = detect_title_risks(old_title, list(core_set))
    old_core_count = sum(1 for w in core_set if w in old_title)
    old_invalid_count = sum(1 for w in invalid_set if w in old_title)
    old_conflict_count = sum(1 for w in conflict_set if w in old_title)
    old_risk_count = len(old_risk["risk_list"])
    old_score = old_risk["risk_score"]

    # --- 新标题统计 ---
    new_risk = detect_title_risks(new_title, list(core_set))
    new_core_count = sum(1 for w in core_set if w in new_title)
    new_potential_count = sum(1 for w in [kw["keyword"] for kw in potential_kws] if w in new_title)
    new_invalid_removed = old_invalid_count  # 新的不应包含无效词
    new_risk_count = len(new_risk["risk_list"])
    new_score = new_risk["risk_score"]

    # --- 权重提升比例 ---
    # 基于核心词增加 + 风险评分下降 + 无效词减少
    if old_core_count > 0:
        core_improvement = (new_core_count - old_core_count) / old_core_count * 100
    else:
        core_improvement = 100 if new_core_count > 0 else 0

    if old_score > 0:
        risk_reduction = (old_score - new_score) / old_score * 100
    else:
        risk_reduction = 0

    if old_risk_count > 0:
        risk_count_reduction = (old_risk_count - new_risk_count) / old_risk_count * 100
    else:
        risk_count_reduction = 0

    # 综合权重提升：核心词提升 40% + 风险下降 35% + 无效词清除 25%
    weight_improvement = round(
        max(0, core_improvement) * 0.4 +
        max(0, risk_reduction) * 0.35 +
        max(0, risk_count_reduction) * 0.25,
        1,
    )
    weight_improvement = min(weight_improvement, 100)

    # --- 流量提升逻辑说明 ---
    reasons: list[str] = []
    if new_core_count > old_core_count:
        reasons.append(f"核心成交词增加 {new_core_count - old_core_count} 个，精准匹配搜索流量")
    if new_score < old_score:
        reasons.append(f"风险评分下降 {old_score - new_score} 分，降低搜索降权概率")
    if old_invalid_count > 0:
        reasons.append(f"剔除 {old_invalid_count} 个无效弱词，提升搜索权重密度")
    if old_risk_count > new_risk_count:
        reasons.append(f"风险项减少 {old_risk_count - new_risk_count} 条，标题更合规")
    if new_potential_count > 0:
        reasons.append(f"新增 {new_potential_count} 个潜力增长词，拓展增量流量")
    if not reasons:
        reasons.append("新标题在结构和合规性上优于原标题")

    return {
        "original_title": {
            "title": old_title,
            "core_count": old_core_count,
            "invalid_count": old_invalid_count,
            "conflict_count": old_conflict_count,
            "risk_count": old_risk_count,
            "risk_score": old_score,
        },
        "new_title": {
            "title": new_title,
            "core_count": new_core_count,
            "potential_count": new_potential_count,
            "invalid_removed": new_invalid_removed,
            "risk_count": new_risk_count,
            "risk_score": new_score,
        },
        "weight_improvement": weight_improvement,
        "traffic_reasons": reasons,
    }
