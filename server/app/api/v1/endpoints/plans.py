from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, timedelta
from typing import List, Dict, Any
import json

from ....core.database import get_db
from ....models.plan import Goal, LearningPlan, PlanItem
from ....models.knowledge import KnowledgePoint
from ....models.progress import UserKnowledgeState, WrongQuestion
from ..deps import get_current_student

router = APIRouter()


class PlanGenerateRequest(BaseModel):
    days: int = 14  # 默认14天


class PlanItemCompleteRequest(BaseModel):
    status: str  # "DONE" or "SKIPPED"


@router.post("/generate")
async def generate_learning_plan(
    request: PlanGenerateRequest,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """生成学习计划"""
    try:
        # 1. 获取用户当前目标
        goal = db.query(Goal).filter(
            Goal.user_id == current_user["id"]
        ).order_by(Goal.created_at.desc()).first()

        if not goal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请先设置学习目标"
            )

        # 2. 计算计划时间范围
        start_date = date.today()
        end_date = start_date + timedelta(days=request.days - 1)

        # 3. 获取所有知识点及其权重
        knowledge_points = db.query(KnowledgePoint).all()
        if not knowledge_points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="暂无知识点数据，无法生成计划"
            )

        # 4. 获取用户的掌握度数据
        mastery_data = {}
        user_states = db.query(UserKnowledgeState).filter(
            UserKnowledgeState.user_id == current_user["id"]
        ).all()

        for state in user_states:
            mastery_data[state.knowledge_id] = float(state.mastery)

        # 5. 获取到期复习的错题
        review_questions = db.query(WrongQuestion).filter(
            WrongQuestion.user_id == current_user["id"],
            WrongQuestion.next_review_at <= start_date + timedelta(days=request.days)
        ).all()

        # 6. 计算知识点优先级并排序
        knowledge_priority = []
        for kp in knowledge_points:
            mastery = mastery_data.get(kp.id, 0.0)
            priority = (1 - mastery) * float(kp.weight)
            knowledge_priority.append({
                "id": kp.id,
                "name": kp.name,
                "priority": priority,
                "mastery": mastery,
                "weight": float(kp.weight),
                "estimated_minutes": kp.estimated_minutes
            })

        # 按优先级排序
        knowledge_priority.sort(key=lambda x: x["priority"], reverse=True)

        # 7. 创建学习计划
        plan = LearningPlan(
            user_id=current_user["id"],
            goal_id=goal.id,
            start_date=start_date,
            end_date=end_date,
            strategy_version="v1.0",
            is_active=True
        )

        db.add(plan)
        db.flush()  # 获取plan.id

        # 8. 生成每日计划项
        plan_items = []
        daily_minutes = goal.daily_minutes
        knowledge_index = 0

        for day in range(request.days):
            current_date = start_date + timedelta(days=day)
            remaining_minutes = daily_minutes

            # 优先安排到期复习的错题
            review_items = []
            for wrong_q in review_questions:
                if wrong_q.next_review_at.date() == current_date:
                    # 查找题目对应的知识点
                    question = wrong_q.question
                    if question and question.knowledge_points:
                        kp_id = question.knowledge_points[0].knowledge_id
                        review_items.append({
                            "type": "REVIEW",
                            "title": f"复习错题：{question.stem[:20]}...",
                            "knowledge_id": kp_id,
                            "expected_minutes": min(15, remaining_minutes),  # 复习每题15分钟
                            "reason": {
                                "type": "review",
                                "wrong_count": wrong_q.wrong_count,
                                "last_wrong": wrong_q.last_wrong_at.isoformat()
                            }
                        })
                        remaining_minutes -= 15
                        if remaining_minutes <= 0:
                            break

            # 生成学习任务
            while remaining_minutes > 0 and knowledge_index < len(knowledge_priority):
                kp = knowledge_priority[knowledge_index]
                learn_minutes = min(kp["estimated_minutes"], remaining_minutes)

                plan_items.append(PlanItem(
                    plan_id=plan.id,
                    date=current_date,
                    type="LEARN",
                    knowledge_id=kp["id"],
                    title=f"学习：{kp['name']}",
                    expected_minutes=learn_minutes,
                    status="TODO",
                    reason_json=json.dumps({
                        "mastery": kp["mastery"],
                        "weight": kp["weight"],
                        "priority": kp["priority"],
                        "explanation": f"掌握度{kp['mastery']:.1%}，权重{kp['weight']}，优先级{kp['priority']:.2f}"
                    })
                ))

                remaining_minutes -= learn_minutes
                knowledge_index += 1

            # 添加复习任务
            for review_item in review_items:
                plan_items.append(PlanItem(
                    plan_id=plan.id,
                    date=current_date,
                    type=review_item["type"],
                    knowledge_id=review_item["knowledge_id"],
                    title=review_item["title"],
                    expected_minutes=review_item["expected_minutes"],
                    status="TODO",
                    reason_json=json.dumps(review_item["reason"])
                ))

        # 批量插入计划项
        if plan_items:
            db.add_all(plan_items)

        db.commit()

        return {
            "plan_id": plan.id,
            "message": f"已生成{request.days}天学习计划",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_items": len(plan_items)
        }

    except HTTPException:
        raise
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
    plan = db.query(LearningPlan).filter(
        LearningPlan.user_id == current_user["id"],
        LearningPlan.is_active == True
    ).first()

    if not plan:
        return None

    # 获取计划项
    items = db.query(PlanItem).filter(
        PlanItem.plan_id == plan.id
    ).order_by(PlanItem.date, PlanItem.id).all()

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
        item = db.query(PlanItem).join(LearningPlan).filter(
            PlanItem.id == item_id,
            LearningPlan.user_id == current_user["id"]
        ).first()

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
