from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel

from ....core.database import get_db
from ....models.progress import WrongQuestion
from ....models.question import Question
from ....models.knowledge import QuestionKnowledgeMap, KnowledgePoint
from ..deps import get_current_student

router = APIRouter()


@router.get("/")
async def list_wrong_questions(
    due_only: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    获取错题本（可仅返回到期复习项）
    """
    try:
        stmt = select(WrongQuestion).where(WrongQuestion.user_id == current_user["id"])
        if due_only:
            stmt = stmt.where(WrongQuestion.next_review_at <= datetime.utcnow())

        # 获取总数
        count_stmt = stmt.with_only_columns(WrongQuestion.id)
        total = db.execute(count_stmt).scalars().count()

        # 获取分页数据
        items = db.execute(stmt.order_by(WrongQuestion.next_review_at).offset((page - 1) * size).limit(size)).scalars().all()

        result = []
        for w in items:
            # question basic info (without correct answer)
            question = db.query(Question).filter(Question.id == w.question_id).first()
            # knowledge points
            kps = db.query(QuestionKnowledgeMap).filter(QuestionKnowledgeMap.question_id == w.question_id).all()
            kp_names = []
            for km in kps:
                kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == km.knowledge_id).first()
                if kp:
                    kp_names.append({"id": kp.id, "name": kp.name})

            result.append({
                "question_id": w.question_id,
                "stem": question.stem if question else "",
                "type": question.type if question else None,
                "options_json": question.options_json if question else None,
                "wrong_count": w.wrong_count,
                "last_wrong_at": w.last_wrong_at.isoformat() if w.last_wrong_at else None,
                "next_review_at": w.next_review_at.isoformat() if w.next_review_at else None,
                "knowledge_points": kp_names
            })

        return {"items": result, "total": total, "page": page, "size": size}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"查询错题本失败: {e}")


class ReviewGenerateRequest(BaseModel):
    count: int = 10


@router.post("/review/generate")
async def generate_review_exam(
    request: ReviewGenerateRequest,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    生成到期复习的考试（从到期错题中抽取）
    """
    try:
        # 查询到期错题
        now = datetime.utcnow()
        due_q_stmt = select(WrongQuestion).where(
            WrongQuestion.user_id == current_user["id"],
            WrongQuestion.next_review_at <= now
        ).order_by(WrongQuestion.next_review_at).limit(request.count)
        due_q = db.execute(due_q_stmt).scalars().all()

        if not due_q:
            raise HTTPException(status_code=400, detail="暂无到期复习的错题")

        question_ids = [w.question_id for w in due_q]

        # 生成 Paper + PaperQuestion
        from ....models.paper import Paper, PaperQuestion, Exam
        paper = Paper(
            title=f"REVIEW_{current_user['id']}_{int(now.timestamp())}",
            mode="AUTO",
            config_json={"type": "review", "source": "wrong_questions"},
            total_score=float(len(question_ids) * 2.0),
            created_by=current_user["id"]
        )
        db.add(paper)
        db.flush()

        order_no = 1
        for qid in question_ids:
            pq = PaperQuestion(paper_id=paper.id, question_id=qid, order_no=order_no, score=2.0)
            db.add(pq)
            order_no += 1

        # 创建 Exam，复用 PRACTICE 类别并在 title 标注 REVIEW
        exam = Exam(
            paper_id=paper.id,
            title=f"到期复习 - {current_user['id']}",
            category="PRACTICE",
            duration_minutes=0,
            status="PUBLISHED",
            created_by=current_user["id"]
        )
        db.add(exam)

        # 更新选中的 WrongQuestion 的 next_review_at（延后）
        for w in due_q:
            # simple exponential schedule already applied when created; advance next_review_at based on wrong_count
            from datetime import timedelta
            intervals = [1, 3, 7, 14, 30]
            idx = min(w.wrong_count, len(intervals)) - 1
            w.next_review_at = datetime.utcnow() + timedelta(days=intervals[idx])

        db.commit()
        db.refresh(exam)

        return {"exam_id": exam.id, "paper_id": paper.id, "count": len(question_ids)}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"生成复习试卷失败: {e}")


