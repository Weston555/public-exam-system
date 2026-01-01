from sqlalchemy import Column, Integer, ForeignKey, Date, Boolean, String, Text, JSON, DECIMAL, Enum, DateTime
from sqlalchemy.orm import relationship

from .base import BaseModel


class Goal(BaseModel):
    """目标模型"""
    __tablename__ = "goals"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exam_date = Column(Date, nullable=False)
    target_score = Column(DECIMAL(5, 1), nullable=True)
    daily_minutes = Column(Integer, nullable=False, default=60)

    # 关联关系
    user = relationship("User", back_populates="goals")
    learning_plans = relationship("LearningPlan", back_populates="goal")

    def __repr__(self):
        return f"<Goal(id={self.id}, user_id={self.user_id}, exam_date={self.exam_date})>"


class LearningPlan(BaseModel):
    """学习计划模型"""
    __tablename__ = "learning_plans"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    strategy_version = Column(String(50), nullable=False, default="v1.0")
    is_active = Column(Boolean, nullable=False, default=True)

    # 关联关系
    user = relationship("User", back_populates="learning_plans")
    goal = relationship("Goal", back_populates="learning_plans")
    plan_items = relationship("PlanItem", back_populates="plan")

    def __repr__(self):
        return f"<LearningPlan(id={self.id}, user_id={self.user_id}, start_date={self.start_date}, end_date={self.end_date})>"


class PlanItem(BaseModel):
    """计划项模型"""
    __tablename__ = "plan_items"

    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=False)
    date = Column(Date, nullable=False)
    type = Column(Enum("LEARN", "PRACTICE", "REVIEW", "MOCK", name="plan_item_type"), nullable=False)
    knowledge_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=True)
    resource_url = Column(String(500), nullable=True)
    title = Column(String(200), nullable=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=True)
    practice_config_json = Column(JSON, nullable=True)
    expected_minutes = Column(Integer, nullable=False)
    status = Column(Enum("TODO", "DONE", "SKIPPED", name="plan_item_status"), nullable=False, default="TODO")
    completed_at = Column(DateTime, nullable=True)
    reason_json = Column(JSON, nullable=True)

    # 关联关系
    plan = relationship("LearningPlan", back_populates="plan_items")
    knowledge_point = relationship("KnowledgePoint", back_populates="plan_items")
    exam = relationship("Exam", back_populates="plan_items")

    def __repr__(self):
        return f"<PlanItem(id={self.id}, plan_id={self.plan_id}, date={self.date}, type='{self.type}', status='{self.status}')>"
