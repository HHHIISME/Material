"""
数据库连接模块
"""
import sys
# 强制 stdout/stderr 使用 UTF-8（Windows GBK 会让 print 中的中文/emoji 崩溃）
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 创建异步引擎
engine = create_engine(
    settings.DATABASE_URL.replace("asyncpg", "psycopg2"),  # 使用同步驱动
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库（创建所有表）"""
    from app.models.knowledge_graph import Entity, Relationship
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功")
