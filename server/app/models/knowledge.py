from sqlalchemy import Column, String, Integer, DECIMAL, ForeignKey, Text
from sqlalchemy.orm import relationship

from .base import BaseModel, Base


class KnowledgePoint(BaseModel):
    """知识点模型"""
    __tablename__ = "knowledge_points"

    parent_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=True)
    weight = Column(DECIMAL(3, 2), nullable=False, default=1.00)
    estimated_minutes = Column(Integer, nullable=False, default=30)

    # 关联关系
    parent = relationship("KnowledgePoint", remote_side="KnowledgePoint.id", backref="children")
    questions = relationship("QuestionKnowledgeMap", back_populates="knowledge_point")
    user_knowledge_states = relationship("UserKnowledgeState", back_populates="knowledge_point")
    plan_items = relationship("PlanItem", back_populates="knowledge_point")

    def __repr__(self):
        return f"<KnowledgePoint(id={self.id}, name='{self.name}', code='{self.code}')>"


class QuestionKnowledgeMap(Base):
    """题目知识点映射模型"""
    __tablename__ = "question_knowledge_map"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    knowledge_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=False, index=True)

    # 关联关系
    question = relationship("Question", back_populates="knowledge_points")
    knowledge_point = relationship("KnowledgePoint", back_populates="questions")

    def __repr__(self):
        return f"<QuestionKnowledgeMap(question_id={self.question_id}, knowledge_id={self.knowledge_id})>"
