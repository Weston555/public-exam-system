from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from ....core.database import get_db
from ....models.attempt import Attempt
from ....models.progress import UserKnowledgeState, WrongQuestion
from ....models.plan import LearningPlan, PlanItem, Goal
from ....models.user import User
from ....models.knowledge import KnowledgePoint
from ..deps import get_current_student, get_current_admin

router = APIRouter()


@router.get("/student/overview")
async def student_overview(
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    try:
        uid = current_user["id"]

        # plan completion rate (active plan)
        plan_stmt = select(LearningPlan).where(LearningPlan.user_id == uid, LearningPlan.is_active == True)
        plan = db.execute(plan_stmt).scalar_one_or_none()
        plan_completion_rate = 0.0
        if plan:
            total_stmt = select(func.count()).select_from(PlanItem).where(PlanItem.plan_id == plan.id)
            total = db.execute(total_stmt).scalar_one()
            done_stmt = select(func.count()).select_from(PlanItem).where(PlanItem.plan_id == plan.id, PlanItem.status == "DONE")
            done = db.execute(done_stmt).scalar_one()
            plan_completion_rate = round((done / total) * 100, 2) if total > 0 else 0.0

        # avg mastery
        avg_stmt = select(func.avg(UserKnowledgeState.mastery)).where(UserKnowledgeState.user_id == uid)
        avg_mastery_val = db.execute(avg_stmt).scalar_one() or 0.0
        avg_mastery_val = round(float(avg_mastery_val), 2)

        # wrong due count
        now = datetime.utcnow()
        wrong_stmt = select(func.count()).select_from(WrongQuestion).where(WrongQuestion.user_id == uid, WrongQuestion.next_review_at <= now)
        wrong_due_count = db.execute(wrong_stmt).scalar_one()

        # last score
        last_stmt = select(Attempt).where(Attempt.user_id == uid, Attempt.status == "SUBMITTED").order_by(Attempt.submitted_at.desc()).limit(1)
        last_attempt = db.execute(last_stmt).scalar_one_or_none()
        last_score = float(last_attempt.total_score) if last_attempt and last_attempt.total_score is not None else None

        return {
            "plan_completion_rate": plan_completion_rate,
            "avg_mastery": avg_mastery_val,
            "wrong_due_count": wrong_due_count,
            "last_score": last_score
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/student/score-trend")
async def student_score_trend(limit: int = Query(10, ge=1, le=100), current_user: dict = Depends(get_current_student), db: Session = Depends(get_db)):
    uid = current_user["id"]
    stmt = select(Attempt).where(Attempt.user_id == uid, Attempt.status == "SUBMITTED").order_by(Attempt.submitted_at.desc()).limit(limit)
    tries = db.execute(stmt).scalars().all()
    items = []
    for a in reversed(tries):
        items.append({"submitted_at": a.submitted_at.isoformat() if a.submitted_at else None, "total_score": float(a.total_score) if a.total_score is not None else None})
    return {"items": items}


@router.get("/student/mastery-top")
async def student_mastery_top(limit: int = Query(10, ge=1), current_user: dict = Depends(get_current_student), db: Session = Depends(get_db)):
    uid = current_user["id"]
    # 使用 SQLAlchemy 2.0 select 语法
    stmt = select(UserKnowledgeState, KnowledgePoint).join(KnowledgePoint, UserKnowledgeState.knowledge_id == KnowledgePoint.id).where(UserKnowledgeState.user_id == uid).order_by(UserKnowledgeState.mastery.asc()).limit(limit)
    rows = db.execute(stmt).all()
    items = []
    for state, kp in rows:
        items.append({"knowledge_id": kp.id, "name": kp.name, "mastery": float(state.mastery)})
    return {"items": items}


@router.get("/student/knowledge-state")
async def student_knowledge_state(limit: int = Query(6, ge=1, le=20), current_user: dict = Depends(get_current_student), db: Session = Depends(get_db)):
    """
    获取学生知识点掌握度雷达图数据
    返回最薄弱的N个知识点的掌握度（按掌握度升序，取薄弱TOP作为雷达维度）
    掌握度范围：0-100（百分制，更直观）
    """
    uid = current_user["id"]

    # 使用 SQLAlchemy 2.0 select 语法
    # 为什么取薄弱TOP作为雷达维度：
    # 1. 雷达图适合展示多维度对比，薄弱知识点更需要关注
    # 2. 聚焦学生最需要改进的方面，便于针对性学习
    # 3. TOP N限制避免图表过于复杂
    stmt = select(UserKnowledgeState, KnowledgePoint).join(
        KnowledgePoint, UserKnowledgeState.knowledge_id == KnowledgePoint.id
    ).where(UserKnowledgeState.user_id == uid).order_by(
        UserKnowledgeState.mastery.asc()
    ).limit(limit)

    rows = db.execute(stmt).all()

    items = []
    for state, kp in rows:
        # 将 0-1 的小数转换为 0-100 的百分制，更直观
        mastery_percentage = round(float(state.mastery) * 100, 1)
        items.append({
            "knowledge_id": kp.id,
            "name": kp.name,
            "mastery": mastery_percentage
        })

    return {"items": items}


@router.get("/student/module-mastery")
async def student_module_mastery(
    subject: str = Query(..., description="科目类型：XINGCE 或 SHENLUN"),
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    获取学生各模块的掌握度聚合数据（用于雷达图）

    Args:
        subject: 科目类型 ("XINGCE" 或 "SHENLUN")
        current_user: 当前学生用户
        db: 数据库会话

    Returns:
        dict: 包含subject和各模块掌握度数据的字典

    Raises:
        HTTPException: 当科目类型无效或查询失败时
    """
    try:
        uid = current_user["id"]

        # 验证subject参数
        if subject not in ["XINGCE", "SHENLUN"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="科目类型必须是 XINGCE 或 SHENLUN"
            )

        # 获取指定科目的模块节点
        from ....services.paper_template import _get_subject_module_nodes, _get_knowledge_point_tree_ids

        module_nodes = _get_subject_module_nodes(db, subject)
        if not module_nodes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到{subject}科目的模块节点"
            )

        items = []

        for module in module_nodes:
            # 获取模块及其所有子知识点的ID
            module_tree_ids = _get_knowledge_point_tree_ids(db, module.id)

            if not module_tree_ids:
                # 如果没有子节点，至少包含模块本身
                module_tree_ids = [module.id]

            # 计算该模块所有知识点的平均掌握度
            avg_stmt = select(func.avg(UserKnowledgeState.mastery)).where(
                UserKnowledgeState.user_id == uid,
                UserKnowledgeState.knowledge_id.in_(module_tree_ids)
            )
            avg_mastery = db.execute(avg_stmt).scalar_one() or 0.0

            # 转换为0-100百分制
            mastery_percentage = round(float(avg_mastery) * 100, 1)

            # 从模块code中提取简写（如XINGCE_CS -> CS, XINGCE_YY -> YY）
            if '_' in module.code:
                parts = module.code.split('_')
                if len(parts) >= 2:
                    module_code_short = parts[1]  # XINGCE_CS -> CS
                else:
                    module_code_short = module.code
            else:
                module_code_short = module.code

            items.append({
                "module": module.name,
                "code": module_code_short,
                "mastery": mastery_percentage
            })

        # 按固定顺序排序：CS, YY, SL, PD, ZL
        if subject == "XINGCE":
            order = {"CS": 0, "YY": 1, "SL": 2, "PD": 3, "ZL": 4}
            items.sort(key=lambda x: order.get(x["code"], 999))
        else:
            # SHENLUN保持原有排序
            items.sort(key=lambda x: x["module"])

        return {
            "subject": subject,
            "items": items
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模块掌握度失败: {str(e)}"
        )


@router.get("/admin/overview")
async def admin_overview(current_user: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    try:
        # total users
        total_users_stmt = select(func.count()).select_from(User)
        total_users = db.execute(total_users_stmt).scalar_one()

        # active users: users with attempts in last 7 days
        since = datetime.utcnow() - timedelta(days=7)
        active_users_stmt = select(func.count(func.distinct(Attempt.user_id))).select_from(Attempt).where(Attempt.submitted_at >= since)
        active_users = db.execute(active_users_stmt).scalar_one()

        # avg completion rate (approx): average of users' active plan completion
        user_stmt = select(User.id)
        user_ids = db.execute(user_stmt).scalars().all()
        rates = []
        for uid in user_ids:
            plan_stmt = select(LearningPlan).where(LearningPlan.user_id == uid, LearningPlan.is_active == True)
            plan = db.execute(plan_stmt).scalar_one_or_none()
            if plan:
                total_stmt = select(func.count()).select_from(PlanItem).where(PlanItem.plan_id == plan.id)
                total = db.execute(total_stmt).scalar_one()
                done_stmt = select(func.count()).select_from(PlanItem).where(PlanItem.plan_id == plan.id, PlanItem.status == "DONE")
                done = db.execute(done_stmt).scalar_one()
                if total > 0:
                    rates.append(done / total)
        avg_completion = round((sum(rates) / len(rates)) * 100, 2) if rates else 0.0

        # avg score recent
        recent_stmt = select(Attempt).where(Attempt.status == "SUBMITTED", Attempt.submitted_at >= since)
        recent_attempts = db.execute(recent_stmt).scalars().all()
        avg_score = round(sum([float(a.total_score or 0) for a in recent_attempts]) / len(recent_attempts), 2) if recent_attempts else 0.0

        # wrong due total
        wrong_stmt = select(func.count()).select_from(WrongQuestion).where(WrongQuestion.next_review_at <= datetime.utcnow())
        wrong_due_total = db.execute(wrong_stmt).scalar_one()

        return {"total_users": total_users, "active_users": active_users, "avg_completion_rate": avg_completion, "avg_score": avg_score, "wrong_due_total": wrong_due_total}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# (No duplicate router or placeholder endpoints - analytics routes defined above)
