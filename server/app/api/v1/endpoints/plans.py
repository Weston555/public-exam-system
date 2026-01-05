from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from typing import Dict, Any
import json

from ....core.database import get_db
from ....models.plan import Goal, LearningPlan, PlanItem
from ....services.recommendation import generate_learning_plan
from ..deps import get_current_student

router = APIRouter()


class PlanGenerateRequest(BaseModel):
    days: int = 14  # 默认14天


class PlanItemCompleteRequest(BaseModel):
    status: str  # "DONE" or "SKIPPED"


@router.post("/generate")
async def generate_learning_plan_endpoint(
    request: PlanGenerateRequest,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """生成学习计划"""
    try:
        # 参数校验
        if request.days < 1 or request.days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="计划天数必须在1-365天之间"
            )

        # 调用推荐服务生成计划
        result = generate_learning_plan(db, current_user["id"], request.days)

        db.commit()
        return result

    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成学习计划失败: {str(e)}"
        )


@router.get("/active")
async def get_active_plan(
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """获取当前活跃的学习计划"""
    stmt = select(LearningPlan).where(
        LearningPlan.user_id == current_user["id"],
        LearningPlan.is_active == True
    )
    plan = db.execute(stmt).scalar_one_or_none()

    if not plan:
        return None

    # 获取计划项
    stmt = select(PlanItem).where(PlanItem.plan_id == plan.id).order_by(PlanItem.date, PlanItem.id)
    items = db.execute(stmt).scalars().all()

    # 按日期分组
    items_by_date = {}
    for item in items:
        date_str = item.date.isoformat()
        if date_str not in items_by_date:
            items_by_date[date_str] = []

        # 解析reason_json
        reason = {}
        if item.reason_json:
            try:
                reason = json.loads(item.reason_json)
            except:
                reason = {"explanation": "系统生成"}

        items_by_date[date_str].append({
            "id": item.id,
            "type": item.type,
            "title": item.title,
            "knowledge_id": item.knowledge_id,
            "expected_minutes": item.expected_minutes,
            "status": item.status,
            "completed_at": item.completed_at.isoformat() if item.completed_at else None,
            "reason": reason
        })

    return {
        "plan_id": plan.id,
        "start_date": plan.start_date.isoformat(),
        "end_date": plan.end_date.isoformat(),
        "strategy_version": plan.strategy_version,
        "items_by_date": items_by_date,
        "goal": {
            "exam_date": plan.goal.exam_date.isoformat() if plan.goal else None,
            "target_score": plan.goal.target_score if plan.goal else None,
            "daily_minutes": plan.goal.daily_minutes if plan.goal else None
        }
    }


@router.patch("/items/{item_id}")
async def update_plan_item_status(
    item_id: int,
    request: PlanItemCompleteRequest,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """更新计划项状态"""
    try:
        # 查找计划项
        stmt = select(PlanItem).join(LearningPlan).where(
            PlanItem.id == item_id,
            LearningPlan.user_id == current_user["id"]
        )
        item = db.execute(stmt).scalar_one_or_none()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="计划项不存在"
            )

        # 验证状态
        if request.status not in ["DONE", "SKIPPED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="状态只能是DONE或SKIPPED"
            )

        # 更新状态
        from datetime import datetime
        item.status = request.status
        if request.status == "DONE":
            item.completed_at = datetime.utcnow()

        db.commit()

        return {
            "id": item.id,
            "status": item.status,
            "completed_at": item.completed_at.isoformat() if item.completed_at else None,
            "message": "计划项状态更新成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新计划项状态失败: {str(e)}"
        )
