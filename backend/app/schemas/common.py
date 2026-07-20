"""
通用 Pydantic 数据模型
定义所有接口的请求/响应结构
"""

from pydantic import BaseModel, Field
from typing import Optional, Any


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(default="ok", description="服务状态")
    version: str = Field(..., description="应用版本号")


class ErrorResponse(BaseModel):
    """通用错误响应"""
    detail: str = Field(..., description="错误详情")
    code: Optional[str] = Field(default=None, description="错误码")


class SuccessResponse(BaseModel):
    """通用成功响应"""
    message: str = Field(default="操作成功", description="提示信息")
    data: Optional[Any] = Field(default=None, description="返回数据")


class PaginationParams(BaseModel):
    """分页请求参数"""
    page: int = Field(default=1, ge=1, description="页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: list = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总条数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页条数")
    total_pages: int = Field(default=0, description="总页数")


# ============================================================
# 京东商智搜索词报表 — 请求/响应模型
# ============================================================

class SearchWordItem(BaseModel):
    """单条搜索词数据"""
    keyword: str = Field(..., description="搜索关键词")
    impressions: int = Field(default=0, description="曝光次数")
    clicks: int = Field(default=0, description="点击次数")
    ctr: float = Field(default=0.0, description="点击率（百分比数值）")
    cart_adds: int = Field(default=0, description="加购次数")
    orders: int = Field(default=0, description="成交订单量")
    amount: float = Field(default=0.0, description="成交金额")
    traffic: int = Field(default=0, description="引流人数")


class SearchWordOverview(BaseModel):
    """搜索词报表 — 数据概览"""
    total_keywords: int = Field(default=0, description="总词数")
    transaction_keywords: int = Field(default=0, description="有成交词数（成交订单量 > 0）")
    total_impressions: int = Field(default=0, description="总曝光量")
    total_amount: float = Field(default=0.0, description="总成交金额")


class SearchWordUploadData(BaseModel):
    """搜索词上传解析 — 完整返回数据"""
    overview: SearchWordOverview = Field(default_factory=SearchWordOverview, description="数据概览")
    keywords: list[SearchWordItem] = Field(default_factory=list, description="搜索词明细列表")


# ============================================================
# 词池分类 — 请求/响应模型
# ============================================================

class ClassifyRequest(BaseModel):
    """分类请求 — 传入搜索词列表"""
    keywords: list[SearchWordItem] = Field(..., description="待分类的搜索词列表", min_length=1)


class ClassifiedWord(BaseModel):
    """单条分类结果 — 包含原字段 + 得分 + 分类信息"""
    keyword: str = Field(..., description="搜索关键词")
    impressions: int = Field(default=0)
    clicks: int = Field(default=0)
    ctr: float = Field(default=0.0)
    cart_adds: int = Field(default=0)
    orders: int = Field(default=0)
    amount: float = Field(default=0.0)
    traffic: int = Field(default=0)
    score: float = Field(default=0.0, description="质量得分（0-100）")
    pool: str = Field(default="", description="词池标识")
    pool_label: str = Field(default="", description="词池中文名")
    pool_tag: str = Field(default="", description="词池标签说明")


class WordPool(BaseModel):
    """单个词池"""
    name: str = Field(..., description="词池名称")
    tag: str = Field(default="", description="词池标签定义")
    count: int = Field(default=0, description="词数量")
    keywords: list[ClassifiedWord] = Field(default_factory=list, description="分类后的关键词列表")


class ClassifyResponseData(BaseModel):
    """分类完整结果"""
    core_transaction: WordPool = Field(default_factory=WordPool, description="核心成交词池")
    potential_growth: WordPool = Field(default_factory=WordPool, description="潜力增长词池")
    invalid_weak: WordPool = Field(default_factory=WordPool, description="无效弱词池")
    conflict_risk: WordPool = Field(default_factory=WordPool, description="冲突违规词池")


# ============================================================
# 标题风险检测 — 请求/响应模型
# ============================================================

class RiskCheckRequest(BaseModel):
    """风险检测请求"""
    title: str = Field(..., description="待检测的商品标题", min_length=1)
    word_list: list[str] = Field(default_factory=list, description="关键词列表（用于堆砌检测）")


class RiskPosition(BaseModel):
    """风险词在标题中的位置"""
    word: str = Field(default="", description="风险词")
    start: int = Field(default=0, description="起始位置（字符索引）")
    end: int = Field(default=0, description="结束位置（字符索引）")


class RiskItem(BaseModel):
    """单条风险详情"""
    type: str = Field(..., description="风险类型：属性冲突/年份冲突/规格冲突/语义重复/关键词堆砌/无意义垃圾词")
    risk_level: str = Field(..., description="风险等级：high/medium/low")
    content: str = Field(..., description="违规内容摘要")
    positions: list[RiskPosition] = Field(default_factory=list, description="违规内容在标题中的位置")
    suggestion: str = Field(default="", description="修改建议")


class RiskCheckData(BaseModel):
    """风险检测完整返回数据"""
    risk_list: list[RiskItem] = Field(default_factory=list, description="风险列表")
    risk_score: int = Field(default=0, description="整体风险评分（0-100，越高越危险）")
    high_count: int = Field(default=0, description="高风险数量")
    medium_count: int = Field(default=0, description="中风险数量")
    low_count: int = Field(default=0, description="低风险数量")


# ============================================================
# 标题生成 — 请求/响应模型
# ============================================================

class TitleGenerateRequest(BaseModel):
    """标题生成请求"""
    word_pools: dict = Field(..., description="四词池分类结果（core_transaction/potential_growth/invalid_weak/conflict_risk）")
    original_title: Optional[str] = Field(default=None, description="原标题（用于新旧对比）")
    max_length: int = Field(default=30, ge=20, le=50, description="标题最大字数（汉字）")


class WordDetail(BaseModel):
    """标题中单个词的来源详情"""
    word: str = Field(..., description="词")
    position: int = Field(default=0, description="在标题中的位置索引")
    source_pool: str = Field(default="", description="来源词池")
    source_type: str = Field(default="", description="来源类型（前置核心词/中段属性词/尾部热搜词）")
    score: Optional[float] = Field(default=None, description="质量得分")
    impressions: Optional[int] = Field(default=None, description="曝光量")


class CompareTitleInfo(BaseModel):
    """单个标题的对比指标"""
    title: str = Field(default="", description="标题文本")
    core_count: int = Field(default=0, description="核心词数量")
    invalid_count: int = Field(default=0, description="无效词数量")
    conflict_count: int = Field(default=0, description="冲突词数量")
    risk_count: int = Field(default=0, description="风险项数量")
    risk_score: int = Field(default=0, description="风险评分")


class CompareNewTitleInfo(BaseModel):
    """新标题对比指标（额外字段）"""
    title: str = Field(default="", description="标题文本")
    core_count: int = Field(default=0, description="核心词数量")
    potential_count: int = Field(default=0, description="潜力词数量")
    invalid_removed: int = Field(default=0, description="剔除无效词数量")
    risk_count: int = Field(default=0, description="风险项数量")
    risk_score: int = Field(default=0, description="风险评分")


class CompareData(BaseModel):
    """新旧标题对比数据"""
    original_title: CompareTitleInfo = Field(default_factory=CompareTitleInfo, description="原标题指标")
    new_title: CompareNewTitleInfo = Field(default_factory=CompareNewTitleInfo, description="新标题指标")
    weight_improvement: float = Field(default=0.0, description="预估权重提升比例（%）")
    traffic_reasons: list[str] = Field(default_factory=list, description="流量提升逻辑说明")


class TitleGenerateData(BaseModel):
    """标题生成完整返回数据"""
    new_title: str = Field(default="", description="生成的最优标题")
    chinese_count: int = Field(default=0, description="汉字数")
    total_chars: int = Field(default=0, description="总字符数")
    word_detail: list[WordDetail] = Field(default_factory=list, description="标题词权重明细")
    compare: Optional[CompareData] = Field(default=None, description="新旧对比数据（仅传入原标题时返回）")


# ============================================================
# 批量优化 — 请求/响应模型
# ============================================================

class BatchSkuResult(BaseModel):
    """单个SKU的批量优化结果"""
    sku_name: str = Field(default="", description="SKU标识（文件名）")
    title: str = Field(default="", description="优化后标题")
    core_count: int = Field(default=0, description="核心词数量")
    potential_count: int = Field(default=0, description="潜力词数量")
    risk_count: int = Field(default=0, description="风险数量")
    score: float = Field(default=0.0, description="质量得分")
    total_keywords: int = Field(default=0, description="总词数")
    total_impressions: int = Field(default=0, description="总曝光量")
    total_amount: float = Field(default=0.0, description="总成交金额")
    error: Optional[str] = Field(default=None, description="错误信息（成功时为null）")


class BatchOptimizeData(BaseModel):
    """批量优化完整返回"""
    results: list[BatchSkuResult] = Field(default_factory=list, description="各SKU结果列表")
    total: int = Field(default=0, description="总SKU数")
    success: int = Field(default=0, description="成功数")
    failed: int = Field(default=0, description="失败数")


class BatchExportRequest(BaseModel):
    """导出请求 — 传入批量优化结果"""
    results: list[BatchSkuResult] = Field(..., description="批量优化结果列表")
