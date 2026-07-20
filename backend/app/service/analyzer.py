"""
业务逻辑层 - 标题关键词分析服务
负责文件解析、关键词提取、风险检测、标题生成与批量优化等核心功能
"""

import pandas as pd
import numpy as np
from typing import Optional
from app.core.config import SEARCH_WORD_REQUIRED_FIELDS, SEARCH_WORD_NUMERIC_FIELDS


class TitleAnalyzer:
    """标题关键词分析器（离线处理）"""

    # ================================================================
    # 通用文件解析
    # ================================================================

    @staticmethod
    def parse_file(file_path: str) -> dict:
        """
        解析上传的文件（Excel/CSV）— 通用解析
        返回解析后的数据结构
        """
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path, engine='openpyxl')

            return {
                "row_count": len(df),
                "columns": df.columns.tolist(),
                "preview": df.head(10).to_dict(orient="records"),
            }
        except Exception as e:
            raise ValueError(f"文件解析失败: {str(e)}")

    # ================================================================
    # 京东商智搜索词报表解析
    # ================================================================

    @staticmethod
    def parse_search_word_report(file_path: str) -> dict:
        """
        解析京东商智搜索词报表（xlsx/xls）

        处理流程：
        1. 读取 Excel 文件
        2. 校验 8 个必填字段
        3. 数据清洗（去空行、去空格、数值转换）
        4. 计算数据概览
        5. 返回结构化数据

        Raises:
            ValueError: 文件为空 / 字段缺失 / 格式错误
        """
        # ---- 1. 读取 Excel ----
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            raise ValueError(f"文件读取失败，请确认上传的是有效的 Excel 文件: {str(e)}")

        if df.empty:
            raise ValueError("文件内容为空，请上传包含搜索词数据的报表")

        # ---- 2. 校验必填字段 ----
        actual_columns = set(df.columns)
        required_set = set(SEARCH_WORD_REQUIRED_FIELDS)
        missing_fields = required_set - actual_columns

        if missing_fields:
            raise ValueError(
                f"字段不匹配，缺失以下必填字段：{'、'.join(sorted(missing_fields))}。"
                f"请确认上传的是京东商智-搜索词报表，应包含 {len(SEARCH_WORD_REQUIRED_FIELDS)} 个字段。"
            )

        # ---- 3. 数据清洗 ----
        # 只保留必填字段列（忽略多余的列）
        df = df[SEARCH_WORD_REQUIRED_FIELDS].copy()

        # 3a. 去除搜索关键词为空的行
        df = df.dropna(subset=["搜索关键词"])
        # 去除关键词为纯空格的无效行
        df = df[df["搜索关键词"].astype(str).str.strip() != ""]

        # 3b. 关键词统一去首尾空格
        df["搜索关键词"] = df["搜索关键词"].astype(str).str.strip()

        # 3c. 数值字段统一转为数字类型（无法转换的置为 0）
        for field in SEARCH_WORD_NUMERIC_FIELDS:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0)
                # 整数字段：曝光、点击、加购、成交订单量、引流人数
                if field in ("曝光次数", "点击次数", "加购次数", "成交订单量", "引流人数"):
                    df[field] = df[field].astype(int)

        # 清洗后再判空
        if df.empty:
            raise ValueError("清洗后无有效数据行，请检查报表中是否包含搜索关键词数据")

        # ---- 4. 构建返回数据 ----
        keywords: list[dict] = []
        for _, row in df.iterrows():
            keywords.append({
                "keyword": str(row["搜索关键词"]),
                "impressions": int(row["曝光次数"]),
                "clicks": int(row["点击次数"]),
                "ctr": round(float(row["点击率CTR"]), 2),
                "cart_adds": int(row["加购次数"]),
                "orders": int(row["成交订单量"]),
                "amount": round(float(row["成交金额"]), 2),
                "traffic": int(row["引流人数"]),
            })

        # ---- 5. 数据概览 ----
        total_keywords = len(keywords)
        transaction_keywords = sum(1 for k in keywords if k["orders"] > 0)
        total_impressions = int(df["曝光次数"].sum())
        total_amount = round(float(df["成交金额"].sum()), 2)

        overview = {
            "total_keywords": total_keywords,
            "transaction_keywords": transaction_keywords,
            "total_impressions": total_impressions,
            "total_amount": total_amount,
        }

        return {
            "overview": overview,
            "keywords": keywords,
        }

    # ================================================================
    # 其他功能（骨架实现，后续扩展）
    # ================================================================

    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> list[str]:
        """从文本中提取关键词"""
        return [w for w in text.split() if len(w) > 1][:max_keywords]

    @staticmethod
    def detect_risks(keywords: list[str]) -> list[dict]:
        """检测关键词中的风险项"""
        return []

    @staticmethod
    def generate_titles(keywords: list[str], count: int = 5) -> list[str]:
        """基于关键词生成推荐标题"""
        return []

    @staticmethod
    def batch_optimize(titles: list[str]) -> list[dict]:
        """批量优化标题"""
        return []
