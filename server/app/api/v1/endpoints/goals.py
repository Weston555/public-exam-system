from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date

from ....core.database import get_db
from ....models.plan import Goal
from ..deps import get_current_student

router = APIRouter()


class GoalCreate(BaseModel):
    exam_date: date
    target_score: float = None
    daily_minutes: int = 60


class GoalUpdate(BaseModel):
    exam_date: date = None
    target_score: float = None
    daily_minutes: int = None


@router.get("/me")
async def get_current_goal(
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """获取当前用户的目标"""
    goal = db.query(Goal).filter(
        Goal.user_id == current_user["id"]
    ).order_by(Goal.created_at.desc()).first()

    if not goal:
        return None

    return {
        "id": goal.id,
        "exam_date": goal.exam_date.isoformat(),
        "target_score": goal.target_score,
        "daily_minutes": goal.daily_minutes,
        "created_at": goal.created_at.isoformat()
    }


@router.post("/")
async def create_goal(
    request: GoalCreate,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """创建学习目标"""
    try:
        # 检查考试日期是否合理（不能是过去）
        if request.exam_date <= date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="考试日期必须是未来日期"
            )

        # 创建目标
        goal = Goal(
            user_id=current_user["id"],
            exam_date=request.exam_date,
            target_score=request.target_score,
            daily_minutes=request.daily_minutes
        )

        db.add(goal)
        db.commit()
        db.refresh(goal)

        return {
            "id": goal.id,
            "message": "学习目标设置成功",
            "exam_date": goal.exam_date.isoformat(),
            "target_score": goal.target_score,
            "daily_minutes": goal.daily_minutes
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建学习目标失败: {str(e)}"
        )


@router.put("/{goal_id}")
async def update_goal(
    goal_id: int,
    request: GoalUpdate,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """更新学习目标"""
    try:
        # 查找目标
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == current_user["id"]
        ).first()

        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="学习目标不存在"
            )

        # 更新字段
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(goal, field):
                if field == "exam_date" and value <= date.today():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="考试日期必须是未来日期"
                    )
                setattr(goal, field, value)

        db.commit()
        db.refresh(goal)

        return {
            "id": goal.id,
            "message": "学习目标更新成功",
            "exam_date": goal.exam_date.isoformat(),
            "target_score": goal.target_score,
            "daily_minutes": goal.daily_minutes
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新学习目标失败: {str(e)}"
        )


@router.get("/")
async def get_goals(
    skip: int = 0,
    limit: int = 10,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """获取用户的所有目标"""
    goals = db.query(Goal).filter(
        Goal.user_id == current_user["id"]
    ).order_by(Goal.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": [
            {
                "id": goal.id,
                "exam_date": goal.exam_date.isoformat(),
                "target_score": goal.target_score,
                "daily_minutes": goal.daily_minutes,
                "created_at": goal.created_at.isoformat()
            } for goal in goals
        ],
        "total": db.query(Goal).filter(Goal.user_id == current_user["id"]).count()
    }
