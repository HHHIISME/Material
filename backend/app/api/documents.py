"""
文档解析API路由
支持PDF、Word等文档的解析
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from typing import Optional
import io

from app.services.pdf_parser import pdf_parser


router = APIRouter(prefix="/documents", tags=["文档解析"])


@router.post("/parse/pdf")
async def parse_pdf(
    file: UploadFile = File(...),
    extract_images: bool = Form(True),
    extract_tables: bool = Form(True),
    start_page: int = Form(0),
    end_page: Optional[int] = Form(None)
):
    """
    解析PDF文件
    
    支持文本提取、图片提取和表格提取
    """
    # 检查文件类型
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    try:
        # 读取文件内容
        file_bytes = await file.read()
        
        # 创建自定义解析器
        from app.services.pdf_parser import PDFParser
        parser = PDFParser(
            extract_images=extract_images,
            extract_tables=extract_tables
        )
        
        # 解析PDF - 只使用file_bytes，不传递file_path避免路径问题
        result = parser.parse_pdf(
            file_bytes=file_bytes,
            start_page=start_page,
            end_page=end_page
        )
        # 设置文件名用于显示
        result.filename = file.filename
        
        # 不返回图片二进制数据，只返回元信息
        for page in result.pages:
            for img in page.images:
                img.pop("image_bytes", None)
        
        return result.model_dump()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF解析失败: {str(e)}")


@router.post("/parse/pdf/text")
async def parse_pdf_text(file: UploadFile = File(...)):
    """
    仅提取PDF文本内容
    
    适用于只需要文本内容的场景
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    try:
        file_bytes = await file.read()
        text = pdf_parser.extract_text_only(file_bytes=file_bytes)
        
        return {
            "filename": file.filename,
            "text": text,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文本提取失败: {str(e)}")


@router.post("/parse/pdf/preview/{page_num}")
async def get_pdf_page_preview(
    file: UploadFile = File(...),
    page_num: int = 0,
    zoom: float = Form(2.0)
):
    """
    获取PDF页面预览图片
    
    将指定页面渲染为PNG图片
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    try:
        file_bytes = await file.read()
        img_bytes = pdf_parser.get_page_image(
            file_bytes=file_bytes,
            page_num=page_num,
            zoom=zoom
        )
        
        if img_bytes is None:
            raise HTTPException(status_code=404, detail="页面不存在")
        
        return Response(
            content=img_bytes,
            media_type="image/png"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"页面渲染失败: {str(e)}")


@router.post("/parse/pdf/images")
async def extract_pdf_images(file: UploadFile = File(...)):
    """
    提取PDF中的所有图片
    
    返回图片列表及其位置信息
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    try:
        file_bytes = await file.read()
        
        from app.services.pdf_parser import PDFParser
        parser = PDFParser(extract_images=True, extract_tables=False)
        result = parser.parse_pdf(file_bytes=file_bytes, file_path=file.filename)
        
        # 收集所有图片
        all_images = []
        for page in result.pages:
            for img in page.images:
                img_info = {
                    "page": img["page"],
                    "index": img["index"],
                    "width": img["width"],
                    "height": img["height"],
                    "format": img["ext"]
                }
                all_images.append(img_info)
        
        return {
            "filename": file.filename,
            "total_images": len(all_images),
            "images": all_images
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片提取失败: {str(e)}")


@router.get("/health")
async def documents_health():
    """
    文档解析服务健康检查
    """
    return {
        "status": "ok",
        "services": {
            "pdf_parser": "available",
            "supported_formats": ["pdf"]
        }
    }
