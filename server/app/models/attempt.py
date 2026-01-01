from sqlalchemy import Column, Integer, ForeignKey, DateTime, DECIMAL, Enum, Boolean, JSON
from sqlalchemy.orm import relationship

from .base import BaseModel


class Attempt(BaseModel):
    """作答记录模型"""
    __tablename__ = "attempts"

    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    total_score = Column(DECIMAL(5, 1), nullable=True)
    status = Column(Enum("DOING", "SUBMITTED", name="attempt_status"), nullable=False, default="DOING")

    # 关联关系
    exam = relationship("Exam", back_populates="attempts")
    user = relationship("User", back_populates="attempts")
    answers = relationship("Answer", back_populates="attempt")

    def __repr__(self):
        return f"<Attempt(id={self.id}, exam_id={self.exam_id}, user_id={self.user_id}, status='{self.status}')>"


class Answer(BaseModel):
    """答案模型"""
    __tablename__ = "answers"

    attempt_id = Column(Integer, ForeignKey("attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_json = Column(JSON, nullable=False)
    is_correct = Column(Boolean, nullable=True)
    score_awarded = Column(DECIMAL(4, 1), nullable=True)
    time_spent_seconds = Column(Integer, nullable=False, default=0)

    # 关联关系
    attempt = relationship("Attempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")

    def __repr__(self):
        return f"<Answer(attempt_id={self.attempt_id}, question_id={self.question_id}, is_correct={self.is_correct})>"
