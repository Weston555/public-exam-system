from sqlalchemy import Column, Integer, ForeignKey, DECIMAL, DateTime, Date
from sqlalchemy.orm import relationship

from .base import BaseModel


class UserKnowledgeState(BaseModel):
    """用户知识点掌握状态模型"""
    __tablename__ = "user_knowledge_state"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    knowledge_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=False)
    mastery = Column(DECIMAL(3, 2), nullable=False, default=0.00)  # 0.00-1.00
    ability = Column(DECIMAL(5, 2), nullable=True)  # 可选能力值

    # 关联关系
    user = relationship("User", back_populates="user_knowledge_states")
    knowledge_point = relationship("KnowledgePoint", back_populates="user_knowledge_states")

    def __repr__(self):
        return f"<UserKnowledgeState(user_id={self.user_id}, knowledge_id={self.knowledge_id}, mastery={self.mastery})>"


class WrongQuestion(BaseModel):
    """错题本模型"""
    __tablename__ = "wrong_questions"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    wrong_count = Column(Integer, nullable=False, default=1)
    last_wrong_at = Column(DateTime, nullable=False)
    next_review_at = Column(DateTime, nullable=True)

    # 关联关系
    user = relationship("User", back_populates="wrong_questions")
    question = relationship("Question")

    def __repr__(self):
        return f"<WrongQuestion(user_id={self.user_id}, question_id={self.question_id}, wrong_count={self.wrong_count})>"
