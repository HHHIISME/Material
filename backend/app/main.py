"""
材料学院智能学习平台 - FastAPI 主入口
"""
import os
import sys
from pathlib import Path

# 强制 stdout/stderr 使用 UTF-8 编码（Windows 默认 GBK 会让 print('中文/emoji') 崩溃）
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

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
    print("[STARTUP] Initializing application...")
    # 初始化数据库表（如果不存在）
    from app.core.database import init_db
    init_db()
    print("[STARTUP] Application started successfully")


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
from app.api.v1 import entities, relationships, graph
app.include_router(zhipu.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(entities.router, prefix="/api/v1")
app.include_router(relationships.router, prefix="/api/v1")
app.include_router(graph.router, prefix="/api/v1")

# TODO: 添加更多路由
# from app.api.v1 import chat, images, ppt, auth
# app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
# app.include_router(images.router, prefix="/api/v1/images", tags=["images"])
# app.include_router(ppt.router, prefix="/api/v1/ppt", tags=["ppt"])
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
