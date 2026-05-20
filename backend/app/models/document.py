"""
文档数据模型 - 支持图片与知识点的关联
"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ContentType(Enum):
    """内容类型"""
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    FORMULA = "formula"


@dataclass
class BoundingBox:
    """边界框 - 表示元素在页面中的位置"""
    x0: float  # 左上角 X
    y0: float  # 左上角 Y
    x1: float  # 右下角 X
    y1: float  # 右下角 Y
    
    def to_dict(self) -> dict:
        return {"x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1}


@dataclass
class ImageInfo:
    """图片信息"""
    id: str                              # 图片唯一ID
    page_num: int                        # 所在页码
    bbox: BoundingBox                    # 页面位置
    caption: Optional[str] = None        # 图注（如"图5-1 晶体结构示意图"）
    ai_description: Optional[str] = None # AI生成的描述
    storage_path: Optional[str] = None   # MinIO存储路径
    related_chunk_ids: list = field(default_factory=list)  # 关联的文本块ID
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "page_num": self.page_num,
            "bbox": self.bbox.to_dict(),
            "caption": self.caption,
            "ai_description": self.ai_description,
            "storage_path": self.storage_path,
            "related_chunk_ids": self.related_chunk_ids
        }


@dataclass
class TextChunk:
    """文本块"""
    id: str                              # 块唯一ID
    page_num: int                        # 所在页码
    text: str                            # 文本内容
    bbox: BoundingBox                    # 页面位置
    embedding: Optional[list] = None     # 向量嵌入
    related_image_ids: list = field(default_factory=list)  # 关联的图片ID
    entities: list = field(default_factory=list)           # 提取的实体
    source_location: Optional[str] = None  # 来源位置（如"第5章第2节"）
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "page_num": self.page_num,
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "embedding": self.embedding,
            "related_image_ids": self.related_image_ids,
            "entities": self.entities,
            "source_location": self.source_location
        }


@dataclass
class TableInfo:
    """表格信息"""
    id: str                              # 表格唯一ID
    page_num: int                        # 所在页码
    bbox: BoundingBox                    # 页面位置
    caption: Optional[str] = None        # 表格标题
    headers: list = field(default_factory=list)      # 表头
    rows: list = field(default_factory=list)         # 数据行
    markdown_text: Optional[str] = None  # Markdown格式
    related_chunk_ids: list = field(default_factory=list)  # 关联文本
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "page_num": self.page_num,
            "bbox": self.bbox.to_dict(),
            "caption": self.caption,
            "headers": self.headers,
            "rows": self.rows,
            "markdown_text": self.markdown_text,
            "related_chunk_ids": self.related_chunk_ids
        }


@dataclass
class PageContent:
    """页面内容"""
    page_num: int
    text_chunks: list = field(default_factory=list)  # TextChunk列表
    images: list = field(default_factory=list)       # ImageInfo列表
    tables: list = field(default_factory=list)       # TableInfo列表
    
    def to_dict(self) -> dict:
        return {
            "page_num": self.page_num,
            "text_chunks": [c.to_dict() for c in self.text_chunks],
            "images": [i.to_dict() for i in self.images],
            "tables": [t.to_dict() for t in self.tables]
        }


@dataclass
class Document:
    """文档"""
    id: str
    filename: str
    total_pages: int
    pages: list = field(default_factory=list)  # PageContent列表
    knowledge_graph_nodes: list = field(default_factory=list)  # 知识图谱节点
    knowledge_graph_edges: list = field(default_factory=list)  # 知识图谱边
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "total_pages": self.total_pages,
            "pages": [p.to_dict() for p in self.pages],
            "knowledge_graph_nodes": self.knowledge_graph_nodes,
            "knowledge_graph_edges": self.knowledge_graph_edges
        }
