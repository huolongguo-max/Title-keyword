"""
API 路由模块
所有接口路由定义，负责请求参数校验、响应格式化
业务逻辑委托给 service 层处理
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.common import (
    HealthResponse,
    SuccessResponse,
    ErrorResponse,
    SearchWordUploadData,
    SearchWordOverview,
    SearchWordItem,
    ClassifyRequest,
    ClassifyResponseData,
    ClassifiedWord,
    WordPool,
    RiskCheckRequest,
    RiskCheckData,
    RiskItem,
    RiskPosition,
    TitleGenerateRequest,
    TitleGenerateData,
    WordDetail,
    CompareData,
    CompareTitleInfo,
    CompareNewTitleInfo,
    BatchSkuResult,
    BatchOptimizeData,
    BatchExportRequest,
)
from app.core.config import (
    APP_VERSION,
    MAX_UPLOAD_SIZE_BYTES,
    ALLOWED_EXTENSIONS,
    SEARCH_WORD_EXTENSIONS,
)
from app.service.analyzer import TitleAnalyzer
from app.service.word_classify_service import classify_keywords
from app.service.risk_detect_service import detect_title_risks
from app.service.title_generate_service import generate_title
from app.service.batch_optimize_service import process_batch_skus, export_to_excel
from fastapi.responses import StreamingResponse
import os, io

router = APIRouter()


# ============================================================
# 健康检查
# ============================================================
@router.get("/health", response_model=HealthResponse, tags=["系统"])
async def health_check():
    """服务健康检查接口"""
    return HealthResponse(status="ok", version=APP_VERSION)


# ============================================================
# 文件上传与解析
# ============================================================
@router.post("/upload", response_model=SuccessResponse, tags=["上传解析"])
async def upload_file(file: UploadFile = File(...)):
    """
    上传并解析文件（Excel/CSV）
    - 支持 .xlsx / .xls / .csv 格式
    - 单文件最大 20MB
    """
    # 校验文件扩展名
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 校验文件大小
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制（最大 {MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB）"
        )

    # 保存临时文件并解析
    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        result = TitleAnalyzer.parse_file(tmp_path)
        return SuccessResponse(message="文件解析成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ============================================================
# 京东商智搜索词报表上传与解析
# ============================================================
@router.post(
    "/upload/search-word",
    response_model=SuccessResponse,
    tags=["上传解析"],
)
async def upload_search_word(file: UploadFile = File(...)):
    """
    上传并解析京东商智-搜索词报表（xlsx/xls）

    固定 8 个必填字段：
    搜索关键词、曝光次数、点击次数、点击率CTR、
    加购次数、成交订单量、成交金额、引流人数

    返回：
    - overview: 数据概览（总词数、有成交词数、总曝光量、总成交金额）
    - keywords: 清洗后的搜索词明细列表
    """
    # ---- 1. 校验文件扩展名 ----
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in SEARCH_WORD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式「{ext}」，请上传 .xlsx 或 .xls 格式的搜索词报表",
        )

    # ---- 2. 校验文件大小 ----
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        max_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过 {max_mb}MB 限制，请拆分报表后重新上传",
        )

    # ---- 3. 存临时文件 ----
    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(content)

    # ---- 4. 调用解析服务 ----
    try:
        result = TitleAnalyzer.parse_search_word_report(tmp_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器解析异常: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # ---- 5. 构建响应 ----
    overview = SearchWordOverview(**result["overview"])
    keywords = [SearchWordItem(**kw) for kw in result["keywords"]]

    return SuccessResponse(
        message=f"解析成功，共 {overview.total_keywords} 个搜索词",
        data=SearchWordUploadData(
            overview=overview,
            keywords=keywords,
        ).model_dump(),
    )


# ============================================================
# 关键词提取（示例接口骨架）
# ============================================================
@router.post("/keywords/extract", response_model=SuccessResponse, tags=["词池分类"])
async def extract_keywords(text: str, max_keywords: int = 10):
    """从文本中提取关键词"""
    keywords = TitleAnalyzer.extract_keywords(text, max_keywords)
    return SuccessResponse(message="关键词提取完成", data={"keywords": keywords})


# ============================================================
# 词池四级分类 + 质量得分
# ============================================================
@router.post(
    "/word/classify",
    response_model=SuccessResponse,
    tags=["词池分类"],
)
async def classify_words(req: ClassifyRequest):
    """
    对搜索词列表执行四层级自动分类 + 质量得分计算

    四词池：
    ① 核心成交词池 — 成交订单量 > 0，高权重高转化
    ② 潜力增长词池 — 零成交但曝光/点击高于均值，增量流量来源
    ③ 无效弱词池 — 有曝光无点击/加购/成交，僵尸词
    ④ 冲突违规词池 — 包含互斥属性词，需人工审核

    质量得分：0-100 分，成交金额 * 0.5 + 点击 * 0.3 + 曝光 * 0.2
    """
    if not req.keywords:
        raise HTTPException(status_code=400, detail="关键词列表不能为空")

    try:
        result = classify_keywords(req.keywords)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分类计算异常: {str(e)}")

    # 构建 Pydantic 响应
    pools = {}
    for pool_key in ["core_transaction", "potential_growth", "invalid_weak", "conflict_risk"]:
        pool_data = result[pool_key]
        pools[pool_key] = WordPool(
            name=pool_data["name"],
            tag=pool_data["tag"],
            count=pool_data["count"],
            keywords=[ClassifiedWord(**kw) for kw in pool_data["keywords"]],
        )

    total = sum(p.count for p in pools.values())
    return SuccessResponse(
        message=f"分类完成，共 {total} 个词归入 4 个词池",
        data=ClassifyResponseData(**pools).model_dump(),
    )


# ============================================================
# 风险检测 — 标题六大降权风险检测
# ============================================================
@router.post(
    "/title/check-risk",
    response_model=SuccessResponse,
    tags=["风险检测"],
)
async def check_title_risk(req: RiskCheckRequest):
    """
    对商品标题执行六大降权风险检测

    六大规则：
    ① 属性冲突 — 互斥属性词（标准版/尊享版、有线/无线等）同时出现
    ② 年份冲突 — 正则匹配 2+ 不同年份数字
    ③ 规格冲突 — 多个不同规格数值（X件套、Xml、Xg 等）
    ④ 语义重复 — 同义词组内多词堆砌（礼盒/套装等）
    ⑤ 关键词堆砌 — 同一关键词出现 ≥2 次
    ⑥ 无意义垃圾词 — 填充词、纯符号、超长长尾

    返回：
    - risk_list: 风险条目列表（类型、等级、内容、位置、建议）
    - risk_score: 整体风险评分 0-100
    - high/medium/low_count: 各等级数量
    """
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="标题不能为空")

    try:
        result = detect_title_risks(req.title, req.word_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"风险检测异常: {str(e)}")

    # 构建 Pydantic 响应
    risk_items = []
    for r in result["risk_list"]:
        risk_items.append(RiskItem(
            type=r["type"],
            risk_level=r["risk_level"],
            content=r["content"],
            positions=[RiskPosition(**p) for p in r["positions"]],
            suggestion=r["suggestion"],
        ))

    data = RiskCheckData(
        risk_list=risk_items,
        risk_score=result["risk_score"],
        high_count=result["high_count"],
        medium_count=result["medium_count"],
        low_count=result["low_count"],
    )

    total = len(risk_items)
    return SuccessResponse(
        message=f"检测完成，发现 {total} 个风险项（高风险:{data.high_count} 中风险:{data.medium_count} 低风险:{data.low_count}）",
        data=data.model_dump(),
    )


# ============================================================
# 标题生成 — 最优标题一键生成 + 新旧权重对比
# ============================================================
@router.post(
    "/titles/generate",
    response_model=SuccessResponse,
    tags=["标题生成"],
)
async def generate_titles(req: TitleGenerateRequest):
    """
    基于四词池数据，一键生成符合京东规范的最优标题

    生成策略：
    1. 核心大词 + 类目词前置（top 1-2，按质量得分）
    2. 高转化属性词中段（按得分降序）
    3. 潜力热搜词尾部（top 1-2，按曝光量）
    4. 自动去重、去冲突、去无效词
    5. 截断到配置字数上限

    若传入 original_title，同步返回新旧标题对比数据
    """
    try:
        result = generate_title(
            word_pools=req.word_pools,
            original_title=req.original_title,
            max_length=req.max_length,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标题生成异常: {str(e)}")

    # 构建 Pydantic 响应
    word_detail = [WordDetail(**wd) for wd in result["word_detail"]]

    compare = None
    if result.get("compare"):
        cmp = result["compare"]
        compare = CompareData(
            original_title=CompareTitleInfo(**cmp["original_title"]),
            new_title=CompareNewTitleInfo(**cmp["new_title"]),
            weight_improvement=cmp["weight_improvement"],
            traffic_reasons=cmp["traffic_reasons"],
        )

    data = TitleGenerateData(
        new_title=result["new_title"],
        chinese_count=result["chinese_count"],
        total_chars=result["total_chars"],
        word_detail=word_detail,
        compare=compare,
    )

    return SuccessResponse(
        message=f"标题生成成功（{result['chinese_count']}字/{result['total_chars']}字符）",
        data=data.model_dump(),
    )


# ============================================================
# 批量优化 — 多文件上传 + 全流程处理
# ============================================================
@router.post(
    "/batch/optimize",
    response_model=SuccessResponse,
    tags=["批量优化"],
)
async def batch_optimize(files: list[UploadFile] = File(...)):
    """
    批量上传多个搜索词报表文件，执行解析 → 分类 → 标题生成全流程

    每个文件对应一个SKU，返回：
    - sku_name: 文件名（SKU标识）
    - title: 生成的优化标题
    - core_count / potential_count / risk_count / score: 核心指标
    - error: 单个文件失败时的错误信息
    """
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一个文件")

    # 校验文件格式
    for file in files:
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in SEARCH_WORD_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"「{file.filename}」格式不支持，仅接受 .xlsx / .xls"
            )

    # 读取所有文件内容
    file_tuples: list[tuple[str, bytes]] = []
    for file in files:
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"「{file.filename}」超过 20MB 限制"
            )
        file_tuples.append((file.filename or "unknown.xlsx", content))

    # 批量处理
    try:
        results = process_batch_skus(file_tuples)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量处理异常: {str(e)}")

    # 构建响应
    result_items = []
    success = sum(1 for r in results if not r.get("error"))
    failed = len(results) - success

    for r in results:
        result_items.append(BatchSkuResult(
            sku_name=r["sku_name"],
            title=r["title"],
            core_count=r["core_count"],
            potential_count=r["potential_count"],
            risk_count=r["risk_count"],
            score=r["score"],
            total_keywords=r["total_keywords"],
            total_impressions=r["total_impressions"],
            total_amount=r["total_amount"],
            error=r.get("error"),
        ))

    data = BatchOptimizeData(
        results=result_items,
        total=len(results),
        success=success,
        failed=failed,
    )

    return SuccessResponse(
        message=f"批量处理完成，成功 {success}/{len(results)} 个",
        data=data.model_dump(),
    )


# ============================================================
# 批量导出 — 结果导出为 Excel
# ============================================================
@router.post("/batch/export", tags=["批量优化"])
async def batch_export(req: BatchExportRequest):
    """
    将批量优化结果导出为 Excel 文件

    输入：批量优化结果列表
    输出：.xlsx 文件流（包含 SKU、标题、核心指标等列）
    """
    if not req.results:
        raise HTTPException(status_code=400, detail="无结果数据可导出")

    try:
        # 转为 dict 列表
        result_dicts = [r.model_dump() for r in req.results]
        excel_bytes = export_to_excel(result_dicts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出异常: {str(e)}")

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=SKU优化结果.xlsx",
        },
    )
