from fastapi import APIRouter

router = APIRouter()


@router.get("/tree")
async def get_knowledge_tree():
    """获取知识点树"""
    # 暂时返回空数据
    return {"tree": []}
