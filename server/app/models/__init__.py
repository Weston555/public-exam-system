# 导入所有模型以确保它们被注册到 SQLAlchemy Base
from .base import BaseModel
from .user import User
from .knowledge import KnowledgePoint, QuestionKnowledgeMap
from .question import Question
from .paper import Paper, PaperQuestion, Exam
from .attempt import Attempt, Answer
from .plan import Goal, LearningPlan, PlanItem
from .progress import UserKnowledgeState, WrongQuestion

# 导出所有模型类
__all__ = [
    "BaseModel",
    "User",
    "KnowledgePoint",
    "QuestionKnowledgeMap",
    "Question",
    "Paper",
    "PaperQuestion",
    "Exam",
    "Attempt",
    "Answer",
    "Goal",
    "LearningPlan",
    "PlanItem",
    "UserKnowledgeState",
    "WrongQuestion",
]
