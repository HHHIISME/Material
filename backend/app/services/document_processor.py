"""
文档处理服务 - 建立图片与知识点的关联
"""
import re
import uuid
from typing import Optional
from app.models.document import (
    Document, PageContent, TextChunk, ImageInfo, TableInfo, BoundingBox
)


class DocumentProcessor:
    """文档处理器 - 解析PDF并建立关联"""
    
    # 图注正则模式
    CAPTION_PATTERNS = [
        r"图\s*(\d+[-‐–—]\d+)\s*(.+?)(?=\n|$)",  # 图5-1 描述
        r"Fig\.\s*(\d+[-‐–—]\d+)\s*(.+?)(?=\n|$)",  # Fig.5-1 description
        r"图\s*(\d+\.?\d*)\s*(.+?)(?=\n|$)",  # 图5.1 描述
    ]
    
    # 交叉引用正则模式
    REFERENCE_PATTERNS = [
        r"如[图图]\s*(\d+[-‐–—]\d+)[所示]",
        r"见图\s*(\d+[-‐–—]\d+)",
        r"如图\s*(\d+[-‐–—]\d+)",
        r"\(图\s*(\d+[-‐–—]\d+)\)",
    ]
    
    def __init__(self):
        pass
    
    def process_pdf(self, pdf_path: str, extract_images: bool = True) -> Document:
        """
        处理PDF文档，提取内容并建立关联
        
        Args:
            pdf_path: PDF文件路径
            extract_images: 是否提取图片
            
        Returns:
            Document对象，包含所有内容和关联关系
        """
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        document = Document(
            id=str(uuid.uuid4()),
            filename=pdf_path.split("/")[-1].split("\\")[-1],
            total_pages=len(doc),
            pages=[]
        )
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_content = self._process_page(page, page_num, extract_images)
            document.pages.append(page_content)
        
        # 建立跨页关联
        self._build_cross_page_relations(document)
        
        doc.close()
        return document
    
    def _process_page(self, page, page_num: int, extract_images: bool) -> PageContent:
        """处理单页"""
        page_content = PageContent(page_num=page_num)
        
        # 1. 提取文本块
        text_dict = page.get_text("dict")
        current_text = ""
        current_bbox = None
        chunk_id = f"chunk_{page_num}_001"
        
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # 文本块
                block_text = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        block_text += span.get("text", "")
                    block_text += "\n"
                
                if block_text.strip():
                    bbox = block.get("bbox", (0, 0, 0, 0))
                    page_content.text_chunks.append(TextChunk(
                        id=f"chunk_{page_num}_{len(page_content.text_chunks)+1:03d}",
                        page_num=page_num,
                        text=block_text.strip(),
                        bbox=BoundingBox(*bbox)
                    ))
        
        # 2. 提取图片
        if extract_images:
            images = page.get_images()
            for img_index, img in enumerate(images):
                img_info = self._extract_image_info(page, img, img_index, page_num)
                if img_info:
                    page_content.images.append(img_info)
        
        # 3. 提取表格（简化版，实际需要更复杂的表格检测）
        # TODO: 使用 pdfplumber 或 camelot 进行表格提取
        
        # 4. 建立页面内关联
        self._build_page_relations(page_content)
        
        return page_content
    
    def _extract_image_info(self, page, img, img_index: int, page_num: int) -> Optional[ImageInfo]:
        """提取图片信息"""
        try:
            xref = img[0]
            pix = fitz.Pixmap(page.parent, xref)
            
            if pix.n < 5:  # 正常图片
                img_id = f"img_{page_num}_{img_index+1:03d}"
                bbox_list = page.get_image_bbox(img)
                bbox = BoundingBox(
                    x0=bbox_list.x0,
                    y0=bbox_list.y0,
                    x1=bbox_list.x1,
                    y1=bbox_list.y1
                )
                
                # 尝试提取图注
                caption = self._find_image_caption(page, bbox)
                
                return ImageInfo(
                    id=img_id,
                    page_num=page_num,
                    bbox=bbox,
                    caption=caption
                )
        except Exception as e:
            print(f"提取图片失败: {e}")
        return None
    
    def _find_image_caption(self, page, img_bbox: BoundingBox) -> Optional[str]:
        """
        查找图片的图注
        通常图注在图片下方，格式如"图5-1 描述"
        """
        text_dict = page.get_text("dict")
        
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # 文本块
                bbox = block.get("bbox", (0, 0, 0, 0))
                text = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text += span.get("text", "")
                
                # 检查是否在图片下方（y坐标大于图片底部）
                if bbox[1] > img_bbox.y1 and bbox[1] < img_bbox.y1 + 50:
                    # 检查是否匹配图注模式
                    for pattern in self.CAPTION_PATTERNS:
                        match = re.search(pattern, text)
                        if match:
                            return text.strip()
        
        return None
    
    def _build_page_relations(self, page_content: PageContent):
        """建立页面内关联"""
        # 方法1: 基于位置的关联 - 图片与上方最近的文本块关联
        for image in page_content.images:
            # 找到图片上方最近的文本块
            for chunk in page_content.text_chunks:
                # 检查文本块是否在图片上方
                if (chunk.bbox.y1 <= image.bbox.y0 and  # 文本在图片上方
                    abs(chunk.bbox.y1 - image.bbox.y0) < 100):  # 距离小于100
                    
                    # 检查水平重叠
                    if (chunk.bbox.x0 < image.bbox.x1 and 
                        chunk.bbox.x1 > image.bbox.x0):
                        image.related_chunk_ids.append(chunk.id)
                        chunk.related_image_ids.append(image.id)
        
        # 方法2: 基于交叉引用的关联 - "如图5-1所示"
        for chunk in page_content.text_chunks:
            for pattern in self.REFERENCE_PATTERNS:
                matches = re.finditer(pattern, chunk.text)
                for match in matches:
                    ref_id = match.group(1)  # 如 "5-1"
                    # 查找对应图注的图片
                    for image in page_content.images:
                        if image.caption and ref_id in image.caption:
                            if chunk.id not in image.related_chunk_ids:
                                image.related_chunk_ids.append(chunk.id)
                            if image.id not in chunk.related_image_ids:
                                chunk.related_image_ids.append(image.id)
    
    def _build_cross_page_relations(self, document: Document):
        """建立跨页关联"""
        # 处理跨页的图注引用
        all_images = {}
        for page in document.pages:
            for image in page.images:
                if image.caption:
                    # 从图注中提取编号
                    for pattern in self.CAPTION_PATTERNS:
                        match = re.search(pattern, image.caption)
                        if match:
                            img_num = match.group(1)  # 如 "5-1"
                            all_images[img_num] = image
        
        # 在所有文本中查找引用
        for page in document.pages:
            for chunk in page.text_chunks:
                for pattern in self.REFERENCE_PATTERNS:
                    matches = re.finditer(pattern, chunk.text)
                    for match in matches:
                        ref_id = match.group(1)
                        if ref_id in all_images:
                            image = all_images[ref_id]
                            if chunk.id not in image.related_chunk_ids:
                                image.related_chunk_ids.append(chunk.id)
                            if image.id not in chunk.related_image_ids:
                                chunk.related_image_ids.append(image.id)


# 使用示例
if __name__ == "__main__":
    processor = DocumentProcessor()
    doc = processor.process_pdf("test.pdf")
    
    # 打印关联关系
    for page in doc.pages:
        print(f"\n=== 第 {page.page_num} 页 ===")
        for img in page.images:
            print(f"图片 {img.id}:")
            print(f"  图注: {img.caption}")
            print(f"  关联文本块: {img.related_chunk_ids}")
        for chunk in page.text_chunks:
            if chunk.related_image_ids:
                print(f"文本块 {chunk.id} 关联图片: {chunk.related_image_ids}")
