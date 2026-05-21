"""
材料学院智能学习平台 - FastAPI 主入口
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件（从backend目录的上级目录）
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="材料学院智能学习平台 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print("🚀 正在启动应用...")
    # 初始化数据库表（如果不存在）
    from app.core.database import init_db
    init_db()
    print("✅ 应用启动完成")


@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "status": "ok",
        "message": "材料学院智能学习平台 API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


# 注册路由
from app.api import zhipu, documents
app.include_router(zhipu.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")

# TODO: 添加更多路由
# from app.api.v1 import chat, images, ppt, auth
# app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
# app.include_router(images.router, prefix="/api/v1/images", tags=["images"])
# app.include_router(ppt.router, prefix="/api/v1/ppt", tags=["ppt"])
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
