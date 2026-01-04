from fastapi import APIRouter

from .endpoints import auth, users, knowledge, questions, papers, exams, attempts, goals, plans, analytics, practice, wrong_questions, admin_export, admin_exams

# 创建主API路由器
api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["知识点"])
api_router.include_router(questions.router, prefix="/questions", tags=["题库"])
api_router.include_router(papers.router, prefix="/papers", tags=["试卷"])
api_router.include_router(exams.router, prefix="/exams", tags=["考试"])
api_router.include_router(attempts.router, prefix="/attempts", tags=["作答记录"])
api_router.include_router(goals.router, prefix="/goals", tags=["学习目标"])
api_router.include_router(plans.router, prefix="/plans", tags=["学习计划"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["数据分析"])
api_router.include_router(practice.router, prefix="/practice", tags=["practice"])
api_router.include_router(wrong_questions.router, prefix="/wrong-questions", tags=["wrong-questions"])
api_router.include_router(admin_export.router, prefix="/admin/export", tags=["admin-export"])
api_router.include_router(admin_exams.router, prefix="/admin/exams", tags=["admin-exams"])
