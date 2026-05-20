"""
智谱AI API路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict

from app.services.zhipu_service import zhipu_service


router = APIRouter(prefix="/zhipu", tags=["智谱AI"])


class ChatRequest(BaseModel):
    """对话请求模型"""
    message: str
    model: str = "glm-4-flash"
    system_prompt: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None
    temperature: float = 0.7
    max_tokens: int = 1024


class EmbedRequest(BaseModel):
    """嵌入请求模型"""
    text: str
    model: str = "embedding-3"


class BatchEmbedRequest(BaseModel):
    """批量嵌入请求模型"""
    texts: List[str]
    model: str = "embedding-3"


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    智谱AI对话接口
    
    支持多轮对话和自定义系统提示词
    """
    result = zhipu_service.chat(
        message=request.message,
        model=request.model,
        system_prompt=request.system_prompt,
        history=request.history,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/embed")
async def embed(request: EmbedRequest):
    """
    文本嵌入接口
    
    将文本转换为向量表示
    """
    result = zhipu_service.embed(
        text=request.text,
        model=request.model
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/embed/batch")
async def batch_embed(request: BatchEmbedRequest):
    """
    批量文本嵌入接口
    
    将多个文本转换为向量表示
    """
    result = zhipu_service.batch_embed(
        texts=request.texts,
        model=request.model
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.get("/models")
async def list_models():
    """
    列出支持的模型
    """
    return {
        "chat_models": [
            {"name": "glm-4-flash", "description": "GLM-4 Flash模型，免费，快速响应"},
            {"name": "glm-4", "description": "GLM-4标准模型，更强的能力"},
            {"name": "glm-4-plus", "description": "GLM-4 Plus模型，最强能力"}
        ],
        "embedding_models": [
            {"name": "embedding-3", "description": "智谱Embedding-3模型，支持2048维度"},
            {"name": "embedding-2", "description": "智谱Embedding-2模型"}
        ]
    }
