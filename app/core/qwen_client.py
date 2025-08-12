import base64
import json
from typing import Dict, List, Optional, Any, Union
import httpx
import asyncio
from loguru import logger
from PIL import Image
import io
import os

from app.core.config import settings


class QwenVLClient:
    """Qwen-VL-Chat API客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model_version: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.api_key = api_key or settings.QWEN_API_KEY
        self.api_base = api_base or settings.QWEN_API_BASE
        self.model_version = model_version or settings.QWEN_MODEL_VERSION
        self.timeout = timeout or settings.QWEN_API_TIMEOUT
        
        # 验证API密钥是否存在
        if not self.api_key and not settings.DEBUG:
            logger.warning("Qwen API密钥未设置，API调用将失败")
    
    async def _encode_image(self, image_path: str) -> str:
        """将图像编码为base64字符串"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图像文件不存在: {image_path}")
        
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    async def _encode_image_from_bytes(self, image_bytes: bytes) -> str:
        """将图像字节编码为base64字符串"""
        return base64.b64encode(image_bytes).decode("utf-8")
    
    async def _prepare_messages(
        self, 
        prompt: str, 
        image_path: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """准备API请求消息"""
        messages = []
        
        # 添加历史消息
        if history:
            messages.extend(history)
        
        # 如果有图像，添加图像消息
        if image_path or image_bytes:
            image_content = {
                "role": "user",
                "content": [
                    {"text": "这是一张穿搭照片，请分析"}
                ]
            }
            
            # 添加图像内容
            if image_path:
                base64_image = await self._encode_image(image_path)
                image_content["content"].append({
                    "image": base64_image
                })
            elif image_bytes:
                base64_image = await self._encode_image_from_bytes(image_bytes)
                image_content["content"].append({
                    "image": base64_image
                })
                
            messages.append(image_content)
        
        # 添加当前提示消息
        messages.append({
            "role": "user",
            "content": [{"text": prompt}]
        })
        
        return messages
    
    async def _prepare_request_payload(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = None,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """准备API请求负载"""
        return {
            "model": self.model_version,
            "messages": messages,
            "temperature": temperature or settings.QWEN_TEMPERATURE,
            "max_tokens": max_tokens or settings.QWEN_MAX_TOKENS,
        }
    
    async def analyze_outfit(
        self,
        image_path: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        prompt: str = "请详细分析这张穿搭照片，包括服装类型、颜色搭配、风格特点，并给出多维度评分和改进建议。",
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = None,
        max_tokens: int = None,
    ) -> Dict[str, Any]:
        """分析穿搭照片"""
        if not image_path and not image_bytes:
            raise ValueError("必须提供image_path或image_bytes参数")
        
        try:
            # 准备消息
            messages = await self._prepare_messages(
                prompt=prompt,
                image_path=image_path,
                image_bytes=image_bytes,
                history=history
            )
            
            # 准备请求负载
            payload = await self._prepare_request_payload(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 如果处于调试模式且没有API密钥，返回模拟响应
            if settings.DEBUG and not self.api_key:
                logger.info("使用模拟响应进行开发")
                return self._get_mock_response()
            
            # 发送API请求
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/services/aigc/multimodal-generation/generation",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"API请求失败: {response.status_code} - {response.text}")
                    raise Exception(f"API请求失败: {response.status_code}")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"分析穿搭时出错: {str(e)}")
            if settings.DEBUG:
                return self._get_mock_response()
            raise
    
    def _get_mock_response(self) -> Dict[str, Any]:
        """获取模拟响应用于开发"""
        return {
            "output": {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": """
# 穿搭分析报告

## 服装组成
- 上装：黑色圆领T恤，简约基础款
- 下装：浅蓝色直筒牛仔裤，高腰设计
- 鞋履：白色简约运动鞋
- 配饰：银色细链项链，简约手表

## 颜色搭配
黑色上衣与浅蓝色牛仔裤形成了经典的对比色搭配，白色鞋子增加了整体的平衡感，色彩搭配和谐自然。

## 风格特点
整体呈现出简约休闲的都市风格，既有日常实用性，又不失时尚感。属于百搭易驾驭的基础穿搭。

## 多维度评分

| 维度 | 评分 | 评价 |
|------|------|------|
| 颜色搭配协调性 | 8/10 | 黑白蓝经典配色，和谐自然 |
| 风格协调性 | 9/10 | 各单品风格统一，整体协调 |
| 场合适宜性 | 8/10 | 适合日常、休闲、学习等场合 |
| 时尚度 | 7/10 | 经典款式，不过于前卫但也不落伍 |
| 个人特色 | 6/10 | 基础款搭配，个人特色不够突出 |
| 预算合理性 | 9/10 | 单品实用性高，性价比优良 |

## 总体评价
这是一套非常实用的日常穿搭，简约而不简单，适合多种场合。黑白蓝的经典配色使整体造型看起来干净利落，同时也便于搭配各种配饰。

## 改进建议
1. 可以添加一件亮色或图案的外套，增加层次感和个人特色
2. 考虑增加一些特色配饰，如个性帽子或特色包包
3. 鞋子可以尝试更有设计感的款式，提升整体时尚度
4. 可以在T恤选择上考虑一些有趣的图案或文字，展现个性

## 搭配推荐
基于您的风格，推荐以下单品搭配：
1. 牛仔外套 + 白色T恤 + 黑色裤装
2. 黑色T恤 + 格纹衬衫外套 + 当前牛仔裤
3. 当前上衣 + 工装裤 + 帆布鞋

希望这份分析对您有所帮助！
                            """
                        }
                    }
                ]
            },
            "usage": {
                "input_tokens": 120,
                "output_tokens": 450,
                "total_tokens": 570
            },
            "request_id": "mock-request-id"
        }


# 创建默认客户端实例
qwen_client = QwenVLClient()import json
from typing import Dict, List, Optional, Any, Union
import httpx
import asyncio
from loguru import logger
from PIL import Image
import io
import os

from app.core.config import settings


class QwenVLClient:
    """Qwen-VL-Chat API客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model_version: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.api_key = api_key or settings.QWEN_API_KEY
        self.api_base = api_base or settings.QWEN_API_BASE
        self.model_version = model_version or settings.QWEN_MODEL_VERSION
        self.timeout = timeout or settings.QWEN_API_TIMEOUT
        
        # 验证API密钥是否存在
        if not self.api_key and not settings.DEBUG:
            logger.warning("Qwen API密钥未设置，API调用将失败")
    
    async def _encode_image(self, image_path: str) -> str:
        """将图像编码为base64字符串"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图像文件不存在: {image_path}")
        
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    async def _encode_image_from_bytes(self, image_bytes: bytes) -> str:
        """将图像字节编码为base64字符串"""
        return base64.b64encode(image_bytes).decode("utf-8")
    
    async def _prepare_messages(
        self, 
        prompt: str, 
        image_path: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """准备API请求消息"""
        messages = []
        
        # 添加历史消息
        if history:
            messages.extend(history)
        
        # 如果有图像，添加图像消息
        if image_path or image_bytes:
            image_content = {
                "role": "user",
                "content": [
                    {"text": "这是一张穿搭照片，请分析"}
                ]
            }
            
            # 添加图像内容
            if image_path:
                base64_image = await self._encode_image(image_path)
                image_content["content"].append({
                    "image": base64_image
                })
            elif image_bytes:
                base64_image = await self._encode_image_from_bytes(image_bytes)
                image_content["content"].append({
                    "image": base64_image
                })
                
            messages.append(image_content)
        
        # 添加当前提示消息
        messages.append({
            "role": "user",
            "content": [{"text": prompt}]
        })
        
        return messages
    
    async def _prepare_request_payload(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = None,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """准备API请求负载"""
        return {
            "model": self.model_version,
            "messages": messages,
            "temperature": temperature or settings.QWEN_TEMPERATURE,
            "max_tokens": max_tokens or settings.QWEN_MAX_TOKENS,
        }
    
    async def analyze_outfit(
        self,
        image_path: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        prompt: str = "请详细分析这张穿搭照片，包括服装类型、颜色搭配、风格特点，并给出多维度评分和改进建议。",
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = None,
        max_tokens: int = None,
    ) -> Dict[str, Any]:
        """分析穿搭照片"""
        if not image_path and not image_bytes:
            raise ValueError("必须提供image_path或image_bytes参数")
        
        try:
            # 准备消息
            messages = await self._prepare_messages(
                prompt=prompt,
                image_path=image_path,
                image_bytes=image_bytes,
                history=history
            )
            
            # 准备请求负载
            payload = await self._prepare_request_payload(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 如果处于调试模式且没有API密钥，返回模拟响应
            if settings.DEBUG and not self.api_key:
                logger.info("使用模拟响应进行开发")
                return self._get_mock_response()
            
            # 发送API请求
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/services/aigc/multimodal-generation/generation",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"API请求失败: {response.status_code} - {response.text}")
                    raise Exception(f"API请求失败: {response.status_code}")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"分析穿搭时出错: {str(e)}")
            if settings.DEBUG:
                return self._get_mock_response()
            raise
    
    def _get_mock_response(self) -> Dict[str, Any]:
        """获取模拟响应用于开发"""
        return {
            "output": {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": """
# 穿搭分析报告

## 服装组成
- 上装：黑色圆领T恤，简约基础款
- 下装：浅蓝色直筒牛仔裤，高腰设计
- 鞋履：白色简约运动鞋
- 配饰：银色细链项链，简约手表

## 颜色搭配
黑色上衣与浅蓝色牛仔裤形成了经典的对比色搭配，白色鞋子增加了整体的平衡感，色彩搭配和谐自然。

## 风格特点
整体呈现出简约休闲的都市风格，既有日常实用性，又不失时尚感。属于百搭易驾驭的基础穿搭。

## 多维度评分

| 维度 | 评分 | 评价 |
|------|------|------|
| 颜色搭配协调性 | 8/10 | 黑白蓝经典配色，和谐自然 |
| 风格协调性 | 9/10 | 各单品风格统一，整体协调 |
| 场合适宜性 | 8/10 | 适合日常、休闲、学习等场合 |
| 时尚度 | 7/10 | 经典款式，不过于前卫但也不落伍 |
| 个人特色 | 6/10 | 基础款搭配，个人特色不够突出 |
| 预算合理性 | 9/10 | 单品实用性高，性价比优良 |

## 总体评价
这是一套非常实用的日常穿搭，简约而不简单，适合多种场合。黑白蓝的经典配色使整体造型看起来干净利落，同时也便于搭配各种配饰。

## 改进建议
1. 可以添加一件亮色或图案的外套，增加层次感和个人特色
2. 考虑增加一些特色配饰，如个性帽子或特色包包
3. 鞋子可以尝试更有设计感的款式，提升整体时尚度
4. 可以在T恤选择上考虑一些有趣的图案或文字，展现个性

## 搭配推荐
基于您的风格，推荐以下单品搭配：
1. 牛仔外套 + 白色T恤 + 黑色裤装
2. 黑色T恤 + 格纹衬衫外套 + 当前牛仔裤
3. 当前上衣 + 工装裤 + 帆布鞋

希望这份分析对您有所帮助！
                            """
                        }
                    }
                ]
            },
            "usage": {
                "input_tokens": 120,
                "output_tokens": 450,
                "total_tokens": 570
            },
            "request_id": "mock-request-id"
        }


# 创建默认客户端实例
qwen_client = QwenVLClient()