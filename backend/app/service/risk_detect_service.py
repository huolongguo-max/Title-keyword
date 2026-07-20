"""
标题六大降权风险自动检测服务
纯离线规则引擎，所有词库均为可配置常量，便于后续扩充

检测规则：
① 属性冲突   — 互斥属性词组同时出现
② 年份冲突   — 正则匹配多个不同年份
③ 规格冲突   — 多个不同规格数值同时出现
④ 语义重复   — 同义词组内多词堆砌
⑤ 关键词堆砌 — 同一关键词重复 ≥2 次
⑥ 无意义垃圾词 — 超长长尾/语气助词/纯符号
"""

import re
from typing import Optional


# ================================================================
# 可配置常量 — 互斥属性词组
# 每组内的词互斥，标题中同时出现 ≥2 个即判定冲突
# ================================================================

CONFLICT_ATTRIBUTE_GROUPS: list[tuple[str, ...]] = [
    # 版本 / 档次
    ("标准版", "尊享版"),
    ("基础版", "高级版"),
    ("普通款", "旗舰款"),
    ("标配", "高配"),
    ("入门", "专业"),
    ("低配", "顶配"),
    ("经济型", "豪华型"),

    # 连接方式
    ("有线", "无线"),
    ("蓝牙", "有线"),
    ("WiFi版", "4G版"),
    ("插电", "充电"),

    # 数量 / 头部
    ("单头", "双头"),
    ("单个", "两个"),
    ("单只", "两只"),

    # 适用场景
    ("家用", "商用"),
    ("室内", "室外"),
    ("办公室", "户外"),

    # 材质互斥
    ("塑料", "金属"),
    ("玻璃", "塑料"),
    ("实木", "人造板"),
    ("真皮", "PU皮"),
    ("纯棉", "化纤"),

    # 形态
    ("折叠", "不可折叠"),
    ("便携", "固定"),
    ("迷你", "大型"),
    ("超薄", "加厚"),

    # 颜色对立
    ("黑色", "白色"),
]

# ================================================================
# 可配置常量 — 语义同义词组
# 每组内的词为同义/近义词，同时出现 ≥2 个即判定堆砌
# ================================================================

SYNONYM_GROUPS: list[tuple[str, ...]] = [
    ("礼盒", "套装", "礼赠", "礼包", "礼品"),
    ("包邮", "免运费", "快递包邮", "全国包邮"),
    ("新款", "新品", "最新款", "新上市", "当季新品"),
    ("正品", "正版", "官方正品", "行货"),
    ("促销", "打折", "特价", "优惠", "让利"),
    ("热销", "热卖", "畅销", "爆款", "爆卖"),
    ("大容量", "高容量", "巨量", "海量"),
    ("高清", "超清", "极清", "高清晰"),
    ("防水", "防潮", "抗水"),
    ("全新", "二手", "翻新"),
    ("纯手工", "手工制作", "人工制作"),
    ("下单", "购买", "选购", "抢购"),
]

# ================================================================
# 可配置常量 — 无意义垃圾词模式
# ================================================================

# 语气助词 / 无意义填充词
FILLER_WORDS = [
    "哦", "呢", "吧", "啦", "呀", "嘛", "哈", "哟", "哎",
    "真", "很", "非常", "特别", "超级", "极其", "确实",
    "赶紧", "立刻", "马上", "错过", "后悔",
    "推荐", "必备", "神器",
]

# 纯符号/乱码正则
JUNK_PATTERNS = [
    r"[★☆✿❀✿✤✧✦]{3,}",          # 连续特殊符号 ≥3
    r"[\.\-\_\=\+]{5,}",            # 连续标点 ≥5
    r"[\d]+[^\w\s]{2,}[\d]+",       # 数字+符号+数字 乱码
    r"[ａ-ｚＡ-Ｚ]{3,}",            # 全角英文字母 ≥3
]

# 超长无意义长尾关键词（≥8个中文字符，且含 ≥3 个品类/属性堆叠）
LONG_TAIL_FILLER_RE = re.compile(
    r'[一-鿿]{8,}'  # 8+ consecutive Chinese chars — checked in context
)


# ================================================================
# 风险等级常量
# ================================================================

RISK_HIGH = "high"
RISK_MEDIUM = "medium"
RISK_LOW = "low"

RISK_LEVEL_MAP = {
    RISK_HIGH: "高风险",
    RISK_MEDIUM: "中风险",
    RISK_LOW: "低风险",
}

# 各风险类型的默认等级
RULE_RISK_LEVEL = {
    "属性冲突":   RISK_HIGH,
    "年份冲突":   RISK_MEDIUM,
    "规格冲突":   RISK_MEDIUM,
    "语义重复":   RISK_LOW,
    "关键词堆砌": RISK_LOW,
    "无意义垃圾词": RISK_MEDIUM,
}


# ================================================================
# 规则 ① — 属性冲突
# ================================================================

def _detect_attribute_conflict(title: str) -> list[dict]:
    """检测标题中的互斥属性词组冲突"""
    risks = []
    for group in CONFLICT_ATTRIBUTE_GROUPS:
        hits = [w for w in group if w in title]
        if len(hits) >= 2:
            # 找到标题中每个命中词的位置
            positions = []
            for w in hits:
                idx = title.find(w)
                if idx >= 0:
                    positions.append({"word": w, "start": idx, "end": idx + len(w)})

            risks.append({
                "type": "属性冲突",
                "risk_level": RULE_RISK_LEVEL["属性冲突"],
                "content": "、".join(hits),
                "positions": positions,
                "suggestion": f"标题中同时包含互斥属性词「{'」「'.join(hits)}」，"
                              f"建议仅保留其中一个，避免属性矛盾影响搜索匹配",
            })
    return risks


# ================================================================
# 规则 ② — 年份冲突
# ================================================================

# 匹配 4 位年份数字（前后非数字即可，适配中文无空格场景）
YEAR_RE = re.compile(r'(?<!\d)(19\d{2}|20\d{2})(?!\d)')

def _detect_year_conflict(title: str) -> list[dict]:
    """检测标题中多个不同年份的冲突"""
    years = YEAR_RE.findall(title)
    unique_years = list(set(years))
    if len(unique_years) < 2:
        return []

    positions = []
    for y in unique_years:
        idx = title.find(y)
        if idx >= 0:
            positions.append({"word": y, "start": idx, "end": idx + len(y)})

    return [{
        "type": "年份冲突",
        "risk_level": RULE_RISK_LEVEL["年份冲突"],
        "content": "、".join(unique_years),
        "positions": positions,
        "suggestion": f"标题中同时出现 {len(unique_years)} 个不同年份（{'、'.join(unique_years)}），"
                      f"建议仅保留一个年份，否则搜索系统可能判定为过期/混乱商品",
    }]


# ================================================================
# 规则 ③ — 规格冲突
# ================================================================

SPEC_PATTERNS = [
    (r'(\d+)\s*件套', '件套'),
    (r'(\d+)\s*ml', 'ml'),
    (r'(\d+)\s*ML', 'ml'),
    (r'(\d+)\s*g\b', 'g'),
    (r'(\d+)\s*G\b', 'g'),
    (r'(\d+)\s*寸', '寸'),
    (r'(\d+)\s*英寸', '英寸'),
    (r'(\d+)\s*cm', 'cm'),
    (r'(\d+)\s*CM', 'cm'),
    (r'(\d+)\s*mm', 'mm'),
    (r'(\d+)\s*L\b', 'L'),
    (r'(\d+)\s*斤', '斤'),
    (r'(\d+)\s*kg', 'kg'),
    (r'(\d+)\s*KG', 'kg'),
    (r'(\d+)\s*只装', '只装'),
    (r'(\d+)\s*个装', '个装'),
    (r'(\d+)\s*瓶装', '瓶装'),
]

def _detect_spec_conflict(title: str) -> list[dict]:
    """检测标题中多个不同规格数值的冲突"""
    spec_hits: dict[str, list[dict]] = {}  # unit_type -> [{value, start, end}]

    for pattern, unit in SPEC_PATTERNS:
        for m in re.finditer(pattern, title):
            value = m.group(1)
            if unit not in spec_hits:
                spec_hits[unit] = []
            spec_hits[unit].append({
                "word": f"{value}{unit}",
                "value": int(value),
                "start": m.start(),
                "end": m.end(),
            })

    risks = []
    for unit, hits in spec_hits.items():
        unique_values = set(h["value"] for h in hits)
        if len(unique_values) >= 2:
            values_str = "、".join(f"{v}{unit}" for v in sorted(unique_values))
            position_entries = [{"word": h["word"], "start": h["start"], "end": h["end"]} for h in hits]
            risks.append({
                "type": "规格冲突",
                "risk_level": RULE_RISK_LEVEL["规格冲突"],
                "content": values_str,
                "positions": position_entries,
                "suggestion": f"标题中同时出现 {len(unique_values)} 个不同的{unit}规格（{values_str}），"
                              f"建议明确唯一规格，避免消费者困惑",
            })
    return risks


# ================================================================
# 规则 ④ — 语义重复（同义词堆砌）
# ================================================================

def _detect_semantic_duplicate(title: str) -> list[dict]:
    """检测标题中的同义/近义词堆砌"""
    risks = []
    for group in SYNONYM_GROUPS:
        hits = [w for w in group if w in title]
        if len(hits) >= 2:
            positions = []
            for w in hits:
                idx = title.find(w)
                if idx >= 0:
                    positions.append({"word": w, "start": idx, "end": idx + len(w)})
            risks.append({
                "type": "语义重复",
                "risk_level": RULE_RISK_LEVEL["语义重复"],
                "content": "、".join(hits),
                "positions": positions,
                "suggestion": f"「{'」「'.join(hits)}」语义重复堆砌，"
                              f"建议仅保留一个核心词，精简标题提升阅读体验",
            })
    return risks


# ================================================================
# 规则 ⑤ — 关键词堆砌
# ================================================================

def _detect_keyword_stuffing(title: str, word_list: list[str]) -> list[dict]:
    """检测同一关键词在标题中重复出现 ≥2 次"""
    risks = []
    for kw in word_list:
        if len(kw) < 2:
            continue
        count = title.count(kw)
        if count >= 2:
            # 找到所有出现位置
            positions = []
            start = 0
            while True:
                idx = title.find(kw, start)
                if idx == -1:
                    break
                positions.append({"word": kw, "start": idx, "end": idx + len(kw)})
                start = idx + 1

            risks.append({
                "type": "关键词堆砌",
                "risk_level": RULE_RISK_LEVEL["关键词堆砌"],
                "content": kw,
                "positions": positions,
                "suggestion": f"关键词「{kw}」在标题中重复出现 {count} 次，"
                              f"堆砌可能导致搜索降权，建议仅出现 1 次",
            })
    return risks


# ================================================================
# 规则 ⑥ — 无意义垃圾词
# ================================================================

def _detect_junk_words(title: str) -> list[dict]:
    """检测无意义垃圾词、语气助词、纯符号"""
    risks = []

    # 6a. 语气助词/填充词
    filler_hits = []
    for w in FILLER_WORDS:
        idx = title.find(w)
        if idx >= 0:
            filler_hits.append({"word": w, "start": idx, "end": idx + len(w)})

    if len(filler_hits) >= 2:
        words = "、".join(h["word"] for h in filler_hits)
        risks.append({
            "type": "无意义垃圾词",
            "risk_level": RISK_LOW,
            "content": words,
            "positions": filler_hits,
            "suggestion": f"标题中包含「{words}」等无转化价值的填充词，"
                          f"建议替换为具体属性/卖点词",
        })

    # 6b. 纯符号/乱码
    for pattern in JUNK_PATTERNS:
        for m in re.finditer(pattern, title):
            risks.append({
                "type": "无意义垃圾词",
                "risk_level": RISK_MEDIUM,
                "content": m.group(),
                "positions": [{"word": m.group(), "start": m.start(), "end": m.end()}],
                "suggestion": f"标题中包含无意义符号/乱码「{m.group()}」，"
                              f"建议删除以保持标题干净",
            })

    # 6c. 超长无意义长尾（≥15个连续中文字符）
    long_tail = re.findall(r'[一-鿿]{15,}', title)
    for lt in long_tail:
        idx = title.find(lt)
        risks.append({
            "type": "无意义垃圾词",
            "risk_level": RISK_MEDIUM,
            "content": lt[:20] + ("..." if len(lt) > 20 else ""),
            "positions": [{"word": lt, "start": idx, "end": idx + len(lt)}],
            "suggestion": f"标题中包含超长连续文本（{len(lt)}字），"
                          f"疑似无转化长尾堆砌，建议精简为关键卖点词",
        })

    return risks


# ================================================================
# 主检测入口
# ================================================================

def detect_title_risks(title: str, word_list: Optional[list[str]] = None) -> dict:
    """
    对标题执行六大降权风险检测

    Args:
        title: 待检测的商品标题
        word_list: 关键词列表（用于规则⑤关键词堆砌检测），可选

    Returns:
        {
            "risk_list": [...],
            "risk_score": int,      # 整体风险评分 0-100（越高越危险）
            "high_count": int,
            "medium_count": int,
            "low_count": int,
        }
    """
    if not title or not title.strip():
        return {
            "risk_list": [],
            "risk_score": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
        }

    title = title.strip()
    word_list = word_list or []

    # 按顺序执行六大规则
    all_risks: list[dict] = []
    all_risks.extend(_detect_attribute_conflict(title))
    all_risks.extend(_detect_year_conflict(title))
    all_risks.extend(_detect_spec_conflict(title))
    all_risks.extend(_detect_semantic_duplicate(title))
    all_risks.extend(_detect_keyword_stuffing(title, word_list))
    all_risks.extend(_detect_junk_words(title))

    # 去重：同一类型 + 同一内容 只保留一条
    seen = set()
    deduped: list[dict] = []
    for r in all_risks:
        key = (r["type"], r["content"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    # 统计各等级数量
    high_count = sum(1 for r in deduped if r["risk_level"] == RISK_HIGH)
    medium_count = sum(1 for r in deduped if r["risk_level"] == RISK_MEDIUM)
    low_count = sum(1 for r in deduped if r["risk_level"] == RISK_LOW)

    # 风险评分计算：high=20分, medium=10分, low=3分，上限100
    raw_score = high_count * 20 + medium_count * 10 + low_count * 3
    risk_score = min(raw_score, 100)

    return {
        "risk_list": deduped,
        "risk_score": risk_score,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
    }
