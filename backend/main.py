"""
FastAPI 应用入口
启动命令: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import APP_TITLE, APP_VERSION, APP_DESCRIPTION, ALLOWED_ORIGINS

# 创建 FastAPI 应用实例
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs",          # Swagger 文档路径
    redoc_url="/redoc",        # ReDoc 文档路径
)

# 配置 CORS 跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # 允许的前端来源
    allow_credentials=True,
    allow_methods=["*"],              # 允许所有 HTTP 方法
    allow_headers=["*"],              # 允许所有请求头
)

# 注册路由
app.include_router(router, prefix="/api")


# ============================================================
# 应用启动/关闭事件（可扩展日志、资源初始化等）
# ============================================================
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print(f"🚀 {APP_TITLE} v{APP_VERSION} 启动成功！")
    print(f"📖 API 文档: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    print("👋 应用已关闭")


# ============================================================
# 直接运行入口
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
