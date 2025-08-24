"""
记忆系统数据库模型
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, Index, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.database import Base


class Memory(Base):
    """长期记忆模型"""
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    memory_type = Column(String(50), nullable=False, index=True)
    content = Column(JSONB, nullable=False)
    content_text = Column(Text, nullable=False)  # 用于全文搜索
    embedding = Column(ARRAY(Float), nullable=True)  # 向量嵌入
    importance_score = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)
    tags = Column(ARRAY(String), nullable=True)
    meta_info = Column(JSONB, nullable=True)  # 重命名 metadata 为 meta_info
    is_forgotten = Column(Boolean, default=False)
    forgotten_reason = Column(String(100), nullable=True)
    forgotten_at = Column(DateTime, nullable=True)
    
    # 创建索引
    __table_args__ = (
        Index('idx_memory_user_type', user_id, memory_type),
        Index('idx_memory_created', created_at),
        Index('idx_memory_importance', importance_score),
        Index('idx_memory_forgotten', is_forgotten),
        # 创建GIN索引用于全文搜索，使用 pg_trgm 扩展的 gin_trgm_ops 操作符类
        Index('idx_memory_content_text_gin', content_text, postgresql_using='gin', postgresql_ops={'content_text': 'gin_trgm_ops'}),
        # 创建GIN索引用于JSONB查询
        Index('idx_memory_content_gin', content, postgresql_using='gin'),
        # 创建GIN索引用于数组查询
        Index('idx_memory_tags_gin', tags, postgresql_using='gin'),
    )


class MemoryRelation(Base):
    """记忆关系模型"""
    __tablename__ = "memory_relations"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(Integer, ForeignKey("memories.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String(50), nullable=False)
    strength = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_info = Column(JSONB, nullable=True)  # 重命名 metadata 为 meta_info
    
    # 关系
    source = relationship("Memory", foreign_keys=[source_id])
    target = relationship("Memory", foreign_keys=[target_id])
    
    # 创建索引
    __table_args__ = (
        Index('idx_memory_relation_source', source_id),
        Index('idx_memory_relation_target', target_id),
        Index('idx_memory_relation_type', relation_type),
    )


class MemoryConsolidation(Base):
    """记忆整合模型"""
    __tablename__ = "memory_consolidations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    source_ids = Column(ARRAY(Integer), nullable=False)  # 源记忆ID列表
    result_id = Column(Integer, ForeignKey("memories.id", ondelete="SET NULL"), nullable=True)  # 整合后的记忆ID
    consolidation_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    meta_info = Column(JSONB, nullable=True)  # 重命名 metadata 为 meta_info
    
    # 关系
    result = relationship("Memory")
    
    # 创建索引
    __table_args__ = (
        Index('idx_memory_consolidation_user', user_id),
        Index('idx_memory_consolidation_created', created_at),
    )