from typing import Dict, List, Optional, Any, Union
import json
from loguru import logger

from app.core.qwen_client import qwen_client
from app.services.image_service import image_service


class AnalysisService:
    """穿搭分析服务"""
    
    async def analyze_outfit(
        self,
        image_path: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        budget_focus: bool = False
    ) -> Dict[str, Any]:
        """分析穿搭照片"""
        if not image_path and not image_bytes:
            raise ValueError("必须提供image_path或image_bytes参数")
        
        # 构建分析提示词
        prompt = self._build_analysis_prompt(user_preferences, budget_focus)
        
        # 调用Qwen-VL-Chat API进行分析
        response = await qwen_client.analyze_outfit(
            image_path=image_path,
            image_bytes=image_bytes,
            prompt=prompt
        )
        
        # 解析API响应
        analysis_result = await self._parse_analysis_response(response)
        
        return analysis_result
    
    def _build_analysis_prompt(
        self,
        user_preferences: Optional[Dict[str, Any]] = None,
        budget_focus: bool = False
    ) -> str:
        """构建分析提示词"""
        prompt = """请详细分析这张穿搭照片，并提供以下信息：
1. 服装组成：详细描述上衣、下装、鞋履、配饰等
2. 颜色搭配：分析色彩组合、对比和协调性
3. 风格特点：识别整体风格类型和特点
4. 多维度评分（1-10分）：
   - 颜色搭配协调性
   - 风格协调性
   - 场合适宜性
   - 时尚度
   - 个人特色"""
        
        # 添加预算维度
        if budget_focus:
            prompt += "\n   - 预算合理性（性价比）"
        
        prompt += """
5. 总体评价：整体穿搭的优缺点
6. 改进建议：3-5条具体的优化建议
7. 搭配推荐：基于当前风格的其他搭配方案

请以结构化的方式返回分析结果，使用Markdown格式。"""

        # 添加用户偏好
        if user_preferences:
            prompt += "\n\n用户偏好信息："
            if "style" in user_preferences:
                prompt += f"\n- 偏好风格：{user_preferences['style']}"
            if "colors" in user_preferences:
                prompt += f"\n- 偏好颜色：{', '.join(user_preferences['colors'])}"
            if "occasions" in user_preferences:
                prompt += f"\n- 常见场合：{', '.join(user_preferences['occasions'])}"
            if "budget" in user_preferences:
                prompt += f"\n- 预算范围：{user_preferences['budget']}"
            
            prompt += "\n\n请根据用户偏好进行个性化分析和推荐。"
        
        return prompt
    
    async def _parse_analysis_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析API响应"""
        try:
            # 从响应中提取文本内容
            if "output" in response and "choices" in response["output"]:
                content = response["output"]["choices"][0]["message"]["content"]
            else:
                logger.error(f"无效的API响应格式: {response}")
                return {"error": "无效的API响应格式"}
            
            # 解析评分
            scores = self._extract_scores(content)
            
            # 解析改进建议
            suggestions = self._extract_suggestions(content)
            
            # 解析搭配推荐
            recommendations = self._extract_recommendations(content)
            
            return {
                "raw_content": content,
                "scores": scores,
                "suggestions": suggestions,
                "recommendations": recommendations,
                "usage": response.get("usage", {}),
                "request_id": response.get("request_id", "")
            }
            
        except Exception as e:
            logger.error(f"解析分析响应时出错: {str(e)}")
            return {
                "error": f"解析分析响应时出错: {str(e)}",
                "raw_content": response.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
            }
    
    def _extract_scores(self, content: str) -> Dict[str, float]:
        """从内容中提取评分"""
        scores = {}
        score_patterns = [
            r"颜色搭配协调性[：:]\s*(\d+)[/／]10",
            r"风格协调性[：:]\s*(\d+)[/／]10",
            r"场合适宜性[：:]\s*(\d+)[/／]10",
            r"时尚度[：:]\s*(\d+)[/／]10",
            r"个人特色[：:]\s*(\d+)[/／]10",
            r"预算合理性[：:]\s*(\d+)[/／]10"
        ]
        
        import re
        for pattern, key in zip(score_patterns, ["color_harmony", "style_consistency", "occasion_suitability", "fashion_level", "personal_style", "budget_value"]):
            match = re.search(pattern, content)
            if match:
                scores[key] = float(match.group(1))
        
        return scores
    
    def _extract_suggestions(self, content: str) -> List[str]:
        """从内容中提取改进建议"""
        suggestions = []
        
        # 尝试找到"改进建议"部分
        import re
        suggestion_section = re.search(r"(改进建议|优化建议|建议)([\s\S]*?)(##|\Z)", content)
        
        if suggestion_section:
            suggestion_text = suggestion_section.group(2)
            # 提取编号的建议
            numbered_suggestions = re.findall(r"\d+\.\s*(.*?)(?=\d+\.|$)", suggestion_text)
            if numbered_suggestions:
                suggestions = [s.strip() for s in numbered_suggestions if s.strip()]
        
        return suggestions
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """从内容中提取搭配推荐"""
        recommendations = []
        
        # 尝试找到"搭配推荐"部分
        import re
        recommendation_section = re.search(r"(搭配推荐|推荐搭配|搭配建议)([\s\S]*?)(##|\Z)", content)
        
        if recommendation_section:
            recommendation_text = recommendation_section.group(2)
            # 提取编号的推荐
            numbered_recommendations = re.findall(r"\d+\.\s*(.*?)(?=\d+\.|$)", recommendation_text)
            if numbered_recommendations:
                recommendations = [r.strip() for r in numbered_recommendations if r.strip()]
        
        return recommendations


# 创建默认服务实例
analysis_service = AnalysisService()