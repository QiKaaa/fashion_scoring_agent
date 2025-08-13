from fastapi import APIRouter

from app.api.endpoints import analysis, intent, unified

api_router = APIRouter()
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(intent.router, prefix="/intent", tags=["intent"])
api_router.include_router(unified.router, prefix="/unified", tags=["unified"])