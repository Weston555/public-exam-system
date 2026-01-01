from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_papers():
    """获取试卷列表"""
    return {"items": [], "total": 0}
