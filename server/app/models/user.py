from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship

from .base import BaseModel


class User(BaseModel):
    """用户模型"""
    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("STUDENT", "ADMIN", name="user_role"), nullable=False, default="STUDENT", index=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # 关联关系
    attempts = relationship("Attempt", back_populates="user")
    wrong_questions = relationship("WrongQuestion", back_populates="user")
    learning_plans = relationship("LearningPlan", back_populates="user")
    goals = relationship("Goal", back_populates="user")
    user_knowledge_states = relationship("UserKnowledgeState", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
