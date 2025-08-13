"""
多维度穿搭打分Agent - 基于AutoGen实现
"""

import os
import json
import time
from typing import Dict, List, Optional, Any, Union
from loguru import logger
import autogen

from app.core.config import settings
from app.models.schemas import OutfitAnalysisResponse, ScoreDimension


class ScoringAgent:
    """多维度穿搭打分Agent"""
    
    def __init__(self):
        """初始化多维度穿搭打分Agent"""
        # 配置LLM
        self.config_list = [
            {
                "model": settings.QWEN_MODEL_NAME,
                "api_key": settings.QWEN_API_KEY,
                "api_base": settings.QWEN_API_BASE,
            }
        ]
        
        # 创建穿搭打分Agent
        self.scoring_agent = autogen.AssistantAgent(
            name="穿搭打分Agent",
            llm_config={"config_list": self.config_list},
            system_message=self._get_scoring_system_prompt()
        )
        
        # 创建用户代理
        self.user_proxy = autogen.UserProxyAgent(
            name="用户代理",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config=False,
        )
    
    def _get_scoring_system_prompt(self) -> str:
        """获取穿搭打分系统提示词"""
        return """你是一个专业的穿搭评分Agent，负责对用户的穿搭进行多维度分析和评分。

你的任务是分析用户上传的穿搭照片，并提供以下信息：
1. 穿搭描述：详细描述上衣、下装、鞋履、配饰等组成部分
2. 颜色搭配：分析使用的颜色及其协调性
3. 风格类型：识别穿搭的整体风格（如商务、休闲、街头等）
4. 多维度评分（1-10分）：
   - 颜色搭配协调性
   - 风格协调性
   - 场合适宜性
   - 时尚度
   - 个人特色
   - 预算合理性（如果要求）
5. 总体评价：整体穿搭的优缺点
6. 改进建议：3-5条具体的优化建议

请以JSON格式返回分析结果，包含以下字段：
- outfit_description: 穿搭详细描述
- color_palette: 颜色列表
- style_type: 风格类型
- scores: 各维度评分对象，每个维度包含score(1-10分)、reasoning(评分理由)、improvement_suggestions(改进建议)
- overall_score: 总体评分(1-10分)
- improvement_suggestions: 整体改进建议列表

请注意：
- 评分要客观公正，基于时尚搭配原则
- 提供具体、可操作的改进建议
- 考虑用户的偏好信息（如果提供）
- 你的回复必须是有效的JSON格式，不要包含任何其他文本

示例输出：
```json
{
  "outfit_description": "这套穿搭由黑色修身西装外套、白色衬衫、深蓝色牛仔裤和棕色皮鞋组成，搭配简约黑色皮带。",
  "color_palette": ["黑色", "白色", "深蓝色", "棕色"],
  "style_type": "商务休闲",
  "scores": {
    "color_coordination": {
      "score": 8.5,
      "reasoning": "黑、白、蓝、棕的经典配色组合协调自然，色彩过渡平滑。",
      "improvement_suggestions": ["可以添加一个亮色口袋巾增加亮点"]
    },
    "style_consistency": {
      "score": 9.0,
      "reasoning": "各单品风格统一，都符合商务休闲风格。",
      "improvement_suggestions": []
    },
    "occasion_suitability": {
      "score": 8.0,
      "reasoning": "适合办公室、商务会议等场合，但略显正式。",
      "improvement_suggestions": ["可根据具体场合调整正式程度"]
    },
    "fashion_sense": {
      "score": 7.5,
      "reasoning": "整体搭配得体但缺乏时尚亮点。",
      "improvement_suggestions": ["可以尝试更有设计感的衬衫款式"]
    },
    "personal_style": {
      "score": 7.0,
      "reasoning": "搭配安全但个人特色不够突出。",
      "improvement_suggestions": ["添加个性配饰如独特袖扣或领带"]
    }
  },
  "overall_score": 8.0,
  "improvement_suggestions": [
    "添加一个亮色口袋巾增加整体亮点",
    "选择更有设计感的衬衫提升时尚度",
    "添加个性配饰如独特袖扣或领带展现个人风格",
    "可以考虑更修身的剪裁提升整体轮廓"
  ]
}
```
"""
    
    async def score_outfit(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        budget_focus: bool = False
    ) -> OutfitAnalysisResponse:
        """对穿搭进行多维度评分"""
        start_time = time.time()
        
        # 构建用户消息
        user_message = "请对这套穿搭进行多维度分析和评分。"
        
        if image_path:
            user_message += f"\n\n图片路径: {image_path}"
        elif image_url:
            user_message += f"\n\n图片URL: {image_url}"
        
        # 添加用户偏好信息
        if user_preferences:
            user_message += "\n\n用户偏好信息:"
            for key, value in user_preferences.items():
                if value:
                    user_message += f"\n- {key}: {value}"
        
        # 添加预算关注
        if budget_focus:
            user_message += "\n\n请特别关注预算合理性维度，评估穿搭的性价比。"
        
        # 使用AutoGen进行穿搭评分
        try:
            # 发送消息给穿搭打分Agent
            self.user_proxy.initiate_chat(
                self.scoring_agent,
                message=user_message
            )
            
            # 获取穿搭评分结果
            response_message = self.scoring_agent.last_message()["content"]
            
            # 解析JSON响应
            json_start = response_message.find('{')
            json_end = response_message.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_message[json_start:json_end]
                result = json.loads(json_str)
            else:
                # 如果无法解析JSON，使用默认值
                logger.error(f"无法从响应中解析JSON: {response_message}")
                result = self._get_default_analysis_result()
            
            # 构建评分维度对象
            scores = {}
            for dim_name, dim_data in result.get("scores", {}).items():
                scores[dim_name] = ScoreDimension(
                    score=dim_data.get("score", 5.0),
                    reasoning=dim_data.get("reasoning", "无评分理由"),
                    improvement_suggestions=dim_data.get("improvement_suggestions", [])
                )
            
            # 构建响应
            analysis_response = OutfitAnalysisResponse(
                outfit_description=result.get("outfit_description", "无穿搭描述"),
                color_palette=result.get("color_palette", ["未识别"]),
                style_type=result.get("style_type", "未识别"),
                scores=scores,
                overall_score=result.get("overall_score", 5.0),
                improvement_suggestions=result.get("improvement_suggestions", ["无改进建议"]),
                user_id=user_preferences.get("user_id") if user_preferences else None
            )
            
            logger.info(f"穿搭评分完成，耗时: {time.time() - start_time:.2f}秒，总分: {analysis_response.overall_score}")
            return analysis_response
            
        except Exception as e:
            logger.error(f"穿搭评分失败: {str(e)}")
            # 返回默认响应
            return self._get_default_analysis_response(user_preferences)
    
    def _get_default_analysis_result(self) -> Dict[str, Any]:
        """获取默认分析结果"""
        return {
            "outfit_description": "无法分析穿搭",
            "color_palette": ["未识别"],
            "style_type": "未识别",
            "scores": {
                "color_coordination": {
                    "score": 5.0,
                    "reasoning": "无法评估颜色搭配",
                    "improvement_suggestions": []
                },
                "style_consistency": {
                    "score": 5.0,
                    "reasoning": "无法评估风格协调性",
                    "improvement_suggestions": []
                },
                "occasion_suitability": {
                    "score": 5.0,
                    "reasoning": "无法评估场合适宜性",
                    "improvement_suggestions": []
                },
                "fashion_sense": {
                    "score": 5.0,
                    "reasoning": "无法评估时尚度",
                    "improvement_suggestions": []
                },
                "personal_style": {
                    "score": 5.0,
                    "reasoning": "无法评估个人特色",
                    "improvement_suggestions": []
                }
            },
            "overall_score": 5.0,
            "improvement_suggestions": ["无法提供改进建议"]
        }
    
    def _get_default_analysis_response(self, user_preferences: Optional[Dict[str, Any]] = None) -> OutfitAnalysisResponse:
        """获取默认分析响应"""
        default_result = self._get_default_analysis_result()
        
        # 构建评分维度对象
        scores = {}
        for dim_name, dim_data in default_result.get("scores", {}).items():
            scores[dim_name] = ScoreDimension(
                score=dim_data.get("score", 5.0),
                reasoning=dim_data.get("reasoning", "无评分理由"),
                improvement_suggestions=dim_data.get("improvement_suggestions", [])
            )
        
        return OutfitAnalysisResponse(
            outfit_description=default_result.get("outfit_description", "无穿搭描述"),
            color_palette=default_result.get("color_palette", ["未识别"]),
            style_type=default_result.get("style_type", "未识别"),
            scores=scores,
            overall_score=default_result.get("overall_score", 5.0),
            improvement_suggestions=default_result.get("improvement_suggestions", ["无改进建议"]),
            user_id=user_preferences.get("user_id") if user_preferences else None
        )
    
    def _mock_analysis_result(self, user_id: Optional[str] = None) -> OutfitAnalysisResponse:
        """模拟分析结果（用于开发测试）"""
        scores = {
            "color_coordination": ScoreDimension(
                score=8.5,
                reasoning="黑、白、蓝、棕的经典配色组合协调自然，色彩过渡平滑。",
                improvement_suggestions=["可以添加一个亮色口袋巾增加亮点"]
            ),
            "style_consistency": ScoreDimension(
                score=9.0,
                reasoning="各单品风格统一，都符合商务休闲风格。",
                improvement_suggestions=[]
            ),
            "occasion_suitability": ScoreDimension(
                score=8.0,
                reasoning="适合办公室、商务会议等场合，但略显正式。",
                improvement_suggestions=["可根据具体场合调整正式程度"]
            ),
            "fashion_sense": ScoreDimension(
                score=7.5,
                reasoning="整体搭配得体但缺乏时尚亮点。",
                improvement_suggestions=["可以尝试更有设计感的衬衫款式"]
            ),
            "personal_style": ScoreDimension(
                score=7.0,
                reasoning="搭配安全但个人特色不够突出。",
                improvement_suggestions=["添加个性配饰如独特袖扣或领带"]
            )
        }
        
        return OutfitAnalysisResponse(
            outfit_description="这套穿搭由黑色修身西装外套、白色衬衫、深蓝色牛仔裤和棕色皮鞋组成，搭配简约黑色皮带。",
            color_palette=["黑色", "白色", "深蓝色", "棕色"],
            style_type="商务休闲",
            scores=scores,
            overall_score=8.0,
            improvement_suggestions=[
                "添加一个亮色口袋巾增加整体亮点",
                "选择更有设计感的衬衫提升时尚度",
                "添加个性配饰如独特袖扣或领带展现个人风格",
                "可以考虑更修身的剪裁提升整体轮廓"
            ],
            user_id=user_id
        )


# 创建多维度穿搭打分Agent实例
scoring_agent = ScoringAgent()