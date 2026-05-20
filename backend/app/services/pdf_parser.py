"""
PDF解析服务模块
支持文本提取、图片提取和结构化解析
"""
import os
import io
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
from pydantic import BaseModel


class PDFPage(BaseModel):
    """PDF页面数据模型"""
    page_number: int
    text: str
    images: List[Dict[str, Any]] = []
    tables: List[List[List[str]]] = []
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


class PDFParser:
    """PDF解析器"""
    
    def __init__(self, extract_images: bool = True, extract_tables: bool = True):
        """
        初始化PDF解析器
        
        Args:
            extract_images: 是否提取图片
            extract_tables: 是否提取表格
        """
        self.extract_images = extract_images
        self.extract_tables = extract_tables
    
    def parse_pdf(
        self, 
        file_path: Optional[str] = None, 
        file_bytes: Optional[bytes] = None,
        start_page: int = 0,
        end_page: Optional[int] = None
    ) -> PDFParseResult:
        """
        解析PDF文件
        
        Args:
            file_path: PDF文件路径
            file_bytes: PDF文件字节内容
            start_page: 起始页码（从0开始）
            end_page: 结束页码（不包含）
            
        Returns:
            PDFParseResult对象
        """
        start_time = datetime.now()
        filename = Path(file_path).name if file_path else "unknown.pdf"
        
        try:
            # 使用PyMuPDF解析
            if file_path:
                doc = fitz.open(file_path)
            elif file_bytes:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
            else:
                raise ValueError("必须提供file_path或file_bytes参数")
            
            total_pages = len(doc)
            end_page = end_page or total_pages
            
            pages = []
            
            for page_num in range(start_page, min(end_page, total_pages)):
                page = doc[page_num]
                page_data = self._parse_page(page, page_num)
                pages.append(page_data)
            
            # 提取元数据
            metadata = self._extract_metadata(doc)
            
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
        
        # 提取图片
        images = []
        if self.extract_images:
            images = self._extract_page_images(page, page_num)
        
        # 使用pdfplumber提取表格
        tables = []
        if self.extract_tables:
            tables = self._extract_page_tables(page)
        
        # 获取页面尺寸
        rect = page.rect
        
        return PDFPage(
            page_number=page_num + 1,
            text=text.strip(),
            images=images,
            tables=tables,
            width=rect.width,
            height=rect.height
        )
    
    def _extract_page_images(self, page: fitz.Page, page_num: int) -> List[Dict[str, Any]]:
        """
        提取页面中的图片
        
        Args:
            page: fitz页面对象
            page_num: 页码
            
        Returns:
            图片信息列表
        """
        images = []
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                
                image_data = {
                    "page": page_num + 1,
                    "index": img_index,
                    "width": base_image["width"],
                    "height": base_image["height"],
                    "colorspace": base_image["colorspace"],
                    "bpc": base_image["bpc"],
                    "ext": base_image["ext"],
                    "image_bytes": base_image["image"]  # 二进制图片数据
                }
                images.append(image_data)
                
            except Exception as e:
                print(f"提取图片失败 (page={page_num+1}, index={img_index}): {e}")
        
        return images
    
    def _extract_page_tables(self, page: fitz.Page) -> List[List[List[str]]]:
        """
        提取页面中的表格
        
        Args:
            page: fitz页面对象
            
        Returns:
            表格数据列表
        """
        tables = []
        
        try:
            # 使用pdfplumber提取表格
            # 需要转换页面为字节
            page_bytes = page.parent.tobytes()
            
            with pdfplumber.open(io.BytesIO(page_bytes)) as pdf:
                plumber_page = pdf.pages[page.number]
                extracted_tables = plumber_page.extract_tables()
                
                for table in extracted_tables:
                    if table:
                        # 清理表格数据
                        cleaned_table = [
                            [cell.strip() if cell else "" for cell in row]
                            for row in table
                        ]
                        tables.append(cleaned_table)
                        
        except Exception as e:
            print(f"提取表格失败: {e}")
        
        return tables
    
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


# 创建全局实例
pdf_parser = PDFParser()
