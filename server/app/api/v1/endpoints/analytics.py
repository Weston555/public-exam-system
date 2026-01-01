from fastapi import APIRouter

router = APIRouter()


@router.get("/progress")
async def get_learning_progress():
    """获取学习进度"""
    return {
        "plan_completion_rate": 0.0,
        "average_mastery": 0.0,
        "wrong_questions_count": 0
    }
