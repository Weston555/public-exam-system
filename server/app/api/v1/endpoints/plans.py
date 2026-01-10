from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, datetime, timedelta
from typing import Dict, Any
import json
import random

from ....core.database import get_db
from ....models.plan import Goal, LearningPlan, PlanItem
from ....models.attempt import Attempt
from ....models.question import Question
from ....models.knowledge import QuestionKnowledgeMap
from ....models.progress import UserKnowledgeState, WrongQuestion
from ....models.paper import Paper, PaperQuestion, Exam
from ....services.recommendation import generate_learning_plan
from ....services.exam_runtime import start_exam_for_user
from ..deps import get_current_student

router = APIRouter()


def generate_practice_exam(db: Session, user_id: int, knowledge_id: int, count: int = 10, mode: str = "ADAPTIVE") -> Exam:
    """生成专项练习考试（抽取自practice.py逻辑）"""
    count = max(1, int(count))
    mode = (mode or "ADAPTIVE").upper()

    # 获取符合知识点的题目
    stmt = select(Question.id, Question.difficulty).join(
        QuestionKnowledgeMap, Question.id == QuestionKnowledgeMap.question_id
    ).where(QuestionKnowledgeMap.knowledge_id == knowledge_id)

    candidates = db.execute(stmt).all()
    if not candidates:
        raise HTTPException(status_code=400, detail="所选知识点暂无题目")

    # 按难度分组题目
    by_diff = {}
    for q in candidates:
        by_diff.setdefault(q.difficulty, []).append(q.id)

    # 选题策略
    def pick_questions(target_diff, need):
        picked = []
        diff = target_diff
        while len(picked) < need and diff >= 1:
            pool = by_diff.get(diff, [])
            remaining = [pid for pid in pool if pid not in picked]
            take = min(len(remaining), need - len(picked))
            if take > 0:
                picked.extend(random.sample(remaining, take))
            diff -= 1
        return picked

    # 获取用户掌握度
    state_stmt = select(UserKnowledgeState).where(
        UserKnowledgeState.user_id == user_id,
        UserKnowledgeState.knowledge_id == knowledge_id
    )
    state = db.execute(state_stmt).scalar_one_or_none()
    mastery = float(state.mastery) if state and state.mastery is not None else 0.0

    # 根据掌握度确定目标难度
    if mode == "ADAPTIVE":
        if mastery < 0.3:
            target = 2
        elif mastery < 0.6:
            target = 3
        else:
            target = 4
    else:
        target = 3

    selected = pick_questions(target, count)

    # 如果还不够，从所有题目中补充
    all_ids = [q.id for q in candidates]
    remaining_pool = [pid for pid in all_ids if pid not in selected]
    if len(selected) < count and remaining_pool:
        need = count - len(selected)
        selected.extend(random.sample(remaining_pool, min(need, len(remaining_pool))))

    if not selected:
        raise HTTPException(status_code=400, detail="无法为该知识点抽题")

    # 创建Paper
    paper = Paper(
        title=f"PRACTICE_KP_{knowledge_id}_{user_id}",
        mode="AUTO",
        config_json={
            "knowledge_id": knowledge_id,
            "count": count,
            "mode": mode,
            "mastery": mastery,
            "target_diff": target
        },
        total_score=float(len(selected) * 2.0),
        created_by=user_id
    )
    db.add(paper)
    db.flush()

    # 创建PaperQuestion
    order_no = 1
    for qid in selected:
        pq = PaperQuestion(
            paper_id=paper.id,
            question_id=qid,
            order_no=order_no,
            score=2.0
        )
        db.add(pq)
        order_no += 1

    # 创建Exam
    exam = Exam(
        paper_id=paper.id,
        title=f"专项练习 - 知识点 {knowledge_id}",
        category="PRACTICE",
        duration_minutes=0,
        status="PUBLISHED",
        created_by=user_id
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    return exam


def generate_review_exam(db: Session, user_id: int, count: int = 10) -> Exam:
    """生成复习考试（抽取自wrong_questions.py逻辑）"""
    now = datetime.utcnow()

    # 查询到期错题
    due_q_stmt = select(WrongQuestion).where(
        WrongQuestion.user_id == user_id,
        WrongQuestion.next_review_at <= now
    ).order_by(WrongQuestion.next_review_at).limit(count)

    due_q = db.execute(due_q_stmt).scalars().all()

    if not due_q:
        raise HTTPException(status_code=400, detail="暂无到期复习的错题")

    question_ids = [w.question_id for w in due_q]

    # 创建Paper
    paper = Paper(
        title=f"REVIEW_{user_id}_{int(now.timestamp())}",
        mode="AUTO",
        config_json={"type": "review", "source": "wrong_questions"},
        total_score=float(len(question_ids) * 2.0),
        created_by=user_id
    )
    db.add(paper)
    db.flush()

    # 创建PaperQuestion
    order_no = 1
    for qid in question_ids:
        pq = PaperQuestion(paper_id=paper.id, question_id=qid, order_no=order_no, score=2.0)
        db.add(pq)
        order_no += 1

    # 创建Exam
    exam = Exam(
        paper_id=paper.id,
        title=f"到期复习 - {user_id}",
        category="REVIEW",
        duration_minutes=0,
        status="PUBLISHED",
        created_by=user_id
    )
    db.add(exam)

    # 更新WrongQuestion的next_review_at
    for w in due_q:
        intervals = [1, 3, 7, 14, 30]
        idx = min(w.wrong_count, len(intervals)) - 1
        w.next_review_at = datetime.utcnow() + timedelta(days=intervals[idx])

    db.commit()
    db.refresh(exam)

    return exam


class PlanGenerateRequest(BaseModel):
    days: int = 14  # 默认14天


class PlanItemCompleteRequest(BaseModel):
    status: str  # "DONE" or "SKIPPED"


class PlanItemStartResponse(BaseModel):
    action: str  # "EXAM" or "NAVIGATE"
    attempt_id: int = None
    path: str = None


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
    ).order_by(LearningPlan.created_at.desc()).limit(1)
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
            "exam_id": item.exam_id,
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


@router.post("/items/{item_id}/start")
async def start_plan_item(
    item_id: int,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
) -> PlanItemStartResponse:
    """
    开始计划项任务（生成考试并开始答题）
    """
    try:
        # 验证计划项存在且属于当前用户
        item_stmt = select(PlanItem).where(
            PlanItem.id == item_id,
            PlanItem.plan_id.in_(
                select(LearningPlan.id).where(
                    LearningPlan.user_id == current_user["id"],
                    LearningPlan.is_active == True
                )
            )
        )
        item = db.execute(item_stmt).scalar_one_or_none()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="计划项不存在"
            )

        if item.status != "TODO":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该任务已完成或已跳过"
            )

        # 根据类型处理
        if item.type in ["PRACTICE", "REVIEW"]:
            # 生成或复用考试
            if not item.exam_id:
                # 生成新考试
                if item.type == "PRACTICE":
                    exam = generate_practice_exam(
                        db, current_user["id"], item.knowledge_id, count=10, mode="ADAPTIVE"
                    )
                else:  # REVIEW
                    exam = generate_review_exam(db, current_user["id"], count=10)

                # 更新计划项的exam_id
                item.exam_id = exam.id
                db.commit()
            else:
                # 使用现有考试
                exam_stmt = select(Exam).where(Exam.id == item.exam_id)
                exam = db.execute(exam_stmt).scalar_one_or_none()
                if not exam:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="关联的考试不存在"
                    )

            # 检查是否已有进行中的attempt
            attempt_stmt = select(Attempt).where(
                Attempt.exam_id == exam.id,
                Attempt.user_id == current_user["id"],
                Attempt.status == "DOING"
            )
            existing_attempt = db.execute(attempt_stmt).scalar_one_or_none()

            if existing_attempt:
                # 返回现有的attempt
                return PlanItemStartResponse(
                    action="EXAM",
                    attempt_id=existing_attempt.id
                )

            # 创建新的attempt
            attempt = Attempt(
                exam_id=exam.id,
                user_id=current_user["id"],
                started_at=datetime.utcnow(),
                status="DOING"
            )
            db.add(attempt)
            db.commit()
            db.refresh(attempt)

            return PlanItemStartResponse(
                action="EXAM",
                attempt_id=attempt.id
            )

        elif item.type == "LEARN":
            # 学习任务，跳转到学习页面
            return PlanItemStartResponse(
                action="NAVIGATE",
                path="/practice"  # 或 "/knowledge"
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的任务类型: {item.type}"
            )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"开始任务失败: {str(e)}"
        )


@router.post("/items/{item_id}/start")
async def start_plan_item(
    item_id: int,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
) -> PlanItemStartResponse:
    """
    开始计划项任务（生成考试并开始答题）
    """
    try:
        # 验证计划项存在且属于当前用户
        item_stmt = select(PlanItem).where(
            PlanItem.id == item_id,
            PlanItem.plan_id.in_(
                select(LearningPlan.id).where(
                    LearningPlan.user_id == current_user["id"],
                    LearningPlan.is_active == True
                )
            )
        )
        item = db.execute(item_stmt).scalar_one_or_none()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="计划项不存在"
            )

        if item.status != "TODO":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该任务已完成或已跳过"
            )

        # 根据类型处理
        if item.type in ["PRACTICE", "REVIEW"]:
            # 生成或复用考试
            if not item.exam_id:
                # 生成新考试
                if item.type == "PRACTICE":
                    exam = generate_practice_exam(
                        db, current_user["id"], item.knowledge_id, count=10, mode="ADAPTIVE"
                    )
                else:  # REVIEW
                    exam = generate_review_exam(db, current_user["id"], count=10)

                # 更新计划项的exam_id
                item.exam_id = exam.id
                db.commit()
            else:
                # 使用现有考试
                exam_stmt = select(Exam).where(Exam.id == item.exam_id)
                exam = db.execute(exam_stmt).scalar_one_or_none()
                if not exam:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="关联的考试不存在"
                    )

            # 开始考试
            return start_exam_for_user(db, exam.id, current_user["id"])

        elif item.type == "LEARN":
            # 学习任务，跳转到学习页面
            return PlanItemStartResponse(
                action="NAVIGATE",
                path="/practice"  # 或 "/knowledge"
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的任务类型: {item.type}"
            )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"开始任务失败: {str(e)}"
        )
