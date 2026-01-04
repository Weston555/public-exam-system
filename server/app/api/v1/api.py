from fastapi import APIRouter

from .endpoints import auth, users, knowledge, questions, papers, exams, attempts, plans, analytics

# 创建主API路由器
api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["知识点"])
api_router.include_router(questions.router, prefix="/questions", tags=["题库"])
api_router.include_router(papers.router, prefix="/papers", tags=["试卷"])
api_router.include_router(exams.router, prefix="/exams", tags=["考试"])
api_router.include_router(attempts.router, prefix="/attempts", tags=["答题"])
api_router.include_router(plans.router, prefix="/plans", tags=["学习计划"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["数据分析"])
