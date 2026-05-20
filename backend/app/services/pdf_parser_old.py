"""
PDF解析服务模块
支持文本提取、图片提取和结构化解析

注：图片位置、图注关联功能暂缓，后续按需加入
"""
import os
import io
import json
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
from pydantic import BaseModel


class ImageInfo(BaseModel):
    """图片信息模型"""
    image_id: str
    page: int
    index: int
    width: int
    height: int
    ext: str = ""
    colorspace: Any = ""
    image_bytes: Optional[bytes] = None


class PDFPage(BaseModel):
    """PDF页面数据模型"""
    page_number: int
    text: str
    images: List[ImageInfo] = []
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
    total_images: int = 0


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
            
            # 计算图片统计信息
            total_images = sum(len(page.images) for page in pages)
            images_with_caption = sum(1 for page in pages for img in page.images if img.caption)
            total_references = sum(len(page.image_references) for page in pages)
            
            return PDFParseResult(
                filename=filename,
                total_pages=total_pages,
                pages=pages,
                metadata=metadata,
                parse_time=f"{parse_time:.2f}s",
                total_images=total_images,
                images_with_caption=images_with_caption,
                total_references=total_references
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
        
        # 提取图片（包含位置和图注）
        images = []
        if self.extract_images:
            images = self._extract_page_images(page, page_num)
        
        # 提取图片引用
        image_references = self._extract_image_references(page, page_num, images)
        
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
            image_references=image_references,
            tables=tables,
            width=rect.width,
            height=rect.height
        )
    
    def _extract_page_images(self, page: fitz.Page, page_num: int) -> List[ImageInfo]:
        """
        提取页面中的图片及其位置、图注信息
        
        Args:
            page: fitz页面对象
            page_num: 页码
            
        Returns:
            图片信息列表
        """
        images = []
        image_list = page.get_images()
        
        # 获取所有图片的位置信息
        img_bboxes = self._get_all_image_bboxes(page)
        
        # 提取页面中的所有图注
        page_captions = self._extract_all_captions(page)
        
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                
                # 获取图片位置
                img_bbox = img_bboxes.get(xref, [])
                
                # 匹配图注（优先使用位置匹配，其次使用索引匹配）
                caption, caption_bbox = self._match_caption_to_image(
                    img_index, img_bbox, page_captions, len(image_list)
                )
                
                image_id = f"img_{page_num + 1}_{img_index + 1}"
                
                image_data = ImageInfo(
                    image_id=image_id,
                    page=page_num + 1,
                    index=img_index,
                    width=base_image["width"],
                    height=base_image["height"],
                    bbox=img_bbox,
                    caption=caption,
                    caption_bbox=caption_bbox,
                    ext=base_image["ext"],
                    colorspace=base_image["colorspace"],
                    image_bytes=base_image["image"]
                )
                images.append(image_data)
                
            except Exception as e:
                print(f"提取图片失败 (page={page_num+1}, index={img_index}): {e}")
        
        return images
    
    def _extract_all_captions(self, page: fitz.Page) -> List[Tuple[str, List[float]]]:
        """
        提取页面中的所有图注
        
        Args:
            page: fitz页面对象
            
        Returns:
            [(图注文本, 位置), ...] 图注列表
        """
        captions = []
        
        try:
            # 获取页面所有文本块
            text_dict = page.get_text("dict")
            
            for block in text_dict["blocks"]:
                if block.get("type") != 0:  # 跳过非文本块
                    continue
                
                text = block.get("text", "").strip()
                bbox = block["bbox"]
                
                # 检查是否匹配中文图注格式
                is_caption = False
                for pattern in self.CAPTION_PATTERNS:
                    if re.match(pattern, text):
                        is_caption = True
                        break
                
                # 检查是否包含英文图注关键词
                if not is_caption:
                    for keyword in self.CAPTION_KEYWORDS:
                        if keyword in text:
                            # 检查是否包含数字
                            if re.search(r'\d+', text):
                                is_caption = True
                                break
                
                if is_caption:
                    captions.append((text, [bbox[0], bbox[1], bbox[2], bbox[3]]))
                        
        except Exception as e:
            print(f"提取所有图注失败: {e}")
        
        return captions
    
    def _match_caption_to_image(
        self, 
        img_index: int, 
        img_bbox: List[float], 
        page_captions: List[Tuple[str, List[float]]],
        total_images: int
    ) -> Tuple[str, List[float]]:
        """
        将图注匹配到图片
        
        Args:
            img_index: 图片索引
            img_bbox: 图片位置
            page_captions: 页面中的所有图注
            total_images: 页面中图片总数
            
        Returns:
            (图注文本, 图注位置)
        """
        if not page_captions:
            return "", []
        
        # 方法1：如果图片有位置，找最近的图注
        if img_bbox:
            img_y_bottom = img_bbox[3]
            min_distance = float('inf')
            best_caption = ""
            best_bbox = []
            
            for caption_text, caption_bbox in page_captions:
                # 图注通常在图片下方
                if caption_bbox[1] >= img_y_bottom:
                    distance = caption_bbox[1] - img_y_bottom
                    if distance < min_distance and distance < 100:  # 100像素阈值
                        min_distance = distance
                        best_caption = caption_text
                        best_bbox = caption_bbox
            
            if best_caption:
                return best_caption, best_bbox
        
        # 方法2：使用图片编号匹配
        # 从图片编号推断应该匹配哪个图注
        for caption_text, caption_bbox in page_captions:
            # 提取图注中的编号
            numbers = re.findall(r'[\d]+', caption_text)
            if numbers:
                caption_num = int(numbers[0])
                # 如果图注编号与图片索引匹配（从1开始）
                if caption_num == img_index + 1:
                    return caption_text, caption_bbox
        
        # 方法3：简单索引匹配
        if img_index < len(page_captions):
            return page_captions[img_index]
        
        return "", []
    
    def _get_all_image_bboxes(self, page: fitz.Page) -> Dict[int, List[float]]:
        """
        获取页面中所有图片的位置信息
        
        Args:
            page: fitz页面对象
            
        Returns:
            {xref: [x0, y0, x1, y1]} 图片位置字典
        """
        bboxes = {}
        
        try:
            # 方法：遍历页面内容，查找图片块
            # 使用get_text("dict")获取页面结构
            text_dict = page.get_text("dict")
            
            # 遍历所有块
            for block in text_dict.get("blocks", []):
                # type=1表示图片块
                if block.get("type") == 1:
                    bbox = block.get("bbox")
                    if bbox:
                        # 获取图片的xref
                        # 在PyMuPDF中，图片块可能不直接包含xref
                        # 我们需要通过其他方式关联
                        
                        # 尝试从块的图像数据中获取
                        # 注意：这里需要使用备用方法
                        
                        # 暂时记录位置，稍后关联
                        pass
            
            # 方法2：使用drawings获取图片位置
            try:
                drawings = page.get_drawings()
                for d in drawings:
                    if d.get("image"):
                        xref = d["image"]
                        rect = d.get("rect")
                        if rect:
                            bboxes[xref] = [rect.x0, rect.y0, rect.x1, rect.y1]
            except Exception as e:
                print(f"使用drawings获取图片位置失败: {e}")
            
            # 方法3：使用图像列表的位置信息
            if not bboxes:
                # 遍历图片，使用图像索引来估计位置
                # 这不是最准确的方法，但可以提供一些信息
                pass
                
        except Exception as e:
            print(f"获取图片位置失败: {e}")
        
        return bboxes
    
    def _extract_image_references(self, page: fitz.Page, page_num: int, images: List[ImageInfo]) -> List[ImageReference]:
        """
        提取页面中的图片引用
        
        Args:
            page: fitz页面对象
            page_num: 页码
            images: 当前页面的图片列表
            
        Returns:
            图片引用列表
        """
        references = []
        
        try:
            # 获取页面所有文本
            text_dict = page.get_text("dict")
            
            # 遍历所有文本块
            for block in text_dict["blocks"]:
                if block.get("type") != 0:  # 跳过非文本块
                    continue
                
                text = block.get("text", "").strip()
                bbox = block["bbox"]
                
                # 检查所有引用模式
                for pattern in self.REFERENCE_PATTERNS:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        ref_text = match.group()
                        
                        # 尝试匹配图片编号
                        image_id = self._match_reference_to_image(ref_text, images)
                        if image_id:
                            ref = ImageReference(
                                ref_text=ref_text,
                                image_id=image_id,
                                page=page_num + 1,
                                bbox=[bbox[0], bbox[1], bbox[2], bbox[3]]
                            )
                            references.append(ref)
            
        except Exception as e:
            print(f"提取图片引用失败: {e}")
        
        return references
    
    def _match_reference_to_image(self, ref_text: str, images: List[ImageInfo]) -> Optional[str]:
        """
        将引用文本匹配到具体图片
        
        Args:
            ref_text: 引用文本，如"如图5-1所示"
            images: 图片列表
            
        Returns:
            匹配的图片ID，如果没有匹配则返回None
        """
        try:
            # 提取引用中的编号
            # 例如从"如图5-1所示"中提取"5-1"
            numbers = re.findall(r'[\d一二三四五六七八九十]+[\-‐–—][\d]+', ref_text)
            if not numbers:
                numbers = re.findall(r'[\d]+[\.．][\d]+', ref_text)
            if not numbers:
                numbers = re.findall(r'[\d]+', ref_text)
            
            if not numbers:
                return None
            
            ref_number = numbers[0]
            
            # 在图片的图注中查找匹配的编号
            for img in images:
                if img.caption:
                    # 从图注中提取编号
                    caption_numbers = re.findall(r'[\d一二三四五六七八九十]+[\-‐–—][\d]+', img.caption)
                    if not caption_numbers:
                        caption_numbers = re.findall(r'[\d]+[\.．][\d]+', img.caption)
                    if not caption_numbers:
                        caption_numbers = re.findall(r'[\d]+', img.caption)
                    
                    if caption_numbers and caption_numbers[0] == ref_number:
                        return img.image_id
            
            # 如果图注中没有编号，尝试使用索引匹配
            ref_num = re.sub(r'[^\d]', '', ref_number)
            if ref_num.isdigit():
                idx = int(ref_num) - 1
                if 0 <= idx < len(images):
                    return images[idx].image_id
            
            return None
            
        except Exception as e:
            print(f"匹配图片引用失败: {e}")
            return None
    
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
