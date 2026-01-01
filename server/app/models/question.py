from sqlalchemy import Column, Text, JSON, Integer, Enum, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel


class Question(BaseModel):
    """题目模型"""
    __tablename__ = "questions"

    type = Column(Enum("SINGLE", "MULTI", "JUDGE", "FILL", "SHORT", name="question_type"), nullable=False)
    stem = Column(Text, nullable=False)
    options_json = Column(JSON, nullable=True)  # 选择题选项
    answer_json = Column(JSON, nullable=False)  # 答案
    analysis = Column(Text, nullable=True)      # 解析
    difficulty = Column(Integer, nullable=False)  # 1-5

    # 关联关系
    knowledge_points = relationship("QuestionKnowledgeMap", back_populates="question")
    paper_questions = relationship("PaperQuestion", back_populates="question")
    answers = relationship("Answer", back_populates="question")

    def __repr__(self):
        return f"<Question(id={self.id}, type='{self.type}', difficulty={self.difficulty})>"
