"""
穿搭分析服务 - 整合多维度穿搭打分Agent
"""

from typing import Dict, List, Optional, Any, Union
import json
from loguru import logger

from app.services.scoring_agent import scoring_agent
from app.services.image_service import image_service
from app.models.schemas import OutfitAnalysisResponse


class AnalysisService:
    """穿搭分析服务"""
    
    async def analyze_outfit(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        budget_focus: bool = False
    ) -> OutfitAnalysisResponse:
        """分析穿搭照片"""
        if not image_path and not image_url:
            raise ValueError("必须提供image_path或image_url参数")
        
        # 调用多维度穿搭打分Agent进行分析
        analysis_result = await scoring_agent.score_outfit(
            image_path=image_path,
            image_url=image_url,
            user_preferences=user_preferences,
            budget_focus=budget_focus
        )
        
        return analysis_result
    
    def _mock_analysis_result(self, user_id: Optional[str] = None) -> OutfitAnalysisResponse:
        """模拟分析结果（用于开发测试）"""
        return scoring_agent._mock_analysis_result(user_id)


# 创建穿搭分析服务实例
analysis_service = AnalysisService()