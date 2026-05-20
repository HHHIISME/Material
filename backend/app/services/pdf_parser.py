"""
PDF解析服务模块（简化版）
专注于文本提取，图片功能保留接口但不实现
"""
import io
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

import fitz  # PyMuPDF
from pydantic import BaseModel


class ImageInfo(BaseModel):
    """图片信息模型"""
    image_id: str
    page: int
    index: int
    width: int = 0
    height: int = 0
    caption: str = ""
    image_bytes: Optional[bytes] = None


class ImageReference(BaseModel):
    """图片引用模型"""
    ref_text: str
    image_id: str
    page: int


class PDFPage(BaseModel):
    """PDF页面数据模型"""
    page_number: int
    text: str
    images: List[ImageInfo] = []
    image_references: List[ImageReference] = []
    tables: List[Any] = []
    width: float
    height: float


class PDFParseResult(BaseModel):
    """PDF解析结果模型"""
    filename: str
    total_pages: int
    pages: List[PDFPage]
    metadata: Dict[str, Any] = {}
    parse_time: str
    success: bool = True
    error: Optional[str] = None
    total_images: int = 0
    images_with_caption: int = 0
    total_references: int = 0


class PDFParser:
    """PDF解析器（简化版）"""
    
    # 图注匹配正则表达式
    CAPTION_PATTERNS = [
        r"图[一二三四五六七八九十\d]+[\-‐–—]\d+[^\n]*",  # 图5-1 xxx
        r"图\s*\d+[\.．]\d+[^\n]*",  # 图5.1 xxx
        r"图\s*\d+[^\n]*",  # 图1 xxx
    ]
    
    # 英文图注关键词
    CAPTION_KEYWORDS = ["Figure", "Fig.", "Fig"]
    
    def __init__(self, extract_images: bool = False):
        """
        初始化PDF解析器
        
        Args:
            extract_images: 是否提取图片（当前版本暂不支持）
        """
        self.extract_images = extract_images
    
    def parse_pdf(
        self, 
        file_path: Optional[str] = None, 
        file_bytes: Optional[bytes] = None,
        filename: str = "unknown.pdf"
    ) -> PDFParseResult:
        """
        解析PDF文件
        
        Args:
            file_path: PDF文件路径
            file_bytes: PDF文件字节内容
            filename: 文件名
            
        Returns:
            PDFParseResult对象
        """
        start_time = datetime.now()
        
        try:
            # 打开PDF文档
            if file_path:
                doc = fitz.open(file_path)
                filename = file_path.split('/')[-1].split('\\')[-1]
            elif file_bytes:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
            else:
                raise ValueError("必须提供file_path或file_bytes参数")
            
            # 提取元数据
            metadata = self._extract_metadata(doc)
            
            # 解析每一页
            pages = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                pdf_page = self._parse_page(page, page_num)
                pages.append(pdf_page)
            
            total_pages = len(doc)
            doc.close()
            
            parse_time = (datetime.now() - start_time).total_seconds()
            
            return PDFParseResult(
                filename=filename,
                total_pages=total_pages,
                pages=pages,
                metadata=metadata,
                parse_time=f"{parse_time:.2f}s"
            )
            
        except Exception as e:
            return PDFParseResult(
                filename=filename,
                total_pages=0,
                pages=[],
                success=False,
                error=str(e),
                parse_time="0s"
            )
    
    def _parse_page(self, page: fitz.Page, page_num: int) -> PDFPage:
        """
        解析单个页面
        
        Args:
            page: fitz页面对象
            page_num: 页码
            
        Returns:
            PDFPage对象
        """
        # 提取文本
        text = page.get_text()
        
        # 获取页面尺寸
        rect = page.rect
        
        # 图片提取（当前版本暂不实现）
        images = []
        image_references = []
        
        # 如果未来需要提取图片，可以在这里调用相关方法
        # if self.extract_images:
        #     images = self._extract_page_images(page, page_num)
        #     image_references = self._extract_image_references(page, page_num, images)
        
        return PDFPage(
            page_number=page_num + 1,
            text=text.strip(),
            images=images,
            image_references=image_references,
            tables=[],
            width=rect.width,
            height=rect.height
        )
    
    def _extract_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        """
        提取PDF元数据
        
        Args:
            doc: fitz文档对象
            
        Returns:
            元数据字典
        """
        metadata = doc.metadata
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "keywords": metadata.get("keywords", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "page_count": len(doc)
        }
    
    def extract_text_only(
        self, 
        file_path: Optional[str] = None, 
        file_bytes: Optional[bytes] = None
    ) -> str:
        """
        仅提取PDF文本内容
        
        Args:
            file_path: PDF文件路径
            file_bytes: PDF文件字节内容
            
        Returns:
            所有页面的文本内容
        """
        try:
            if file_path:
                doc = fitz.open(file_path)
            elif file_bytes:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
            else:
                raise ValueError("必须提供file_path或file_bytes参数")
            
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            
            doc.close()
            return "\n\n".join(text_parts)
            
        except Exception as e:
            return f"提取文本失败: {e}"
    
    def get_page_image(
        self, 
        file_path: Optional[str] = None, 
        file_bytes: Optional[bytes] = None,
        page_num: int = 0,
        zoom: float = 2.0
    ) -> Optional[bytes]:
        """
        将PDF页面渲染为图片
        
        Args:
            file_path: PDF文件路径
            file_bytes: PDF文件字节内容
            page_num: 页码（从0开始）
            zoom: 缩放比例
            
        Returns:
            PNG格式的图片字节
        """
        try:
            if file_path:
                doc = fitz.open(file_path)
            elif file_bytes:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
            else:
                raise ValueError("必须提供file_path或file_bytes参数")
            
            if page_num >= len(doc):
                return None
            
            page = doc[page_num]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            img_bytes = pix.tobytes("png")
            doc.close()
            
            return img_bytes
            
        except Exception as e:
            print(f"渲染页面图片失败: {e}")
            return None
    
    def extract_captions_from_text(self, text: str) -> List[str]:
        """
        从文本中提取图注
        
        Args:
            text: PDF文本内容
            
        Returns:
            图注列表
        """
        captions = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 检查中文图注
            for pattern in self.CAPTION_PATTERNS:
                if re.match(pattern, line):
                    captions.append(line)
                    break
            
            # 检查英文图注
            if not captions or captions[-1] != line:
                for keyword in self.CAPTION_KEYWORDS:
                    if keyword in line and re.search(r'\d+', line):
                        captions.append(line)
                        break
        
        return captions


# 创建全局实例
pdf_parser = PDFParser()
