"""
意图识别服务 - 基于AutoGen实现双意图分类
支持的意图类型：多维度穿搭打分、穿搭推荐
"""

import os
import json
import time
from typing import Dict, List, Optional, Any, Union, Literal
from loguru import logger
import autogen
from pydantic import BaseModel

from app.core.config import settings
from app.models.schemas import IntentRequest, IntentResponse


class IntentService:
    """意图识别服务 - 基于AutoGen实现双意图分类"""
    
    def __init__(self):
        """初始化意图识别服务"""
        # 配置LLM
        self.config_list = [
            {
                "model": settings.QWEN_MODEL_NAME,
                "api_key": settings.QWEN_API_KEY,
                "api_base": settings.QWEN_API_BASE,
            }
        ]
        
        # 创建意图识别Agent
        self.intent_agent = autogen.AssistantAgent(
            name="意图识别Agent",
            llm_config={"config_list": self.config_list},
            system_message=self._get_intent_system_prompt()
        )
        
        # 创建用户代理
        self.user_proxy = autogen.UserProxyAgent(
            name="用户代理",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config=False,
        )
    
    def _get_intent_system_prompt(self) -> str:
        """获取意图识别系统提示词"""
        return """你是一个专业的意图识别Agent，负责判断用户的真实需求意图。
        
你的任务是分析用户的输入（文本和/或图像描述），并确定用户的意图属于以下两种类型之一：
1. outfit_scoring：用户希望对穿搭进行评分、分析或评价
2. outfit_recommendation：用户希望获取穿搭建议、搭配推荐或风格指导

请根据用户输入的内容，判断用户最可能的意图，并以JSON格式返回结果，包含以下字段：
- intent_type: 意图类型，必须是"outfit_scoring"或"outfit_recommendation"之一
- confidence: 置信度，0.0-1.0之间的浮点数
- reasoning: 推理过程，解释为什么判断为该意图类型

请注意：
- 如果用户明确表达了希望对穿搭进行评价、打分、分析，判断为"outfit_scoring"
- 如果用户明确表达了希望获取穿搭建议、搭配推荐，判断为"outfit_recommendation"
- 如果用户输入模糊，请根据上下文和关键词判断最可能的意图
- 你的回复必须是有效的JSON格式，不要包含任何其他文本

示例输出：
```json
{
  "intent_type": "outfit_scoring",
  "confidence": 0.95,
  "reasoning": "用户明确要求对他的穿搭进行评分和分析，使用了'打分'、'评价'等关键词，表明他希望获得对当前穿搭的评价而非推荐新的穿搭。"
}
```
"""
    
    async def detect_intent(self, request: IntentRequest) -> IntentResponse:
        """检测用户意图"""
        start_time = time.time()
        
        # 构建用户消息
        user_message = f"用户消息: {request.message}"
        if request.image_path:
            user_message += f"\n\n图片描述: 用户上传了一张穿搭照片，路径为 {request.image_path}"
        
        # 使用AutoGen进行意图识别
        try:
            # 发送消息给意图识别Agent
            self.user_proxy.initiate_chat(
                self.intent_agent,
                message=user_message
            )
            
            # 获取意图识别结果
            response_message = self.intent_agent.last_message()["content"]
            
            # 解析JSON响应
            json_start = response_message.find('{')
            json_end = response_message.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_message[json_start:json_end]
                result = json.loads(json_str)
            else:
                # 如果无法解析JSON，使用默认值
                logger.error(f"无法从响应中解析JSON: {response_message}")
                result = {
                    "intent_type": "outfit_scoring",
                    "confidence": 0.5,
                    "reasoning": "无法确定用户意图，默认为穿搭评分。"
                }
            
            # 构建响应
            intent_response = IntentResponse(
                intent_type=result.get("intent_type", "outfit_scoring"),
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", ""),
                raw_content=response_message
            )
            
            logger.info(f"意图识别完成，耗时: {time.time() - start_time:.2f}秒，结果: {intent_response.intent_type}，置信度: {intent_response.confidence}")
            return intent_response
            
        except Exception as e:
            logger.error(f"意图识别失败: {str(e)}")
            # 返回默认响应
            return IntentResponse(
                intent_type="outfit_scoring",
                confidence=0.5,
                reasoning=f"意图识别过程中发生错误: {str(e)}",
                raw_content=None
            )
    
    def _mock_intent_detection(self, request: IntentRequest) -> IntentResponse:
        """模拟意图识别（用于开发测试）"""
        # 关键词匹配
        scoring_keywords = ["评分", "打分", "分析", "评价", "怎么样", "好看吗", "搭配得如何"]
        recommendation_keywords = ["推荐", "建议", "搭配", "穿什么", "怎么穿", "如何搭配", "搭什么"]
        
        # 计算匹配度
        scoring_score = sum(1 for kw in scoring_keywords if kw in request.message)
        recommendation_score = sum(1 for kw in recommendation_keywords if kw in request.message)
        
        # 确定意图类型
        if scoring_score > recommendation_score:
            intent_type = "outfit_scoring"
            confidence = min(0.5 + scoring_score * 0.1, 0.95)
            reasoning = f"用户消息中包含评分相关关键词，可能希望对穿搭进行评价。匹配关键词数: {scoring_score}"
        elif recommendation_score > scoring_score:
            intent_type = "outfit_recommendation"
            confidence = min(0.5 + recommendation_score * 0.1, 0.95)
            reasoning = f"用户消息中包含推荐相关关键词，可能希望获取穿搭建议。匹配关键词数: {recommendation_score}"
        else:
            # 默认为评分
            intent_type = "outfit_scoring"
            confidence = 0.6
            reasoning = "无法明确判断用户意图，默认为穿搭评分。"
        
        return IntentResponse(
            intent_type=intent_type,
            confidence=confidence,
            reasoning=reasoning,
            raw_content=None
        )


# 创建意图识别服务实例
intent_service = IntentService()