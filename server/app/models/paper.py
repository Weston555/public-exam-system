from sqlalchemy import Column, String, Text, JSON, DECIMAL, Integer, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from .base import BaseModel


class Paper(BaseModel):
    """试卷模型"""
    __tablename__ = "papers"

    title = Column(String(200), nullable=False)
    mode = Column(Enum("MANUAL", "AUTO", name="paper_mode"), nullable=False, default="AUTO")
    config_json = Column(JSON, nullable=True)  # 自动组卷配置
    total_score = Column(DECIMAL(5, 1), nullable=False, default=100.0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 关联关系
    creator = relationship("User")
    paper_questions = relationship("PaperQuestion", back_populates="paper")
    exams = relationship("Exam", back_populates="paper")

    def __repr__(self):
        return f"<Paper(id={self.id}, title='{self.title}', mode='{self.mode}')>"


class PaperQuestion(BaseModel):
    """试卷题目模型"""
    __tablename__ = "paper_questions"

    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    order_no = Column(Integer, nullable=False)
    score = Column(DECIMAL(4, 1), nullable=False, default=2.0)

    # 关联关系
    paper = relationship("Paper", back_populates="paper_questions")
    question = relationship("Question", back_populates="paper_questions")

    def __repr__(self):
        return f"<PaperQuestion(paper_id={self.paper_id}, question_id={self.question_id}, order_no={self.order_no})>"


class Exam(BaseModel):
    """考试模型"""
    __tablename__ = "exams"

    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    title = Column(String(200), nullable=False)
    category = Column(Enum("DIAGNOSTIC", "PRACTICE", "MOCK", name="exam_category"), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(Enum("DRAFT", "PUBLISHED", "ARCHIVED", name="exam_status"), nullable=False, default="DRAFT")
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 关联关系
    paper = relationship("Paper", back_populates="exams")
    creator = relationship("User")
    attempts = relationship("Attempt", back_populates="exam")
    plan_items = relationship("PlanItem", back_populates="exam")

    def __repr__(self):
        return f"<Exam(id={self.id}, title='{self.title}', category='{self.category}')>"
