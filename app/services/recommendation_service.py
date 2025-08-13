"""
穿搭推荐Agent - 基于AutoGen实现
"""

import os
import json
import time
from typing import Dict, List, Optional, Any, Union
from loguru import logger
import autogen

from app.core.config import settings
from app.models.schemas import OutfitRecommendation, OutfitItem


class RecommendationAgent:
    """穿搭推荐Agent"""
    
    def __init__(self):
        """初始化穿搭推荐Agent"""
        # 配置LLM
        self.config_list = [
            {
                "model": settings.QWEN_MODEL_NAME,
                "api_key": settings.QWEN_API_KEY,
                "api_base": settings.QWEN_API_BASE,
            }
        ]
        
        # 创建穿搭推荐Agent
        self.recommendation_agent = autogen.AssistantAgent(
            name="穿搭推荐Agent",
            llm_config={"config_list": self.config_list},
            system_message=self._get_recommendation_system_prompt()
        )
        
        # 创建用户代理
        self.user_proxy = autogen.UserProxyAgent(
            name="用户代理",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config=False,
        )
    
    def _get_recommendation_system_prompt(self) -> str:
        """获取穿搭推荐系统提示词"""
        return """你是一个专业的穿搭推荐Agent，负责为用户提供个性化的穿搭建议。

你的任务是根据用户的需求、偏好和参考图片（如果有），提供详细的穿搭推荐，包括：
1. 具体单品推荐：上衣、下装、鞋履、配饰等
2. 风格描述：推荐穿搭的整体风格和特点
3. 场合适宜性：适合的场合和活动
4. 预算估计：各单品和整体的预算范围
5. 搭配技巧：如何穿着和搭配这些单品

请以JSON格式返回推荐结果，包含以下字段：
- outfit_items: 穿搭单品列表，每个单品包含item_type(类型)、description(描述)、color(颜色)、style(风格)、estimated_price_range(预算范围)、brand_suggestions(品牌建议)
- style_description: 整体风格描述
- occasion_suitability: 适合场合列表
- estimated_total_budget: 总预算范围
- styling_tips: 搭配技巧和建议列表

请注意：
- 推荐要符合用户的偏好和需求
- 考虑用户提供的场合、季节、预算等信息
- 提供具体、可操作的搭配建议
- 你的回复必须是有效的JSON格式，不要包含任何其他文本

示例输出：
```json
{
  "outfit_items": [
    {
      "item_type": "上衣",
      "description": "浅蓝色牛津纺衬衫，修身剪裁，带有细微条纹",
      "color": "浅蓝色",
      "style": "商务休闲",
      "estimated_price_range": {"min": 300, "max": 600},
      "brand_suggestions": ["优衣库", "Gap", "无印良品"]
    },
    {
      "item_type": "下装",
      "description": "深卡其色修身休闲裤，直筒剪裁",
      "color": "深卡其色",
      "style": "商务休闲",
      "estimated_price_range": {"min": 400, "max": 800},
      "brand_suggestions": ["优衣库", "H&M", "Zara"]
    },
    {
      "item_type": "鞋履",
      "description": "棕色皮革德比鞋，圆头设计",
      "color": "棕色",
      "style": "商务休闲",
      "estimated_price_range": {"min": 600, "max": 1200},
      "brand_suggestions": ["Clarks", "Ecco", "Geox"]
    },
    {
      "item_type": "配饰",
      "description": "深棕色皮带，简约金属扣",
      "color": "深棕色",
      "style": "商务休闲",
      "estimated_price_range": {"min": 200, "max": 500},
      "brand_suggestions": ["优衣库", "Zara", "H&M"]
    }
  ],
  "style_description": "这是一套商务休闲风格的穿搭，色彩协调，既正式又不失休闲感，适合日常办公和轻商务场合。",
  "occasion_suitability": ["办公室日常", "商务会议", "休闲聚会", "周末约会"],
  "estimated_total_budget": {"min": 1500, "max": 3100},
  "styling_tips": [
    "衬衫可以卷起袖子增加休闲感",
    "衬衫下摆可以塞入裤子增加整洁感",
    "可以添加简约手表提升整体质感",
    "鞋子和皮带颜色应该协调一致"
  ]
}
```
"""
    
    async def get_recommendation(
        self,
        user_id: Optional[str] = None,
        occasion: Optional[str] = None,
        style_preference: Optional[str] = None,
        color_preference: Optional[List[str]] = None,
        budget_range: Optional[Dict[str, float]] = None,
        season: Optional[str] = None,
        reference_image_path: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> OutfitRecommendation:
        """获取穿搭推荐"""
        start_time = time.time()
        
        # 构建用户消息
        user_message = "请为我推荐一套穿搭。"
        
        # 添加场合信息
        if occasion:
            user_message += f"\n\n场合: {occasion}"
        
        # 添加风格偏好
        if style_preference:
            user_message += f"\n\n风格偏好: {style_preference}"
        
        # 添加颜色偏好
        if color_preference:
            user_message += f"\n\n颜色偏好: {', '.join(color_preference)}"
        
        # 添加预算范围
        if budget_range:
            user_message += f"\n\n预算范围: {budget_range}"
        
        # 添加季节信息
        if season:
            user_message += f"\n\n季节: {season}"
        
        # 添加参考图片
        if reference_image_path:
            user_message += f"\n\n参考图片路径: {reference_image_path}"
        
        # 添加用户偏好信息
        if preferences:
            user_message += "\n\n用户偏好信息:"
            for key, value in preferences.items():
                if value:
                    user_message += f"\n- {key}: {value}"
        
        # 使用AutoGen进行穿搭推荐
        try:
            # 发送消息给穿搭推荐Agent
            self.user_proxy.initiate_chat(
                self.recommendation_agent,
                message=user_message
            )
            
            # 获取穿搭推荐结果
            response_message = self.recommendation_agent.last_message()["content"]
            
            # 解析JSON响应
            json_start = response_message.find('{')
            json_end = response_message.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_message[json_start:json_end]
                result = json.loads(json_str)
            else:
                # 如果无法解析JSON，使用默认值
                logger.error(f"无法从响应中解析JSON: {response_message}")
                result = self._get_default_recommendation_result()
            
            # 构建穿搭单品对象
            outfit_items = []
            for item_data in result.get("outfit_items", []):
                outfit_items.append(OutfitItem(
                    item_type=item_data.get("item_type", "未知"),
                    description=item_data.get("description", "无描述"),
                    color=item_data.get("color", "未知"),
                    style=item_data.get("style", "未知"),
                    estimated_price_range=item_data.get("estimated_price_range"),
                    brand_suggestions=item_data.get("brand_suggestions", [])
                ))
            
            # 构建响应
            recommendation_response = OutfitRecommendation(
                outfit_items=outfit_items,
                style_description=result.get("style_description", "无风格描述"),
                occasion_suitability=result.get("occasion_suitability", ["未知"]),
                estimated_total_budget=result.get("estimated_total_budget"),
                styling_tips=result.get("styling_tips", ["无搭配技巧"]),
                user_id=user_id
            )
            
            logger.info(f"穿搭推荐完成，耗时: {time.time() - start_time:.2f}秒，推荐单品数: {len(outfit_items)}")
            return recommendation_response
            
        except Exception as e:
            logger.error(f"穿搭推荐失败: {str(e)}")
            # 返回默认响应
            return self._get_default_recommendation_response(user_id)
    
    def _get_default_recommendation_result(self) -> Dict[str, Any]:
        """获取默认推荐结果"""
        return {
            "outfit_items": [
                {
                    "item_type": "上衣",
                    "description": "白色纯棉T恤，简约圆领设计",
                    "color": "白色",
                    "style": "休闲",
                    "estimated_price_range": {"min": 100, "max": 300},
                    "brand_suggestions": ["优衣库", "H&M", "无印良品"]
                },
                {
                    "item_type": "下装",
                    "description": "深蓝色直筒牛仔裤，经典五袋款式",
                    "color": "深蓝色",
                    "style": "休闲",
                    "estimated_price_range": {"min": 200, "max": 500},
                    "brand_suggestions": ["优衣库", "Levi's", "Gap"]
                },
                {
                    "item_type": "鞋履",
                    "description": "白色低帮帆布鞋，简约百搭",
                    "color": "白色",
                    "style": "休闲",
                    "estimated_price_range": {"min": 200, "max": 400},
                    "brand_suggestions": ["匡威", "万斯", "无印良品"]
                }
            ],
            "style_description": "这是一套基础休闲风格的穿搭，简约百搭，适合日常休闲场合。",
            "occasion_suitability": ["日常休闲", "购物", "朋友聚会"],
            "estimated_total_budget": {"min": 500, "max": 1200},
            "styling_tips": [
                "T恤可以选择宽松版型增加休闲感",
                "牛仔裤可以卷起裤脚展现个性",
                "可以添加简约配饰如手表或项链提升整体感"
            ]
        }
    
    def _get_default_recommendation_response(self, user_id: Optional[str] = None) -> OutfitRecommendation:
        """获取默认推荐响应"""
        default_result = self._get_default_recommendation_result()
        
        # 构建穿搭单品对象
        outfit_items = []
        for item_data in default_result.get("outfit_items", []):
            outfit_items.append(OutfitItem(
                item_type=item_data.get("item_type", "未知"),
                description=item_data.get("description", "无描述"),
                color=item_data.get("color", "未知"),
                style=item_data.get("style", "未知"),
                estimated_price_range=item_data.get("estimated_price_range"),
                brand_suggestions=item_data.get("brand_suggestions", [])
            ))
        
        return OutfitRecommendation(
            outfit_items=outfit_items,
            style_description=default_result.get("style_description", "无风格描述"),
            occasion_suitability=default_result.get("occasion_suitability", ["未知"]),
            estimated_total_budget=default_result.get("estimated_total_budget"),
            styling_tips=default_result.get("styling_tips", ["无搭配技巧"]),
            user_id=user_id
        )
    
    def _mock_recommendation_result(self, user_id: Optional[str] = None) -> OutfitRecommendation:
        """模拟推荐结果（用于开发测试）"""
        outfit_items = [
            OutfitItem(
                item_type="上衣",
                description="浅蓝色牛津纺衬衫，修身剪裁，带有细微条纹",
                color="浅蓝色",
                style="商务休闲",
                estimated_price_range={"min": 300, "max": 600},
                brand_suggestions=["优衣库", "Gap", "无印良品"]
            ),
            OutfitItem(
                item_type="下装",
                description="深卡其色修身休闲裤，直筒剪裁",
                color="深卡其色",
                style="商务休闲",
                estimated_price_range={"min": 400, "max": 800},
                brand_suggestions=["优衣库", "H&M", "Zara"]
            ),
            OutfitItem(
                item_type="鞋履",
                description="棕色皮革德比鞋，圆头设计",
                color="棕色",
                style="商务休闲",
                estimated_price_range={"min": 600, "max": 1200},
                brand_suggestions=["Clarks", "Ecco", "Geox"]
            ),
            OutfitItem(
                item_type="配饰",
                description="深棕色皮带，简约金属扣",
                color="深棕色",
                style="商务休闲",
                estimated_price_range={"min": 200, "max": 500},
                brand_suggestions=["优衣库", "Zara", "H&M"]
            )
        ]
        
        return OutfitRecommendation(
            outfit_items=outfit_items,
            style_description="这是一套商务休闲风格的穿搭，色彩协调，既正式又不失休闲感，适合日常办公和轻商务场合。",
            occasion_suitability=["办公室日常", "商务会议", "休闲聚会", "周末约会"],
            estimated_total_budget={"min": 1500, "max": 3100},
            styling_tips=[
                "衬衫可以卷起袖子增加休闲感",
                "衬衫下摆可以塞入裤子增加整洁感",
                "可以添加简约手表提升整体质感",
                "鞋子和皮带颜色应该协调一致"
            ],
            user_id=user_id
        )


# 创建穿搭推荐Agent实例
recommendation_service = RecommendationAgent()