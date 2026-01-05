from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Dict, Any
import json

from ..models.plan import Goal, LearningPlan, PlanItem
from ..models.knowledge import KnowledgePoint
from ..models.progress import UserKnowledgeState, WrongQuestion


def generate_learning_plan(db: Session, user_id: int, days: int) -> dict:
    """
    生成学习计划的核心算法

    Args:
        db: 数据库会话
        user_id: 用户ID
        days: 计划天数

    Returns:
        dict: 包含计划信息的字典
    """
    # 1. 获取用户当前目标
    stmt = select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at.desc())
    goal = db.execute(stmt).scalar_one_or_none()

    if not goal:
        raise ValueError("请先设置学习目标")

    # 2. 计算计划时间范围
    start_date = date.today()
    end_date = start_date + timedelta(days=days - 1)

    # 3. 获取所有知识点及其权重
    stmt = select(KnowledgePoint)
    knowledge_points = db.execute(stmt).scalars().all()
    if not knowledge_points:
        raise ValueError("暂无知识点数据，无法生成计划")

    # 4. 获取用户的掌握度数据
    mastery_data = {}
    stmt = select(UserKnowledgeState).where(UserKnowledgeState.user_id == user_id)
    user_states = db.execute(stmt).scalars().all()

    for state in user_states:
        mastery_data[state.knowledge_id] = float(state.mastery)

    # 5. 获取到期复习的错题
    review_deadline = start_date + timedelta(days=days)
    stmt = select(WrongQuestion).where(
        WrongQuestion.user_id == user_id,
        WrongQuestion.next_review_at <= review_deadline
    )
    review_questions = db.execute(stmt).scalars().all()

    # 6. 计算知识点优先级并排序
    # 优先级计算：(1 - 掌握度) * 权重
    # 掌握度越低、权重越高的知识点优先级越高
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

    # 按优先级从高到低排序
    knowledge_priority.sort(key=lambda x: x["priority"], reverse=True)

    # 7. 创建学习计划
    plan = LearningPlan(
        user_id=user_id,
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

    for day in range(days):
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

        # 生成学习任务 - 从剩余时间中安排薄弱知识点学习
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

    return {
        "plan_id": plan.id,
        "message": f"已生成{days}天学习计划",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_items": len(plan_items)
    }
