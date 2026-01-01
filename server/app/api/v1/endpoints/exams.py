from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_exams():
    """获取考试列表"""
    return {"items": [], "total": 0}


@router.post("/{exam_id}/start")
async def start_exam(exam_id: int):
    """开始考试"""
    return {"attempt_id": 1, "exam": {}, "questions": []}
