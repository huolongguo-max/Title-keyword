"""
批量SKU优化服务
支持多文件批量处理：解析 → 分类 → 风险检测 → 标题生成 全流程
"""

import pandas as pd
import io
import os
import tempfile
from typing import Optional
from app.service.analyzer import TitleAnalyzer
from app.service.word_classify_service import classify_keywords
from app.service.title_generate_service import generate_title


# ================================================================
# 可调参数
# ================================================================

# 导出 Excel 列定义
EXPORT_COLUMNS = [
    ("SKU/文件名", "sku_name"),
    ("优化后标题", "title"),
    ("核心词数量", "core_count"),
    ("潜力词数量", "potential_count"),
    ("风险数量", "risk_count"),
    ("质量得分", "score"),
    ("总曝光量", "total_impressions"),
    ("总成交金额", "total_amount"),
]


# ================================================================
# 批量处理
# ================================================================

def process_batch_skus(files: list[tuple[str, bytes]]) -> list[dict]:
    """
    批量处理多个SKU文件

    Args:
        files: [(filename, file_bytes), ...] — 多个上传文件

    Returns:
        [
            {
                "sku_name": str,
                "title": str,
                "core_count": int,
                "potential_count": int,
                "risk_count": int,
                "score": float,
                "total_keywords": int,
                "total_impressions": int,
                "total_amount": float,
                "error": str | None,         # 单个文件失败时记录错误
                "detail": dict | None,       # 成功时的详细数据
            },
            ...
        ]
    """
    results: list[dict] = []

    for filename, content in files:
        sku_name = os.path.splitext(filename)[0]

        try:
            # 1. 写临时文件并解析
            tmp_path = f"/tmp/batch_{filename}"
            with open(tmp_path, "wb") as f:
                f.write(content)

            try:
                parse_result = TitleAnalyzer.parse_search_word_report(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            # 2. 构建 SearchWordItem 列表
            from app.schemas.common import SearchWordItem
            keywords = [SearchWordItem(**kw) for kw in parse_result["keywords"]]
            overview = parse_result["overview"]

            if not keywords:
                results.append({
                    "sku_name": sku_name,
                    "title": "",
                    "core_count": 0,
                    "potential_count": 0,
                    "risk_count": 0,
                    "score": 0,
                    "total_keywords": 0,
                    "total_impressions": overview["total_impressions"],
                    "total_amount": overview["total_amount"],
                    "error": "文件中无有效关键词数据",
                    "detail": None,
                })
                continue

            # 3. 分类
            pools = classify_keywords(keywords)

            # 4. 标题生成
            title_result = generate_title(pools, max_length=30)

            # 5. 汇总指标
            core_count = pools["core_transaction"]["count"]
            potential_count = pools["potential_growth"]["count"]

            # 平均质量得分（取核心词池）
            core_kws = pools["core_transaction"]["keywords"]
            avg_score = round(
                sum(kw["score"] for kw in core_kws) / len(core_kws), 1
            ) if core_kws else 0

            # 风险数（取冲突词池的词数）
            risk_count = pools["conflict_risk"]["count"]

            results.append({
                "sku_name": sku_name,
                "title": title_result["new_title"],
                "core_count": core_count,
                "potential_count": potential_count,
                "risk_count": risk_count,
                "score": avg_score,
                "total_keywords": overview["total_keywords"],
                "total_impressions": overview["total_impressions"],
                "total_amount": overview["total_amount"],
                "error": None,
                "detail": {
                    "pools": pools,
                    "title_detail": title_result,
                },
            })

        except ValueError as e:
            results.append({
                "sku_name": sku_name,
                "title": "",
                "core_count": 0,
                "potential_count": 0,
                "risk_count": 0,
                "score": 0,
                "total_keywords": 0,
                "total_impressions": 0,
                "total_amount": 0,
                "error": str(e),
                "detail": None,
            })
        except Exception as e:
            results.append({
                "sku_name": sku_name,
                "title": "",
                "core_count": 0,
                "potential_count": 0,
                "risk_count": 0,
                "score": 0,
                "total_keywords": 0,
                "total_impressions": 0,
                "total_amount": 0,
                "error": f"处理异常: {str(e)}",
                "detail": None,
            })

    return results


# ================================================================
# 导出 Excel
# ================================================================

def export_to_excel(results: list[dict]) -> bytes:
    """
    将批量优化结果导出为 Excel 文件（字节流）

    Args:
        results: 批量处理结果列表

    Returns:
        Excel 文件的二进制内容
    """
    rows = []
    for r in results:
        rows.append({
            "SKU/文件名": r.get("sku_name", ""),
            "优化后标题": r.get("title", ""),
            "核心词数量": r.get("core_count", 0),
            "潜力词数量": r.get("potential_count", 0),
            "风险数量": r.get("risk_count", 0),
            "质量得分": r.get("score", 0),
            "总曝光量": r.get("total_impressions", 0),
            "总成交金额": r.get("total_amount", 0),
            "错误信息": r.get("error") or "",
        })

    df = pd.DataFrame(rows)

    # 写入字节流
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="SKU优化结果")

        # 调整列宽
        worksheet = writer.sheets["SKU优化结果"]
        col_widths = {
            'A': 28,  # SKU/文件名
            'B': 55,  # 优化后标题
            'C': 12,  # 核心词数量
            'D': 12,  # 潜力词数量
            'E': 10,  # 风险数量
            'F': 10,  # 质量得分
            'G': 14,  # 总曝光量
            'H': 14,  # 总成交金额
            'I': 30,  # 错误信息
        }
        for col_letter, width in col_widths.items():
            worksheet.column_dimensions[col_letter].width = width

    output.seek(0)
    return output.getvalue()
