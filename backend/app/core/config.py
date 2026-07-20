"""
应用核心配置模块
包含 CORS、文件上传限制、应用元信息等配置常量
"""

# 应用信息
APP_TITLE = "Title-Keyword 智能分析平台"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "离线标题关键词解析、分类、风险检测与批量优化工具"

# CORS 跨域配置 - 允许前端本地开发端口访问
ALLOWED_ORIGINS = [
    "http://localhost:5173",   # Vite 默认端口
    "http://localhost:3000",   # 备用端口
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

# 文件上传限制
MAX_UPLOAD_SIZE_MB = 20       # 单文件最大 20MB
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# 支持的文件格式
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}
SEARCH_WORD_EXTENSIONS = {".xlsx", ".xls"}

# 京东商智搜索词报表 — 8 个必填字段
SEARCH_WORD_REQUIRED_FIELDS = [
    "搜索关键词",
    "曝光次数",
    "点击次数",
    "点击率CTR",
    "加购次数",
    "成交订单量",
    "成交金额",
    "引流人数",
]

# 搜索词报表数值字段（用于类型转换 + 千分位展示）
SEARCH_WORD_NUMERIC_FIELDS = [
    "曝光次数",
    "点击次数",
    "点击率CTR",
    "加购次数",
    "成交订单量",
    "成交金额",
    "引流人数",
]
