from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_questions(page: int = 1, size: int = 20):
    """获取题目列表"""
    return {"items": [], "total": 0, "page": page, "size": size}
