"""
智谱AI服务模块
提供GLM-4对话和Embedding功能
"""
import os
from typing import List, Optional, Dict, Any
from zhipuai import ZhipuAI


class ZhipuService:
    """智谱AI服务类"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化智谱AI客户端
        
        Args:
            api_key: API密钥，如果不提供则从环境变量获取
        """
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY", "")
        self._client = None
    
    @property
    def client(self) -> ZhipuAI:
        """延迟初始化客户端"""
        if self._client is None:
            if not self.api_key:
                raise ValueError("智谱API Key未配置，请检查.env文件中的ZHIPU_API_KEY")
            self._client = ZhipuAI(api_key=self.api_key)
        return self._client
    
    def chat(
        self, 
        message: str, 
        model: str = "glm-4-flash",
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        对话接口
        
        Args:
            message: 用户消息
            model: 模型名称，默认使用免费的glm-4-flash
            system_prompt: 系统提示词
            history: 历史对话记录
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            包含响应内容和元数据的字典
        """
        messages = []
        
        # 添加系统提示
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史对话
        if history:
            messages.extend(history)
        
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def embed(
        self, 
        text: str, 
        model: str = "embedding-3"
    ) -> Dict[str, Any]:
        """
        文本嵌入接口
        
        Args:
            text: 需要嵌入的文本
            model: 嵌入模型名称
            
        Returns:
            包含嵌入向量和元数据的字典
        """
        try:
            response = self.client.embeddings.create(
                model=model,
                input=text
            )
            
            return {
                "success": True,
                "embedding": response.data[0].embedding,
                "model": model,
                "dimension": len(response.data[0].embedding)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "embedding": None
            }
    
    def batch_embed(
        self, 
        texts: List[str], 
        model: str = "embedding-3"
    ) -> Dict[str, Any]:
        """
        批量文本嵌入接口
        
        Args:
            texts: 需要嵌入的文本列表
            model: 嵌入模型名称
            
        Returns:
            包含嵌入向量列表和元数据的字典
        """
        try:
            response = self.client.embeddings.create(
                model=model,
                input=texts
            )
            
            embeddings = [item.embedding for item in response.data]
            
            return {
                "success": True,
                "embeddings": embeddings,
                "model": model,
                "dimension": len(embeddings[0]) if embeddings else 0,
                "count": len(embeddings)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "embeddings": None
            }


# 创建全局实例
zhipu_service = ZhipuService()
