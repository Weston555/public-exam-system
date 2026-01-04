from fastapi import APIRouter, Depends, HTTPException, status, Query
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
        plan = db.query(LearningPlan).filter(LearningPlan.user_id == uid, LearningPlan.is_active == True).first()
        plan_completion_rate = 0.0
        if plan:
            total = db.query(PlanItem).filter(PlanItem.plan_id == plan.id).count()
            done = db.query(PlanItem).filter(PlanItem.plan_id == plan.id, PlanItem.status == "DONE").count()
            plan_completion_rate = round((done / total) * 100, 2) if total > 0 else 0.0

        # avg mastery
        avg_mastery = db.query(UserKnowledgeState).filter(UserKnowledgeState.user_id == uid).with_entities(
            UserKnowledgeState.mastery).all()
        avg_mastery_val = 0.0
        if avg_mastery:
            avg_mastery_val = round(sum([float(x[0]) for x in avg_mastery]) / len(avg_mastery), 2)

        # wrong due count
        now = datetime.utcnow()
        wrong_due_count = db.query(WrongQuestion).filter(WrongQuestion.user_id == uid, WrongQuestion.next_review_at <= now).count()

        # last score
        last_attempt = db.query(Attempt).filter(Attempt.user_id == uid, Attempt.status == "SUBMITTED").order_by(Attempt.submitted_at.desc()).first()
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
    tries = db.query(Attempt).filter(Attempt.user_id == uid, Attempt.status == "SUBMITTED").order_by(Attempt.submitted_at.desc()).limit(limit).all()
    items = []
    for a in reversed(tries):
        items.append({"submitted_at": a.submitted_at.isoformat() if a.submitted_at else None, "total_score": float(a.total_score) if a.total_score is not None else None})
    return {"items": items}


@router.get("/student/mastery-top")
async def student_mastery_top(limit: int = Query(10, ge=1), current_user: dict = Depends(get_current_student), db: Session = Depends(get_db)):
    uid = current_user["id"]
    rows = db.query(UserKnowledgeState, KnowledgePoint).join(KnowledgePoint, UserKnowledgeState.knowledge_id == KnowledgePoint.id).filter(UserKnowledgeState.user_id == uid).order_by(UserKnowledgeState.mastery.asc()).limit(limit).all()
    items = []
    for state, kp in rows:
        items.append({"knowledge_id": kp.id, "name": kp.name, "mastery": float(state.mastery)})
    return {"items": items}


@router.get("/admin/overview")
async def admin_overview(current_user: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    try:
        total_users = db.query(User).count()
        # active users: users with attempts in last 7 days
        since = datetime.utcnow() - timedelta(days=7)
        active_users = db.query(Attempt.user_id).filter(Attempt.submitted_at >= since).distinct().count()
        # avg completion rate (approx): average of users' active plan completion
        user_ids = [u.id for u in db.query(User).all()]
        rates = []
        for uid in user_ids:
            plan = db.query(LearningPlan).filter(LearningPlan.user_id == uid, LearningPlan.is_active == True).first()
            if plan:
                total = db.query(PlanItem).filter(PlanItem.plan_id == plan.id).count()
                done = db.query(PlanItem).filter(PlanItem.plan_id == plan.id, PlanItem.status == "DONE").count()
                if total > 0:
                    rates.append(done / total)
        avg_completion = round((sum(rates) / len(rates)) * 100, 2) if rates else 0.0
        # avg score recent
        recent_attempts = db.query(Attempt).filter(Attempt.status == "SUBMITTED", Attempt.submitted_at >= since).all()
        avg_score = round(sum([float(a.total_score or 0) for a in recent_attempts]) / len(recent_attempts), 2) if recent_attempts else 0.0
        wrong_due_total = db.query(WrongQuestion).filter(WrongQuestion.next_review_at <= datetime.utcnow()).count()
        return {"total_users": total_users, "active_users": active_users, "avg_completion_rate": avg_completion, "avg_score": avg_score, "wrong_due_total": wrong_due_total}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

from fastapi import APIRouter

router = APIRouter()


@router.get("/progress")
async def get_learning_progress():
    """获取学习进度"""
    return {
        "plan_completion_rate": 0.0,
        "average_mastery": 0.0,
        "wrong_questions_count": 0
    }
