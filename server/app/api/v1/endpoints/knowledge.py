from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ....core.database import get_db
from ....models.knowledge import KnowledgePoint
from ..deps import get_current_admin

router = APIRouter()


class KnowledgePointCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None
    code: Optional[str] = None
    weight: float = 1.0
    estimated_minutes: int = 30


class KnowledgePointUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    code: Optional[str] = None
    weight: Optional[float] = None
    estimated_minutes: Optional[int] = None


def build_tree(nodes: List[KnowledgePoint], parent_id: Optional[int] = None) -> List[dict]:
    """递归构建树形结构"""
    tree = []
    for node in nodes:
        if node.parent_id == parent_id:
            children = build_tree(nodes, node.id)
            node_dict = {
                "id": node.id,
                "name": node.name,
                "code": node.code,
                "weight": node.weight,
                "estimated_minutes": node.estimated_minutes,
                "children": children
            }
            tree.append(node_dict)
    return tree


@router.get("/tree")
async def get_knowledge_tree(db: Session = Depends(get_db)):
    """获取知识点树"""
    try:
        # 获取所有知识点
        knowledge_points = db.query(KnowledgePoint).order_by(KnowledgePoint.id).all()

        # 构建树形结构
        tree = build_tree(knowledge_points)

        return {"tree": tree}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取知识点树失败: {str(e)}"
        )


@router.post("/")
async def create_knowledge_point(
    request: KnowledgePointCreate,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """创建知识点 (管理员权限)"""
    try:
        # 检查父节点是否存在
        if request.parent_id:
            parent = db.query(KnowledgePoint).filter(KnowledgePoint.id == request.parent_id).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="父节点不存在"
                )

        # 检查编码是否重复
        if request.code:
            existing = db.query(KnowledgePoint).filter(KnowledgePoint.code == request.code).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="知识点编码已存在"
                )

        # 创建知识点
        knowledge_point = KnowledgePoint(
            name=request.name,
            parent_id=request.parent_id,
            code=request.code,
            weight=request.weight,
            estimated_minutes=request.estimated_minutes
        )

        db.add(knowledge_point)
        db.commit()
        db.refresh(knowledge_point)

        return {
            "id": knowledge_point.id,
            "message": "知识点创建成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建知识点失败: {str(e)}"
        )


@router.put("/{point_id}")
async def update_knowledge_point(
    point_id: int,
    request: KnowledgePointUpdate,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新知识点 (管理员权限)"""
    try:
        # 查找知识点
        knowledge_point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
        if not knowledge_point:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识点不存在"
            )

        # 检查父节点是否存在
        if request.parent_id is not None:
            if request.parent_id != point_id:  # 防止自己成为自己的父节点
                parent = db.query(KnowledgePoint).filter(KnowledgePoint.id == request.parent_id).first()
                if not parent:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="父节点不存在"
                    )
            else:
                request.parent_id = knowledge_point.parent_id  # 不允许修改

        # 检查编码是否重复
        if request.code and request.code != knowledge_point.code:
            existing = db.query(KnowledgePoint).filter(
                KnowledgePoint.code == request.code,
                KnowledgePoint.id != point_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="知识点编码已存在"
                )

        # 更新字段
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(knowledge_point, field):
                setattr(knowledge_point, field, value)

        db.commit()
        db.refresh(knowledge_point)

        return {
            "id": knowledge_point.id,
            "message": "知识点更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新知识点失败: {str(e)}"
        )


@router.delete("/{point_id}")
async def delete_knowledge_point(
    point_id: int,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """删除知识点 (管理员权限)"""
    try:
        # 查找知识点
        knowledge_point = db.query(KnowledgePoint).filter(KnowledgePoint.id == point_id).first()
        if not knowledge_point:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="知识点不存在"
            )

        # 检查是否有子节点
        children = db.query(KnowledgePoint).filter(KnowledgePoint.parent_id == point_id).count()
        if children > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法删除包含子节点的知识点"
            )

        # 删除知识点
        db.delete(knowledge_point)
        db.commit()

        return {"message": "知识点删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除知识点失败: {str(e)}"
        )
