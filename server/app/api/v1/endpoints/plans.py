from fastapi import APIRouter

router = APIRouter()


@router.post("/generate")
async def generate_learning_plan():
    """生成学习计划"""
    return {"plan_id": 1, "items": []}
